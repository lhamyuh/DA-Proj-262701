"""A 复核（第二遍）：敏感性、阈值档位，以及 log.md 中 200 格/202 万 的来源。"""
import numpy as np
import pandas as pd

zm = pd.read_csv("handoff/2026-11-10/zone_master.csv")
acc = pd.read_csv("handoff/2026-11-10/accessibility.csv")
study = zm[zm.in_study.astype(bool)][["cell_id", "pop"]]


def spearman(x, y):
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    rx -= rx.mean(); ry -= ry.mean()
    return float((rx @ ry) / np.sqrt((rx @ rx) * (ry @ ry)))


def load(d0):
    a = acc[acc.d0_m == d0][["cell_id", "A_i", "n_stations_in_radius"]].merge(study, on="cell_id")
    return a


base = load(3000)
v = base[base["pop"] > 0].reset_index(drop=True)
print("=== 阈值档位（3 km，有效格网 951）===")
for q in (0.10, 0.20, 0.30):
    thr = float(np.percentile(v.A_i * 1000, q * 100))
    low = (v.A_i * 1000) < thr
    nc = v.n_stations_in_radius.values == 0
    print(f"q={q:.0%}  thr={thr:.6f} 低可达 {int(low.sum()):>3d} 格 / {v['pop'][low].sum():>10,.0f} 人"
          f" | 并集 {int((low | nc).sum()):>3d} 格 / {v['pop'][low | nc].sum():>10,.0f} 人")

print("\n=== 半径敏感性（A_i 秩相关 + 并集重合）===")
sets = {}
for d0 in (1000, 3000, 5000):
    a = load(d0)
    a = a[a["pop"] > 0].reset_index(drop=True)
    thr = float(np.percentile(a.A_i * 1000, 20))
    low = (a.A_i * 1000) < thr
    nc = a.n_stations_in_radius.values == 0
    sets[d0] = set(a.cell_id[(low | nc)])
    if d0 in (1000, 5000):
        print(f"  rho(3000,{d0}) = {spearman(base[base['pop']>0].A_i.values, a.A_i.values):.6f}")

for d0 in (1000, 5000):
    inter = len(sets[3000] & sets[d0])
    uni = len(sets[3000] | sets[d0])
    print(f"  并集 {3000} vs {d0}: 交集 {inter} / 并集 {uni} = jaccard {inter/uni:.6f}"
          f" | 3km 集合保留率 {inter/len(sets[3000]):.6f}")

print("\n=== log.md 中「200 格 / 2,023,405」的来源排查 ===")
allc = base.sort_values("A_i").reset_index(drop=True)
for n in (199, 200, 201):
    print(f"  997 格（含零人口）按 A 升序前 {n} 格：人口 {allc['pop'][:n].sum():,.0f}")
vv = base[base["pop"] > 0].sort_values("A_i").reset_index(drop=True)
for n in (190, 199, 200, 191):
    print(f"  951 有效格网按 A 升序前 {n} 格：人口 {vv['pop'][:n].sum():,.0f}")

print("\n=== bottom20 口径差异排查 ===")
for d0 in (3000,):
    a = load(d0); a = a[a["pop"] > 0].sort_values("A_i").reset_index(drop=True)
    W = a["pop"].values.astype(float); A = a.A_i.values * 1000
    target = 0.2 * W.sum()
    cw = np.cumsum(W)
    k = int(np.searchsorted(cw, target))
    whole = A[:k].sum() * 0 + (A[:k] * W[:k]).sum() / W[:k].sum()
    # 末格按份额拆分
    prev = cw[k - 1]
    frac = (target - prev) / W[k]
    w2 = W[:k].copy(); w2 = np.append(w2, W[k] * frac)
    a2 = np.append(A[:k], A[k])
    exact = (a2 * w2).sum() / w2.sum()
    print(f"  整格口径（{k} 格, 人口 {W[:k].sum():,.0f}）均值 {whole:.6f}")
    print(f"  末格拆分（人口恰好 {target:,.0f}）均值 {exact:.6f}")
