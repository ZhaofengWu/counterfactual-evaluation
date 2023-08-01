# Natural Language Logic with First-Order Logic

As explained in our paper, we used a new version of the FOLIO dataset that the authors privately shared with us. We therefore cannot publicly share the data and model interactions (which would contain the data). However, if you request access to the dataset from the authors, you can use the commands below to run a subset of our experiments. You could also use [an earlier though public version of the dataset](https://github.com/Yale-LILY/FOLIO/). Note that there may be formatting differences between the two versions of the dataset.

The dataset that the authors sent us have the following two files, with their MD5:
```bash
0b1eb74ce897efd9f7ff0d8ff82c11ba  folio_v2_train.jsonl
a35c9de562befdc8fcd6be41939c489b  folio_v2_validation.jsonl
```
We combined both files into a single file `folio_v2_combined.jsonl`.

You can then run the logistic regression analysis with:
```bash
model=gpt-4-0314  # or gpt-3.5-turbo-0301, claude-v1.3, models/text-bison-001
python logic/query.py folio_v2_combined.jsonl ${model} output.txt
python logic/eval.py folio_v2_combined.jsonl ${model} output.txt
```

Though for our main counterfactual experiments, because we manually perturbed the original dataset, we do not see a way to release either the perturbed file or a diff that does not reveal the original file (feel free to open an issue if you have ideas!). But if you email Zhaofeng Wu (the first author here) and show you have the permission from the original FOLIO authors, we can privately share the counterfactual data with you. With the data, you can replicate our experiments with:
```bash
model=gpt-4-0314  # or gpt-3.5-turbo-0301, claude-v1.3, models/text-bison-001
use_unperturbed_data=False  # or True
python logic/query.py folio_v2_perturbed.jsonl ${model} output.txt ${use_unperturbed_data}
python logic/eval.py folio_v2_perturbed.jsonl ${model} output.txt
```

And the CCC experiments with:
```bash
python logic/generate_ccc.py folio_v2_perturbed.jsonl folio_v2_ccc.jsonl
model=gpt-4-0314  # or gpt-3.5-turbo-0301, claude-v1.3, models/text-bison-001
python logic/query_ccc.py folio_v2_ccc.jsonl ${model} output.txt
python logic/eval_ccc.py folio_v2_ccc.jsonl output.txt
```
