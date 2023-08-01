"""This file provide song and key functionalities for melody retrieval tasks."""

import dataclasses

from typing import List, Optional, Set, Tuple, Union

from music.lib import *

class Key:
    def __init__(self, name: str, key_type: str):
        if key_type not in ['major', 'minor']:
            raise ValueError(key_type)
        self.name = name
        self.standardized_name = standardize(name)
        self.key_type = key_type
        
    def __str__(self):
#        return self.standardized_name + ' ' + self.key_type
        return self.name + ' ' + self.key_type



class Song:
    def __init__(self, 
            notes: str, 
            key: Key,
            name: str):
        self.notes = notes.split(' ')
        self.int_notes = [note_to_int(n) for n in self.notes]
        self.key = key
        self.name = name

    def play(self):
        for note in self.notes:
            print(f"Playing note: {note}")
    
    def get_note(self, note_idx):
        return self.notes[note_idx]
    
    def get_int_note(self, note_idx):
        return self.int_notes[note_idx]
            
    def transpose(self, target_key):
        if target_key.key_type != 'major':
            raise NotImplementedError()
        
        diff = note_to_int(target_key.name) - note_to_int(self.key.name)
        new_notes = [(n + diff) % 12 for n in self.int_notes]
        return [INT_TO_NOTE[n] for n in new_notes] 

KEYS = {f'{k}_major': Key(k, 'major') for k in NOTE_TO_INT.keys() if 'bb' not in k and '##' not in k}

  
SONGS = {
    # both of these prob have other canonical keys too
    'twinkle': Song(
        'C C G G A A G F F E E D D C G G F F E E D G G F F E E D C C G G A A G F F E E D D C',
        KEYS['C_major'],
        'Twinkle Twinkle Little Star',
    ),

    'mary': Song(
        'E D C D E E E D D D E G G E D C D E E E D D E D C',
        KEYS['C_major'],
        'Mary Had a Little Lamb',
    ),
    'happy_birthday': Song(
        'C C D C F E C C D C G F C C C A F E D',
        KEYS['C_major'],
        'Happy Birthday to You'
    ),
    'rainbow': Song(
        'C C B G A B C C A G A F E C D A F D B C D E C',
        KEYS['C_major'],
        'Somewhere Over the Rainbow'
    ),
    'row': Song(
        'C C C D E E D E F G C C C G G G E E E C C C G F E D C',
        KEYS['C_major'],
        'Row, Row, Row Your Boat'
    ),
    'old_macdonald': Song(
        'C C C G A A G E E D D C G C C C G A A G E E D D C',
        KEYS['C_major'],
        'Old MacDonald Had A Farm'
    ),
    'spider': Song(
        'C C C D E E E D C D E C E E F G G F E F G E',
        KEYS['C_major'],
        'Itsy Bitsy Spider'
    ),
    'london': Song(
        'G A G F E F G D E F E F G G A G F E F G D G E C',
        KEYS['C_major'],
        'London Bridge Is Falling Down'
    ),
    }

