# Running experiments

You can use the following command to run an experiment (with `--is_control` to run the CCC experiments):
```bash
export PYTHONPATH=.
model=gpt-4-0314  # or gpt-3.5-turbo-0301, claude-v1.3, models/text-bison-001
exp_dir=music/melodies/output
python music/melodies/query.py --model ${model} --exp_dir ${exp_dir} --chain_of_thought
python music/melodies/eval.py --model ${model} --exp_dir ${exp_dir} --chain_of_thought
```

Alternatively, we provide a shell script that runs all experiments in a loop:
```bash
bash music/melodies/run.sh
```

## Viewing results

The [`results.ipynb`](results.ipynb) notebook contains code for viewing results.
