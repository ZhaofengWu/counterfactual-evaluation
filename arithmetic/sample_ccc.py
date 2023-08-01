import sys

import numpy as np
from tqdm import tqdm


def main(output_file, n_samples, base):
    n_samples = int(n_samples)
    assert n_samples % 2 == 0
    base = int(base)

    digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    with open(output_file, "w") as f:
        for i in tqdm(range(int(n_samples // 2))):
            if i == 0:
                prefix = ""
            else:
                prefix = np.base_repr(i, base)
            f.write(f"{prefix}0\n")
            f.write(f"{prefix}{digits[base - 1]}\n")


if __name__ == "__main__":
    try:
        main(*sys.argv[1:])  # pylint: disable=no-value-for-parameter,too-many-function-args
    except Exception as e:
        import pdb
        import traceback

        if not isinstance(e, (pdb.bdb.BdbQuit, KeyboardInterrupt)):
            print("\n" + ">" * 100 + "\n")
            traceback.print_exc()
            print()
            pdb.post_mortem()
