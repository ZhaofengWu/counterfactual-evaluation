import json
import os
from pathlib import Path
import random
import sys

random.seed(0)
sys.path.append(str(Path(__file__).parent.parent.absolute()))

from query_utils import query_batch


def load_data(data_file):
    return [json.loads(line.strip()) for line in open(data_file)]


def templatize(obj):
    premises = obj["premises"].strip()
    new_premises = []
    for line in premises.split("\n"):
        line = line.strip()
        assert line[-1] in {".", '"'}
        new_premises.append(line)
    premises = " ".join(new_premises)

    option_a = obj["target_premise"]
    option_b = obj["target_orig_premise"]
    label = "a"
    if random.random() > 0.5:
        option_a, option_b = option_b, option_a
        label = "b"
    return f"Consider the following premises: \"{premises}\" Assuming no other commonsense or world knowledge, which sentence between (a) \"{option_a}\" and (b) \"{option_b}\" is definitely true? Answer just \"(a)\" or \"(b)\" and nothing else. You MUST choose one and only one, so DO NOT say neither or both.", label


def escape(str):
    assert "\t" not in str and "\\\\n" not in str
    return str.replace("\\n", "\\\\n").replace("\n", "\\n")


def parse_bool(flag):
    if isinstance(flag, bool):
        return flag
    assert flag in {"True", "False"}
    return flag == "True"


def main(data_file, model_name, output_file):
    assert not os.path.exists(output_file)

    data = load_data(data_file)
    assert all(
        len(d["premises"].strip().split("\n")) == len(d["premises-FOL"].strip().split("\n"))
        for d in data
    )
    templatized, labels = zip(*[templatize(obj) for obj in data])

    responses = query_batch(templatized, model_name)

    with open(output_file, "w") as log:
        for obj, template, response, label in zip(data, templatized, responses, labels, strict=True):
            log.write(
                f"{obj['example_id']}\t{escape(template)}\t{escape(label)}\t{escape(response)}\n"
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
