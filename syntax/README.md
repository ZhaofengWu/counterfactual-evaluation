# Basic Syntax

To run the main test:
```bash
export PYTHONPATH=.
model=gpt-4-0314  # or gpt-3.5-turbo-0301, claude-v1.3, models/text-bison-001
word_order=svo  # or sov, vso, vos, ovs, osv
template="main_verb_and_subj_std"  # or main_verb_and_subj_cot; for w/o and w/ 0-shot cot, respectively
python syntax/query.py --word_order ${word_order} --llm_engine ${model} --prompt_template ${template}
```

To run the CCC experiments:
```bash
export PYTHONPATH=.
model=gpt-4-0314  # or gpt-3.5-turbo-0301, claude-v1.3, models/text-bison-001
word_order=sov  # or vso, vos, ovs, osv; svo is the default order so we don't need to test CCC under it
template="reconstruct_std"  # or reconstruct_cot; for w/o and w/ 0-shot cot, respectively
python syntax/query.py --word_order ${word_order} --llm_engine ${model} --prompt_template ${template}  --use_synthetic_data --eval_control
```

If you want to re-generate the data, see `syntax/rnn_typology/datasets_creation/README.md` for instructions.
