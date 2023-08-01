import warnings
import re
import sys
from typing import List, Tuple

import numpy as np
import pandas as pd

from music.lib import *
from music.utils import * 

from music.chords.lib import *
from music.chords.query import get_output_file
from music.chords.utils import get_parser, get_world

def match_regex(output):
    for regex_pattern in [
            "([A-Z]) string[^:]*:(?: fret\s*)?\s*(open|\d+|X)",
            "([A-Z]) string[^:]*:(?:\s*)?\s*(open|\d+|X)",
            r"([A-Z]) string: (1st|2nd|3rd|4th|5th|6th|7th|8th|9th|10th|open) fret",
            ]:
        result = (re.findall(regex_pattern, output))

        # matched none, so continue
        if len(result) == 0:
            continue
        # if matched any, assume this is the right pattern
        else:
            break
    return result

def parse_control(raw_output: str, strings, parse_answer=True, strict=False, verbose=False):
    if parse_answer:
        if 'ANSWER' not in raw_output:
            if verbose:
                print()
                print("Didn't find 'ANSWER' in raw_output...")
                print(f'OUTPUT: {raw_output}'.replace('\\n', '\n'))
            if strict:
                assert False
            output = raw_output
        else:
            output = raw_output[raw_output.index('ANSWER'):]
    
    else:
        output = raw_output

    output = output.strip()

    output_lst = output.split('-')
    pattern = r'\b[A-G](?:b|#){0,2}(?=\b| |/|\\)'
    pattern = r'\b[A-G](?:b|#){0,2}(?=[^A-Za-z]|$)'
    match = [re.findall(pattern, o) for o in output_lst]
    
    notes = []
    for m in match:
        if len(m) != 1:
            if verbose:
                print("FOUND MULTIPLE NOTES IN SLOT: ", m)
                print("Taking first")
        notes.append(m[0])
   
    return notes


def parse_output(raw_output: str, strings, strict=False, parse_answer=True, verbose=False) -> List[Tuple[str, int]]:
    
    if parse_answer:
        if 'ANSWER' not in raw_output:
            if verbose:
                print()
                print("Didn't find 'ANSWER' in raw_output...")
                print(f'OUTPUT: {raw_output}'.replace('\\n', '\n'))
            if strict:
                assert False
            output = raw_output
        else:
            output = raw_output[raw_output.index('ANSWER'):]
    
    else:
        output = raw_output

    num_strings = len(strings)
   
    result = match_regex(output)

    if len(result) == 0:
        if verbose:
            print()
            print('Found no matches')
            print(f'RAW OUTPUT: {raw_output}'.replace('\\n', '\n'))
            print(f'Treating as wrong')
        if strict:
            assert False
        return None

    # take last num_strings matches (bc in COT prompting, may sometimes output strings twice)
    if len(result) != num_strings:
        if verbose:
            print()
            print(f"NUM PARSED {len(result)} != NUM STRINGS {num_strings}:")
            print(f'RAW OUTPUT: {raw_output}'.replace('\\n', '\n'))
            print(f'PARSED: {result}')
        if strict:
            assert False

        # This is hacky, but meant to handle the fact that models often give multiple answers or give the correct answer multiple times, and double enters usually separate those, so in those cases we want to only look at the last answer
        paragraph_results = [match_regex(o) for o in output.split('\\n\\n')]
        paragraph_results = [r for r in paragraph_results if r != []]

        result = paragraph_results[-1]

        if verbose:
            print('Splitting by double enters and re-parsing...')
            print(f'NEW PARSED: {result}')
            print(f'Taking last {num_strings} parsed as answer...')
            print(f'PARSED: {result[-num_strings:]}')
    
    result = result[-num_strings:]

    if not all([s in strings for s, _ in result]):
        if verbose:
            print()
            print("Not all parsed strings are in the instrument strings")
            print(f'RAW OUTPUT: {raw_output}'.replace('\\n', '\n'))
            print(f'PARSED: {result}')
            print(f'STRINGS: {strings}')
            print(f'Treating as wrong')
        if strict:
            assert False
        return None

    output_list = []
    for x in result:
        if x[1] == "X":
            continue
        if x[1] in ['open', '0']:
            output_list.append((x[0], 0))
        else:
            output_list.append((x[0], int(x[1][0])))

    return output_list
    print("Failed to parse output:", output)
    assert False


def get_subset_acc(df, metric='is_correct', keys=None, chord_types=None):
    """ Get accuracy on (subset of) dataframe df """
    if keys is not None:
        df = df[df['key'].isin(keys)]
    if chord_types is not None:
        df = df[df['chord_type'].isin(chord_types)]
    num_correct = df[metric].sum()
    num_total = len(df)
    acc = num_correct/num_total * 100
    results = {'accuracy': acc, 'num_correct': num_correct, 'num_total': num_total}
    return acc, num_correct, num_total

def get_subset_control_acc(df, num_strings, metric='is_correct', keys=None, chord_types=None):
    """ Get accuracy on (subset of) dataframe df for controls """
    if keys is not None:
        df = df[df['key'].isin(keys)]
    if chord_types is not None:
        df = df[df['chord_type'].isin(chord_types)]
        
    # this is considering failure of parses as num_strings wrong instances
    num_total = num_strings * len(df)
    df['num_correct'] = df.apply(lambda row: sum(row['is_correct']), axis=1)
    
    num_correct = df['num_correct'].sum()
    acc = num_correct/num_total * 100
    results = {'accuracy': acc, 'num_correct': num_correct, 'num_total': num_total}
    return acc, num_correct, num_total

def load_results(input_file, instrument, tunings, is_control):
    """ Load and parse results """
    preds = []
    with open(input_file) as f:
        for line in f:
            
            num_strings = len(tunings)
            
            if is_control:
                try:
                    fret_idx, inp, pred = line.strip().split("\t")
                    parsed_control = parse_control(pred, tunings, strict=False, parse_answer=True)
                    
                except ValueError as e: 
                    fret_idx, inp  = line.strip().split("\t")
                    print(e)
                    print("Not enough values to unpack")
                    pred = None
                    parsed_control = None
            
                gold_control_notes = [note_to_int(instrument.get_note(string, int(fret_idx))) for string in tunings]

                if parsed_control is not None:
                    parsed_control_notes = [note_to_int(n) for n in parsed_control]
                    is_correct = [p==g for p, g in zip(parsed_control_notes, gold_control_notes)]
                else:
                    is_correct = [False]
                    parsed_control_notes = None            

                
                chord = None
                key = None
                chord_type = None
                gold_chord_notes = None
                parsed_frets = None
                converted_notes_pred = None
                chord_name = None
                
            else:
                try:
                    chord, inp, pred = line.strip().split("\t")
                except ValueError:
                    chord, inp = line.strip().split("\t")
                    print("PRED IS NONE")
                    pred = None
                
                chord_name, gold_chord_notes = eval(chord)
                key, chord_type = chord_name.split("-")
                    
                if pred is not None:

                    parsed_frets = parse_output(pred, tunings, strict=False, parse_answer=True)
                else:
                    parsed_frets = None
            
                # Only happens if there was an error with parsing the strings (parsed strings != instrument strings)
                if parsed_frets is None:
                    is_correct = False
                    converted_notes_pred = None

                else:
                    converted_notes_pred = [note_to_int(instrument.get_note(string, fret)) for string, fret in parsed_frets]
                    gold_chord_notes_int = [note_to_int(g) for g in gold_chord_notes]
                    is_correct = set(gold_chord_notes_int) == set(converted_notes_pred)
                    
                parsed_control_notes = None
                gold_control_notes = None
            
            preds.append({
                'is_control': is_control,
                
                'chord': chord_name, 
                'key': key,
                'chord_type': chord_type,
                'gold_chord_notes': gold_chord_notes,
                'parsed_frets': parsed_frets,
                'pred_notes': converted_notes_pred, # parsed_frets converted to notes
                
                'gold_control_note': gold_control_notes,
                'parsed_control_note': parsed_control_notes,
                
                'inp': inp, 
                'pred_raw': pred,        
                'is_correct': is_correct,
            })
    preds_df = pd.DataFrame(preds)
    return preds_df

def load_all_results(exp, tunings_list, models, instrument_name):
    """ Load all results for models/tunings_list/instrument_name in directory exp """
    all_results = []
    
    for tunings in tunings_list:
        for model in models:
                
            for cot in [True, False]:
                
                for control in [True, False]:
                    world = get_world(instrument_name, tunings)
                    file_name = get_output_file(exp, instrument_name, world, tunings, model, chain_of_thought=cot, is_control=control)

                    strings_list = list(tunings)
                    instrument = INSTRUMENTS[instrument_name](strings_list)

                    try:
                        print(f"LOADING RESULTS FROM: {file_name}")
                        preds_df = load_results(file_name, instrument, tunings, is_control=control)
                        
                    except FileNotFoundError as e:
                        print(f"FILE NOT FOUND: {file_name}")
                        continue

                    preds_df['model'] = model
                    preds_df['chain_of_thought'] = cot
                    preds_df['world'] = world
                    preds_df['instrument'] = instrument
                    preds_df['tunings'] = tunings
                    preds_df['is_control'] = control

                    all_results.append(preds_df)

    
    return pd.concat(all_results)

def main(args):
    exp_dir = args.exp_dir
    model = args.model
    cot = args.chain_of_thought
    control = args.is_control
    tunings = args.tunings
    instrument_name = args.instrument
    
    world = get_world(instrument_name, tunings)
    file_name = get_output_file(exp_dir, instrument_name, world, tunings, model, cot, control)
    
    print("EVALUATING...")
    print(
        f"preds_file: {file_name}",
    )
    
    instrument = INSTRUMENTS[instrument_name](list(tunings))
    preds_df = load_results(file_name, instrument, tunings, control)
   
    if control:
        results = get_subset_control_acc(preds_df, len(tunings), metric='is_correct')
    else:
        results = get_subset_acc(preds_df, metric='is_correct')
    print(f'MODEL: {model}')
    print(f'TUNING: {tunings}')
    print(f'ACC: {format_results(*results)}')

if __name__ == "__main__":
    parser = get_parser()

    args = parser.parse_args()

    print(args)
    
    main(args)
