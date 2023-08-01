import ast
import json
import os
import re
import sys

import numpy as np

VEC2DIR = {
    "top": (0, -1),
    "up": (0, -1),
    "above": (0, -1),
    "bottom": (0, 1),
    "down": (0, 1),
    "below": (0, 1),
    "left": (-1, 0),
    "right": (1, 0),
}


def canonicalize_name(name):
    return name.lower().replace("_", " ")


def fix_json_string(json_string):
    start_idx = json_string.find("{")
    end_idx = json_string.rfind("}")
    json_string = json_string[start_idx : end_idx + 1]
    brackets = []
    open2close = {"{": "}", "[": "]"}
    for char in json_string:
        if char in ["{", "["]:
            brackets.append(char)
        elif char in ["}", "]"]:
            if len(brackets) == 0:
                return None
            open_bracket = brackets.pop()
            if open2close[open_bracket] != char:
                return None
    if len(brackets) > 0:
        for bracket in brackets:
            json_string += open2close[bracket]
    return json_string.replace("(", "[").replace(")", "]")


def load_json(json_string):
    try:
        data = json.loads(json_string)
        return data
    except json.JSONDecodeError as e:
        json_string = fix_json_string(json_string)
        if json_string is None:
            return None
        try:
            data = json.loads(json_string)
            return data
        except json.JSONDecodeError as e:
            return None


def parse_objects(result):
    objects = None
    if "objects" in result:
        objects = result["objects"]
    elif isinstance(result, dict):
        objects = result
    try:
        for obj in objects:
            obj["x"] = float(obj["x"])
            obj["y"] = float(obj["y"])
    except Exception as e:
        return None
    if objects is not None:
        for obj in objects:
            obj["name"] = canonicalize_name(obj["name"])
    return objects


def parse_directions(result):
    if "directions" not in result:
        return None
    directions = result["directions"]
    for key, value in directions.items():
        vec = value
        if isinstance(value, str):
            try:
                vec = tuple(ast.literal_eval(value))
            except Exception:
                vec = VEC2DIR.get(value, value)
        elif isinstance(value, list):
            vec = tuple(value)
        elif isinstance(value, dict):
            try:
                vec = tuple([int(value["x"]), int(value["y"])])
            except Exception as e:
                print(f"Can't parse direction: {value} due to {e}")
        if (
            isinstance(vec, tuple)
            and isinstance(vec[0], int)
            and isinstance(vec[1], int)
        ):
            length = np.sqrt(int(vec[0]) ** 2 + int(vec[1]) ** 2)
            vec = (int(vec[0] / length), int(vec[1] / length))
        directions[key] = vec
    return directions


def parse_str(output):
    pattern = r"```json\s*([\s\S]+?)\s*```"
    matches = re.findall(pattern, output)
    results = []
    for match in matches[::-1]:
        result = match.strip().replace("\\n", "")
        result = load_json(result)
        if result is not None:
            results.append(result)
    return results


def parse_output(output):
    results = parse_str(output)
    outputs = []
    for result in results:
        objects = parse_objects(result)
        directions = parse_directions(result)
        if objects is not None:
            outputs.append((objects, directions))
    if not outputs:
        return None
    if len(outputs) != 1:
        assert ValueError(f"Expected 1 output, but got {len(outputs)}")
    return outputs[0]


def extract_objects_and_directions(text, num_objects=3):
    pattern = r"There is a (.*?) on the (.*?) side"
    matches = re.findall(pattern, text)

    obj2dir = {}

    for match in matches:
        obj2dir[canonicalize_name(match[0])] = match[1]
    assert len(obj2dir) == num_objects
    return obj2dir


def extract_direction_vectors(text):
    pattern = r"The (\w+) direction is \(([-\d]+), ([-\d]+)\)"
    matches = re.findall(pattern, text)
    dir2vec = {}
    for match in matches:
        direction = match[0]
        vector = (int(match[1]), int(match[2]))
        dir2vec[direction] = vector
    assert len(dir2vec) == 4, f"Expected 4 directions, but got {dir2vec}"
    return dir2vec


def eval_one(query, objects, directions):
    if not objects:
        return 0, None
    name2obj = {obj["name"]: obj for obj in objects}
    center_x = np.mean([obj["x"] for obj in objects])
    center_y = np.mean([obj["y"] for obj in objects])
    obj2dir = extract_objects_and_directions(query)
    dir2vec = extract_direction_vectors(query)

    control_acc = None
    if directions is not None:
        if dir2vec != directions:
            # print(f"Expected {dir2vec}, but got {directions}")
            control_acc = 0
        else:
            control_acc = 1

    num_objects = len(obj2dir)
    num_correct = 0
    for obj, dir in obj2dir.items():
        if obj not in name2obj:
            continue
        vec = dir2vec[dir]
        assert vec[0] == 0 or vec[1] == 0
        if vec[0] != 0:
            obj_x = name2obj[obj]["x"]
            if (obj_x - center_x) * vec[0] > 0:
                num_correct += 1
        if vec[1] != 0:
            obj_y = name2obj[obj]["y"]
            if (obj_y - center_y) * vec[1] > 0:
                num_correct += 1
    acc = num_correct / num_objects
    return acc, control_acc


def main(output_file, result_file=None):
    accs = []
    num_output = 0
    control_found = 0
    control_pass = 0
    with open(output_file) as f:
        for line in f:
            num_output += 1
            expr, response = line.strip().split("\t")[:2]
            out = parse_output(response)
            if out:
                objects, directions = parse_output(response)
                acc, control_acc = eval_one(expr, objects, directions)
                if control_acc is not None:
                    control_found += 1
                    control_pass += control_acc
            else:
                acc = 0
            accs.append(acc)

    num_examples = len(accs)
    object_acc = np.mean(accs) * 100
    acc = np.mean([acc == 1 for acc in accs]) * 100
    print("====================Summary====================")
    print(f"Output file: {output_file}")
    print(f"Number of examples: {num_examples}")
    print(f"Number of outputs: {num_output}")
    print(f"Object accuracy: {acc:.2f}")
    print(f"Accuracy: {object_acc:.2f}")
    print(f"Number of control found: {(control_found)}")
    print(f"Control/total: {100 * control_pass/len(accs):.2f}")
    print(f"Control/found: {100 * control_pass/control_found:.2f}")

    if result_file is not None:
        if not os.path.exists(result_file):
            header = "output_file,num_examples,num_output,acc,object_acc,control_found,control_pass\n"
            with open(result_file, "w") as f:
                f.write(header)
        with open(result_file, "a") as f:
            f.write(
                f"{output_file},{num_examples},{num_output},{acc},{object_acc},{control_found},{control_pass}\n"
            )


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
