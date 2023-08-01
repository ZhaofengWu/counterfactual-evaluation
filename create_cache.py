import os
import pickle
import sys

from query_utils import CACHE_FILE, unescape


def add_file_to_cache(file, cache):
    print(f"Processing {file}")
    with open(file) as f:
        for line in f:
            fields = line.strip().split("\t")
            assert len(fields) in {9, 10}
            (
                prompt,
                response,
                response_is_list,
                model_name,
                system_msg,
                history,
                max_tokens,
                temperature,
                num_beams,
            ) = fields[:9]
            assert system_msg == "None"
            system_msg = None
            assert history == "None"
            history = None
            if max_tokens == "None":
                max_tokens = None
            else:
                max_tokens = int(max_tokens)
            if temperature == "0":
                temperature = 0
            else:
                temperature = float(temperature)
            num_beams = int(num_beams)
            if len(fields) == 9:
                key = (
                    unescape(prompt),
                    unescape(model_name),
                    system_msg,
                    history,
                    max_tokens,
                    temperature,
                    num_beams,
                )
            else:
                n = int(fields[9])
                key = (
                    unescape(prompt),
                    unescape(model_name),
                    system_msg,
                    history,
                    max_tokens,
                    temperature,
                    num_beams,
                    n,
                )
            value = unescape(response)
            assert response_is_list in {"True", "False"}
            if response_is_list == "True":
                value = eval(value)
            cache[key] = value


def main(*files_or_dirs):
    assert not os.path.exists(CACHE_FILE)
    cache = {}
    for file_or_dir in files_or_dirs:
        if os.path.isdir(file_or_dir):
            # recursively find all files that ends with .tsv
            for subdir, _, files in os.walk(file_or_dir):
                for file in files:
                    if file.endswith(".tsv"):
                        add_file_to_cache(os.path.join(subdir, file), cache)
        else:
            assert file_or_dir.endswith(".tsv")
            add_file_to_cache(file_or_dir, cache)
    pickle.dump(cache, open(CACHE_FILE, "wb"))


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
