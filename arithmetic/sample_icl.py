import random
from pathlib import Path
import sys

random.seed(0)
sys.path.append(str(Path(__file__).parent.parent.absolute()))

from arithmetic.sample import sample_single, expr_is_hard


def main(input_file, output_file, n_demos, n_digits, base):
    n_demos = int(n_demos)
    n_digits = int(n_digits)
    base = int(base)

    with open(input_file, "r") as f, open(output_file, "w") as o:
        for line in f:
            line = line.strip()
            o.write(line + "\t")
            for i in range(n_demos):
                sample = sample_single(n_digits, base)
                while (base != 10 and not expr_is_hard(sample, base)) or set(sample.split("+")) == set(line.split("+")):
                    sample = sample_single(n_digits, base)
                o.write(sample + ("," if i != n_demos - 1 else ""))
            o.write("\n")


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
