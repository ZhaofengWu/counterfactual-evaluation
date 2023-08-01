import json
import os
import sys


def main(input_file, output_file):
    assert not os.path.exists(output_file)
    with open(input_file) as f, open(output_file, "w") as o:
        for line in f:
            obj = json.loads(line)
            for premise, orig_premise in zip(
                obj["premises"].strip().split("\n"),
                obj["orig_premises"].strip().split("\n"),
                strict=True,
            ):
                if premise != orig_premise:
                    obj["target_premise"] = premise
                    obj["target_orig_premise"] = orig_premise
                    o.write(json.dumps(obj) + "\n")


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
