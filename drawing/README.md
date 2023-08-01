# Drawing

To run the main test:
```bash
model=gpt-4-0314  # or gpt-3.5-turbo-0301, claude-v1.3
type=default  # or r90 r180 vflip
cot=True  # or False
prompt_version=1 # we use version 1 for gpt-4 and version 2 for gpt-3.5 and claude
python drawing/query.py drawing/data/100obj.txt ${model} output.txt ${type} ${prompt_version} ${cot}
```

For this task, we do not consider PaLM-2 due to its limited context length. See section A.6 in our paper for a discussion.

## Evaluation

You can render the output drawings in `output.txt` (from the steps above) yourself using instructions in the _next_ section. However, you may see many un-parseable drawings. We manually fixed some model outputs that resulted in un-renderable or un-parseable drawing code and have included the corrected drawing code and the corresponding rendered drawings in `drawing/model_outputs.zip`. If a rendered drawing does not exist in this zip, it means that the drawing code remains un-renderable even after our simple fixes.
Unzip it using `unzip drawing/model_outputs.zip -d drawing`.

We perform both human evaluation and automatic evaluation using zero-shot classifier based on the CLIP large model. For the former, you can directly look at the rendered drawings in `drawing/model_outputs`.

To evaluate the saved drawings using CLIP large (Table 25):

```bash
model=gpt4  # or gpt3.5, claude
type=default  # or r90 r180 vflip
cot_type=with_0cot # or without_0cot
python drawing/eval.py drawing/data/100obj.txt drawing/model_outputs/${cot_type}/${model}_${type} ${type}
```

## Render drawings

This section provides instructions if you want to render the drawings yourself instead of using our `drawing/model_outputs.zip`.

### Download Processing

You need to download [Processing](https://processing.org/download) to render the drawing code:
```bash
wget https://github.com/processing/processing4/releases/download/processing-1292-4.2/processing-4.2-linux-x64.tgz
tar -xvzf processing-4.2-linux-x64.tgz
```

If you're running Processing on a headless server (a server without a display), you'll need to use something like Xvfb, which is a "virtual" display server for Unix-like operating systems.

```bash
sudo apt-get update
sudo apt-get install xvfb
```

Install processing-java
```bash
Xvfb :99 -screen 0 1024x768x24 &
export DISPLAY=:99
cd /path/to/processing
./processing
```

Add processing-java to PATH or alias
```
export PATH="$PATH:/path/to/processing-4.2/processing-java"
```

### Save drawings
To render the drawing using Processing, we need to put the drawing code in the following format:

```
- output_dir
    - obj1
        - obj1.pde
    - obj2
        - obj2.pde
    ...
```

To extract the drawing code from the model output and save them in the above format:
```bash
python drawing/save.py drawing/data/100obj.txt output.txt output_dir
```

### Render drawings

Then you can render drawings using:
```
export PROCESSING=/path/to/processing
bash drawing/render.sh output_dir
```

Running the above command will render the drawings in the `output_dir` folder in this format:

```
- output_dir
    - obj1
        - obj1.pde
        - obj1.png
    - obj2
        - obj2.pde
        - obj2.png
    ...
```
