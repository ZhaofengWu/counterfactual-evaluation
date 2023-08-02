# SET Game

To run the main test and CCC:
```bash
export PYTHONPATH=.
model=gpt-4-0314  # or gpt-3.5-turbo-0301, claude-v1.3, models/text-bison-001
cot=True  # or False
python set/set_game.py --model=${model} --cot=${cot} --load_data=True
```

Use `bash set/run.sh` to run all experiments together.

If you want to re-genereate the data:
```bash
export PYTHONHASHSEED=0  # # important for reproducibility as we use some Set structures
export PYTHONPATH=.
model=gpt-4-0314  # or gpt-3.5-turbo-0301, claude-v1.3, models/text-bison-001
cot=True  # or False
num_samples=100
seed=42
python set/set_game.py --model=${model} --cot=${cot} --load_data=False --rounds=${num_samples} --seed=${seed}
```

In our code, output, and data/interaction file names, we use the term "hint" to refer to the number of cards revealed, and the model needs to find the remaining `(3 - hints)` number of cards. Our main tests use `hint=2`. See our paper for more details.
