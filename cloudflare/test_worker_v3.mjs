import worker from './worker_v3_hardened.mjs';

class KV {
  constructor(init={}) { this.m = new Map(Object.entries(init)); this.puts=[]; }
  async get(k) { return this.m.has(k) ? this.m.get(k) : null; }
  async put(k,v,opts) { this.m.set(k,v); this.puts.push({k,v,opts}); }
}

let mode = 'OPEN';
let failCode = null;
let githubWrites = [];
globalThis.fetch = async function(input, init={}) {
  const u = new URL(typeof input === 'string' ? input : input.url);

  if (u.hostname === 'polling.finance.naver.com') {
    const q = decodeURIComponent(u.searchParams.get('query') || '');
    if (q.startsWith('SERVICE_INDEX:')) {
      return new Response(JSON.stringify({
        result:{areas:[{datas:[
          {cd:'KOSPI',nv:'3000',cv:'10',cr:'0.3',ov:'2990',hv:'3010',lv:'2980',aq:'1',aa:'2',ms:mode},
          {cd:'KOSDAQ',nv:'900',cv:'5',cr:'0.5',ov:'895',hv:'905',lv:'890',aq:'3',aa:'4',ms:mode}
        ]}]}
      }), {status:200,headers:{'Content-Type':'application/json'}});
    }

    const code = q.split(':')[1];
    if (code === failCode) throw new Error('simulated upstream failure');
    return new Response(JSON.stringify({
      result:{pollingInterval:1000,areas:[{datas:[{
        cd:code,nm:`N${code}`,nv:'1000',sv:'990',cv:'10',cr:'1.01',ov:'995',hv:'1010',lv:'990',aq:'12345',aa:'67890',ms:mode,
        nxtOverMarketPriceInfo:{localTradedAt:'2026-09-24T09:00:00+09:00'}
      }]}]}
    }), {status:200,headers:{'Content-Type':'application/json'}});
  }

  if (u.hostname === 'm.stock.naver.com') {
    const sortType=u.searchParams.get('sortType');
    const category=u.searchParams.get('category');
    const base = category==='KOSPI' ? 0 : 100;
    const rows = sortType==='quantTop'
      ? [
          {itemCode:String(base+1).padStart(6,'0'),stockName:`Q${category}1`,closePrice:'1000',fluctuationsRatio:'1.2',accumulatedTradingVolume:'500000',accumulatedTradingValue:'60000000000'},
          {itemCode:String(base+2).padStart(6,'0'),stockName:`Q${category}2`,closePrice:'2000',fluctuationsRatio:'2.2',accumulatedTradingVolume:'400000',accumulatedTradingValue:'50000000000'}
        ]
      : [
          {itemCode:String(base+3).padStart(6,'0'),stockName:`U${category}1`,closePrice:'3000',fluctuationsRatio:'12.5',accumulatedTradingVolume:'300000',accumulatedTradingValue:'70000000000'},
          {itemCode:String(base+4).padStart(6,'0'),stockName:`U${category}2`,closePrice:'4000',fluctuationsRatio:'9.5',accumulatedTradingVolume:'250000',accumulatedTradingValue:'45000000000'}
        ];
    return new Response(JSON.stringify({result:{stocks:rows}}), {status:200,headers:{'Content-Type':'application/json'}});
  }

  if (u.hostname === 'api.github.com') {
    if ((init.method || 'GET') === 'GET') {
      return new Response(JSON.stringify({sha:'old-live-sha'}), {status:200,headers:{'Content-Type':'application/json'}});
    }
    if (init.method === 'PUT') {
      const body = JSON.parse(init.body);
      githubWrites.push(body);
      return new Response(JSON.stringify({commit:{sha:'new-live-commit'}}), {status:200,headers:{'Content-Type':'application/json'}});
    }
  }

  throw new Error('unexpected fetch '+u);
};

function assert(cond,msg){ if(!cond) throw new Error('ASSERT: '+msg); }
const sched = Date.parse('2026-09-24T00:00:00Z');

// 1) Closed/holiday payload must not create minute/latest keys.
{
  mode='CLOSE'; failCode=null;
  const kv=new KV({watchlist:JSON.stringify(['000001','000002'])});
  await worker.scheduled({scheduledTime:sched},{STOCK_KV:kv,WRITE_TOKEN:'secret'});
  assert(!kv.m.has('minute:20260924:0900'),'closed market wrote minute key');
  assert(!kv.m.has('latest_minute'),'closed market overwrote latest');
}

// 2) Open market writes both minute and latest with PASS guard.
{
  mode='OPEN'; failCode=null;
  const kv=new KV({watchlist:JSON.stringify(['000001','000002'])});
  await worker.scheduled({scheduledTime:sched},{STOCK_KV:kv,WRITE_TOKEN:'secret'});
  assert(kv.m.has('minute:20260924:0900'),'open market missing minute');
  assert(kv.m.has('latest_minute'),'open market missing latest');
  const row=JSON.parse(kv.m.get('minute:20260924:0900'));
  assert(row.guard.openRatio===1,'open ratio not recorded');
  assert(Object.keys(row.stocks).length===2,'stock payload missing');
}

// 3) Upstream degradation below 80% valid payload fails closed.
{
  mode='OPEN'; failCode='000002';
  const kv=new KV({watchlist:JSON.stringify(['000001','000002'])});
  await worker.scheduled({scheduledTime:sched},{STOCK_KV:kv,WRITE_TOKEN:'secret'});
  assert(!kv.m.has('minute:20260924:0900'),'degraded payload wrote minute');
  assert(!kv.m.has('latest_minute'),'degraded payload overwrote latest');
  failCode=null;
}

// 4) Watchlist mutation: GET blocked; POST without token blocked; POST with token succeeds.
{
  mode='OPEN';
  const kv=new KV({watchlist:JSON.stringify(['000001'])});
  let res=await worker.fetch(new Request('https://x/watchlist?codes=000002',{method:'GET'}),{STOCK_KV:kv,WRITE_TOKEN:'secret'});
  assert(res.status===405,'mutating GET not blocked');
  res=await worker.fetch(new Request('https://x/watchlist?codes=000002',{method:'POST'}),{STOCK_KV:kv,WRITE_TOKEN:'secret'});
  assert(res.status===401,'unauthenticated POST not blocked');
  res=await worker.fetch(new Request('https://x/watchlist?codes=000002',{method:'POST',headers:{Authorization:'Bearer secret'}}),{STOCK_KV:kv,WRITE_TOKEN:'secret'});
  assert(res.status===200,'authenticated POST failed');
  const body=await res.json();
  assert(body.status==='WATCHLIST_SAVED','wrong save status');
  assert(kv.m.get('watchlist')===JSON.stringify(['000002']),'watchlist not saved');
}

// 5) Public read remains available.
{
  const kv=new KV({watchlist:JSON.stringify(['000001'])});
  const res=await worker.fetch(new Request('https://x/watchlist'),{STOCK_KV:kv,WRITE_TOKEN:'secret'});
  assert(res.status===200,'read-only watchlist unavailable');
  const body=await res.json();
  assert(body.codes[0]==='000001','read-only watchlist incorrect');
}

// 6) run-now is protected and also fails closed on closed market.
{
  mode='CLOSE';
  const kv=new KV({watchlist:JSON.stringify(['000001','000002'])});
  let res=await worker.fetch(new Request('https://x/run-now',{method:'POST'}),{STOCK_KV:kv,WRITE_TOKEN:'secret'});
  assert(res.status===401,'run-now unauthenticated not blocked');
  res=await worker.fetch(new Request('https://x/run-now',{method:'POST',headers:{Authorization:'Bearer secret'}}),{STOCK_KV:kv,WRITE_TOKEN:'secret'});
  assert(res.status===409,'closed run-now should skip');
  assert(!kv.m.has('latest_minute'),'closed run-now overwrote latest');
}


function minuteRow(date, minute, codes=['000001','000002']) {
  const stocks = {};
  for (const [i,code] of codes.entries()) {
    stocks[code] = {
      code,
      name: `N${code}`,
      currentPrice: 1000 + i + minute,
      volume: 10000 + minute,
      tradingValue: 100000 + minute,
      marketStatus: 'OPEN'
    };
  }
  return {atKst: `${date} 09${String(minute).padStart(2,'0')}`, guard:{openRatio:1}, stocks};
}

// 7) 09:35 with a complete minute chain publishes a versioned live.json snapshot.
{
  mode='OPEN'; failCode=null; githubWrites=[];
  const init={watchlist:JSON.stringify(['000001','000002'])};
  for(let m=0;m<35;m++) init[`minute:20260924:09${String(m).padStart(2,'0')}`] = JSON.stringify(minuteRow('20260924',m));
  init['market_scan:20260924:0930']=JSON.stringify({
    status:'PASS', atKst:'20260924 0930',
    coverage:{requestedConfigs:4,successfulConfigs:4,failedConfigs:0,rowCount:4},
    rankings:[],
    volumeTop:[{code:'000001',name:'QKOSPI1',price:990,changePct:1,volume:450000,tradingValue:50000000000}],
    turnoverTop:[{code:'000003',name:'UKOSPI1',price:2900,changePct:10,volume:250000,tradingValue:60000000000}],
    risingLiquid:[{code:'000003',name:'UKOSPI1',price:2900,changePct:10,volume:250000,tradingValue:60000000000}]
  });
  const kv=new KV(init);
  await worker.scheduled(
    {scheduledTime:Date.parse('2026-09-24T00:35:00Z')},
    {STOCK_KV:kv,WRITE_TOKEN:'secret',GITHUB_PUBLISH_TOKEN:'gh-token'}
  );
  assert(githubWrites.length===1,'09:35 did not publish live.json');
  const req=githubWrites[0];
  assert(req.sha==='old-live-sha','publisher did not preserve live.json sha');
  const payload=JSON.parse(Buffer.from(req.content,'base64').toString('utf8'));
  assert(payload.tradeDate==='20260924','wrong published tradeDate');
  assert(payload.history.count===36,'wrong 09:35 history count');
  assert(payload.history.from==='20260924 0900','wrong history start');
  assert(payload.history.to==='20260924 0935','wrong history end');
  assert(payload.latest.atKst==='20260924 0935','wrong latest minute');
  assert(payload.watchlist.join(',')==='000001,000002','wrong published watchlist');
  assert(payload.publisher.type==='CLOUDFLARE_WORKER_GITHUB_CONTENTS_API','publisher identity missing');
  assert(payload.scan.status==='PASS','market scan did not publish PASS');
  assert(payload.scan.turnoverTop.length>0,'turnoverTop missing');
  assert(payload.scan.turnoverTop[0].tradingValue!=null,'turnover money missing');
  assert(payload.scanDelta && payload.scanDelta.comparedCount>0,'scan delta missing');
  assert(payload.scanDelta.turnoverAcceleration.some(x=>x.deltaTradingValue>0),'turnover acceleration missing');
  const ps=JSON.parse(kv.m.get('last_publish_status'));
  assert(ps.status==='PASS' && ps.commitSha==='new-live-commit','publish status not recorded');
}

// 8) 09:35 refuses to publish a discontinuous/incomplete minute chain.
{
  mode='OPEN'; failCode=null; githubWrites=[];
  const kv=new KV({
    watchlist:JSON.stringify(['000001','000002']),
    'minute:20260924:0900':JSON.stringify(minuteRow('20260924',0))
  });
  let threw=false;
  try {
    await worker.scheduled(
      {scheduledTime:Date.parse('2026-09-24T00:35:00Z')},
      {STOCK_KV:kv,WRITE_TOKEN:'secret',GITHUB_PUBLISH_TOKEN:'gh-token'}
    );
  } catch (e) {
    threw=true;
    assert(String(e.message).includes('INCOMPLETE_PUBLISH_HISTORY'),'unexpected incomplete-history error');
  }
  assert(threw,'incomplete history did not fail publisher');
  assert(githubWrites.length===0,'incomplete history was published');
  assert(kv.m.has('minute:20260924:0935'),'valid minute capture should survive publisher failure');
  const ps=JSON.parse(kv.m.get('last_publish_status'));
  assert(ps.status==='FAIL','publisher failure status missing');
}

// 9) /scan preserves money-aware rise/volume/turnover rankings.
{
  mode='OPEN'; failCode=null;
  const kv=new KV({});
  const res=await worker.fetch(new Request('https://x/scan'),{STOCK_KV:kv,WRITE_TOKEN:'secret'});
  assert(res.status===200,'scan endpoint failed');
  const body=await res.json();
  assert(body.status==='PASS','scan status not PASS');
  assert(body.volumeTop.length>0 && body.turnoverTop.length>0 && body.risingLiquid.length>0,'scan rankings missing');
  assert(body.turnoverTop[0].tradingValue!=null,'scan tradingValue missing');
  assert(body.volumeTop[0].volume!=null,'scan volume missing');
  assert(body.coverage.successfulConfigs===4,'scan coverage incomplete');
}

// 10) Root endpoint must expose the exact deployable build fingerprint.
{
  const kv=new KV({});
  const res=await worker.fetch(new Request('https://x/'),{STOCK_KV:kv,WRITE_TOKEN:'secret'});
  assert(res.status===200,'root endpoint failed');
  const body=await res.json();
  assert(body.build==='worker_v3_hardened_money_scan_v1','wrong build fingerprint');
  assert(body.capabilities.includes('MONEY_AWARE_MARKET_SCAN'),'money scan capability missing');
  assert(body.capabilities.includes('GITHUB_LIVE_PUBLISHER'),'publisher capability missing');
}

console.log('ALL_TESTS_PASS');
