import csv
import glob
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
rows = {}
for path in glob.glob('logs/*.out'):
    for line in Path(path).read_text(errors='replace').splitlines():
        fields = line.split(',')
        if len(fields) != 4 or fields[0] not in ['pthreads', 'openmp', 'c_mpi', 'python_mpi']:
            continue
        name, n, p, t = (fields[0], int(fields[1]), int(fields[2]), float(fields[3]))
        key = (name, n, p)
        rows[key] = min(rows.get(key, float('inf')), t)
if not rows:
    raise SystemExit('No benchmark results in logs/*.out')
Path('results').mkdir(exist_ok=True)
with open('results/benchmark.csv', 'w', newline='') as f:
    out = csv.writer(f)
    out.writerow(['implementation', 'n', 'workers', 'seconds', 'speedup', 'efficiency'])
    for (name, n, p), t in sorted(rows.items()):
        base = rows.get((name, n, 1))
        out.writerow([name, n, p, t, base / t if base else '', base / t / p if base else ''])
for n in sorted({k[1] for k in rows}):
    fig, ax = plt.subplots(1, 3, figsize=(15, 4))
    for name in sorted({k[0] for k in rows}):
        points = sorted(((p, t) for (impl, nn, p), t in rows.items() if impl == name and nn == n))
        if not points or (name, n, 1) not in rows:
            continue
        p, t = zip(*points)
        base = rows[name, n, 1]
        for axis, values in zip(ax, [t, [base / v for v in t], [base / v / w for w, v in points]]):
            axis.plot(p, values, 'o-', label=name)
    for axis, label in zip(ax, ['Time, s', 'Speedup', 'Efficiency']):
        axis.set(xlabel='Workers', ylabel=label)
        axis.grid(alpha=0.3)
        axis.legend()
    fig.suptitle(f'Natural cubic spline, n={n}')
    fig.tight_layout()
    fig.savefig(f'results/benchmark-{n}.png', dpi=160)
    plt.close(fig)
