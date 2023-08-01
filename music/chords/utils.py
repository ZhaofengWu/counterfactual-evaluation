import argparse

def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default='gpt-4-0314')
    parser.add_argument("--instrument", type=str, choices=['ukulele', 'guitar'])
    parser.add_argument("--tunings", type=str)
    parser.add_argument("--exp_dir", type=str)
    
    parser.add_argument('--chain_of_thought', action='store_true', dest='chain_of_thought')
    parser.set_defaults(chain_of_thought=False)
    parser.add_argument('--is_control', action='store_true', dest='is_control')
    parser.set_defaults(is_control=False)

    return parser

def get_world(instrument, tunings):
    if instrument == 'ukulele':
        if list(tunings) == ['G', 'C', 'E', 'A']:
            return 'original'
        else:
            return 'counterfactual'
    elif instrument == 'guitar':
        if list(tunings) == ['E', 'A', 'D', 'G', 'B', 'E']:
            return 'original'
        else:
            return 'counterfactual'
    else:
        raise ValueError()

