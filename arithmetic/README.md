# Arithmetic

To run the main test:
```bash
model=gpt-4-0314  # or gpt-3.5-turbo-0301, claude-v1.3, models/text-bison-001
base=10  # or 8, 9, 11, 16
cot=True  # or False
python arithmetic/query.py arithmetic/data/0shot/base${base}.txt ${base} ${model} output.txt ${cot}
python arithmetic/eval.py output.txt ${base}
```

To run the CCC:
```bash
model=gpt-4-0314  # or gpt-3.5-turbo-0301, claude-v1.3, models/text-bison-001
base=10  # or 8, 9, 11, 16
python arithmetic/query_ccc.py arithmetic/data/ccc/base${base}.txt ${base} ${model} output.txt
python arithmetic/eval_ccc.py output.txt ${base}
```

To run the analysis with more digits:
```bash
n_digits=3  # or 4; the main experiment is equivalent to 2
model=gpt-4-0314  # we only considered gpt4 for this analysis
base=10  # or 8, 9, 11, 16
cot=True  # we only considered with cot for this analysis
python arithmetic/query.py arithmetic/data/0shot_${n_digits}digits/base${base}.txt ${base} ${model} output.txt ${cot}
python arithmetic/eval.py output.txt ${base}
```

To run the analysis with few-shot demonstrations in the style of in-context learning (ICL):
```bash
n_shots=1  # or 2, 4, 8, 16
model=gpt-4-0314  # we only considered gpt4 for this analysis
base=10  # or 8, 9, 11, 16
cot=True  # we only considered with cot for this analysis
python arithmetic/query.py arithmetic/data/icl/base${base}.txt ${base} ${model} output.txt ${cot} ${n_shots}
python arithmetic/eval.py output.txt ${base}
```

If you want to re-generate the data (these default values are what we used):
```bash
base=10  # or 8, 9, 11, 16
n_digits=2  # or 3, 4
n_samples=1000
python arithmetic/sample.py data.txt ${n_samples} ${n_digits} ${base}
n_samples=200
python arithmetic/sample_ccc.py ccc.txt ${n_samples} ${base}
```

Due to historical reasons, for the few-shot ICL experiments, we do not sample from scratch but rather augment the base data with additional demonstration examples. This ensures comparability. We sampled 32 demonstration per instance but use only a subset of them (with different sizes) for the analysis.
```bash
base=10  # or 8, 9, 11, 16
n_digits=2  # or 3, 4
num_shots=32
python arithmetic/sample_icl.py data.txt data_icl.txt ${num_shots} ${n_digits} ${base}
```
