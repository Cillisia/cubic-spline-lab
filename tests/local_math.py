from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import numpy as np
from scipy.interpolate import CubicSpline
from spline_math import system, reduce_rows, coefficients
rng = np.random.default_rng(24)
total = 0
for n in [2, 3, 17, 128, 129, 1000]:
    for kind in ['constant', 'linear', 'sin', 'uneven']:
        x = np.cumsum(rng.uniform(0.1, 1, n)) if kind == 'uneven' else np.linspace(0, 20, n)
        y = np.full(n, 7.0) if kind == 'constant' else 2 * x - 3 if kind == 'linear' else np.sin(x)
        for p in [1, 2, 4, 7]:
            old = system(x, y)
            edges = np.arange(p + 1) * n // p
            stride = 1
            while stride < n:
                old = np.concatenate([reduce_rows(old, int(a), int(b), stride) for a, b in zip(edges[:-1], edges[1:])])
                stride *= 2
            m = old[:, 3] / old[:, 1]
            c = coefficients(x, y, m, 0, n - 1)
            reference = CubicSpline(x, y, bc_type='natural')
            np.testing.assert_allclose(c, reference.c[::-1].T, rtol=1e-07, atol=1e-07)
            q = 0.37 * np.diff(x)
            values = c[:, 0] + q * (c[:, 1] + q * (c[:, 2] + q * c[:, 3]))
            np.testing.assert_allclose(values, reference(x[:-1] + q), rtol=1e-09, atol=1e-09)
            total += 1
print(f'PASS: {total} numerical kernel cases against SciPy; actual MPI/C runs still required')
