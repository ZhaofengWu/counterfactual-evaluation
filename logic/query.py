import json
import os
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent.absolute()))

from query_utils import query_batch


def load_data(data_file):
    return [json.loads(line.strip()) for line in open(data_file)]


def templatize(obj, eval_orig=False):
    if eval_orig:
        premises = obj["orig_premises"].strip()
    else:
        premises = obj["premises"].strip()
    new_premises = []
    for line in premises.split("\n"):
        line = line.strip()
        if line[-1] in {".", '"'}:
            new_premises.append(line)
        elif "a" <= line[-1] <= "z" or "A" <= line[-1] <= "Z":
            new_premises.append(line + ".")
        else:
            assert False
    premises = " ".join(new_premises)
    if eval_orig:
        conclusion = obj["orig_conclusion"].strip()
    else:
        conclusion = obj["conclusion"].strip()
    return f"Consider the following premises: \"{premises}\" Assuming no other commonsense or world knowledge, is the sentence \"{conclusion}\" necessarily true, necessarily false, or neither? Let's think step by step, and end the response with either \"necessarily true\", \"necessarily false\", or \"neither\"."


def escape(str):
    assert "\t" not in str and "\\\\n" not in str
    return str.replace("\\n", "\\\\n").replace("\n", "\\n")


def parse_bool(flag):
    if isinstance(flag, bool):
        return flag
    assert flag in {"True", "False"}
    return flag == "True"


def main(data_file, model_name, output_file, eval_orig=False):
    assert not os.path.exists(output_file)
    eval_orig = parse_bool(eval_orig)

    data = load_data(data_file)
    assert all(
        len(d["premises"].strip().split("\n")) == len(d["premises-FOL"].strip().split("\n"))
        for d in data
    )
    templatized = [templatize(obj, eval_orig=eval_orig) for obj in data]

    responses = query_batch(templatized, model_name)

    with open(output_file, "w") as log:
        for obj, template, response in zip(data, templatized, responses, strict=True):
            log.write(
                f"{obj['example_id']}\t{escape(template)}\t{escape(obj['label'])}\t{escape(response)}\n"
            )


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
