"""A 的独立复核：用 handoff/2026-11-10 的原始输出复算 B 的四张表。"""
import numpy as np
import pandas as pd

ZM = "handoff/2026-11-10/zone_master.csv"
AC = "handoff/2026-11-10/accessibility.csv"
zm = pd.read_csv(ZM)
acc = pd.read_csv(AC)


def weighted_gini(a, w):
    """G = ΣΣ w_i w_j |a_i-a_j| / (2 * mean_w * (Σw)^2)"""
    order = np.argsort(a)
    a, w = a[order], w[order]
    cw = np.cumsum(w)
    total_w = w.sum()
    # ΣΣ w_i w_j |a_i - a_j| = 2 * Σ_j w_j (a_j * W_{<j} - Σ_{i<j} w_i a_i)
    cum_wa = np.cumsum(w * a)
    left_w = cw - w
    left_wa = cum_wa - w * a
    s = 2.0 * np.sum(w * (a * left_w - left_wa))
    mean_w = np.sum(w * a) / total_w
    return s / (2.0 * mean_w * total_w ** 2)


def wpct(a, w, q):
    """人口加权分位数"""
    o = np.argsort(a)
    a, w = a[o], w[o]
    cw = np.cumsum(w) / w.sum()
    return float(a[np.searchsorted(cw, q)])


def bottom_share(a, w, q=0.2):
    """按 A 升序累计人口，取最低 q 份额人口，返回其人口加权均值与人口数"""
    o = np.argsort(a)
    a, w = a[o], w[o]
    cw = np.cumsum(w)
    k = np.searchsorted(cw, q * w.sum())
    grp_a, grp_w = a[:k + 1], w[:k + 1]
    return float(np.sum(grp_a * grp_w) / grp_w.sum()), float(grp_w.sum())


print("=== 0. 输入核对 ===")
print(f"zone_master 行数 {len(zm)} | accessibility 行数 {len(acc)} | d0 取值 {sorted(acc.d0_m.unique())}")
study = zm[zm.in_study.astype(bool)]
print(f"in_study 格网 {len(study)} | 人口 {study['pop'].sum():,.0f} | pop>0 格网 {(study['pop'] > 0).sum()}")

rows = []
for d0 in (1000, 3000, 5000):
    a = acc[acc.d0_m == d0][["cell_id", "A_i", "n_stations_in_radius"]].merge(
        study[["cell_id", "pop"]], on="cell_id")
    a = a[a["pop"] > 0].copy()
    A = a.A_i.values * 1000.0  # 桩/千人
    W = a["pop"].values.astype(float)
    no_cov = a.n_stations_in_radius.values == 0
    thr = float(np.percentile(A, 20))
    low = A < thr
    both = no_cov | low
    bm, bp = bottom_share(A / 1000.0, W, 0.2)
    rows.append(dict(
        d0=d0, valid=len(a), pop=W.sum(),
        no_cov_cells=int(no_cov.sum()), no_cov_pop=W[no_cov].sum(),
        thr_p20=thr, low_cells=int(low.sum()), low_pop=W[low].sum(),
        overlap=int((no_cov & low).sum()),
        union_cells=int(both.sum()), union_pop=W[both].sum(),
        union_share=W[both].sum() / W.sum(),
        wmean=A @ W / W.sum(), gini=weighted_gini(A / 1000.0, W),
        p10=wpct(A, W, 0.10) , bottom20_mean=bm * 1000, bottom20_pop=bp,
    ))

R = pd.DataFrame(rows)
pd.set_option("display.width", 200)
print("\n=== 1. A 独立复算 ===")
print(R.round(4).to_string(index=False))

print("\n=== 2. 与 B 的 equity_table 对比 ===")
B = pd.read_csv("handoff/2026-11-14/tables/equity_table.csv")
for _, r in R.iterrows():
    b = B[B.d0_m == r.d0].iloc[0]
    print(f"d0={r.d0}")
    for k, bv in (("wmean", "weighted_mean_per_1000"), ("gini", "gini"),
                  ("p10", "p10"), ("bottom20_mean", "bottom20_mean_per_1000"),
                  ("bottom20_pop", "bottom20_population")):
        av = r[k]
        d = abs(av - float(b[bv]))
        flag = "OK " if d <= max(1e-6, abs(float(b[bv])) * 1e-6) else "!! "
        print(f"   {flag}{k:14s} A={av:14.6f}  B={float(b[bv]):14.6f}  Δ={d:.2e}")

print("\n=== 3. 与 B 的 desert_table 对比（20% 档）===")
D = pd.read_csv("handoff/2026-11-14/tables/desert_table.csv")
for _, r in R.iterrows():
    b = D[(D.d0_m == r.d0) & (np.isclose(D.threshold_share, 0.2))].iloc[0]
    for k, bv in (("no_cov_cells", "no_coverage_cells"), ("no_cov_pop", "no_coverage_population"),
                  ("low_cells", "low_access_cells"), ("low_pop", "low_access_population"),
                  ("overlap", "overlap_cells"), ("union_cells", "union_cells"),
                  ("union_pop", "union_population")):
        av, bb = r[k], float(b[bv])
        flag = "OK " if abs(av - bb) <= max(1e-6, abs(bb) * 1e-6) else "!! "
        print(f"   d0={r.d0:<5} {flag}{k:12s} A={av:14.1f}  B={bb:14.1f}  Δ={av-bb:+.1f}")
