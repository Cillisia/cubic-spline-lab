import numpy as np

def system(x, y):
    h = np.diff(x)
    rows = np.zeros((len(x), 4))
    rows[:, 1] = 1
    rows[1:-1, 0] = h[:-1]
    rows[1:-1, 1] = 2 * (h[:-1] + h[1:])
    rows[1:-1, 2] = h[1:]
    rows[1:-1, 3] = 6 * np.diff(np.diff(y) / h)
    return rows

def reduce_rows(old, lo, hi, stride):
    idx = np.arange(lo, hi)
    local = np.zeros((hi - lo, 4))
    local[:, 1] = old[lo:hi, 1]
    local[:, 3] = old[lo:hi, 3]
    for direction, col, other in [(-1, 0, 2), (1, 2, 0)]:
        neighbor = idx + direction * stride
        mask = (neighbor >= 0) & (neighbor < len(old))
        q = old[neighbor[mask]]
        factor = -old[idx[mask], col] / q[:, 1]
        local[mask, col] = factor * q[:, col]
        local[mask, 1] += factor * q[:, other]
        local[mask, 3] += factor * q[:, 3]
    return local

def coefficients(x, y, m, lo, hi):
    h = x[lo + 1:hi + 1] - x[lo:hi]
    return np.column_stack((y[lo:hi], (y[lo + 1:hi + 1] - y[lo:hi]) / h - h * (2 * m[lo:hi] + m[lo + 1:hi + 1]) / 6, m[lo:hi] / 2, (m[lo + 1:hi + 1] - m[lo:hi]) / (6 * h)))
