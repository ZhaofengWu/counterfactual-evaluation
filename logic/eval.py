import hashlib
import json
from pathlib import Path
import random
import sys

random.seed(0)
sys.path.append(str(Path(__file__).parent.parent.absolute()))

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler
from tqdm import tqdm

from query_utils import query_batch


def load_data(data_file):
    return [json.loads(line.strip()) for line in open(data_file)]


def unescape(str):
    placeholder = "<TMP>"
    assert placeholder not in str
    return str.replace("\\\\n", placeholder).replace("\\n", "\n").replace(placeholder, "\\n")


def parse_output(output):
    if len(output) == 0:
        return "FAILED"

    output_hash = hashlib.md5(output.encode("utf-8")).hexdigest()
    if output_hash in {"606fcb87c4df5fc4a83df0e69a1fab9d", "2d8e268be27160282157e2e21df58812", "5bf0ea98ce2d3755010e7d3d720176bf", "5765ae2759248d14bafe382f38de40f3"}:
        # a few cases we manually inspected that can't be parsed
        return "FAILED"

    for mapping in [
        {"necessarily true": "True", "necessarily false": "False", "neither": "Uncertain"},
        {"yes": "True", "no": "False"},
    ]:
        output = output.lower().strip().rstrip(".")
        if output in mapping.keys():
            return mapping[output]
        endings = [
            lambda key: f' is "{key}"',
            lambda key: f' is "{key}."',
            lambda key: f" is {key}",
            lambda key: f" is {key} based on the given premises",
        ]
        for ending in endings:
            if any(output.endswith(ending(key)) for key in mapping.keys()):
                for key, value in mapping.items():
                    if output.endswith(ending(key)):
                        return value
        if sum(1 if key in output.split("\n")[-1] else 0 for key in mapping.keys()) == 1:
            for key, value in mapping.items():
                if key in output.split("\n")[-1]:
                    return value
        if sum(1 if key in output.split("\n")[0] else 0 for key in mapping.keys()) == 1:
            for key, value in mapping.items():
                if key in output.split("\n")[0]:
                    return value
        if sum(1 if key in output.split(".")[0] else 0 for key in mapping.keys()) == 1:
            for key, value in mapping.items():
                if key in output.split(".")[0]:
                    return value
        if sum(1 if key in output.split(".")[-1] else 0 for key in mapping.keys()) == 1:
            for key, value in mapping.items():
                if key in output.split(".")[-1]:
                    return value
    if output.split("\n")[-1] == "so, in either case, pokemon diamond version cannot be both multiplatform and one of the top-3 best selling video games. therefore, the conclusion in step 2 is necessarily true, as it states that pokemon diamond version is neither multiplatform nor one of the top-3 best selling video games":
        # sorry, don't know how to make this case more general
        return "True"
    if "If we take the premises as they are" in output:
        # sometimes gpt4 thinks our subs are typos and tries to correct them...
        sent = [sent for sent in output.split("\n") if "If we take the premises as they are" in sent]
        assert len(sent) == 1
        sent = sent[0]
        if sum(1 if key in sent else 0 for key in mapping.keys()) == 1:
            for key, value in mapping.items():
                if key in sent:
                    return value
    uncertainty_phrases = [
        "neither necessarily true nor necessarily false",
        "we cannot determine",
        "we cannot conclude",
        "we cannot definitively conclude",
        "it is impossible to determine",
        "it is impossible to accurately determine",
        "making it impossible to determine",
    ]
    if any(phrase in output for phrase in uncertainty_phrases):
        return "Uncertain"
    if output.count(".") <= 1 and output.count("\n") <= 1 and "is not necessarily a" in output and "true" not in output and "false" not in output:
        return "False"
    if "based on these premises, it is necessarily false" in output:
        return "False"

    if '"' in output:
        outside_quotes = "".join(output.split('"')[::2])
        return parse_output(outside_quotes)

    print("Failed to parse output:", output, flush=True)
    print(output_hash)
    assert False


def check_truthfulness(sents, model_name):
    templatize = (
        lambda s: f'Is the sentence "{s}" true, false, or uncertain? Answer just "true", "false", or "uncertain" and nothing else.'
    )
    responses = query_batch([templatize(sent) for sent in sents], model_name)

    trues = []
    for response in responses:
        response = response.strip('".').lower()
        assert response in ["true", "false", "uncertain", ""]
        if response == "":
            response = "uncertain"
        trues.append(response)
    return trues


def add_truthfulness(data, model_name):
    all_premise_sents = []
    all_conclusion_sents = []
    for ex in data:
        for sent in ex["premises"].strip().split("\n"):
            all_premise_sents.append(sent)
        all_conclusion_sents.append(ex["conclusion"])

    trues = check_truthfulness(all_premise_sents + all_conclusion_sents, model_name)
    premise_sents_trues = trues[: len(all_premise_sents)]
    conclusion_sents_trues = trues[len(all_premise_sents) :]

    i = 0
    for ex, conclusion_true in zip(data, conclusion_sents_trues, strict=True):
        n_premises = len(ex["premises"].strip().split("\n"))
        ex["premises_trues"] = premise_sents_trues[i : i + n_premises]
        ex["conclusion_true"] = conclusion_true
        i += n_premises
    assert i == len(premise_sents_trues)


def logistic_regression(data, preds, labels, print_stats=True):
    X = []
    y = []
    for ex, pred, label in zip(data, preds, labels, strict=True):
        p_trues = ex["premises_trues"]
        n_t = sum(t == "true" for t in p_trues)
        n_f = sum(t == "false" for t in p_trues)
        n_u = sum(t == "uncertain" for t in p_trues)
        n = n_t + n_f + n_u
        X.append(
            # (n, n_t, n_f, n_u, n_t / n, n_f / n, n_u / n, ex["conclusion_true"] == label.lower())
            (n, n_t / n, n_f / n, n_u / n, ex["conclusion_true"] == label.lower())
        )
        y.append(label == pred)
    X = StandardScaler().fit_transform(X)
    clf = LogisticRegression(random_state=0).fit(X, y)
    if print_stats:
        for coef, name in zip(
            clf.coef_[0],
            # ["n", "n_t", "n_f", "n_u", "p_t", "p_f", "p_u", "conclusion_match"],
            ["n", "p_t", "p_f", "p_u", "conclusion_match"],
        ):
            print(f"{name}: {coef:.3f}")
        print(f"intercept: {clf.intercept_[0]:.3f}")
    return clf.coef_[0].tolist() + [clf.intercept_[0]]


def bootstrap_logistic_regression(data, preds, labels):
    all_coefs = []
    for _ in tqdm(range(1000)):
        data_r, preds_r, labels_r = zip(
            *random.choices(list(zip(data, preds, labels, strict=True)), k=len(data))
        )
        all_coefs.append(logistic_regression(data_r, preds_r, labels_r, print_stats=False))
    all_coefs = np.array(all_coefs)

    # computer confidence intervals
    uppers = []
    lowers = []
    for i, name in enumerate(["n", "p_t", "p_f", "p_u", "conclusion_match", "intercept"]):
        coefs = all_coefs[:, i]
        print(f"{name}: {np.mean(coefs):.3f} ({np.percentile(coefs, 2.5):.3f}, {np.percentile(coefs, 97.5):.3f})")
        uppers.append(np.percentile(coefs, 97.5))
        lowers.append(np.percentile(coefs, 2.5))
    return uppers, lowers



def main(data_file, model_name, output_file):
    data = load_data(data_file)
    add_truthfulness(data, model_name)

    correct = total = 0
    bucketed_stats = {}
    filtered_data = []
    preds = []
    labels = []
    with open(output_file) as f:
        for line in tqdm(f, total=len(data)):
            id, expr, label, pred = line.strip(" \n").split("\t")
            pred = parse_output(unescape(pred))
            # print(expr, pred, label)
            if label == pred:
                correct += 1
            total += 1

            ex = [ex for ex in data if ex["example_id"] == int(id)][0]
            p_trues = ex["premises_trues"]

            bucket_key = (
                sum(t == "true" for t in p_trues),
                sum(t == "false" for t in p_trues),
                sum(t == "uncertain" for t in p_trues),
                ex["conclusion_true"] == label.lower(),
            )
            if bucket_key not in bucketed_stats:
                bucketed_stats[bucket_key] = [0, 0]
            if label == pred:
                bucketed_stats[bucket_key][0] += 1
            bucketed_stats[bucket_key][1] += 1

            filtered_data.append(ex)
            preds.append(pred)
            labels.append(label)
    print("Accuracy:", accuracy_score(labels, preds))

    print(logistic_regression(filtered_data, preds, labels))
    print(bootstrap_logistic_regression(filtered_data, preds, labels))

if __name__ == "__main__":
    try:
        main(*sys.argv[1:])  # pylint: disable=no-value-for-parameter,too-many-function-args
    except Exception as e:
        import pdb
        import traceback

        if not isinstance(e, (pdb.bdb.BdbQuit, KeyboardInterrupt)):
            print("\n" + ">" * 100 + "\n")
            traceback.print_exc()
            print()
            pdb.post_mortem()
