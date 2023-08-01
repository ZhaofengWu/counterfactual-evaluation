"""Call LLMs on the chess task. Requires running generate_chess.py first."""

import os
import pathlib
import sys
from query_utils import query_batch


def load_data(data_file):
    return [line.strip().replace(" *", "") for line in open(data_file)]


def templatize(mode, pgn_string, cot=True, is_control=False):
    if mode not in ["real_world", "counter_factual"]:
        raise ValueError(f"Unknown mode {mode}")

    prompt = "You are a chess player."

    if mode == "counter_factual":
        prompt += " You are playing a chess variant where the starting positions for knights and bishops are swapped. For each color, the knights are at placed that where bishops used to be and the bishops are now placed at where knights used to be."
    prompt += "\n"
    if is_control:
        prompt += "Question: In this chess variant, t" if mode == "counter_factual" else "Question: T"
        prompt += f"he two {pgn_string}s on the board should be initially at which squares? Answer:"
        if cot:
            prompt += " Let's think step by step:"
        return prompt

    prompt += "Given an opening, determine whether the opening is legal. The opening doesn't need to be a good opening. Answer \"yes\" if all moves are legal. Answer \"no\" if the opening violates any rules of chess.\n"

    if mode == "real_world":
        prompt += f"Is the new opening \"{pgn_string}\" legal? "
    elif mode == "counter_factual":
        prompt += f"Under the custom variant, is the new opening \"{pgn_string}\" legal? "

    if cot:
        prompt += "Let's think step by step:"

    return prompt


def escape(str):
    return str.replace("\n", "\\n")


def parse_bool(flag):
    if isinstance(flag, bool):
        return flag
    assert flag in {"True", "False"}
    return flag == "True"


def main(model_name: str = "gpt-4-0314", cot: bool = True):
    cot = parse_bool(cot)
    for exp in os.listdir("chess/data"):
        if "chess" in exp:
            data_dir = os.path.join("chess/data", exp)
            output_dir = f"chess/output/{exp}/{model_name.replace('models/', '')}_0cot{cot}"
            pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)
            for mode in ["real_world", "counter_factual"]:
                pieces = ["white bishop", "black bishop", "white knight", "black knight"]
                templatized = [templatize(mode, piece, cot=cot, is_control=True) for piece in pieces]
                responses = query_batch(templatized, model_name, temperature=0.1, n=15)
                output_file = os.path.join(output_dir, f"{mode}_control.txt")
                with open(output_file, "w") as log:
                    for piece, response_batch in zip(pieces, responses, strict=True):
                        for response in response_batch:
                            log.write(f"{piece} *\t{escape(response)}\n")
                # continue
                for real_world_legal in [True, False]:
                    for counter_factual_legal in [True, False]:
                        data_file = \
                            f"{data_dir}/{mode}_{'T' if real_world_legal else 'F'}_{'T' if counter_factual_legal else 'F'}.txt"
                        output_file = \
                            f"{output_dir}/{mode}_{'T' if real_world_legal else 'F'}_{'T' if counter_factual_legal else 'F'}.txt"
                        if not os.path.exists(data_file):
                            raise RuntimeError(f"data file {data_file} doesn't exist")

                        data = load_data(data_file)

                        templatized = [templatize(mode, pgn_string, cot=cot) for pgn_string in data]
                        responses = query_batch(templatized, model_name)

                        with open(output_file, "w") as log:
                            for expr, response in zip(data, responses, strict=True):
                                log.write(f"{expr} *\t{escape(response)}\n")


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
