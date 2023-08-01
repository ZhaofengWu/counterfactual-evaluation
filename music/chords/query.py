import itertools
import argparse
import os
import sys
from collections import OrderedDict

from query_utils import query_batch
from music.lib import *
from music.utils import *
from music.chords.lib import *
from music.chords.utils import *

def get_output_file(exp_dir, instrument, world, tunings, model, chain_of_thought, is_control):
    output_dir = os.path.join(exp_dir, 'preds')
    os.makedirs(output_dir, exist_ok=True)
    cot_str = '_stepbystep' if chain_of_thought else ''
    control_str = '_control' if is_control else ''

    # for palm
    model = model.replace('models/', '')
    
    output_file = os.path.join(output_dir, f'{instrument}_{world}_{tunings}_{model}{cot_str}{control_str}.txt')
    return output_file

def escape(text: str) -> str:
    if text is None:
        return None
    return text.replace("\n", "\\n")

def find_change(s1, s2):
    """Find the single point change between two arrays"""
    assert len(s1) == len(s2)
    differences = []
    for i, (c1, c2) in enumerate(zip(s1, s2)):
        if c1 != c2:
            differences.append(i)

    return differences

#    if len(differences) == 1:
#        index = differences[0]
#        return (index, s1[index], s2[index])
#    else:
#        return None


def get_chord_name(chord_str):
    chord_name = chord_str

    # Ordered so that first looks for m7 over 7
    chord_map = OrderedDict(
        {
            "sus2": "suspended second chord (sus2)",
            "sus4": "suspended fourth chord (sus4)",
            "minor": "minor triad",
            "major": "major triad",
            "dim7": "diminished seventh chord (dim7)",
            "aug7": "augmented seventh chord (aug7)",
            "maj7": "major seventh chord (maj7)",
            "m7": "minor seventh chord (min7)",
            "7": "dominant seventh chord (dom7)",
            "6": "sixth chord",
            "5": "fifth interval",
        }
    )

    for name, out in chord_map.items():
        if name in chord_name:
            chord_name = chord_name.replace(name, f"{out}")
            break
    assert chord_name != chord_str, f"{chord_name} == {chord_str}"
    return chord_name

def get_string_change_prompt(
        instrument,
        strings_chars: str, 
        standard_strings_chars: str):
    change_str = '' 
    changes = find_change(strings_chars, standard_strings_chars)
    for idx, change in enumerate(changes):
        if change == 0 and instrument.name == 'guitar':
            orig_str_name = 'low E'
        elif change == len(strings_chars)-1 and instrument.name == 'guitar':
            orig_str_name = 'high E'
        else:
            orig_str_name = standard_strings_chars[change]

        if len(changes) == 1:
            change_str += (
                f"Note that what is the standard {orig_str_name} string is instead tuned to"
                f" {strings_chars[change]}. All other strings are the same."
            )
            break
        elif len(changes) > 1 and idx == 0:
            change_str += (
                f"Note that what is the standard {orig_str_name} string is instead tuned to"
                f" {strings_chars[change]}, "
            )
        elif len(changes) > 1 and idx > 0 and idx < len(changes)-1:
            change_str += (
                f"the standard {orig_str_name} string is instead tuned to"
                f" {strings_chars[change]}, "
            )
        elif len(changes) > 1 and idx==len(changes)-1:
            change_str += (
                f"and the standard {orig_str_name} string is instead tuned to"
                f" {strings_chars[change]}. All other strings are the same."
            )
    return change_str

def templatize(
        instrument: StringInstrument, 
        chain_of_thought: bool,
        is_control: bool,
        chord: str = None,
        fret_idx_for_control: int = None,
        string_for_control: str = None) -> str:
    strings_chars = instrument.tunings
    strings = "-".join(strings_chars)
    standard_instrument = INSTRUMENTS[instrument.name]()
    standard_strings_chars = standard_instrument.tunings
    standard_strings = "-".join(standard_strings_chars)
    change_str = get_string_change_prompt(instrument, strings_chars, standard_strings_chars)

    form = "\n\nANSWER:"
#    form = ''
    for s in instrument.tunings:
        form += f"\n{s} string: fret FRET"

    if strings != standard_strings:
        # find the string that is different
        # find which string is different

        prompt = (
            f"You are an expert {instrument.name} player. I have a special"
            f" {instrument.name} with strings tuned to {strings} instead of the"
            f" standard {standard_strings}. {change_str}"
        )
    else:
        prompt = (
            f"You are an expert {instrument.name} player. I have a"
            f" {instrument.name} with standard strings {strings}."
        )
            
    if is_control:
        note_sequence = "\n"
        for s in instrument.tunings:
            note_sequence += f"\n{s} string: fret {fret_idx_for_control}"
        prompt += (
            f"\n\nI want you to tell me what notes the following "
            f"sequences of finger positions corresponds to: {note_sequence}"
            "\n\nNote that fret 0 indicates an open string, and each increase "
            "in fret corresponds to an increase in half a note. "
            f"\n\nMake sure to choose one final answer, which you should "
            f"start with 'ANSWER:' and format with dash-separated notes in the order "
            f"of strings {strings}."
        )
        
    else:
        key, chord_type = chord.split("-")
        chord_name = get_chord_name(chord_type)
        prompt += (
            f"\n\nI want you to tell me how I could play the "
            f"{key} {chord_name} on this {instrument.name}.\n\n"
            f"Make sure to choose one final answer, which you should "
            f"start with 'ANSWER:' and specify in the following format: {form}"
        )

        prompt += (
            "\n\nUse fret 0 to indicate an open string and fret X to indicate not playing a"
            " string. Each increase in fret corresponds to an increase in half a note."
        )
    if chain_of_thought:
        prompt += "\n\nLet's think step by step."
    return prompt


def main(args):

    tunings = args.tunings
    instrument = args.instrument
    model = args.model

    instrument = INSTRUMENTS[instrument](list(tunings))

    world = get_world(args.instrument, args.tunings)

    # Automatically create output file
    output_file = get_output_file(
            args.exp_dir, 
            args.instrument, 
            world, 
            args.tunings, 
            args.model, 
            args.chain_of_thought, 
            args.is_control)
    
    print("output file: ", output_file)

    assert not os.path.exists(output_file), f"output_file already exists: {output_file}"

    data_loader = ChordsLoader(instrument)


    if args.is_control:
#        templatized = [templatize(instrument, args.chain_of_thought, args.is_control, 
#                chord=None, 
#                fret_idx_for_control=fret_idx, 
#                string_for_control=string) for fret_idx, string in itertools.product([1, 2], instrument.tunings)] 
        templatized = [templatize(instrument, args.chain_of_thought, args.is_control, 
                chord=None, 
                fret_idx_for_control=fret_idx, 
                string_for_control=None) for fret_idx in [0, 1, 2]]
    else:
        templatized = [templatize(instrument, args.chain_of_thought, args.is_control, 
                chord=chord, 
                fret_idx_for_control=None, 
                string_for_control=None) for chord, _ in data_loader.items()] 

#    templatized = [
#        templatize(instrument, chord, args.chain_of_thought, args.is_control) for chord, notes in data_loader.items()
#    ]

    print('EXAMPLE INPUT:\n=====================')
    print(templatized[0])
    print('\n\n')

    responses = query_batch(templatized, model, skip_cache=False)

    with open(output_file, "w") as log:
        if args.is_control:
#            for (fret_idx, string), expr, response in zip(itertools.product([1, 2], instrument.tunings), templatized, responses):
#                log.write(f"{str(fret_idx)}\t{string}\t{escape(expr)}\t{escape(response)}\n")
            for fret_idx, expr, response in zip([0, 1, 2], templatized, responses):
                log.write(f"{str(fret_idx)}\t{escape(expr)}\t{escape(response)}\n")
        else:
            for chord, expr, response in zip(data_loader.items(), templatized, responses):
                log.write(f"{str(chord)}\t{escape(expr)}\t{escape(response)}\n")


if __name__ == "__main__":
    
    parser = get_parser()
    args = parser.parse_args()

    print(args)
    print(os.environ.get("INTERACTIONS_SAVE_PATH"))

    main(args)
