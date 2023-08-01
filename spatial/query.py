import json
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.absolute()))

from query_utils import query_batch

DIR2VEC_DICT = {
    "default": {
        "north": (0, -1),
        "south": (0, 1),
        "east": (1, 0),
        "west": (-1, 0),
    },
    "random": {
        "north": (0, -1),
        "south": (1, 0),
        "east": (-1, 0),
        "west": (0, 1),
    },
    "r90": {
        "north": (-1, 0),
        "south": (1, 0),
        "east": (0, -1),
        "west": (0, 1),
    },
    "r180": {
        "north": (0, 1),
        "south": (0, -1),
        "east": (-1, 0),
        "west": (1, 0),
    },
    "r270": {
        "north": (1, 0),
        "south": (-1, 0),
        "east": (0, 1),
        "west": (0, -1),
    },
    "vflip": {
        "north": (0, 1),
        "south": (0, -1),
        "east": (1, 0),
        "west": (-1, 0),
    },
    "hflip": {
        "north": (0, -1),
        "south": (0, 1),
        "east": (-1, 0),
        "west": (1, 0),
    },
}


SAMPLE_ROOM = {
    "name": "??",
    "width": 500,
    "height": 500,
    "directions": {"north": "??", "south": "??", "east": "??", "west": "??"},
    "objects": [{"name": "??", "x": "??", "y": "??"}],
}


def load_data(data_file):
    return [line.strip() for line in open(data_file)]


def templatize(expr, type, cot):
    dir_str = " ".join(
        [f"The {dir} direction is {vec}." for dir, vec in DIR2VEC_DICT[type].items()]
    )
    prompt = f"""{expr} We define the following directions. {dir_str} What's the layout of the room in the following format? You can estimate the size of the objects.
```json
{json.dumps(SAMPLE_ROOM)}
```"""
    if cot:
        prompt += """
Let's think step by step.
"""
    return prompt


def escape(str):
    return str.replace("\n", "\\n")


def parse_bool(flag):
    if isinstance(flag, bool):
        return flag
    assert flag in {"True", "False"}
    return flag == "True"


def main(data_file, model_name, output_file, type, cot):
    data = load_data(data_file)
    cot = parse_bool(cot)

    assert not os.path.exists(output_file)
    templatized = [templatize(obj, type, cot) for obj in data]

    responses = query_batch(templatized, model_name)
    with open(output_file, "w") as log:
        for obj, response in zip(templatized, responses):
            log.write(f"{escape(obj)}\t{escape(response)}\n")


if __name__ == "__main__":
    try:
        main(
            *sys.argv[1:]
        )  # pylint: disable=no-value-for-parameter,too-many-function-args
    except Exception as e:
        import pdb
        import traceback

        if not isinstance(e, (pdb.bdb.BdbQuit, KeyboardInterrupt)):
            print("\n" + ">" * 100 + "\n")
            traceback.print_exc()
            print()
            pdb.post_mortem()
