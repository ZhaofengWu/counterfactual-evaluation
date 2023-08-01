"""This file provide note functionalities, shared across music sub-tasks."""

from collections import OrderedDict
from typing import List, Optional, Set, Tuple, Union

# mapping notes to integers
NOTE_TO_INT = OrderedDict(
    {
        "B#": 0,
        "Dbb": 0,
        "C": 0,
        "B##": 1,
        "C#": 1,
        "Db": 1,
        "C##": 2,
        "Ebb": 2,
        "D": 2,
        "D#": 3,
        "Fbb": 3,
        "Eb": 3,
        "D##": 4,
        "Fb": 4,
        "E": 4,
        "E#": 5,
        "Gbb": 5,
        "F": 5,
        "F#": 6,
        "Gb": 6,
        "F##": 7,
        "Abb": 7,
        "G": 7,
        "G#": 8,
        "Ab": 8,
        "G##": 9,
        "Bbb": 9,
        "A": 9,
        "A#": 10,
        "Cbb": 10,
        "Bb": 10,
        "A##": 11,
        "Cb": 11,
        "B": 11,
    }
)
# and vice versa
INT_TO_NOTE = {v: k for k, v in NOTE_TO_INT.items()}

def standardize(note: str):
    """Standardize notes to single format sharp vs bemols."""
    note = note.replace("sharp", "#")
    note = note.replace("flat", "b")
    return INT_TO_NOTE[NOTE_TO_INT[note]]

def note_to_int(note: str):
    """Standardize notes to single format sharp vs bemols."""
    note = standardize(note)
    return NOTE_TO_INT[note]
