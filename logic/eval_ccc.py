import json
import sys


def load_data(data_file):
    return [json.loads(line.strip()) for line in open(data_file)]


def unescape(str):
    placeholder = "<TMP>"
    assert placeholder not in str
    return str.replace("\\\\n", placeholder).replace("\\n", "\n").replace(placeholder, "\\n")


def parse_output(output):
    if "(a)" in output and "(b)" not in output:
        return "a"
    if "(b)" in output and "(a)" not in output:
        return "b"
    if "neither" in output.lower() or "both" in output.lower():
        return "FAILED"
    print("Failed to parse output:", output, flush=True)
    assert False


def main(data_file, output_file):
    data = load_data(data_file)

    correct = total = 0
    with open(output_file) as f:
        for line in f:
            id, expr, label, pred = line.strip().split("\t")
            pred = parse_output(unescape(pred))
            # print(expr, pred, label)
            if pred == label:
                correct += 1
            total += 1

    print(f"Accuracy: {correct} / {total} = {correct / total}")


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
