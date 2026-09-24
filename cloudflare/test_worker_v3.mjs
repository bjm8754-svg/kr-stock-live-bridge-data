import worker from './worker_v3_hardened.mjs';

class KV {
  constructor(init={}) { this.m = new Map(Object.entries(init)); this.puts=[]; }
  async get(k) { return this.m.has(k) ? this.m.get(k) : null; }
  async put(k,v,opts) { this.m.set(k,v); this.puts.push({k,v,opts}); }
}

let mode = 'OPEN';
let failCode = null;
globalThis.fetch = async function(input, init={}) {
  const u = new URL(typeof input === 'string' ? input : input.url);
  if (u.hostname === 'polling.finance.naver.com') {
    const q = decodeURIComponent(u.searchParams.get('query') || '');
    const code = q.split(':')[1];
    if (code === failCode) throw new Error('simulated upstream failure');
    const ms = mode;
    return new Response(JSON.stringify({
      result:{pollingInterval:1000,areas:[{datas:[{
        cd:code,nm:`N${code}`,nv:'1000',sv:'990',cv:'10',cr:'1.01',ov:'995',hv:'1010',lv:'990',aq:'12345',aa:'67890',ms,
        nxtOverMarketPriceInfo:{localTradedAt:'2026-09-24T09:00:00+09:00'}
      }]}]}
    }), {status:200,headers:{'Content-Type':'application/json'}});
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

console.log('ALL_TESTS_PASS');
