"""BINPATH diagnostic (development data only, descriptive, no rule scored): is the model's price for the side it buys the price Kalshi actually quoted?
By model ask bin and arm: Binance history 2019-2024 (model ask, realised win rate) against Kalshi development windows (model ask, Kalshi's actual ask, Kalshi's
settled win rate). MODEL RESULT, not a live figure."""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scan_binance as B, scan as S

BINS = {"cheap": [(0.03, 0.06), (0.06, 0.10), (0.10, 0.15), (0.15, 0.20), (0.20, 0.30)],
        "band": [(0.88, 0.90), (0.90, 0.92), (0.92, 0.94), (0.94, 0.97)]}


def main():
    grids, frames = B.kalshi_setup()
    model = B.load_model()
    out = {}
    for arm, bins in BINS.items():
        # Kalshi rows
        krow = []
        for i, sym in enumerate(B.SYMS):
            for f in frames[i]:
                keep = f["ok"] & ~np.isnan(f["bid"])
                cr = B.core(f["G"], f["idd"][keep], f["ido"][keep], f["L"], model)
                side = B.pick_side(cr, arm)
                ask_m = np.where(side > 0, cr["ask_yes"], cr["ask_no"])
                ask_a = np.where(side > 0, f["ask"][keep], 1 - f["bid"][keep])
                won = np.where(side > 0, f["res"][keep] == 1, f["res"][keep] == 0)
                k = side != 0
                krow.append(np.stack([ask_m[k], ask_a[k], won[k]], 1))
        K = np.concatenate(krow)
        H = []
        for sym in B.SYMS:
            ad = B.BinAdapter(sym, arm); tab = ad.build_dev()
            H.append(np.stack([tab.meta["ask"], tab.meta["won"].astype(float)], 1))
        H = np.concatenate(H)
        rows = []
        for lo, hi in bins:
            hm = (H[:, 0] >= lo - 1e-9) & (H[:, 0] < hi - 1e-9 if hi < 0.97 else H[:, 0] <= hi + 1e-9)
            km = (K[:, 0] >= lo - 1e-9) & (K[:, 0] < hi - 1e-9 if hi < 0.97 else K[:, 0] <= hi + 1e-9)
            r = dict(bin="%d-%dc" % (lo * 100, hi * 100), hist_n=int(hm.sum()), hist_model_ask=float(H[hm, 0].mean()) if hm.any() else None,
                     hist_win=float(H[hm, 1].mean()) if hm.any() else None, kalshi_n=int(km.sum()),
                     kalshi_model_ask=float(K[km, 0].mean()) if km.any() else None, kalshi_actual_ask=float(K[km, 1].mean()) if km.any() else None,
                     kalshi_win=float(K[km, 2].mean()) if km.any() else None)
            if hm.any():
                net = S.kalshi_net_cents(H[hm, 1], H[hm, 0]); r["hist_pf_at_model_ask"] = S.pf_of(net)
            if km.any():
                net = S.kalshi_net_cents(K[km, 2], K[km, 1]); r["kalshi_pf_at_actual_ask"] = S.pf_of(net)
            rows.append(r)
        out[arm] = rows
    json.dump(out, open(os.path.join(S.WORKERS, "BINPATH_CALIBRATION.json"), "w"), indent=1)
    for arm, rows in out.items():
        print(arm)
        for r in rows:
            print("  ", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()})



def kalshi_check():
    """Each validated survivor applied to the Kalshi development windows (Oct 2026, BTC or ETH) with Kalshi's ACTUAL ask and settled result, using the
    survivor's W1 cut points. Tiny n, descriptive only; the question is whether a rule that wins at the model's price also wins at Kalshi's price."""
    grids, frames = B.kalshi_setup()
    model = B.load_model()
    fts = {s: B.load_funding(s) for s in B.SYMS}
    res = {}
    for sym_i, sym in enumerate(B.SYMS):
        for arm in B.ARMS:
            name = "binpath_%s_%s" % (sym, arm)
            vf = os.path.join(S.SCAN_DATA, "runs_validated", name + "_VALIDATED.json")
            doc = json.load(open(vf)); cuts = doc["cuts"]["ALL"]
            X, ask_m, ask_a, won, side_, look_, tt = [], [], [], [], [], [], []
            for f in frames[sym_i]:
                G = f["G"]; keep = f["ok"] & ~np.isnan(f["bid"])
                idd, ido = f["idd"][keep], f["ido"][keep]
                cr = B.core(G, idd, ido, f["L"], model); s = B.pick_side(cr, arm); k = s != 0
                idd, ido = idd[k], ido[k]; crk = {x: v[k] for x, v in cr.items()}; sk = s[k]
                t = f["closes"][keep][k] - f["L"]
                F = B.side_features(G, idd, ido, t, f["L"], model, sk, crk, *fts[sym])
                X.append(F); tt.append(t)
                ask_m.append(np.where(sk > 0, crk["ask_yes"], crk["ask_no"]))
                ask_a.append(np.where(sk > 0, f["ask"][keep][k], 1 - f["bid"][keep][k]))
                r = f["res"][keep][k]; won.append(np.where(sk > 0, r == 1, r == 0)); side_.append(sk); look_.append(np.full(len(sk), f["L"]))
            X = np.concatenate(X); ask_m = np.concatenate(ask_m); ask_a = np.concatenate(ask_a); won = np.concatenate(won)
            side_ = np.concatenate(side_); look_ = np.concatenate(look_); tt = np.concatenate(tt)
            cat = {"hod4": ((tt % 86400) // 14400), "dow": (((tt // 86400) + 3) % 7)}
            per = []; union = np.zeros(len(X), bool)
            for sv in doc["survivors"]:
                m = (side_ == (1 if sv["dir"] == "yes" else -1)) & (look_ == sv["variant"])
                for sp in sv["atoms"]:
                    if sp["kind"] == "cat":
                        m &= cat[sp["feat"]] == sp["val"]
                    else:
                        c = cuts[sp["feat"]][B.S.QS.index(sp["q"])]
                        col = X[:, B.FEATS.index(sp["feat"])]
                        with np.errstate(invalid="ignore"):
                            m &= (col >= c) if sp["op"] == "ge" else (col <= c)
                union |= m
                if m.sum():
                    per.append(dict(n=int(m.sum()), pf_actual=S.pf_of(S.kalshi_net_cents(won[m], ask_a[m])), pf_model_price=S.pf_of(S.kalshi_net_cents(won[m], ask_m[m]))))
            pooled = None
            if union.any():
                pooled = dict(n=int(union.sum()), win=float(won[union].mean()), model_ask=float(ask_m[union].mean()), actual_ask=float(ask_a[union].mean()),
                              pf_at_actual_ask=S.pf_of(S.kalshi_net_cents(won[union], ask_a[union])), pf_at_model_ask=S.pf_of(S.kalshi_net_cents(won[union], ask_m[union])),
                              mean_net_actual_c=float(S.kalshi_net_cents(won[union], ask_a[union]).mean()))
            res[name] = dict(survivors=len(doc["survivors"]), kalshi_rows_in_arm=int(len(X)), survivors_with_trades=len(per), pooled_union=pooled,
                             median_pf_actual=float(np.median([p["pf_actual"] for p in per])) if per else None,
                             share_pf_actual_ge_1_5=float(np.mean([p["pf_actual"] >= 1.5 for p in per])) if per else None)
            print(name, json.dumps(res[name]))
    json.dump(res, open(os.path.join(S.WORKERS, "BINPATH_KALSHI_CHECK.json"), "w"), indent=1)


if __name__ == "__main__":
    (kalshi_check if "kcheck" in sys.argv else main)()
