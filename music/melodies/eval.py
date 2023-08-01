import warnings
import re
import sys
from typing import List, Tuple

import numpy as np
import pandas as pd

from music.lib import * 
from music.utils import * 
from music.melodies.lib import * 
from music.melodies.utils import get_parser 
from music.melodies.query import get_output_file 

# Gives the nth note of a major scale
def get_nth_note_major_scale(
        key, # e.g. A, Ab (starting note of major scale) 
        n):
    intervals_from_root = [0, 2, 4, 5, 7, 9, 11, 12]
    interval = intervals_from_root[n]
    root_int = NOTE_TO_INT[key]
    nth_note_int = (root_int + interval) % 12
    return nth_note_int 

# TODO: give parse_controls as an argument
def parse_output(output: str, ) -> List[Tuple[str, int]]:

    for pattern in [
            r'NOTE.*=.*([ABCDEFG])([#b]{1,2})?',
#            r'is: ([ABCDEFG])([#b]?)',
            ]:
        results = re.findall(pattern, output)
        if len(results) != 1:
            warnings.warn(
            (
                f"Expected to find one match in parsing output, but found {len(results)}"
                f"\nOutput: {output}\nResult: {results}"
                f"\nDefaulting to using last match:")
            )
        if len(results) == 0:
            continue

        break

    if len(results) == 0:
        return None

    result = results[-1]

    return result[0]+result[1]

def get_subset_acc(df, metric='is_correct', songs=None, keys=None):
    """ Get accuracy on (subset of) dataframe df """
    if songs is not None:
        df = df[df['song'].isin(songs)]
    if keys is not None:
        df = df[df['key'].isin(keys)]
    num_correct = df[metric].sum()
    num_total = len(df)
    acc = num_correct/num_total * 100
    results = {
            'accuracy': acc, 
            'num_correct': num_correct, 
            'num_total': num_total
            }
    return acc, num_correct, num_total

def load_all_results(exp, models):
    """ Load all results for models in directory exp """
    all_results = []
    
    for model in models:

        for cot in [True, False]:

            for control in [True, False]:
                file_name = get_output_file(exp, model, cot, control)

                try:
                    print(f"LOADING RESULTS FROM: {file_name}")
                    preds_df = load_results(file_name, control)

                except FileNotFoundError as e:
                    print(f"FILE NOT FOUND: {file_name}")
                    continue

                preds_df['model'] = model
                preds_df['chain_of_thought'] = cot
                preds_df['is_control'] = control

                all_results.append(preds_df)

    
    return pd.concat(all_results)

def load_results(input_file, is_control):
    """ Load and parse results """

    preds = []
    with open(input_file) as f:
        for line in f:
            
            try:
                song_name, target_key_name, note, inp, response = line.strip().split("\t")
            except ValueError as e:
                print("PRED IS NONE")
                song_name, target_key_name, note, inp = line.strip().split("\t")
                print("LINE: ", line)
                response = None
                
            
            key_name = target_key_name.split(' ')[0]
            target_key = KEYS[key_name+'_major']
            if song_name == "None":
                song_name = None
            if song_name is not None:
                song = SONGS[song_name]
            else:
                song = None
            note = int(note)
            
            if response is None:
                parsed = None
            
            else:
                parsed = parse_output(response)
    

            if not is_control:
            
                transposed_notes = song.transpose(target_key)
                transposed_note = transposed_notes[note]            
                nth_note_of_scale=None
            
            
                if parsed is None:
                    is_correct = False

                else:
                    try:
                        is_correct = (note_to_int(transposed_note) == note_to_int(parsed))
                    except KeyError as e:
                        print("ERROR CALCULATING CORRECTNESS")
                        print("PARSED:", parsed)
                        print("RAW:", response)
                        is_correct = False
                
            else:
                transposed_note = None
                
                nth_note_of_scale = get_nth_note_major_scale(key_name, note)
                
                is_correct = (note_to_int(parsed)==nth_note_of_scale)
            preds.append({
                'is_control': is_control,
                'nth_note_of_scale': nth_note_of_scale,
                'transposed_note': transposed_note,
                'key': target_key_name,
                'song': song_name,
                'is_correct': is_correct,
                'inp': inp,
                'pred_raw': response,
                'parsed': parsed,
                'note': note,
            })
    
    preds_df = pd.DataFrame(preds)
    return preds_df

def main(args):
    exp_dir = args.exp_dir
    model = args.model
    cot = args.chain_of_thought
    control = args.is_control

    file_name = get_output_file(exp_dir, model, cot, control)

    preds_df = load_results(file_name, control)
    
    print("EVALUATING...")
    print(
        f"preds_file: {file_name}",
    )
    
    non_cmajor_keys = [k for k in preds_df['key'].unique() if k != 'C major']
    keys = [['C major'], non_cmajor_keys]

    for key_lst in keys:
        results = get_subset_acc(preds_df[preds_df['key'].isin(key_lst)])
        print(f'KEYS: {key_lst}')
        print(f'ACC: {format_results(*results)}')

if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()

    print(args)
    
    main(args)
