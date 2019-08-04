import os
from get_overall_score import public_scheme

def get_indev_schemes():
    all_schemes = set()
    curr_dir = os.path.dirname(os.path.abspath(__file__))

    for test in os.listdir(curr_dir):
        if not test.endswith('_test'):
            continue

        test_path = os.path.join(curr_dir, test, 'data')
        for scheme in os.listdir(test_path):
            scheme_path = os.path.join(test_path, scheme)
            if not os.path.isdir(scheme_path):
                continue
            all_schemes.add(scheme)

    return all_schemes.difference(public_scheme)


indev_schemes = get_indev_schemes()

for s in indev_schemes:
    print(s)
