# Natural Language Logic with First-Order Logic

We used the [FOLIO dataset](https://huggingface.co/datasets/yale-nlp/FOLIO) for the experiments in this section. As the FOLIO authors enabled gated dataset access on Huggingface, we respect this decision and similarly release our counterfactual data and model interactions through Huggingface, also with gated access, at https://huggingface.co/datasets/ZhaofengWu/FOLIO-counterfactual/tree/main.

As noted in our paper, we only manually rewrote a subset of the original FOLIO data to be counterfactual. This subset is released at https://huggingface.co/datasets/ZhaofengWu/FOLIO-counterfactual/blob/main/folio_v2_perturbed.jsonl. After downloading it, you can replicate our experiments with:
```bash
model=gpt-4-0314  # or gpt-3.5-turbo-0301, claude-v1.3, models/text-bison-001
cot=True  # or False
use_unperturbed_data=False  # or True
python logic/query.py folio_v2_perturbed.jsonl ${model} output.txt ${cot} ${use_unperturbed_data}
python logic/eval.py folio_v2_perturbed.jsonl ${model} output.txt
```

And the CCC experiments with:
```bash
python logic/generate_ccc.py folio_v2_perturbed.jsonl folio_v2_ccc.jsonl  # this only needs to be done once
model=gpt-4-0314  # or gpt-3.5-turbo-0301, claude-v1.3, models/text-bison-001
python logic/query_ccc.py folio_v2_ccc.jsonl ${model} output.txt
python logic/eval_ccc.py folio_v2_ccc.jsonl output.txt
```

To run the logistic regression analysis, you can combine the two _original_ FOLIO files ([folio_v2_train.jsonl](https://huggingface.co/datasets/yale-nlp/FOLIO/blob/main/folio_v2_train.jsonl) and [folio_v2_validation.jsonl](https://huggingface.co/datasets/yale-nlp/FOLIO/blob/main/folio_v2_validation.jsonl)) into a single file `folio_v2_combined.jsonl`. You can then run the analysis with:
```bash
model=gpt-4-0314  # or gpt-3.5-turbo-0301, claude-v1.3, models/text-bison-001
cot=True  # we only considered with cot for this analysis
logreg=True
python logic/query.py folio_v2_combined.jsonl ${model} output.txt ${cot}
python logic/eval.py folio_v2_combined.jsonl ${model} output.txt ${logreg}
```

And like for the other tasks, you can download the [model interaction files](https://huggingface.co/datasets/ZhaofengWu/FOLIO-counterfactual/tree/main/model_interactions) to avoid re-querying the language models for all the experiments mentioned above.
