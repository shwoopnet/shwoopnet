import math, random
random.seed(20261112)
def q_for_pf(p, pf):
    # buy at price p, fee f per contract; win pays 1-p-f, loss costs p+f ; PF = q*(1-c)/((1-q)*c), c = p+f
    f = 0.07*p*(1-p); c = p+f
    r = pf*c/(1-c); return r/(1+r), c
def n_for_z(p, pf, z, power_z=0.0):
    q, c = q_for_pf(p, pf); mu = q - c; sd = math.sqrt(q*(1-q))
    return ((z+power_z)*sd/mu)**2
print("A. Independent trades needed for a TRUE cash PF of 1.5 (and 1.3) to reach the deflated z bar")
print("price  winrate@PF1.5  n(z5.34,50%)  n(z5.34,80%)  n(z4.39,50%)  n(z2.0,50%) | PF1.3: n(z5.34,50%)")
for p in (0.10,0.20,0.35,0.50,0.70,0.92):
    q,c=q_for_pf(p,1.5)
    print("%.2f   %.3f          %6d        %6d        %6d        %5d   | %6d"%(p,q,n_for_z(p,1.5,5.34),n_for_z(p,1.5,5.34,0.84),n_for_z(p,1.5,4.39),n_for_z(p,1.5,2.0),n_for_z(p,1.3,5.34)))
def sim(p, true_pf, n, rule, reps=20000):
    q,c=q_for_pf(p,true_pf); hit=0
    for _ in range(reps):
        w=[1 if random.random()<q else 0 for _ in range(n)]
        if rule(w,c): hit+=1
    return hit/reps
def pf(ws,c):
    g=sum(ws)*(1-c); l=(len(ws)-sum(ws))*c
    return g/l if l>0 else 99
def halves(th):
    return lambda w,c: pf(w[:len(w)//2],c)>=th and pf(w[len(w)//2:],c)>=th
def whole(th):
    return lambda w,c: pf(w,c)>=th
def two_of_three(th):
    def r(w,c):
        k=len(w)//3; parts=[w[:k],w[k:2*k],w[2*k:]]
        return pf(w,c)>=th and sum(1 for x in parts if pf(x,c)>=th)>=2
    return r
print()
print("B. How often each screen PASSES, by true cash PF (simulated, independent trades)")
print("screen                                   price  P(pass|PF 1.0)  P(pass|PF 0.9)  P(pass|PF 1.5)")
for name,n,rule in (("PF>=1.3 in both halves, n 40 per half",80,halves(1.3)),("PF>=1.5 whole sample, n 40",40,whole(1.5)),("PF>=1.5 whole sample, n 100",100,whole(1.5)),("PF>=1.5 whole sample, n 300",300,whole(1.5)),("proven bar: PF>=1.3 over 100, 2 of 3 windows",100,two_of_three(1.3)),("shadow gate: PF>=1.3 over 150, 2nd half>=1.2",150,lambda w,c: pf(w,c)>=1.3 and pf(w[75:],c)>=1.2)):
    for p in (0.20,0.50,0.92):
        print("%-40s %.2f     %.3f           %.3f           %.3f"%(name,p,sim(p,1.0,n,rule),sim(p,0.9,n,rule),sim(p,1.5,n,rule)))
print()
print("C. Chance a card is FALSIFIED (development PF under 1.0) when the truth is PF 1.0, 1.2, 1.5")
for n in (40,100,300):
    for p in (0.20,0.50):
        print("n %3d price %.2f: P(PF<1 | true 1.0) %.2f  | true 1.2 %.2f | true 1.5 %.2f"%(n,p,sim(p,1.0,n,lambda w,c: pf(w,c)<1.0,8000),sim(p,1.2,n,lambda w,c: pf(w,c)<1.0,8000),sim(p,1.5,n,lambda w,c: pf(w,c)<1.0,8000)))
