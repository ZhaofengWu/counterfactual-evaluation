# Programming

We consider two programming-related tasks: program execution and program generation. Both use the HumanEval dataset, obtained from the [official repo](https://github.com/openai/human-eval), but with minor changes. The `data.jsonl` files under the respective directory is the changed data files.

## Execution

### Data

There are two examples in HumanEval whose assertions contain loops. These cannot be easitly handled by our pipeline. Fortunately, these examples have short loops, so we manually unroll them in the data file.

We also exclude 4 examples with complicated assetions. See `EXCLUDE_IDS` in `programming/execution/query.py`.

### Commands

To query the model:
```bash
model=gpt-4-0314  # or gpt-3.5-turbo-0301, claude-v1.3; as explained in our paper, we don't evaluate PaLM-2
index=0  # or 1
cot=True  # or False
python programming/execution/query.py programming/execution/data.jsonl ${model[0]} output.txt ${index} function ${cot}
```

For this setup, we manually patch the model outputs for ease of automatic parsing, for example aligning the number of output to be the same as the number of expected output. If you directly evaluate using the `output.txt` produced above, it likely will break some assertions for most models/setups. We put the patched output in the `patched_output` directory. You can see what we changed by diff-ing with the `output.txt` produced above. To evaluate the patched output:
```bash
model=gpt-4-0314  # or gpt-3.5-turbo-0301, claude-v1.3; as explained in our paper, we don't evaluate PaLM-2
index=0  # or 1
cot_folder=with_0cot  # or without_0cot
python programming/execution/eval.py programming/execution/patched_output/${cot_folder}/${model}_${index}based.txt ${index}
```

## Generation

The `human_eval/` directory is from the [official repo](https://github.com/openai/human-eval) with minor changes.

### Data

Some examples in HumanEval uses `str` as variable names, which causes issues with our automatic evaluation. We manually rewrite these varaibles to use the name `strr` instead.

### Commands

```bash
model=gpt-4-0314  # or gpt-3.5-turbo-0301, claude-v1.3, models/text-bison-001
index=0  # or 1
k=1  # or 10; use 1 for pass@1 and 10 for pass@10
temperature=0.1  # or 0.8; use 0.1 for pass@1 and 0.8 for pass@10
only_programs_that_dont_pass_under_one_based_indexing=True  # or False
python programming/generation/run.py programming/generation/data.jsonl ${model} output.txt ${index} ${temperature} 50 ${k} ${only_programs_that_dont_pass_under_one_based_indexing}
```

We have noticed that different runs may yield slightly different results (within ~1% absolute). We found the reason to be that the same program may time out or complete in different runs, depending on how busy the machine is.
