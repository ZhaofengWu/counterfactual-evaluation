import json
import os
from pathlib import Path
import random
import sys

random.seed(0)
sys.path.append(str(Path(__file__).parent.parent.parent.absolute()))

from tqdm import tqdm

from programming.utils import (
    assemble_program_with_calls,
    one_based_indexing_unit_tests,
    one_based_indexing_checks,
)
from query_utils import query_batch


# These have tests based on random numbers are not trivial (impossible?) to come up with
# equivalent tests.
EXCLUDE_IDS = {"HumanEval/32", "HumanEval/38", "HumanEval/50", "HumanEval/53"}


def load_data(data_file):
    return [json.loads(line.strip()) for line in open(data_file)]


def templatize_0based(obj, fn_name=None, cot=True):
    # Important: we need to use the 1-based indexing perturbation filter to make sure the set of
    # calls are the same.
    program, filtered_call_indices = assemble_program_with_calls(
        obj, perturbation_filter="one_based_indexing", fn_name=fn_name
    )
    prompt = f"""You are an expert programmer. What does the following code snippet in Python 3.7 print?
```python
{program}
{one_based_indexing_checks()}
```
"""
    if cot:
        prompt += "Let's think step by step. "
    prompt += """Write out intermediate results and reasoning processes as needed. End the response by saying "The final output is:" and a unified summary ```python``` code block with *ALL* the output, in which each line represents the output of each print statement."""
    return prompt, program, filtered_call_indices


def templatize_1based(obj, fn_name=None, cot=True):
    program, filtered_call_indices = assemble_program_with_calls(
        obj, perturbation_filter="one_based_indexing", fn_name=fn_name
    )
    # Design decision: list[:3] returns two elements, and so does range(3). This might be slightly
    # counterintuitive, but is not uncommon in other programming languages. E.g. in Ruby,
    # `puts [1,2,3,4,5][..4]` prints five elements.
    prompt = f"""You are an expert programmer who can readily adapt to new programming languages. \
There is a new programming language, ThonPy, which is identical to Python 3.7 except all variables \
of the `list`, `tuple`, and `str` types use 1-based indexing, like in the MATLAB and R languages, where sequence indices start from 1. \
That is, index `n` represents the `n`-th element in a sequence, NOT the `n+1`-th as in 0-based indexing. \
This change only affects when the index is non-negative. \
When the index is negative, the behavior is the same as Python 3.7. \
This also affects methods of these classes such as `index` and `pop`. \
The built-in functions `enumerate` and `range` also use 1-based indexing: by default, the index of \
`enumerate` starts from 1, and so does the lower bound of `range` when not supplied (the higher bound is unchanged).

For example,
```thonpy
{one_based_indexing_unit_tests()}
```

What does the following code snippet in ThonPy print?
```thonpy
{program}
{one_based_indexing_checks()}
```
"""
    if cot:
        prompt += "Let's think step by step. "
    prompt += """Write out intermediate results and reasoning processes as needed. End the response by saying "The final output is:" and a unified summary ```thonpy``` code block with *ALL* the output, in which each line represents the output of each print statement."""
    return prompt, program, filtered_call_indices


def escape(str):
    assert "\t" not in str and "\\\\n" not in str
    return str.replace("\\n", "\\\\n").replace("\n", "\\n")


def parse_bool(flag):
    if isinstance(flag, bool):
        return flag
    assert flag in {"True", "False"}
    return flag == "True"


def main(data_file, model_name, output_file, index_from, fn_name=None, cot=True):
    cot = parse_bool(cot)
    data = load_data(data_file)

    assert not os.path.exists(output_file)

    templatized = []
    for ex in tqdm(data):
        if ex["task_id"] in EXCLUDE_IDS:
            continue
        if index_from == "0":
            prompt, program, filtered_call_indices = templatize_0based(ex, fn_name=fn_name, cot=cot)
        elif index_from == "1":
            prompt, program, filtered_call_indices = templatize_1based(ex, fn_name=fn_name, cot=cot)
        else:
            assert False
        if len(filtered_call_indices) == 0:
            continue
        templatized.append((prompt, program, filtered_call_indices))

    responses = query_batch([prompt for prompt, _, _ in templatized], model_name)

    with open(output_file, "w") as log:
        for (prompt, program, filtered_call_indices), response in zip(
            templatized, responses, strict=True
        ):
            assert "\t" not in prompt and "\t" not in program and "\t" not in response
            log.write(
                f"{escape(prompt)}\t{escape(program)}\t{filtered_call_indices}\t{escape(response)}\n"
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
