import random
import sys

import numpy as np
from tqdm import tqdm

random.seed(0)


def sample_number(n_digits, base):
    digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"[:base]
    number = "".join(str(random.choice(digits[1:] if i == 0 else digits)) for i in range(n_digits))
    assert number[0] != "0" and len(number) == n_digits  # i'm paranoid
    return number


def sample_single(n_digits, base):
    left = sample_number(n_digits, base)
    right = sample_number(n_digits, base)
    return f"{left}+{right}"


def get_label(expr, base):
    lhs, rhs = expr.split("+")
    lhs_base10 = int(lhs, base)
    rhs_base10 = int(rhs, base)
    sum_base10 = lhs_base10 + rhs_base10
    return np.base_repr(sum_base10, base)


def expr_is_hard(expr, base):
    if any("A" <= d <= "Z" for d in expr):
        return True
    label = get_label(expr, base)
    lhs, rhs = expr.split("+")
    base10_label = str(int(lhs) + int(rhs))
    return label != base10_label


def main(output_file, n_samples, n_digits, base):
    n_samples = int(n_samples)
    n_digits = int(n_digits)
    base = int(base)

    with open(output_file, "w") as f:
        for _ in tqdm(range(n_samples)):
            sample = sample_single(n_digits, base)
            if base != 10:
                while not expr_is_hard(sample, base):
                    sample = sample_single(n_digits, base)
            f.write(sample + "\n")


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
