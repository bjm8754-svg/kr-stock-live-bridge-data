"""Research-only, historical reservation-buy replay. No broker orders or live connection.

A decision is locked at a completed daily close. The assistant independently chooses
a limit buy price and budget. The bid can fill only on a LATER session that crosses
that price. Unfilled orders persist until explicitly canceled, invalidated, or expired.
A three-session review is not a trade's expiry or a market-buy instruction.
"""
from __future__ import annotations

import datetime as dt
import math
from collections import defaultdict


def simulate(decs, dates, catalog, fetch_price, cfg):
    initial = float(cfg.get("initialCapitalKrw", 10_000_000))
    buy_fee = float(cfg.get("buyCostBps", 5)) / 10000
    sell_fee = float(cfg.get("sellCostBps", 20)) / 10000
    step = int(cfg.get("stepSessions", 3))
    cash = initial
    positions = {}
    pending = {}
    history = []
    intervals = []
    daily_equity = [initial]
    cost_total = 0.0
    turnover = 0.0
    data = {}
    used_ids = set()

    def series(aid):
        if aid not in data:
            meta = catalog.get(aid)
            if not meta:
                raise ValueError("unknown asset " + aid)
            begin = dates[0] - dt.timedelta(days=120)
            data[aid] = fetch_price(meta, begin, dates[-1])
        return data[aid]

    def row_at(aid, day):
        df = series(aid)
        subset = df.loc[df.index.date == day]
        return subset.iloc[-1] if not subset.empty else None

    def close(aid, day):
        df = series(aid)
        subset = df.loc[df.index.date <= day]
        if subset.empty:
            raise ValueError("missing close " + aid)
        return float(subset.iloc[-1]["Close"])

    def equity(day):
        return cash + sum(p["shares"] * close(aid, day) for aid, p in positions.items())

    def emit(j, abs_session, aid, event, **values):
        history.append({"step": j, "session": abs_session, "assetId": aid,
                        "event": event, **values})

    def sell_all(aid, price, j, n, reason):
        nonlocal cash, cost_total, turnover
        p = positions.pop(aid)
        shares = p["shares"]
        gross = shares * price
        fee = gross * sell_fee
        cash += gross - fee
        cost_total += fee
        turnover += gross
        emit(j, n, aid, reason, shares=shares, fillPrice=round(price, 2),
             feeKrw=round(fee, 2))
        for oid in list(pending):
            if pending[oid]["assetId"] == aid:
                drop_order(oid, j, n, "CANCEL_AFTER_EXIT")

    def drop_order(oid, j, n, reason):
        o = pending.pop(oid)
        emit(j, n, o["assetId"], reason, orderId=oid,
             kind=o["kind"], limitPrice=o["limitPrice"])

    def create_orders(row, j, n, eq, first_allowed, add_allowed):
        aid = row["assetId"]
        tranches = row.get("buyOrders")
        if not isinstance(tranches, list) or not tranches:
            raise ValueError("BUY_LIMIT requires explicit buyOrders " + aid)
        kinds = [o.get("kind") for o in tranches]
        if any(k not in ("FIRST", "ADD") for k in kinds):
            raise ValueError("unknown tranche kind " + aid)
        if first_allowed and (kinds[0] != "FIRST" or kinds.count("FIRST") != 1):
            raise ValueError("entry must begin with one FIRST tranche " + aid)
        if add_allowed and any(k != "ADD" for k in kinds):
            raise ValueError("ADD action can only stage ADD tranches " + aid)
        for tranche in tranches:
            kind = tranche["kind"]
            oid = str(tranche.get("orderId", ""))
            if not oid or oid in used_ids:
                raise ValueError("duplicate or missing orderId " + oid)
            limit = float(tranche["limitPrice"])
            allocation = float(tranche["capitalPct"])
            stop = float(row["stop"])
            if not all(math.isfinite(v) for v in (limit, allocation, stop)):
                raise ValueError("non-finite limit/stop/budget")
            if limit <= stop or stop <= 0 or allocation <= 0 or allocation > 100:
                raise ValueError("invalid structural limit, stop or allocation " + oid)
            expiry = tranche.get("expireAtSession")
            if expiry is not None:
                expiry = int(expiry)
                if expiry <= n:
                    raise ValueError("reservation expires before activation")
            used_ids.add(oid)
            pending[oid] = {
                "orderId": oid, "assetId": aid, "kind": kind,
                "limitPrice": limit, "stop": stop, "budgetKrw": eq * allocation / 100,
                "capitalPctAtLock": allocation, "startSession": n,
                "expireAtSession": expiry, "target": row.get("target"),
            }
            emit(j, n, aid, "ORDER_PLACED", orderId=oid,
                 kind=kind, limitPrice=limit, budgetKrw=round(eq * allocation / 100, 2),
                 expireAtSession=expiry)

    if not decs:
        result_session = 0
    else:
        result_session = min(len(decs) * step, len(dates) - 1)
    if len(dates) < len(decs) * step + 1:
        raise ValueError("insufficient episode review calendar")

    for j, decision in enumerate(decs):
        if int(decision.get("step", -1)) != j:
            raise ValueError("non-sequential frozen decisions")
        n0 = j * step
        cutoff = dates[n0]
        interval_end = dates[(j + 1) * step]
        before = equity(cutoff)
        actions = {}
        sell_next = {}
        total_pct = 0.0
        for raw in decision.get("portfolio", []):
            aid = str(raw["assetId"])
            action = str(raw["action"])
            if aid in actions:
                raise ValueError("one instruction per asset per review")
            actions[aid] = raw
            if action in ("ENTER", "ROTATE_IN"):
                if aid in positions or any(o["assetId"] == aid for o in pending.values()):
                    raise ValueError("cannot re-enter held/pending symbol")
                alloc = sum(float(x["capitalPct"]) for x in raw.get("buyOrders", []))
                total_pct += alloc
                create_orders(raw, j, n0, before, first_allowed=True, add_allowed=False)
            elif action == "ADD":
                if aid not in positions:
                    raise ValueError("ADD requires held stock")
                total_pct += sum(float(x["capitalPct"]) for x in raw.get("buyOrders", []))
                create_orders(raw, j, n0, before, first_allowed=False, add_allowed=True)
                if raw.get("stop") is not None:
                    positions[aid]["stop"] = float(raw["stop"])
            elif action == "HOLD":
                if aid not in positions:
                    raise ValueError("HOLD requires a filled position " + aid)
                if raw.get("stop") is not None:
                    positions[aid]["stop"] = float(raw["stop"])
                positions[aid]["lastAction"] = "HOLD"
            elif action in ("REDUCE", "EXIT", "ROTATE_OUT"):
                if aid not in positions:
                    raise ValueError("sell requires held stock")
                sell_next[aid] = raw
            elif action == "CANCEL":
                ids = [oid for oid, o in pending.items() if o["assetId"] == aid]
                for oid in ids:
                    drop_order(oid, j, n0, "CANCEL_USER")
            elif action == "KEEP_PENDING":
                if not any(o["assetId"] == aid for o in pending.values()):
                    raise ValueError("KEEP_PENDING requires outstanding order")
            else:
                raise ValueError("unknown action " + action)
        if total_pct > 100.000001:
            raise ValueError("new reservations exceed 100% of initial portfolio")
        # Never promise more resting buy orders than unencumbered cash could cover.
        # Cash is not debited before a fill; this is a reservation risk gate only.
        if sum(o["budgetKrw"] for o in pending.values()) * (1 + buy_fee) > cash + 0.01:
            raise ValueError("UNFUNDED_PENDING_RESERVATIONS")

        # A held position omitted from the complete portfolio is an EXIT decision,
        # but omission never silently converts an outstanding reservation into a fill.
        for aid in positions:
            if aid not in actions:
                sell_next[aid] = {"action": "EXIT"}

        start_after = before
        stop_events = []
        for day_offset in range(1, step + 1):
            n = n0 + day_offset
            day = dates[n]
            if n == n0 + 1:
                for aid, row in list(sell_next.items()):
                    bar = row_at(aid, day)
                    if bar is None:
                        raise ValueError("missing sell next open")
                    open_px = float(bar["Open"])
                    action = row["action"]
                    if action == "REDUCE":
                        shares = positions[aid]["shares"]
                        pct = float(row["capitalPct"])
                        desired = (before * pct / 100) / open_px
                        amount = max(0, shares - math.floor(desired))
                        if amount > 0:
                            gross = amount * open_px
                            fee = gross * sell_fee
                            cash += gross - fee
                            cost_total += fee
                            turnover += gross
                            positions[aid]["shares"] -= amount
                            emit(j, n, aid, "REDUCE_FILLED", shares=amount,
                                 fillPrice=open_px, feeKrw=round(fee, 2))
                            if positions[aid]["shares"] <= 0:
                                del positions[aid]
                    else:
                        sell_all(aid, open_px, j, n, "EXIT_FILLED")
            # Existing stop orders: assume protective exit before any new adds
            # if the same day's intrabar sequence is unknown.
            stopped_today = set()
            for aid in list(positions):
                bar = row_at(aid, day)
                if bar is None:
                    continue
                stop = positions[aid].get("stop")
                if stop is None:
                    continue
                op, lo = float(bar["Open"]), float(bar["Low"])
                if op <= stop or lo <= stop:
                    fill_px = op if op <= stop else stop
                    sell_all(aid, fill_px, j, n, "STOP_EXIT")
                    stopped_today.add(aid)
                    stop_events.append({"assetId": aid, "exitPrice": round(fill_px, 2)})
            # Pending bids are processed in FIRST -> ADD order, for all days of
            # every review interval until canceled, invalidated, or expired.
            for oid, o in sorted(list(pending.items()), key=lambda x: (x[1]["kind"] != "FIRST", x[1]["startSession"], x[0])):
                if oid not in pending:
                    continue
                aid = o["assetId"]
                if n > o["startSession"] and o["expireAtSession"] is not None and n > o["expireAtSession"]:
                    drop_order(oid, j, n, "CANCEL_EXPIRED")
                    continue
                if aid in stopped_today:
                    drop_order(oid, j, n, "CANCEL_AFTER_STOP")
                    continue
                if o["kind"] == "ADD" and aid not in positions:
                    # Tranche waits for first fill; it never buys a new standalone position.
                    continue
                if o["kind"] == "FIRST" and aid in positions:
                    drop_order(oid, j, n, "CANCEL_ALREADY_HELD")
                    continue
                bar = row_at(aid, day)
                if bar is None:
                    continue
                op, lo = float(bar["Open"]), float(bar["Low"])
                limit, stop = o["limitPrice"], o["stop"]
                if op <= stop:
                    drop_order(oid, j, n, "CANCEL_GAP_BELOW_STOP")
                    continue
                # Strict penetration required if not fillable at the opening.
                if op > limit and not lo < limit:
                    continue
                price = op if op <= limit else limit
                budget = min(o["budgetKrw"], cash)
                shares = math.floor(budget / (price * (1 + buy_fee)) + 1e-9)
                if shares <= 0:
                    drop_order(oid, j, n, "CANCEL_NO_CASH")
                    continue
                gross = shares * price
                fee = gross * buy_fee
                cash -= gross + fee
                cost_total += fee
                turnover += gross
                existing = positions.get(aid)
                if existing:
                    existing_cost = existing["avgCost"] * existing["shares"]
                    existing["shares"] += shares
                    existing["avgCost"] = (existing_cost + gross + fee) / existing["shares"]
                    existing["lastAction"] = "ADD"
                else:
                    positions[aid] = {
                        "shares": shares, "avgCost": (gross + fee) / shares,
                        "stop": stop, "target": o["target"], "lastAction": "ENTER",
                    }
                del pending[oid]
                emit(j, n, aid, "BUY_LIMIT_FILLED", orderId=oid, kind=o["kind"],
                     shares=shares, limitPrice=limit, fillPrice=round(price, 2),
                     feeKrw=round(fee, 2))
                # Conservative OHLC rule: if limit and stop were both reached,
                # assume filled then stopped on same day; do not count a free winner.
                if lo <= positions[aid]["stop"]:
                    sell_all(aid, positions[aid]["stop"], j, n, "STOP_SAME_DAY")
                    stopped_today.add(aid)
                    stop_events.append({"assetId": aid, "exitPrice": round(stop, 2)})
            daily_equity.append(equity(day))
        end = equity(interval_end)
        intervals.append({"step": j,
                          "startEquityKrw": round(before, 2),
                          "postTradeEquityKrw": round(start_after, 2),
                          "endEquityKrw": round(end, 2),
                          "returnPct": round((end / before - 1) * 100, 3),
                          "stopped": stop_events})
    final_date = dates[result_session]
    eq = equity(final_date)
    peak = daily_equity[0]
    mdd = 0.0
    for value in daily_equity:
        peak = max(peak, value)
        if peak > 0:
            mdd = min(mdd, value / peak - 1.0)
    snapshot = []
    for aid, p in positions.items():
        price = close(aid, final_date)
        snapshot.append({"assetId": aid, "marketValueKrw": round(p["shares"] * price, 2),
                         "capitalPct": round(100 * p["shares"] * price / eq, 2),
                         "avgEntry": round(p["avgCost"], 2), "currentPrice": round(price, 2),
                         "unrealizedPct": round((price / p["avgCost"] - 1) * 100, 2),
                         "stop": p["stop"], "target": p["target"],
                         "lastAction": p["lastAction"], "shares": p["shares"]})
    waiting = [
        {k: v for k, v in o.items() if k in ("orderId", "assetId", "kind", "limitPrice",
            "stop", "budgetKrw", "capitalPctAtLock", "startSession", "expireAtSession")}
        for o in pending.values()
    ]
    return {"equity": eq, "cash": cash, "positions": snapshot,
            "pendingOrders": waiting, "orderEvents": history, "intervals": intervals,
            "mddPct": 100 * mdd, "turnoverKrw": turnover, "costKrw": cost_total,
            "compositionChanges": 0, "dailyEquity": daily_equity}
