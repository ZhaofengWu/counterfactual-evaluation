import os
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent.absolute()))

from query_utils import query_batch


def load_data(data_file):
    return [line.strip() for line in open(data_file)]


def templatize(expr, base):
    digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return f"You are a mathematician. Assuming that all numbers are in base-{base} where the digits are \"{digits[:base]}\", what is the next number after {expr}? Do this by counting the few preceding numbers and completing the sequence. End the response with the result."


def escape(str):
    return str.replace("\n", "\\n")


def main(data_file, base, model_name, output_file):
    base = int(base)
    data = load_data(data_file)

    assert not os.path.exists(output_file)

    templatized = [templatize(expr, base) for expr in data]
    responses = query_batch(templatized, model_name)

    with open(output_file, "w") as log:
        for expr, response in zip(data, responses, strict=True):
            log.write(f"{expr}\t{escape(response)}\n")


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
