import ast
from pathlib import Path
import re
import sys

sys.path.append(str(Path(__file__).parent.parent.parent.absolute()))

from tqdm import tqdm

from programming.utils import eval_program_with_calls, one_based_indexing_checks


def unescape(str):
    placeholder = "<TMP>"
    assert placeholder not in str
    return str.replace("\\\\n", placeholder).replace("\\n", "\n").replace(placeholder, "\\n")


def extract_preds(output):
    original_output = output

    def expand_single_line(output):
        if "\n" not in output and output.startswith("[") and output.endswith("]"):
            # this is a bit of a stretch to consider it correct...
            return "\n".join([str([line]) for line in ast.literal_eval(output)])
        return output

    def parse_code_block(output):
        if output.startswith("python"):
            output = output[len("python") :]
        if output.startswith("thonpy"):
            output = output[len("thonpy") :]
        output = output.strip(" \n")

        matches = re.findall(r"print\(.*\)\n# .*\n# (.*)\n", output + "\n", flags=re.MULTILINE)
        if len(matches) > 0:
            assert len(matches) > len(one_based_indexing_checks().split("\n"))
            return "\n".join(matches)

        matches = re.findall(r"print\(.*\)\n# (.*)\n", output + "\n", flags=re.MULTILINE)
        if len(matches) > 0:
            assert len(matches) > len(one_based_indexing_checks().split("\n"))
            return "\n".join(matches)

        orig_output = output
        if output[0] == "[" and output[-1] == "]":
            lines = []
            prev = 0
            lsb = 0
            lrb = 0
            output = output[1:-1]
            matched = True
            for i, c in enumerate(output):
                if c == "[":
                    lsb += 1
                elif c == "]":
                    if lsb <= 0:
                        matched = False
                    lsb -= 1
                elif c == "(":
                    lrb += 1
                elif c == ")":
                    if lrb <= 0:
                        matched = False
                    lrb -= 1
                elif c == "," and lsb == 0 and lrb == 0:
                    lines.append(output[prev:i].strip())
                    prev = i + 1
            if len(output[prev:].strip()) > 0:
                lines.append(output[prev:].strip())
            if matched:
                return "\n".join(lines)
            # return "\n".join([line.strip(" ,") for line in output[1:-1].strip("\n").split("\n")])
        output = orig_output

        lines = []
        for line in output.split("\n"):
            if (match := re.match(r"^print\(.*\)\s+#\s+prints (.*)$", line)) is not None:
                line = match[1]
            elif (match := re.match(r"^print\(.*\)\s+#\s+(.*)$", line)) is not None:
                line = match[1]
            elif (match := re.match(r"^print\((.*)\)$", line)) is not None:
                line = match[1]
            lines.append(line)
        output = "\n".join(lines)

        return expand_single_line(output)

    delims = (
        "output of the code snippet is:",
        "output of the code snippet will be:",
        "the code snippet prints the following:",
        "the output of the entire code snippet is:",
        "the output of the entire code snippet will be:",
        "the final output of the entire code snippet will be:",
        "the output of the ThonPy code snippet is:",
        "the output of the given ThonPy code snippet is:",
        "the output of the code snippet in ThonPy is:",
        "the complete output of the code snippet is:",
        "he final output is:",
        "he final output will be:",
        "the output will be:",
        "the complete output will be:",
        "final output of the code snippet is:",
        "final output of the code snippet in ThonPy is:",
        "the output of the given code snippet will be:",
        "Putting all the outputs together, the code snippet will print:",
        "Putting it all together, the code snippet will print:",
        "Putting it all together, the entire code snippet will print:",
        "Putting all the outputs together, the code snippet prints:",
        "the code snippet will print the following:",
        "So, the ThonPy code snippet prints:",
        "So, the complete output of the code snippet in ThonPy will be:",
        "So the total printed output is:",
        "Putting it all together, the code snippet in ThonPy prints:",
        "the ThonPy code snippet will print the following:",
        "The code snippet in ThonPy prints:",
        "The output of the ThonPy code snippet will be:",
        "Here's the output for each print statement:",
        "Now, let's put all the results together:",
        "Now, let's put all the outputs together:",
        "Now, let's combine all the results:",
        "This will print:",
        "Here is the output of the code snippet:",
        "The code will print:",
        "The following is the output of the code:",
        "Final output:",
    )
    for delim in delims:
        if delim in output:
            output = output.split(delim)[-1]

    if output.count("```") == 3 and output.strip("\n").startswith("```\n```"):
        output = output[len("```\n"):]

    if output.count("```") == 1:
        if output.strip("\n").startswith("```"):
            output += "\n```"
        elif output.strip("\n").endswith("```"):
            output = "```\n" + output

    if output.count("```") == 2:
        _, output, _ = output.split("```")
        ret = parse_code_block(output)
        if len(ret.split("\n")) > len(one_based_indexing_checks().split("\n")):
            return ret

    match = re.findall("The final output( of [^.:,]+)? is:?\s*\n*\s*`(``)?(python|thonpy)?([^`\n]*)\n*`(``)?", original_output)
    if len(match) > len(one_based_indexing_checks().split("\n")):
        return "\n".join([m[-2] for m in match])

    output = output.strip("\n")
    if all(line[0] == "[" for line in output.split("\n")):
        return expand_single_line(output)
    if all(line[0] == "[" for line in output.strip(" \n`").split("\n")):
        return expand_single_line(output.rstrip("\n`"))
    if output[0] == output[-1] == "`" and "\n" not in output:
        return expand_single_line(output[1:-1])
    if all(re.match(r"^\d+\. .* \(.*\)$", line) for line in output.split("\n")):
        output_lines = []
        for line in output.split("\n"):
            answer = re.search(r"^\d+\. (.*)", line)[1]
            # strip last parenthetical
            assert answer[-1] == ")"
            level = 0
            for i, c in enumerate(answer[::-1]):
                if c == ")":
                    level += 1
                elif c == "(":
                    level -= 1
                if level == 0:
                    break
            assert answer[len(answer) - i - 2] == " "
            output_lines.append(answer[: len(answer) - i - 2])
        return "\n".join(output_lines)
    if all(re.match(r"^\d+\. `.*` - .*$", line) for line in output.split("\n")):
        output_lines = []
        for line in output.split("\n"):
            answer = re.search(r"^\d+\. `(.*)` - .*$", line)[1]
            output_lines.append(answer)
        return "\n".join(output_lines)
    mid_sentence_delims = [
        "output will be",
        "output will also be",
        "print statement will output",
    ]
    if all(
        any(re.match(rf"^\d+\. .* {delim} `?\[.*\]`?\.$", line) for delim in mid_sentence_delims)
        for line in output.replace("\n\n", "\n").split("\n")
    ):
        output_lines = []
        for line in output.replace("\n\n", "\n").split("\n"):
            for delim in mid_sentence_delims:
                if (match := re.search(rf"^\d+\. .* {delim} `?(\[.*\])`?.$", line)) is not None:
                    output_lines.append(match[1])
        return "\n".join(output_lines)

    if "print statement will print" in output:
        output_lines = []
        for line in output.split("\n"):
            if (match := re.search(r"print statement will print (\[.*\]).$", line)) is not None:
                output_lines.append(match[1])
        return "\n".join(output_lines)

    print("Failed to parse output:")
    print(original_output)
    breakpoint()


def parse_output(output):
    output = extract_preds(output)
    assert "print" not in output  # to avoid things like "print(orig_question)    # answer"
    return output.split("\n")


def unwrap_unnecessary_list(l):
    if isinstance(l, (list, tuple)) and len(l) == 1:
        return unwrap_unnecessary_list(l[0])
    return l


def compare_objs(obj1, obj2, eps=1e-5):
    # Handles float precision issues, different quotation marks, etc.
    if isinstance(obj1, float) and isinstance(obj2, float):
        return abs(obj1 - obj2) < eps
    elif isinstance(obj1, (list, tuple)) and isinstance(obj2, (list, tuple)):
        if len(obj1) != len(obj2):
            return False
        return all(compare_objs(o1, o2, eps=eps) for o1, o2 in zip(obj1, obj2, strict=True))
    elif isinstance(obj1, dict) and isinstance(obj2, dict):
        if len(obj1) != len(obj2) or set(obj1.keys()) != set(obj2.keys()):
            return False
        assert all(not isinstance(k, float) for k in obj1.keys())
        return all(compare_objs(obj1[k], obj2[k], eps=eps) for k in obj1.keys())
    else:
        return obj1 == obj2

def lenient_eval(pred, try_adding_brackets=True):
    try:
        return ast.literal_eval(pred)
    except ValueError:
        # Not entirely safe (https://nedbatchelder.com/blog/201206/eval_really_is_dangerous.html)
        # but looks like the worst case is a segfault?
        try:
            return eval(pred, {"__builtins__": {}})
        except NameError:
            return None
        except TypeError:
            return None
    except SyntaxError as e:
        if not try_adding_brackets:
            raise e
        try:
            return lenient_eval(pred + "]", try_adding_brackets=False)
        except SyntaxError:
            try:
                return lenient_eval("[" + pred, try_adding_brackets=False)
            except SyntaxError:
                return None


def equal(pred, label):
    # be lenient and count ignore very minor syntactic issues
    stripped_pred = pred.lstrip("[ ").rstrip("] ")
    stripped_label = label.lstrip("[ ").rstrip("] ")
    if len(stripped_pred) == 0 or len(stripped_label) == 0:
        return stripped_pred == stripped_label
    if (
        stripped_label == f"'{stripped_pred}'"
        or stripped_label == f'"{stripped_pred}"'
        or stripped_pred == f"'{stripped_label}'"
        or stripped_pred == f'"{stripped_label}"'
    ):
        return True

    evaled_pred = lenient_eval(pred)
    evaled_label = ast.literal_eval(label)
    return compare_objs(unwrap_unnecessary_list(evaled_pred), unwrap_unnecessary_list(evaled_label))


def correct_total(pred, label, zero_based_label=None, one_based_label=None):
    correct = correct_hard = total = total_hard = 0
    for i, (p, l) in enumerate(zip(pred, label, strict=True)):
        is_hard = zero_based_label is not None and zero_based_label[i] != one_based_label[i]
        if is_hard:
            total_hard += 1
        total += 1
        if p == "[\"___manually_patched_incorrect\"]" or p == "[\"___manually_patched\"]":
            continue
        assert "manually_patched" not in p  # just to be safe

        if equal(p, l):
            if is_hard:
                correct_hard += 1
            correct += 1
    return correct_hard, correct, total_hard, total


def main(output_file, index_from):
    if index_from == "0":
        perturbation = None
    elif index_from == "1":
        perturbation = "one_based_indexing"
    else:
        assert False

    checks_correct = checks_total = correct = total = 0
    with open(output_file) as f:
        for line in tqdm(f):
            _, program, _, orig_pred = line.strip().split("\t")
            program = unescape(program)
            orig_pred = unescape(orig_pred)
            pred = parse_output(orig_pred)
            zero_based_label = eval_program_with_calls(program)
            one_based_label = eval_program_with_calls(program, perturbation="one_based_indexing")
            label = zero_based_label if perturbation is None else one_based_label
            checks_label = eval_program_with_calls(
                one_based_indexing_checks(), perturbation=perturbation
            )

            assert len(label) == len(zero_based_label)
            assert len(pred) == len(label) + len(checks_label), "Number of outputs mismatched. Use our patched output or patch yourself"
            pred, checks_pred = pred[: len(label)], pred[len(label) :]
            ch, _, th, _ = correct_total(
                pred, label, zero_based_label=zero_based_label, one_based_label=one_based_label
            )
            _, cc, _, tc = correct_total(checks_pred, checks_label)
            correct += ch
            total += th
            checks_correct += cc
            checks_total += tc
    print(f"Test accuracy: {correct} / {total} = {correct / total if total > 0 else 'nan'}")
    print(f"Checks accuracy: {checks_correct} / {checks_total} = {checks_correct / checks_total if checks_total > 0 else 'nan'}")


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
