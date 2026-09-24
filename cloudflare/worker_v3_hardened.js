const SOURCE = "NAVER_PUBLIC_WEB_ENDPOINT";

export default {
  async scheduled(controller, env) {
    const kst = new Date(controller.scheduledTime + 9 * 60 * 60 * 1000);
    const day = kst.getUTCDay();
    const hhmm = kst.getUTCHours() * 100 + kst.getUTCMinutes();

    // Scheduler-level guard: weekdays 09:00~09:40 KST only.
    // Exchange holidays are additionally blocked by the semantic market-status guard below.
    if (day === 0 || day === 6 || hhmm < 900 || hhmm > 940) return;

    const saved = await env.STOCK_KV.get("watchlist");
    if (!saved) return;

    const codes = normalizeSavedCodes(saved);
    if (!codes.length) return;

    const capture = await buildGuardedCapture(codes, kst);
    if (capture.status !== "PASS") {
      // Fail closed: do not create a minute key or replace latest_minute with stale/closed data.
      return;
    }

    await env.STOCK_KV.put(
      `minute:${capture.date}:${capture.time}`,
      JSON.stringify(capture.data),
      { expirationTtl: 604800 }
    );

    await env.STOCK_KV.put(
      "latest_minute",
      JSON.stringify(capture.data)
    );
  },

  async fetch(request, env) {
    const url = new URL(request.url);

    try {
      if (url.pathname === "/kv-test") {
        if (request.method !== "POST") return methodNotAllowed(["POST"]);
        if (!isAuthorizedWrite(request, env)) return unauthorized();

        await env.STOCK_KV.put("ping", new Date().toISOString());
        const value = await env.STOCK_KV.get("ping");
        return json({ status: "KV_OK", value });
      }

      if (url.pathname === "/watchlist") {
        const codes = parseCodes(url.searchParams.get("codes"));

        // Read-only watchlist lookup remains public.
        if (!codes.length) {
          if (request.method !== "GET" && request.method !== "HEAD") {
            return methodNotAllowed(["GET", "HEAD"]);
          }
          const saved = await env.STOCK_KV.get("watchlist");
          return json({
            status: "OK",
            codes: saved ? normalizeSavedCodes(saved) : []
          });
        }

        // Mutating the watchlist requires POST + a shared Worker secret.
        if (request.method !== "POST") return methodNotAllowed(["POST"]);
        if (!isAuthorizedWrite(request, env)) return unauthorized();

        await env.STOCK_KV.put("watchlist", JSON.stringify(codes));
        return json({ status: "WATCHLIST_SAVED", codes });
      }

      if (url.pathname === "/run-now") {
        if (request.method !== "POST") return methodNotAllowed(["POST"]);
        if (!isAuthorizedWrite(request, env)) return unauthorized();

        const saved = await env.STOCK_KV.get("watchlist");
        const codes = saved ? normalizeSavedCodes(saved) : [];
        if (!codes.length) return json({ status: "SKIPPED", reason: "EMPTY_WATCHLIST" }, 409);

        const kst = new Date(Date.now() + 9 * 60 * 60 * 1000);
        const capture = await buildGuardedCapture(codes, kst);
        if (capture.status !== "PASS") {
          return json({
            status: "SKIPPED",
            reason: capture.reason,
            guard: capture.guard
          }, 409);
        }

        await env.STOCK_KV.put("latest_minute", JSON.stringify(capture.data));
        return json({ status: "SAVED", data: capture.data });
      }

      if (url.pathname === "/latest") {
        const saved = await env.STOCK_KV.get("latest_minute");
        return json({ status: "OK", data: saved ? JSON.parse(saved) : null });
      }

      if (url.pathname === "/history") {
        const now = new Date(Date.now() + 9 * 60 * 60 * 1000);
        const date =
          url.searchParams.get("date") ||
          String(now.getUTCFullYear()) +
          String(now.getUTCMonth() + 1).padStart(2, "0") +
          String(now.getUTCDate()).padStart(2, "0");

        if (!/^\d{8}$/.test(date)) {
          return json({ error: "date=YYYYMMDD 형식이 필요합니다." }, 400);
        }

        const keys = [];
        for (let m = 0; m <= 40; m++) {
          const time = "09" + String(m).padStart(2, "0");
          keys.push(`minute:${date}:${time}`);
        }

        const values = await Promise.all(keys.map(key => env.STOCK_KV.get(key)));
        const rows = values.filter(Boolean).map(v => JSON.parse(v));

        return json({ status: "OK", date, count: rows.length, rows });
      }
      if (url.pathname === "/") {
        return json({
          status: "OK",
          message: "KR Stock Live Bridge V2",
          endpoints: {
            live: "/live?codes=295310,064400",
            chart: "/chart?code=295310",
            technical: "/technical?code=295310",
            scan: "/scan"
          }
        });
      }

      if (url.pathname === "/live") {
        const codes = parseCodes(url.searchParams.get("codes"));

        if (!codes.length) {
          return json({
            error: "codes=6자리종목코드,6자리종목코드 형식이 필요합니다."
          }, 400);
        }

        const stocks = {};
        const results = await Promise.all(
          codes.map(code => getLiveStock(code))
        );

        for (const r of results) {
          stocks[r.code] = r;
        }

        const indexes = await getIndexes();

        return json({
          checkedAtUtc: new Date().toISOString(),
          source: SOURCE,
          requestedCodes: codes,
          stocks,
          indexes
        });
      }

      if (url.pathname === "/chart") {
        const code = validateCode(url.searchParams.get("code"));

        if (!code) {
          return json({
            error: "code=6자리 종목코드가 필요합니다."
          }, 400);
        }

        const [day, week] = await Promise.all([
          getLegacyChart(code, "day", 320),
          getLegacyChart(code, "week", 160)
        ]);

        return json({
          checkedAtUtc: new Date().toISOString(),
          source: SOURCE,
          code,
          day,
          week
        });
      }

      if (url.pathname === "/technical") {
        const code = validateCode(url.searchParams.get("code"));

        if (!code) {
          return json({
            error: "code=6자리 종목코드가 필요합니다."
          }, 400);
        }

        const day = await getLegacyChart(code, "day", 320);
        const technical = buildTechnical(day);

        return json({
          checkedAtUtc: new Date().toISOString(),
          source: SOURCE,
          code,
          bars: day.length,
          technical
        });
      }

      if (url.pathname === "/scan") {
        const scan = await getMarketScan();

        return json({
          checkedAtUtc: new Date().toISOString(),
          source: SOURCE,
          ...scan
        });
      }

      return json({ error: "Not Found" }, 404);

    } catch (e) {
      return json({
        status: "ERROR",
        message: String(e?.message || e)
      }, 500);
    }
  }
};


function normalizeSavedCodes(saved) {
  try {
    const parsed = JSON.parse(saved);
    if (!Array.isArray(parsed)) return [];
    return parsed.map(validateCode).filter(Boolean).slice(0, 20);
  } catch {
    return [];
  }
}

function isAuthorizedWrite(request, env) {
  const expected = String(env?.WRITE_TOKEN || "");
  if (!expected) return false;
  const auth = request.headers.get("Authorization") || "";
  return auth === `Bearer ${expected}`;
}

function unauthorized() {
  return json({ status: "UNAUTHORIZED" }, 401, {
    "WWW-Authenticate": 'Bearer realm="kr-stock-live-bridge"'
  });
}

function methodNotAllowed(allowed) {
  return json({ status: "METHOD_NOT_ALLOWED", allowed }, 405, {
    "Allow": allowed.join(", ")
  });
}

async function buildGuardedCapture(codes, kst) {
  const settled = await Promise.allSettled(codes.map(code => getLiveStock(code)));
  const results = [];
  for (const item of settled) {
    if (item.status === "fulfilled" && item.value && !item.value.error) {
      results.push(item.value);
    }
  }

  const validCount = results.length;
  const requestedCount = codes.length;
  const validRatio = requestedCount ? validCount / requestedCount : 0;
  const openCount = results.filter(r => r.marketStatus === "OPEN").length;
  const openRatio = validCount ? openCount / validCount : 0;

  const guard = {
    requestedCount,
    validCount,
    validRatio: Number(validRatio.toFixed(4)),
    openCount,
    openRatio: Number(openRatio.toFixed(4))
  };

  // Fail closed on data-source degradation or a closed/stale market snapshot.
  // A suspended/exceptional individual stock is tolerated; a majority-closed payload is not.
  if (validCount === 0 || validRatio < 0.8) {
    return { status: "FAIL", reason: "INSUFFICIENT_VALID_PAYLOAD", guard };
  }
  if (openRatio < 0.5) {
    return { status: "FAIL", reason: "MARKET_CLOSED_OR_STALE", guard };
  }

  const stocks = {};
  for (const r of results) stocks[r.code] = r;

  const date =
    String(kst.getUTCFullYear()) +
    String(kst.getUTCMonth() + 1).padStart(2, "0") +
    String(kst.getUTCDate()).padStart(2, "0");
  const time =
    String(kst.getUTCHours()).padStart(2, "0") +
    String(kst.getUTCMinutes()).padStart(2, "0");

  return {
    status: "PASS",
    date,
    time,
    guard,
    data: {
      atKst: `${date} ${time}`,
      guard,
      stocks
    }
  };
}

function parseCodes(raw) {
  if (!raw) return [];

  const out = [];

  for (const s of raw.split(",")) {
    const c = validateCode(s.trim());

    if (c && !out.includes(c)) {
      out.push(c);
    }
  }

  return out.slice(0, 20);
}

function validateCode(code) {
  return /^\d{6}$/.test(String(code || ""))
    ? String(code)
    : null;
}

async function getLiveStock(code) {
  const endpoint =
    "https://polling.finance.naver.com/api/realtime?query=" +
    encodeURIComponent(`SERVICE_ITEM:${code}`);

  const data = await fetchJson(endpoint);

  const areas = data?.result?.areas || [];
  const raw = areas.flatMap(x => x.datas || [])[0];

  if (!raw) {
    return {
      code,
      error: "NO_LIVE_DATA"
    };
  }

  return {
    code,
    name: raw.nm ?? null,
    currentPrice: num(raw.nv),
    previousClose: num(raw.sv),
    change: num(raw.cv),
    changePct: num(raw.cr),
    open: num(raw.ov),
    high: num(raw.hv),
    low: num(raw.lv),
    volume: num(raw.aq),
    tradingValue: num(raw.aa),
    marketStatus: raw.ms ?? null,
    pollingIntervalMs: num(data?.result?.pollingInterval),
    nxtOverMarketPriceInfo: raw.nxtOverMarketPriceInfo ?? null
  };
}

async function getIndexes() {
  const endpoint =
    "https://polling.finance.naver.com/api/realtime?query=" +
    encodeURIComponent("SERVICE_INDEX:KOSPI,KOSDAQ");

  const data = await fetchJson(endpoint);

  const areas = data?.result?.areas || [];
  const rows = areas.flatMap(x => x.datas || []);

  const out = {};

  for (const raw of rows) {
    const code = raw.cd;

    if (!code) continue;

    out[code] = {
      value: num(raw.nv),
      change: num(raw.cv),
      changePct: num(raw.cr),
      open: num(raw.ov),
      high: num(raw.hv),
      low: num(raw.lv),
      volume: num(raw.aq),
      tradingValue: num(raw.aa),
      marketStatus: raw.ms ?? null
    };
  }

  return out;
}

async function getLegacyChart(code, timeframe, count) {
  const endpoint =
    `https://fchart.stock.naver.com/sise.nhn?symbol=${code}` +
    `&timeframe=${timeframe}` +
    `&count=${count}` +
    `&requestType=0`;

  const res = await fetch(endpoint, {
    headers: {
      "User-Agent": "Mozilla/5.0",
      "Accept": "text/xml,application/xml,text/plain,*/*",
      "Referer": "https://finance.naver.com/"
    }
  });

  if (!res.ok) {
    throw new Error(`CHART_HTTP_${res.status}`);
  }

  const text = await res.text();
  const rows = [];

  const re = /<item\s+data="([^"]+)"/g;
  let m;

  while ((m = re.exec(text)) !== null) {
    const [
      date,
      open,
      high,
      low,
      close,
      volume
    ] = m[1].split("|");

    rows.push({
      date,
      open: num(open),
      high: num(high),
      low: num(low),
      close: num(close),
      volume: num(volume)
    });
  }

  rows.sort((a, b) =>
    a.date.localeCompare(b.date)
  );

  return rows;
}

function buildTechnical(day) {
  const rows = day.filter(x =>
    x &&
    x.close != null &&
    x.high != null &&
    x.low != null
  );

  const closes = rows.map(x => x.close);
  const volumes = rows.map(x => x.volume ?? 0);

  const latest =
    rows.length
      ? rows[rows.length - 1]
      : null;

  return {
    latest,
    ma20: sma(closes, 20),
    ma50: sma(closes, 50),
    ma100: sma(closes, 100),
    ma200: sma(closes, 200),
    volumeMA20: sma(volumes, 20),
    rsi14: rsi(closes, 14),
    macd: macd(closes),
    swing20: swing(rows, 20),
    swing60: swing(rows, 60),
    swing120: swing(rows, 120)
  };
}

function sma(values, period) {
  if (values.length < period) {
    return null;
  }

  const a = values.slice(-period);

  return round(
    a.reduce((sum, x) => sum + x, 0) / period,
    2
  );
}

function emaSeries(values, period) {
  if (!values.length) return [];

  const k = 2 / (period + 1);
  const out = [values[0]];

  for (let i = 1; i < values.length; i++) {
    out.push(
      values[i] * k +
      out[i - 1] * (1 - k)
    );
  }

  return out;
}

function macd(values) {
  if (values.length < 35) {
    return null;
  }

  const e12 = emaSeries(values, 12);
  const e26 = emaSeries(values, 26);

  const line = values.map(
    (_, i) => e12[i] - e26[i]
  );

  const signal = emaSeries(
    line.slice(25),
    9
  );

  const macdNow =
    line[line.length - 1];

  const signalNow =
    signal[signal.length - 1];

  return {
    macd: round(macdNow, 2),
    signal: round(signalNow, 2),
    histogram: round(
      macdNow - signalNow,
      2
    )
  };
}

function rsi(values, period) {
  if (values.length <= period) {
    return null;
  }

  let gains = 0;
  let losses = 0;

  for (let i = 1; i <= period; i++) {
    const d =
      values[i] - values[i - 1];

    if (d >= 0) gains += d;
    else losses -= d;
  }

  let avgGain =
    gains / period;

  let avgLoss =
    losses / period;

  for (
    let i = period + 1;
    i < values.length;
    i++
  ) {
    const d =
      values[i] - values[i - 1];

    const gain =
      Math.max(d, 0);

    const loss =
      Math.max(-d, 0);

    avgGain =
      ((avgGain * (period - 1)) + gain)
      / period;

    avgLoss =
      ((avgLoss * (period - 1)) + loss)
      / period;
  }

  if (avgLoss === 0) {
    return 100;
  }

  const rs =
    avgGain / avgLoss;

  return round(
    100 - (100 / (1 + rs)),
    2
  );
}

function swing(rows, period) {
  if (!rows.length) {
    return null;
  }

  const a =
    rows.slice(
      -Math.min(period, rows.length)
    );

  let hi = a[0];
  let lo = a[0];

  for (const r of a) {
    if (r.high > hi.high) {
      hi = r;
    }

    if (r.low < lo.low) {
      lo = r;
    }
  }

  return {
    period:
      Math.min(period, rows.length),

    high: hi.high,
    highDate: hi.date,

    low: lo.low,
    lowDate: lo.date
  };
}

async function getMarketScan() {
  const url =
    "https://stock.naver.com/api/domestic/market/stock/default" +
    "?tradeType=KRX" +
    "&marketType=ALL" +
    "&orderType=priceTop" +
    "&startIdx=0" +
    "&pageSize=100";

  const data = await fetchJson(url);
  const rows = Array.isArray(data) ? data : [];

  const normalized = rows.map((r, i) => ({
    rank: i + 1,
    code: r.itemcode ?? null,
    name: r.itemname ?? null,
    price: looseNum(r.nowPrice),
    changePct: looseNum(r.prevChangeRate)
  }));

  return {
    volumeTop: normalized.slice(0, 20),
    risingLiquid: [...normalized]
      .filter(x => x.changePct != null)
      .sort((a, b) => b.changePct - a.changePct)
      .slice(0, 20)
  };
}
function normalizeStockList(arr) {
  if (!Array.isArray(arr)) {
    return [];
  }

  return arr.map((r, i) => ({
    rank: i + 1,

    code:
      r.itemCode ??
      r.code ??
      null,

    name:
      r.stockName ??
      r.name ??
      null,

    price:
      looseNum(
        r.closePrice ??
        r.currentPrice ??
        r.price
      ),

    changePct:
      looseNum(
        r.fluctuationsRatio ??
        r.changeRate
      ),

    volume:
      looseNum(
        r.accumulatedTradingVolume ??
        r.tradingVolume
      ),

    tradingValue:
      looseNum(
        r.accumulatedTradingValue ??
        r.tradingValue
      )
  }));
}

function findFirstArray(obj) {
  if (Array.isArray(obj)) {
    return obj;
  }

  if (
    !obj ||
    typeof obj !== "object"
  ) {
    return [];
  }

  for (const k of Object.keys(obj)) {
    const x =
      findFirstArray(obj[k]);

    if (
      Array.isArray(x) &&
      x.length
    ) {
      return x;
    }
  }

  return [];
}

async function fetchJson(url) {
  const response =
    await fetch(url, {
      headers: {
        "User-Agent":
          "Mozilla/5.0",

        "Accept":
          "application/json,text/plain,*/*",

        "Referer":
          "https://finance.naver.com/"
      }
    });

  if (
    response.status === 403 ||
    response.status === 429
  ) {
    throw new Error(
      `NAVER_BLOCK_${response.status}`
    );
  }

  if (!response.ok) {
    throw new Error(
      `HTTP_${response.status}`
    );
  }

  return await response.json();
}

function looseNum(v) {
  if (
    v === null ||
    v === undefined ||
    v === ""
  ) {
    return null;
  }

  if (typeof v === "number") {
    return v;
  }

  const x =
    Number(
      String(v)
        .replaceAll(",", "")
        .replace("%", "")
        .trim()
    );

  return Number.isFinite(x)
    ? x
    : null;
}

function num(v) {
  if (
    v === null ||
    v === undefined ||
    v === ""
  ) {
    return null;
  }

  const x =
    Number(
      String(v)
        .replaceAll(",", "")
    );

  return Number.isFinite(x)
    ? x
    : null;
}

function round(v, d = 2) {
  const m =
    10 ** d;

  return Math.round(v * m) / m;
}

function json(data, status = 200, extraHeaders = {}) {
  return new Response(
    JSON.stringify(data, null, 2),
    {
      status,
      headers: {
        "Content-Type": "application/json; charset=UTF-8",
        "Cache-Control": "no-store",
        ...extraHeaders
      }
    }
  );
}