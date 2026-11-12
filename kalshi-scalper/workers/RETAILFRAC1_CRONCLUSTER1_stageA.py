import sys, os, glob, json
import numpy as np, pandas as pd
RAW, OUT = sys.argv[1], sys.argv[2]
MARK = OUT + ".done"
if os.path.exists(MARK): sys.exit("refuse: second scored run")
open(MARK, "w").write("started")
SER = ["KXBTC15M","KXETH15M","KXXRP15M","KXDOGE15M","KXGOLD15M"]
# coverage: result used as presence flag only
cov = []
for d in sorted(glob.glob(RAW+"/*/*/")):
    c = pd.read_csv(d+"coverage.csv.gz", usecols=["close_time","series","ticker","max_gap_ms","tape_trades","tape_sum_count","volume_fp","result"])
    c["has_result"] = c["result"].notna() & (c["result"].astype(str).str.strip()!="")
    c = c.drop(columns="result"); c["dir"] = d; cov.append(c)
cov = pd.concat(cov)
cov = cov.sort_values("tape_trades").drop_duplicates("ticker", keep="last")
ok = cov.has_result & ((cov.tape_sum_count - cov.volume_fp).abs() <= 0.01*cov.volume_fp.clip(lower=1e-9)) & (cov.max_gap_ms < 10000) & cov.series.isin(SER)
cnt_all = cov.series.value_counts().to_dict()
cov = cov[ok]
cnt_ok = cov.series.value_counts().to_dict()
cov["T"] = pd.to_datetime(cov.close_time, utc=True, format="ISO8601").astype("datetime64[s, UTC]").astype("int64")
Tmap = dict(zip(cov.ticker, cov["T"])); Smap = dict(zip(cov.ticker, cov.series))
good = set(cov.ticker)
# accumulators
sizes = {s:{0:[],1:[]} for s in SER}            # class 0 whole,1 frac
agg_mtc = {s:np.zeros((15,2,2)) for s in SER}  # [bucket][class][ trades, contracts]
agg_blk = {s:np.zeros((6,2)) for s in SER}      # contracts by class per 4h block [whole, frac]
yes_c = {s:np.zeros((2,2)) for s in SER}        # [class][yes contracts, total]
paid = {s:np.zeros((2,2)) for s in SER}         # [class][sum price*cnt, cnt]
wins = []   # per window: series, F, W, secarr[15,60]
bk = []     # per window: series, sums arrays
for d in sorted(glob.glob(RAW+"/*/*/")):
    c = cov[cov.dir==d]
    if c.empty: continue
    t = pd.read_csv(d+"trades.csv.gz")
    t = t[t.ticker.isin(c.ticker)]
    if len(t):
        ct = pd.to_datetime(t.created_time, utc=True, format="ISO8601")
        ts = ct.astype("datetime64[us, UTC]").astype("int64").to_numpy()/1e6
        T = t.ticker.map(Tmap).to_numpy(float); ser = t.ticker.map(Smap).to_numpy()
        cnt = t.count_fp.to_numpy(float); fr = (np.abs(cnt-np.rint(cnt))>0.001).astype(int)
        isyes = (t.taker_outcome_side=="yes").to_numpy()
        px = t.yes_price_dollars.to_numpy(float); pp = np.where(isyes, px, 1-px)
        mtc = T - ts
        b = np.clip(np.floor(mtc/60).astype(int),0,14)
        sec = (np.floor(ts)%60).astype(int)
        blk = ((np.floor(ts)%86400)//14400).astype(int)
        signed = np.where(isyes, cnt, -cnt)
        for s in SER:
            m = ser==s
            if not m.any(): continue
            for k in (0,1):
                mk = m & (fr==k)
                sizes[s][k].append(cnt[mk].astype(np.float32))
                np.add.at(agg_mtc[s], (b[mk], k, 0), 1); np.add.at(agg_mtc[s], (b[mk], k, 1), cnt[mk])
                np.add.at(agg_blk[s], (blk[mk], k), cnt[mk])
                yes_c[s][k] += [cnt[mk&isyes].sum(), cnt[mk].sum()]
                paid[s][k] += [(pp[mk]*cnt[mk]).sum(), cnt[mk].sum()]
        df = pd.DataFrame(dict(tk=t.ticker.to_numpy(), ser=ser, b=b, sec=sec, cnt=cnt, fr=fr, sg=signed, mtc=mtc))
        for tk,g in df.groupby("tk"):
            A = np.zeros((15,60)); np.add.at(A,(g.b.to_numpy(),g.sec.to_numpy()),g.cnt.to_numpy())
            w = g[(g.mtc>360)&(g.mtc<=600)]
            wins.append((g.ser.iloc[0], w.sg[w.fr==1].sum(), w.sg[w.fr==0].sum(), A))
        have = set(df.tk)
        for tk in set(c.ticker)-have:
            wins.append((Smap[tk],0.0,0.0,np.zeros((15,60))))
    # book
    bkdf = pd.read_csv(d+"book.csv.gz", usecols=["t_recv_ms","ticker","yes_bid_px_1","yes_bid_sz_1","no_bid_px_1","no_bid_sz_1"])
    bkdf = bkdf[bkdf.ticker.isin(c.ticker)].dropna()
    if bkdf.empty: continue
    tr = bkdf.t_recv_ms.to_numpy()/1000.0
    bkdf["mb"] = np.floor(tr/60).astype(np.int64); bkdf["sec"] = tr%60; bkdf["tr"]=tr
    bkdf["T"] = bkdf.ticker.map(Tmap)
    bkdf["spread"] = 1-bkdf.yes_bid_px_1-bkdf.no_bid_px_1
    bkdf["ask_sz"] = (bkdf.no_bid_sz_1+bkdf.yes_bid_sz_1)/2   # mean of YES-ask size and NO-ask size
    bkdf = bkdf.sort_values(["ticker","tr"])
    bef = bkdf[bkdf.sec>=52].groupby(["ticker","mb"]).last()
    aft = bkdf[(bkdf.sec>=8)&(bkdf.sec<=15)].groupby(["ticker","mb"]).first()
    bef = bef.reset_index(); bef["mb"] = bef.mb+1   # boundary = start of next minute
    m = bef.merge(aft.reset_index(), on=["ticker","mb"], suffixes=("_b","_a"))
    m = m[m.mb*60 < m["T_b"]]
    m["bucket"] = np.clip(np.floor((m["T_b"]-(m.mb*60+10))/60).astype(int),0,14)  # minutes-to-close of the post-boundary minute
    m["ser"] = m.ticker.map(Smap)
    for (s,tk),g in m.groupby(["ser","ticker"]):
        a = np.zeros((15,5))
        np.add.at(a,(g.bucket.to_numpy(),0),g.ask_sz_b.to_numpy()); np.add.at(a,(g.bucket.to_numpy(),1),g.ask_sz_a.to_numpy())
        np.add.at(a,(g.bucket.to_numpy(),2),g.spread_b.to_numpy()); np.add.at(a,(g.bucket.to_numpy(),3),g.spread_a.to_numpy())
        np.add.at(a,(g.bucket.to_numpy(),4),1)
        bk.append((s,a))
    print(d, flush=True)
rng = np.random.default_rng(20261112)
res = {"windows_total_by_series":cnt_all,"windows_used":cnt_ok}
def boot(arrs, fn, n=1000):
    arrs = np.array(arrs); N=len(arrs); out=[]
    for _ in range(n):
        out.append(fn(arrs[rng.integers(0,N,N)].sum(0)))
    return [float(np.percentile(out,2.5)), float(np.percentile(out,97.5))]
P3={}; P4={}
for s in SER:
    sz = {k:np.concatenate(sizes[s][k]) if sizes[s][k] else np.array([]) for k in (0,1)}
    n = [len(sz[0]),len(sz[1])]; c = [float(sz[0].sum()), float(sz[1].sum())]
    tot_c = sum(c)
    P3[s] = dict(trades_whole=n[0], trades_frac=n[1], frac_trade_share=n[1]/max(1,sum(n)),
      contracts_whole=c[0], contracts_frac=c[1], frac_contract_share=c[1]/max(1e-9,tot_c),
      median=[float(np.median(sz[k])) if n[k] else None for k in (0,1)],
      p90=[float(np.percentile(sz[k],90)) if n[k] else None for k in (0,1)],
      frac_share_by_mtc=[float(agg_mtc[s][i,1,1]/max(1e-9,agg_mtc[s][i,:,1].sum())) for i in range(15)],
      frac_share_by_utc4h=[float(agg_blk[s][i,1]/max(1e-9,agg_blk[s][i].sum())) for i in range(6)],
      yes_share=[float(yes_c[s][k,0]/max(1e-9,yes_c[s][k,1])) for k in (0,1)],
      mean_price_paid=[float(paid[s][k,0]/max(1e-9,paid[s][k,1])) for k in (0,1)])
    W = [(F,Wn) for (ss,F,Wn,A) in wins if ss==s]
    F=np.array([x[0] for x in W]); Wn=np.array([x[1] for x in W])
    P3[s]["corr_net_frac_vs_whole"] = float(np.corrcoef(F,Wn)[0,1]) if F.std()>0 and Wn.std()>0 else None
    P3[s]["n_windows"]=len(W)
    A = [x[3] for x in wins if x[0]==s]
    def peak(M): return M[:,0:10].sum()/(M.sum()*10/60)
    allA = [a.sum(0) for a in A]  # per window total by second (15->60)
    arr = np.array(A)  # N,15,60
    def peakN(M): return M[0:10].sum()/(M.sum()*10/60)
    P4[s] = dict(sec_share=[float(x) for x in arr.sum((0,1))/arr.sum()],
        peak_all=float(peakN(arr.sum((0,1)))), peak_all_ci=boot([a.sum(0) for a in A], peakN),
        peak_by_mtc=[float(peakN(arr[:,i,:].sum(0))) for i in range(15)])
    for lab,i in (("mtc6to7",6),("mtc2to3",2)):
        P4[s]["peak_"+lab]=float(peakN(arr[:,i,:].sum(0)))
        P4[s]["peak_"+lab+"_ci"]=boot([a[i] for a in A], peakN)
    B=[x[1] for x in bk if x[0]==s]
    if B:
        Barr=np.array(B)
        def ratio(M,i0,i1): return M[:,i1].sum()/max(1e-9,M[:,i0].sum())
        def agg(sel): return lambda M: M[sel,1].sum()/M[sel,0].sum()
        allsel=slice(0,15)
        P4[s]["depth_ratio_after_over_before_all"]=float(Barr[:,:,1].sum()/Barr[:,:,0].sum())
        P4[s]["depth_ratio_ci"]=boot(list(Barr), lambda M: M[:,1].sum()/M[:,0].sum())
        P4[s]["spread_before_after_all"]=[float(Barr[:,:,2].sum()/Barr[:,:,4].sum()), float(Barr[:,:,3].sum()/Barr[:,:,4].sum())]
        for lab,i in (("mtc6to7",6),("mtc2to3",2)):
            P4[s]["depth_ratio_"+lab]=float(Barr[:,i,1].sum()/max(1e-9,Barr[:,i,0].sum()))
            P4[s]["depth_ratio_"+lab+"_ci"]=boot(list(Barr), lambda M,i=i: M[i,1]/max(1e-9,M[i,0]))
            P4[s]["spread_"+lab]=[float(Barr[:,i,2].sum()/max(1,Barr[:,i,4].sum())), float(Barr[:,i,3].sum()/max(1,Barr[:,i,4].sum()))]
        P4[s]["boundary_pairs"]=int(Barr[:,:,4].sum())
res["P3"]=P3; res["P4"]=P4
json.dump(res, open(OUT,"w"), indent=1)
open(MARK,"w").write("done")
