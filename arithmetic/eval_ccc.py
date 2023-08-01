from pathlib import Path
import re
import sys

sys.path.append(str(Path(__file__).parent.parent.absolute()))

from arithmetic.eval import get_label


def parse_output(output):
    original_output = output
    if output.endswith(", with each digit incremented as needed."):
        output = output[:-len(", with each digit incremented as needed.")]
    if output.endswith("End of response."):
        output = output[:-len("End of response.")]
    output = output.rstrip()

    if (match := re.search("^[0-9A-Z]+$", output)) is not None:
        return output

    if (match := re.search(r"\n([0-9A-Z]+ \+ [0-9A-Z]+ = )?([0-9A-Z]+)( \(?(in )?base-[0-9]+\)?)?\.?$", output)) is not None:
        return match.groups()[-3]
    if (match := re.search(r"^([0-9A-Z]+ \+ [0-9A-Z]+ = )?([0-9A-Z]+)( \(?(in )?base-[0-9]+\)?)?\.?$", output)) is not None:
        return match.groups()[-3]
    if (match := re.search(r"(would be|is|as)( therefore)?:?\s*([0-9]+\. )?([0-9A-Z]+ \+ [0-9A-Z]+ = )?([0-9A-Z]+)\.?$", output)) is not None:
        return match.groups()[-1]
    if (match := re.search(r"in base-[0-9]+:?\s+([0-9]+\. )?([0-9A-Z]+)\.?$", output)) is not None:
        return match.groups()[-1]
    if (match := re.search(r"(written as|is|would be|the number) ([0-9A-Z]+)( \(?(in )?base-[0-9]+\)?)?(, which is (equal|equivalent) to [0-9A-Z +*=^]+( in (decimal|base-[0-9]+))?)?\.$", output)) is not None:
        return match.groups()[-7]
    if (match := re.search(r"\n[0-9]+\. ([0-9A-Z]+)\.?$", output)) is not None:
        return match.groups()[-1]
    if (match := re.search(r"(([0-9A-Z]+\+1=)?[0-9A-Z]+(, |\n))+([0-9A-Z]+\+1=)?([0-9A-Z]+)\n*\.*$", output)) is not None:
        return match.groups()[-1]
    if (match := re.search(r"(answer|result): ([0-9A-Z]+)\.?$", output)) is not None:
        return match.groups()[-1]
    if (match := re.search(r"\.\.\. ([0-9A-Z]+)\.?$", output)) is not None:
        return match.groups()[-1]
    # The next number after 360 in base-8 is 361,
    if (match := re.search(r"(T|t)he next number after [0-9A-Z]+( in base-[0-9]+)? is:?\s*([0-9A-Z]+)(,| \()", output)) is not None:
        return match.groups()[-2]

    print("Failed to parse output:", original_output)
    assert False


def unescape(str):
    return str.replace("\\n", "\n")


def main(output_file, base):
    base = int(base)

    correct = total = 0
    with open(output_file) as f:
        for line in f:
            expr, orig_pred = line.strip().split("\t")
            orig_pred = unescape(orig_pred)
            pred = parse_output(orig_pred)
            label = get_label(f"{expr}+1", base)
            assert label[-1] == "0" or expr[-1] == "0"  # this is how the ccc is set up

            if label == pred:
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
