import json
import numpy as np
import numpy.linalg as la
from pprint import pprint

with open('res.json') as f:
    d = json.load(f)
    # pprint(d)
    for test in d["Tests"]:
        for _, scores in test.items():
            if _ == 'name':
                continue
            vals = [x for x in scores.values()]
            val_norm = la.norm(vals, 1)
            for k, v in scores.items():
                scores[k] = round(v / val_norm, 3)

    # pprint(d)
    with open('res1.json', 'w') as f:
        f.write(json.dumps(d, indent=4))
