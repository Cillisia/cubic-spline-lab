import argparse
from pathlib import Path
import numpy as np
p = argparse.ArgumentParser()
p.add_argument('output')
p.add_argument('--n', type=int, default=100000)
p.add_argument('--case', choices=['sin', 'linear', 'constant', 'two', 'uneven'], default='sin')
a = p.parse_args()
if a.n < 2:
    p.error('n >= 2 required')
x = np.linspace(0, 20, a.n)
if a.case == 'two':
    x = np.array([0.0, 2.0])
if a.case == 'uneven':
    x = np.cumsum(np.random.default_rng(24).uniform(0.1, 1, a.n))
y = 2 * x - 3 if a.case in ['linear', 'two'] else np.full_like(x, 7.0) if a.case == 'constant' else np.sin(x)
Path(a.output).parent.mkdir(parents=True, exist_ok=True)
np.savetxt(a.output, np.column_stack((x, y)), header=str(len(x)), comments='', fmt='%.17g')
