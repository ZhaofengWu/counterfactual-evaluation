# Data Generation Instructions for the Syntax Experiments

This README file contains instructions for re-generating the data used in the syntax experiments.
Note that unlike the other commands, you need to run the following commands from this directory (`syntax/rnn_typology/datasets_creation`).

### Generating data for the main test

1. Set up a separate Python 2.7 environment (because that's what the original RNNTopology code used).

2. Run the following command to generate the synthetic sentences.

``` bash
bash run.sh
```

The synthesized data will be generated under `syntax/rnn_typology/datasets` folder and also copied to `syntax/data` (i.e., the data directory for syntax prompting).

3. Run `putyon syntax/data/ptb_filtered_data/filter.py` to obtain a filtered version of the synthesized data. For our experiments, we only use sentences whose SVO variants are the same as the original ones. This file selects only those sentences.

### Generating data for CCC

Run `putyon syntax/data/synthetic_data/gen_data.py` to generate the data for our CCC experiments. This file contains the grammar used for sampling sentences.
