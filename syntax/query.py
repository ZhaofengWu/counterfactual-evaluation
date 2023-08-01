import pandas as pd
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent.absolute()))

from utils import logger
from flags import FLAGS, parse_flags
from query_utils import query_batch
from prompts import prompt_templates

order2description = {
    "svo": "subject-verb-object",
    "sov": "subject-object-verb",
    "vso": "verb-subject-object",
    "vos": "verb-object-subject",
    "osv": "object-subject-verb",
    "ovs": "object-verb-subject",
}

def escape(s):
    return s.encode("unicode_escape").decode("utf-8")


def unescape(s):
    return s.encode("utf-8").decode("unicode_escape")


def load_data(word_order):
    if FLAGS.use_synthetic_data:
        filename = f"syntax/data/synthetic_data/{word_order}/test.csv"
    else:
        filename = f"syntax/data/ptb_filtered_data/{word_order}/deps_train.csv"
    df = pd.read_csv(filename, engine="python")
    return df

def parse_to_obtain_main_verb_subj(sentence):
    last_line = sentence.split("\n")[-1]
    main_verb_subj = last_line.split("Main verb and subject: ")[-1].strip()
    return main_verb_subj

def parse_to_obtain_control_res(response_text):
    last_line = response_text.split("\n")[-1]
    orig_sent = last_line.split("Original sentence: ")[-1]
    orig_sent = orig_sent.strip()
    orig_sent = orig_sent.strip("\"")
    return orig_sent


def llm_predict(llm, prompt_template, dataset):
    prompts = []
    for example_idx, example in dataset.iterrows():
        if FLAGS.word_order != "svo":
            prompt = prompt_template["instruction"].format_map({"order_description": order2description[FLAGS.word_order]})
        else:
            prompt = prompt_template["english_instruction"]

        prompt += prompt_template["prediction"].format_map(example)
        prompts.append(prompt)

    responses = query_batch(prompts, llm)
    return responses


def evaluate_one_example(prediction, example, eval_control):
    if eval_control:
        references = [example["original_sent"].lower()]
    else:
        reference1 = " ".join([example["main_verb"], example["main_subj"]]).lower()
        reference2 = ", ".join([example["main_verb"], example["main_subj"]]).lower()
        reference3 = " - ".join([example["main_verb"], example["main_subj"]]).lower()
        references = [reference1, reference2, reference3]

    # ignore case
    prediction = prediction.lower()
    if not eval_control:
        prediction = prediction.rstrip(".")
    return prediction in references

def evaluate(predictions, holdout_dataset, eval_control):
    counter = 0

    for example_idx, example in holdout_dataset.iterrows():
        prediction = predictions[example_idx]
        if evaluate_one_example(prediction, example, eval_control):
            counter += 1
    acc = counter / len(predictions)
    return acc

if __name__ == "__main__":
    # disable logging
    logger.setLevel(100)

    parse_flags()
    test_dataset = load_data(FLAGS.word_order)
    test_dataset = test_dataset.iloc[:100]
    logger.info(f"number of testing examples: {test_dataset.shape[0]}")

    prompt_template = prompt_templates[FLAGS.prompt_template]
    raw_responses = llm_predict(FLAGS.llm_engine, prompt_template, test_dataset)

    predictions = []
    for raw_response in raw_responses:
        if FLAGS.eval_control:
            prediction = parse_to_obtain_control_res(raw_response)
        else:
            prediction = parse_to_obtain_main_verb_subj(raw_response)
        predictions.append(prediction)

    pred_acc = evaluate(predictions, test_dataset, FLAGS.eval_control)
    logger.info(f"Prediction accuracy: {pred_acc}")
    print(f"Prediction accuracy: {pred_acc}")
