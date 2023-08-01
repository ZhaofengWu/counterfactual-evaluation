import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.absolute()))

from query_utils import query_batch


def load_data(data_file):
    return [line.strip() for line in open(data_file)]


def templatize(obj, type, prompt_version, cot):
    det = "an" if obj[0].lower() in "aeiou" else "a"

    prompt = f"You are an expert programmer and drawer. Imagine an image: there is a line at the top and {det} {obj} in the middle. "
    if prompt_version == 1:
        if type == "default":
            prompt += "Can you try your best to draw this image using the `processing` language? "
        elif type.startswith("r"):
            degree = int(type[1:])
            prompt += f"Can you rotate this image {degree} degrees and try your best to draw it using the `processing` language? "
        elif type == "vflip":
            prompt += f"Can you flip this image vertically and try your best to draw it using the `processing` language? "
        else:
            raise NotImplementedError(f"Unknown type: {type}")
        prompt += "Please do not use any built-in transformation functions, such as `rotate` and `scale`. Also, avoid defining any custom transformation functions yourself. Do not load any existing images. "
    else:
        if type == "default":
            prompt += f"Can you try your best to draw the line and the {obj} using the `processing` language? "
        elif type.startswith("r"):
            degree = int(type[1:])
            prompt += f"Can you rotate this image {degree} degrees and try your best to draw the {degree}-degree rotated line and the {degree}-degree rotated {obj} using the `processing` language? "
        elif type == "vflip":
            prompt += f"Can you flip this image vertically and try your best to draw the vertically flipped line and the vertically flipped {obj} using the `processing` language? "
        else:
            raise NotImplementedError(f"Unknown type: {type}")
        prompt += "Please do not use any built-in transformation functions, such as `rotate`, `scale`, and `translate`. Also, avoid defining any custom transformation functions yourself. Do not load any existing images. "
    if type != "default":
        prompt += "Do not draw the original objects. "
    prompt += f"Please include as many details of the {obj} as possible and put everything together in the end."
    if cot:
        prompt += " Let's think step by step."
    return prompt


def escape(str):
    assert "\t" not in str and "\\\\n" not in str
    return str.replace("\\n", "\\\\n").replace("\n", "\\n")


def parse_bool(flag):
    if isinstance(flag, bool):
        return flag
    assert flag in {"True", "False"}
    return flag == "True"


def main(data_file, model_name, output_file, type, prompt_version, cot):
    data = load_data(data_file)
    prompt_version = int(prompt_version)
    cot = parse_bool(cot)

    assert not os.path.exists(output_file)
    templatized = [templatize(obj, type, prompt_version, cot) for obj in data]

    responses = query_batch(templatized, model_name)

    with open(output_file, "w") as log:
        for template, response in zip(templatized, responses):
            log.write(f"{escape(template)}\t{escape(response)}\n")


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
