import json
import sys
from pathlib import Path
data = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
a = data['matrix']
if not a or not a[0] or any((len(row) != len(a[0]) for row in a)):
    raise ValueError('Expected a nonempty rectangular matrix')
Path(sys.argv[2]).write_text(json.dumps({'matrix': [list(row) for row in zip(*a)]}, indent=2), encoding='utf-8')
