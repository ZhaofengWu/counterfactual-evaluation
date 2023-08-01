# Chess

This directory contains the code for the chess experiments in the paper. In this experiment, we ask LLMs whether a chess opening is legal. In counterfactual variants, we swap the initial position of knights and bishops.

To run the main test:
```bash
export PYTHONPATH=.
model=gpt-4-0314  # or gpt-3.5-turbo-0301, claude-v1.3, models/text-bison-001
cot=True  # or False
python chess/query.py ${model} ${cot}
```

You can evaluate the output with:
```bash
python chess/eval.py
```
This command automatically evaluates all the experiments that have run.

### A note on the data

If you use our data directly, the file suffix `_{T,F}_{T,F}` indicates if the opening is legal in regular/counterfactual chess, respectively. The `_T_T` and `_F_F` files are empty because we want to make our test discriminative between default vs. counterfactual chess, but we keep these files for historical reasons.
