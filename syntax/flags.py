import argparse
import logging

FLAGS = argparse.Namespace() 


def parse_flags() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument("--word_order", required=True, type=str)
    parser.add_argument("--use_synthetic_data", action="store_true")

    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--quickrun", action="store_true")

    parser.add_argument("--eval_control", action="store_true")
    parser.add_argument("--llm_engine", required=True, type=str)
    parser.add_argument("--llm_cache_dir", required=False, type=str, default="llm_cache")
    parser.add_argument("--prompt_template", required=True, type=str)
    parser.add_argument("--output_path", required=False, type=str)
    args = parser.parse_args()
    FLAGS.__dict__.update(args.__dict__)
