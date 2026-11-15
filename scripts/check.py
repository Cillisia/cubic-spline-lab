import sys
import numpy as np
from scipy.interpolate import CubicSpline
data = np.loadtxt(sys.argv[1], skiprows=1, ndmin=2)
x, y = data.T
c = np.loadtxt(sys.argv[2], ndmin=2)
assert c.shape == (len(x) - 1, 4), c.shape
assert np.isfinite(c).all()
ref = CubicSpline(x, y, bc_type='natural')
h = np.diff(x)
q = x[:-1] + 0.37 * h
value = c[:, 0] + 0.37 * h * (c[:, 1] + 0.37 * h * (c[:, 2] + 0.37 * h * c[:, 3]))
np.testing.assert_allclose(value, ref(q), rtol=1e-09, atol=1e-09)
np.testing.assert_allclose(c, ref.c[::-1].T, rtol=1e-07, atol=1e-07)
np.testing.assert_allclose(c[:, 0] + h * (c[:, 1] + h * (c[:, 2] + h * c[:, 3])), y[1:], rtol=1e-09, atol=1e-09)
if len(c) > 1:
    np.testing.assert_allclose(c[:-1, 1] + 2 * h[:-1] * c[:-1, 2] + 3 * h[:-1] ** 2 * c[:-1, 3], c[1:, 1], rtol=1e-09, atol=1e-09)
    np.testing.assert_allclose(2 * c[:-1, 2] + 6 * h[:-1] * c[:-1, 3], 2 * c[1:, 2], rtol=1e-09, atol=1e-09)
np.testing.assert_allclose([2 * c[0, 2], 2 * c[-1, 2] + 6 * h[-1] * c[-1, 3]], 0, atol=1e-09)
print('PASS', sys.argv[2], 'max value error', np.max(np.abs(value - ref(q))))
