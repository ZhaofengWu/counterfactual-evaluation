# Running experiments

You can use the following command to run an experiment (with `--is_control` to run the CCC experiments):
```bash
export PYTHONPATH=.
model=gpt-4-0314  # or gpt-3.5-turbo-0301, claude-v1.3, models/text-bison-001
exp_dir=music/chords/output
instrument=guitar # or ukulele
tuning=EADGBE # or DADGBE/FADGBE/EBDGBE/ECDGBE/ECFGBE for guitar / GCEA/FCEA/ACEA/BCEA/BEEA for ukulele
python music/chords/query.py --model ${model} --exp_dir ${exp_dir} --instrument ${instrument} --tunings ${tuning} --chain_of_thought
python music/chords/eval.py --model ${model} --exp_dir ${exp_dir} --instrument ${instrument} --tunings ${tuning} --chain_of_thought
```

Alternatively, we provide shell scripts that run all experiments in a loop:
```bash
bash music/chords/run_guitar.sh
bash music/chords/run_ukulele.sh
```

## Viewing results

The [`results.ipynb`](results.ipynb) notebook contains code for viewing results.
