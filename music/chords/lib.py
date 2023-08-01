"""This file provide chord data loaders and instrument functionalities for chord fingering tasks."""

import os
import abc
import requests
import json
import dataclasses

from typing import List, Optional, Set, Tuple, Union

from music.lib import *

class StringInstrument(abc.ABC):
    """Abstract class for string instruments."""

    def __init__(self, tunings=None):
        if tunings:
            self.set_tune(tunings)

    @abc.abstractproperty
    def name(self) -> str:
        raise NotImplementedError

    @abc.abstractproperty
    def tunings(self) -> List[str]:
        raise NotImplementedError

    @abc.abstractmethod
    def set_tune(self, tunings: List[str]):
        raise NotImplementedError

    def get_note(self, string: Union[str, int], fret: int) -> str:
        """Get the note of a string at a given fret.

        Assumes the intervals are 1/2 notes.
        """
        if isinstance(string, str):
            string = self.tunings.index(string)

        tunings = self.tunings
        start_note = note_to_int(tunings[string])
        end_note = (start_note + fret) % 12
        return INT_TO_NOTE[end_note]


class Guitar(StringInstrument):
    """6-string Guitar class."""

    _tunings: List[str] = ["E", "A", "D", "G", "B", "E"]

    @property
    def tunings(self) -> List[str]:
        return self._tunings

    @property
    def name(self) -> str:
        return "guitar"

    def set_tune(self, tunings: List[str]):
        assert len(tunings) == 6, "Guitar accepts 6-string tunings"
        self._tunings = tunings


class Ukulele(StringInstrument):
    """4-string Ukulele class."""

    _tunings = ["G", "C", "E", "A"]

    @property
    def tunings(self):
        return self._tunings

    @property
    def name(self):
        return "ukulele"

    def set_tune(self, tunings):
        assert len(tunings) == 4, f"Ukulele accepts 4-string tunings; {tunings}"
        self._tunings = tunings

# name -> class for easy access
INSTRUMENTS = {"guitar": Guitar, "ukulele": Ukulele}

@dataclasses.dataclass
class Chord:
    """Chord dataclass."""

    key: str
    suffix: str
    notes: Tuple[str]

    def __hash__(self) -> int:
        return hash((self.key, self.suffix))

    def __eq__(self, other) -> bool:
        return self.key == other.key and self.suffix == other.suffix

    def __str__(self) -> str:
        return self.key + "-" + self.suffix




class ChordsLoader:
    """Chord data loader.

    This class loads chord data from. Example usage:
    ```
        data_loader = ChordsLoader(Guitar())
    ```
    """

    CHORDS_DB_URL: str = (
        "https://raw.githubusercontent.com/tombatossals/chords-db/master/lib/"
    )
    CHORDS_DB_FOLDER: str = "data/"
    INCLUDE: str = {
        "major": 3,
        "minor": 3,
        "7": 4,
        "m7": 4,
        "5": 2,
        "6": 4,
        "sus2": 3,
        "sus4": 3,
        "aug7": 4,
        "dim7": 4,
    }

    def __init__(self, instrument: StringInstrument, task="chord recognition"):
        self.instrument = instrument
        self.chords = self.load_chords(self.instrument)
        # TODO: add chord to position task
        self.task = task

    def download_chord_data(self, url: str, file: str):
        """Download DB from url and save it to file."""
        folder = os.path.dirname(file)
        os.makedirs(folder, exist_ok=True)
        response = requests.get(url)
        data = json.loads(response.text)
        with open(file, "w") as f:
            json.dump(data, f)

    def load_chord_data(self, instrument: StringInstrument):
        """Load chord data from file."""
        # Check if data is already downloaded
        file = os.path.join(self.CHORDS_DB_FOLDER, instrument.name + ".json")
        url = self.CHORDS_DB_URL + instrument.name.lower() + ".json"
        if not os.path.exists(file):
            self.download_chord_data(url, file)
        # Load data
        data = json.load(open(file))
        return data

    def load_chords(self, instrument: StringInstrument) -> List[Chord]:
        """Load chords from data."""
        data = self.load_chord_data(instrument)

        standard_tunings = [tune[:-1] for tune in data["tunings"]["standard"]]
        standard_instrument = INSTRUMENTS[instrument.name](standard_tunings)

        chords = set([])
        for key_note, chord_list in data["chords"].items():
            key_note = standardize(key_note)
            for chord_info in chord_list:
                chord_suffix = chord_info["suffix"]

                if chord_suffix not in self.INCLUDE:
                    # TODO: handle other chords, eg, 9, 11, 13
                    # but think they are buggy in this database
                    continue

                chord_positions = chord_info["positions"]

                for position in chord_positions:
                    frets = position["frets"]
                    base_fret = position["baseFret"] - 1
                    notes = set([])
                    for string, fret in enumerate(frets):
                        if fret != -1:
                            note = standard_instrument.get_note(
                                string, fret + base_fret
                            )
                            notes.add(note)
                    notes = tuple(sorted(notes))

                    # Some chords in the DB is buggy
                    # I check whether the key note in the chord
                    # and the number of notes in the chord is correct
                    if key_note in notes and len(notes) == self.INCLUDE[chord_suffix]:
                        chord = Chord(key_note, chord_suffix, notes)
                        chords.add(chord)
                    elif key_note not in notes:
                        print("Key note not in chord: ", key_note, chord_suffix, notes)
                    elif len(notes) != self.INCLUDE[chord_suffix]:
                        print("Wrong number of notes: ", key_note, chord_suffix, notes)
                    else:
                        print("Unknown error: ", key_note, chord_suffix, notes)

        return list(chords)

    def __len__(self):
        return len(self.chords)

    def __iter__(self):
        """Helper function for iterating over chords."""
        return iter(self.chords)

    def items(self):
        for chord in self.chords:
            yield (str(chord), chord.notes)

if __name__ == "__main__":
    guitar_chords = ChordsLoader(Guitar())
    ukulele_chords = ChordsLoader(Ukulele())
