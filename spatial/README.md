# Spatial Reasoning

If you want to re-generate data:
```bash 
n_samples=100
n_objects=3
python spatial/sample.py data.txt ${n_samples} ${n_objects}
```

To run the main test:
```bash
model=gpt-4-0314  # or gpt-3.5-turbo-0301, claude-v1.3, models/text-bison-001
type=default  # or r90 r180 r270 vflip hflip random
cot=True  # or False
python spatial/query.py spatial/data/3obj.txt ${model} output.txt ${type} ${cot}
python spatial/eval.py output.txt
```