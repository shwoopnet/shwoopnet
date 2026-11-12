import gzip, json, sys, os, collections
d = sys.argv[1]; c = collections.Counter(); ex = []
def f(v):
    try: return round(float(v), 4)
    except (TypeError, ValueError): return None
for fn in sorted(os.listdir(d)):
    if not fn.endswith(".json.gz"): continue
    body = json.load(gzip.open(os.path.join(d, fn)))
    nodes = body.get("markets") if isinstance(body.get("markets"), list) else [body]
    for n in nodes:
        cs = n.get("candlesticks") or []
        if cs and not c["shown"]:
            c["shown"] = 1; print(json.dumps(cs[0])[:700])
        cs = sorted(cs, key=lambda x: x["end_period_ts"])
        for a, b in zip(cs, cs[1:]):
            step = b["end_period_ts"] - a["end_period_ts"]
            for side in ("yes_bid", "yes_ask"):
                A, B = a.get(side) or {}, b.get(side) or {}
                ka = [k for k in A if k.startswith("close")]; 
                pc = f(A.get("close_dollars", A.get("close"))); o = f(B.get("open_dollars", B.get("open"))); lo = f(B.get("low_dollars", B.get("low"))); hi = f(B.get("high_dollars", B.get("high")))
                if None in (pc, o, lo, hi): c["missing"] += 1; continue
                tag = "adjacent" if step in (60, 3600) else "gap"
                c[tag + " pairs"] += 1
                if o == pc: c[tag + " open == prev close"] += 1
                else:
                    c[tag + " open != prev close"] += 1
                    if lo <= pc <= hi: c[tag + " differs but prev close inside [low, high]"] += 1
                    else:
                        c[tag + " prev close OUTSIDE [low, high]"] += 1
                        if abs(o - pc) >= 0.05: c[tag + " OUTSIDE and jump >= 5c"] += 1
                        if len(ex) < 6: ex.append((n.get("market_ticker", fn), side, step, pc, o, lo, hi))
for k, v in sorted(c.items()): print("%-55s %d" % (k, v))
for e in ex: print(e)
