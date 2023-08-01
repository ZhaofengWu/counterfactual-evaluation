import argparse
import os
import sys
from collections import OrderedDict

from query_utils import query_batch
from music.lib import *
from music.melodies.lib import *
from music.melodies.utils import get_parser

def get_output_file(exp_dir, model, chain_of_thought, is_control):
    output_dir = os.path.join(exp_dir, 'preds')
    os.makedirs(output_dir, exist_ok=True)
    cot_str = '_stepbystep' if chain_of_thought else ''
    control_str = '_control' if is_control else ''

    # for palm
    model = model.replace('models/', '')
    
    output_file = os.path.join(output_dir, f'{model}{cot_str}{control_str}.txt')
    return output_file

def escape(text: str) -> str:
    if text is None:
        return None
    return text.replace("\n", "\\n")

NTH_MAP = {
    1: "first",
    2: "second",
    3: "third",
    4: "fourth",
    5: "fifth",
    6: "sixth",
    7: "seventh",
    8: "eighth",
    9: "ninth",
    10: "tenth",
    11: "eleventh",
    12: "twelfth",
    13: "thirteenth",
    14: "fourteenth",
    15: "fifteenth",
    16: "sixteenth",
    17: "seventeenth",
    18: "eighteenth",
    19: "nineteenth",
    20: "twentieth",
}

def templatize(
        song: Song, 
        key: Key, 
        note_idx: int,
        chain_of_thought: bool,
        is_control: bool,
        ) -> str:
    nth = NTH_MAP[note_idx+1] # use 1 indexing

    prompt = f"You are an expert musician. " 
    if is_control:
        prompt += (
            f"What is the {nth} note of the {key} scale? "
        ) 
    else:
        prompt += (
            f"What is the {nth} note of the melody of the song '{song.name}' in {key}? " 
        )

    prompt += (
        f"Make sure to choose one final answer, which you should "
        "start with 'ANSWER:' and specify in the following format: NOTE={note}."
    )
    if args.chain_of_thought:
        prompt += "\n\nLet's think step by step."

    return prompt

def main(args,
    songs: list = ['twinkle', 'mary', 'happy_birthday', 'rainbow', 'row', 'old_macdonald', 'spider', 'london'], # key for SONGS 
    ):
    model_name = args.model


    # iterate through all given songs, all target keys, indices 0-9
    templatized, query_infos = [], []
        
    target_keys = KEYS.values()
    print(f"KEYS: {[k.name for k in target_keys]}")
    print(f"MODEL:\t{model_name}")

    for target_key in target_keys:
        if args.is_control:
            max_val = 7
        else:
            max_val = 7 
        for note_idx in range(max_val):
            
            if args.is_control:
                songs = [None]
        
            for song_name in songs:
                if song_name is not None:
                    song = SONGS[song_name]
                else:
                    song = None
                templatized.append(
                        templatize(song, target_key, note_idx, args.chain_of_thought, args.is_control))
                query_infos.append({'song': song_name, 'target_key': str(target_key), 'note': note_idx})

    print('\nEXAMPLE INPUT:')
    print(templatized[0])
    print()
    responses = query_batch(templatized, model_name, skip_cache=False)

    output_file = get_output_file(args.exp_dir, args.model, args.chain_of_thought, args.is_control)
    print(f"OUTPUT FILE:\t{output_file}")
    assert not os.path.exists(output_file), f"output_file already exists: {output_file}"

    with open(output_file, "w") as log:
        for template, response, query_info in zip(templatized, responses, query_infos):
            log.write(f"{query_info['song']}\t{query_info['target_key']}\t{query_info['note']}\t{escape(template)}\t{escape(response)}\n")

if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()

    print("ARGS:")
    print(args)
    
    main(args)
