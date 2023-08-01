"""Evaluate chess queries. Requires running query_chess.py first."""


import ast
import json
import os.path
import re
import sys
from sklearn.metrics import f1_score

import numpy as np


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
    if isinstance(result, list):
        objects = result
    elif (
        "rooms" in result
        and len(result["rooms"]) > 0
        and "objects" in result["rooms"][0]
        and len(result["rooms"][0]["objects"]) > 0
    ):
        objects = result["rooms"][0]["objects"]
    if "objects" in result:
        objects = result["objects"]
    if objects is None:
        return None
    try:
        for obj in objects:
            obj["x"] = float(obj["x"])
            obj["y"] = float(obj["y"])
    except ValueError:
        return None
    return objects


def parse_directions(result):
    if "directions" not in result:
        return None
    directions = result["directions"]
    for key, value in directions.items():
        if isinstance(value, str):
            try:
                directions[key] = tuple(ast.literal_eval(value))
            except SyntaxError:
                return None
        elif isinstance(value, list):
            directions[key] = tuple(value)
    return directions


def parse_str(output):
    pattern = r"```\s*([\s\S]+?)\s*```"
    matches = re.findall(pattern, output)
    results = []
    for match in matches:
        result = match.lstrip("json").strip().replace("\\n", "")
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
        obj2dir[match[0]] = match[1]
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
    name2obj = {obj["name"]: obj for obj in objects}
    center_x = np.mean([obj["x"] for obj in objects])
    center_y = np.mean([obj["y"] for obj in objects])
    obj2dir = extract_objects_and_directions(query)
    dir2vec = extract_direction_vectors(query)

    if directions is not None:
        assert dir2vec == directions, f"Expected {dir2vec}, but got {directions}"

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
    return acc


readable_name = {
    "gpt-4-0314": "gpt4",
    "gpt-3.5-turbo-0301": "gpt3.5",
    "claude-v1.3": "claude",
    "models/text-bison-001": "palm2",
}


def main():
    for exp in os.listdir("chess/output"):
        if "chess" not in exp:
            continue
        for model_name in ["gpt-4-0314", "gpt-3.5-turbo-0301", "claude-v1.3", "models/text-bison-001"]:
            for cot in [True, False]:
                output_dir = f"chess/output/{exp}/{model_name.replace('models/', '')}_0cot{cot}"
                if not os.path.exists(output_dir):
                    continue
                print("="*25, exp, readable_name[model_name], f"cot = {cot}", "="*25)

                for mode in ["real_world", "counter_factual"]:
                    # control
                    output_file = os.path.join(output_dir, f"{mode}_control.txt")
                    if not os.path.exists(output_file):
                        continue
                    pos_bishop = ["c1", "f1", "c8", "f8"] if mode == "real_world" else ["b1", "g1", "b8", "g8"]
                    pos_knight = ["b1", "g1", "b8", "g8"] if mode == "real_world" else ["c1", "f1", "c8", "f8"]
                    gt_dict = {
                        "white bishop": pos_bishop[:2],
                        "black bishop": pos_bishop[2:],
                        "white knight": pos_knight[:2],
                        "black knight": pos_knight[2:]
                    }
                    success = 0
                    count = 0
                    with open(output_file, "r") as f:
                        for line in f:
                            line = line.lower()
                            question, answer = line.split("*")
                            question = question.strip()
                            answer = answer.strip()
                            for pos in gt_dict[question]:
                                count += 1
                                if pos in answer:
                                    success += 1
                    print(f"Control accuracy for {mode} is {success / count * 100 :.1f}%")

                    # non control
                    all_pred = []
                    all_gt = []
                    for real_world_legal in [True, False]:
                        for counter_factual_legal in [True, False]:
                            output_file = \
                                f"{output_dir}/{mode}_{'T' if real_world_legal else 'F'}_{'T' if counter_factual_legal else 'F'}.txt"
                            if not os.path.exists(output_file):
                                continue
                                # raise RuntimeError(f"Required output file {output_file} doesn't exist.")
                            pred = []
                            with open(output_file, "r") as f:
                                for line in f:
                                    line = line.strip().replace("\\n", ". ").replace("\"", " ").replace("\t", " ")
                                    answer = line.split("*")[1].lower()
                                    answer = answer.replace(".", " ")
                                    success = False
                                    if answer.endswith(" yes") or " yes " in answer or " yes, " in answer or " yes " in answer or " yes." in answer:
                                        pred.append(1)
                                        success = True
                                    elif answer.endswith(" no") or " no " in answer or " no, " in answer or " no " in answer or " no." in answer:
                                        pred.append(0)
                                        success = True
                                    if not success and " illegal." or "not legal" in answer:
                                        pred.append(0)
                                        success = True
                                    elif not success and " legal." in answer:
                                        pred.append(1)
                                        success = True
                                    # print(pred[-1], answer)
                                    if not success:
                                        raise RuntimeError(f"cannot parse the line [{line}]")
                            pred = np.array(pred).astype(bool)
                            if mode == "real_world":
                                gt = np.ones_like(pred) if real_world_legal else np.zeros_like(pred)
                            elif mode == "counter_factual":
                                gt = np.ones_like(pred) if counter_factual_legal else np.zeros_like(pred)
                            all_pred.append(pred)
                            all_gt.append(gt)
                            # if len(gt):
                            #     print(f"Accuracy for {output_file.split('/')[-1]} is {(gt == pred).mean()}")

                    all_pred = np.concatenate(all_pred)
                    all_gt = np.concatenate(all_gt)
                    if len(all_gt):
                        acc = (all_pred == all_gt).mean()
                        print(f"Overall accuracy for {mode} with CoT mode {cot} is {acc * 100:.1f}%")
                        f1 = f1_score(all_gt, all_pred)
                        # print(f"Overall F1 Score for {mode} with CoT mode {cot} is {f1:.2f}\n")


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
