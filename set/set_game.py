"""SET SETGame data generator"""
import dataclasses
import itertools
from enum import Enum
from typing import List, Tuple
import logging
import numpy as np
import regex as re
import os
import pickle

from query_utils import escape


class Color(Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


class Shape(Enum):
    SQUIGGLE = "squiggle"
    DIAMOND = "diamond"
    OVAL = "oval"


class Fill(Enum):
    SOLID = "solid"
    STRIPED = "striped"
    OPEN = "open"


@dataclasses.dataclass(frozen=True, eq=True)
class Figure:
    color: Color
    shape: Shape
    fill: Fill

    def __str__(self):
        return f"{self.color.value} | {self.shape.value} | {self.fill.value}"


@dataclasses.dataclass(frozen=True, eq=True)
class Card:
    figure: Figure
    number: int

    def __str__(self):
        return f"({self.number} | {self.figure})"

    @classmethod
    def from_str(cls, string: str):
        number, *figure = string.strip().replace("(", "").replace(")", "").split(" | ")
        color, shape, fill = figure
        return cls(Figure(Color(color), Shape(shape), Fill(fill)), int(number))


class SETGame:
    num_cards_per_round: int = 12

    def __init__(self, num_cards_per_round: int = 12, seed: int = 42):
        deck = []
        for color in Color:
            for shape in Shape:
                for fill in Fill:
                    figure = Figure(color, shape, fill)
                    deck.append(Card(figure, 1))
                    deck.append(Card(figure, 2))
                    deck.append(Card(figure, 3))

        self.deck = deck

        self.rng = np.random.default_rng(seed)
        self.rng.shuffle(self.deck)
        self.num_cards_per_round = num_cards_per_round
        self.index = 0
        self.board = []

    def meta_info(self):
        info = "You will be shown 12 cards. Each card has a figure and a number.\n"
        info += "A figure is a combination of a color, a shape, and a fill.\n\n"
        info += "Set of colors are: "
        for color in Color:
            info += color.value + " , "
        info = info[:-2] + ".\n"
        info += "Set of shapes are: "
        for shape in Shape:
            info += shape.value + " , "
        info = info[:-2] + ".\n"
        info += "Set of fills are: "
        for fill in Fill:
            info += fill.value + " , "
        info = info[:-2] + ".\n"
        return info

    def rule_info(self):
        info = (
            "--THE RULE OF THE GAME--\nA GAME-SET is set of three cards: For each attribute,"
            " (color, shape, fill, number), the"
            " three cards should either be ALL the SAME or NONE the SAME (=ALL"
            " DIFFERENT, e.g. if 2 of the cards have the same value, and 1 of them has"
            " a different value, the set is NOT valid; for example, (blue, green,"
            " blue) is MIXED and does not satisfy any of the rule, whereas (oval, diamond, squiggle) is all"
            " different.\n"
        )
        return info

    def pick_info(self):
        info = (
            "You can pick a set by typing the cards in the below format:\n"
            "First card: CARD1\n"
            "Second card: CARD2\n"
            "Third card: CARD3\n"
            "Now remember the rule and tell me which three cards here constitutes"
            " a GAME-SET in the same format.\n"
        )

        return info

    def board_info(self):
        info = "Here is the board:\n"
        for i in range(3):
            info += (
                str(" ".join([str(card) for card in self.board[i * 4 : (i + 1) * 4]]))
                + "\n"
            )
        return info

    def reset(self) -> List[Card]:
        self.index = self.num_cards_per_round
        self.board = self.deck[: self.num_cards_per_round]
        return self.board

    def is_valid(self, cards: Tuple[Card]) -> bool:
        if len(cards) != 3:
            return False
        elif not all([card in self.board for card in cards]):
            return False
        else:
            return True

    def is_set(self, cards: Tuple[Card]) -> bool:
        if self.is_valid(cards):
            if len(set([card.number for card in cards])) == 2:
                return False

            for attr in ["color", "shape", "fill"]:
                if len(set([getattr(card.figure, attr) for card in cards])) == 2:
                    return False

            return True
        return False

    def find_sets(self) -> List[List[Card]]:
        # search for sets in the board
        sets = []
        sets_indices = []
        for i in range(len(self.board)):
            for j in range(i + 1, len(self.board)):
                for k in range(j + 1, len(self.board)):
                    cards = (self.board[i], self.board[j], self.board[k])
                    if self.is_set(cards):
                        sets.append(cards)
                        sets_indices.append((i, j, k))
        return list(set(sets)), list(set(sets_indices))

    def next(self, set_cards: List[Card]) -> List[Card]:
        success = False
        if self.is_set(set_cards):
            success = True
            new_cards = self.deck[self.index : self.index + 3]
            self.index += 3
            for index, card in enumerate(self.board):
                if card in set_cards:
                    self.board[index] = new_cards.pop()
        return self.board, success


class CounterfactualSetGame(SETGame):
    def is_set(self, cards: Tuple[Card]) -> bool:
        if self.is_valid(cards):
            if len(set([card.number for card in cards])) != 2:
                return False

            for attr in ["color", "shape", "fill"]:
                if len(set([getattr(card.figure, attr) for card in cards])) == 2:
                    return False

            return True
        return False

    def rule_info(self):
        info = (
            "--THE RULE OF THE GAME--\n(This is not the original SET game. It has a"
            " tweaked rule.)\nIn this version, a GAME-SET is a set of three cards:\n-"
            " For each figure attribute except the number (color, shape, fill), the"
            " three cards should either be ALL the SAME or NONE the SAME (=ALL"
            " DIFFERENT, e.g. if 2 of the cards have the same value, and 1 of them has"
            " a different value, the set is NOT valid; for example, (blue, green,"
            " blue) is MIXED and does not satisfy any of the rule, whereas (oval, diamond, squiggle) is all"
            " different.\n- But only for the number attribute, 2 of the cards should"
            " have the same number, and 1 of them should have a different number in"
            " order for the set to be valid.\n"
        )
        return info


def prepare_data(
    Game: SETGame = SETGame,
    rounds: int = 100,
    hints: int = 1,
    seed: int = 42,
    cot: bool = False,
):
    assert hints in [0, 1, 2]
    data = []
    rng = np.random.default_rng(seed)
    seed += 1
    trials = 1
    while True:
        # we could iterate over actual rounds from same game
        # but since we will do one round evaluation we just need random samples
        game = Game(seed=seed + trials)
        trials += 1
        board = game.reset()
        sets, indices = game.find_sets()
        if len(sets) == 1:
            # random choice
            hint_set = rng.choice(list(sets))
            input = "\n".join(
                [
                    game.meta_info(),
                    game.rule_info(),
                    game.board_info(),
                    game.pick_info(),
                ]
            )
            hint_text = ""
            if hints > 0:
                input += (
                    f"I will give you {hints} cards as a hint, and you tell me the"
                    " third one.\n"
                )
                order_words = ["First", "Second", "Third"]
                for t in range(hints):
                    input += f"{order_words[t]} card: {hint_set[t]}\n"
                    hint_text += (  # same as above
                        f"{order_words[t]} card: {hint_set[t]}\n"
                    )
                if cot:
                    input += "Let's think step by step.\n"
                input = input[:-1]
            data.append((input, game, hint_text))
            if len(data) == rounds:
                break
    return data


def prepare_control(
    Game: SETGame = SETGame, rounds: int = 100, seed: int = 42, cot: bool = True
):
    data = []
    rng = np.random.default_rng(seed)
    seed += 1
    trials = 1
    while True:
        # we could iterate over actual rounds from same game
        # but since we will do one round evaluation we just need random samples
        game = Game(seed=seed + trials)
        trials += 1
        board = game.reset()
        sets, indices = game.find_sets()
        if len(sets) == 1:
            # random choice
            if rng.random() < 0.5:
                hint_set = rng.choice(list(sets))
            else:
                hint_set = rng.choice(game.board, size=3, replace=False)

            label = game.is_set(hint_set)

            input = "\n".join(
                [
                    game.meta_info().replace("You will be shown 12 cards. ", ""),
                    game.rule_info(),
                    #        game.board_info(),
                ]
            )
            hint_text = ""
            input += (
                f"I will give you three cards from the board, and you will tell me"
                f" whether this constitutes a GAME-SET.\n\n"
            )
            order_words = ["First", "Second", "Third"]
            for t in range(3):
                input += f"{order_words[t]} card: {hint_set[t]}\n"
                hint_text += f"{order_words[t]} card: {hint_set[t]}\n"  # same as above
            input = input[:-1]
            if cot:
                input += (
                    "\n\nIs this a GAME-SET? Answer with yes or no in the last line. Let's"
                    " verify rules for each attribute step-by-step:\n"
                )
            else:
                input += "\n\nIs this a GAME-SET?"
            data.append((input, game, hint_text, label))
            if len(data) == rounds:
                break
    return data


def parse_control(output: str) -> str:
    answer = output.split("\n")[-1].strip().lower()
    label = False
    if "yes" in answer:
        label = True
    elif "do not constitute" in answer:
        label = False
    elif "not a game-set" in answer:
        label = False
    elif "is a game-set" in answer:
        label = True
    elif "is a valid game-set" in answer:
        label = True
    else:
        answer = output.split("\n")[0].strip().lower()
        if "yes" in answer:
            label = True
    return label


def parse_output(output: str, hints: int = 0, is_hint_text=False) -> List[str]:
    cards = []
    lines = output.split("\n")
    for line in lines:
        if hints == 0 and "First card:" in line:
            cards.append(line.split(":")[1].strip())
        if hints <= 1 and "Second card:" in line:
            cards.append(line.split(":")[1].strip())
        if hints <= 2 and "Third card:" in line:
            cards.append(line.split(":")[1].strip())
    if not is_hint_text:
        required = 3 - hints
        if len(cards) != required:
            remaining = required - len(cards)
            found = re.findall(
                r"\([0-9] \| [A-Za-z]{0,8} \| [A-Za-z]{0,8} \| [A-Za-z]{0,8}\)", output
            )
            if found:
                cards += found[-remaining:]
        # take last three cards
        cards = cards[-required:]
    try:
        cards = [Card.from_str(card) for card in cards]
    except:
        print("Error parsing cards: ", cards)

    return tuple(cards)


def evaluate(
    Game: SETGame = SETGame,
    model="gpt-4-0314",
    rounds: int = 100,
    hints: int = 1,
    seed: int = 42,
    cot: bool = True,
    save_data: bool = True,
    load_data: bool = False,
):
    if load_data:
        data_type = "cf" if Game == CounterfactualSetGame else "real"
        path = f"set/data/{data_type}/h{hints}/cot_{cot}/data.pkl"
        with open(path, "rb") as handle:
            data = pickle.load(handle)
    else:
        data = prepare_data(Game, rounds=rounds, hints=hints, seed=seed, cot=cot)

    if save_data:
        data_type = "cf" if Game == CounterfactualSetGame else "real"
        path = f"set/data/{data_type}/h{hints}/cot_{cot}/data.pkl"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as handle:
            pickle.dump(data, handle)

    inputs = [example[0] for example in data]
    responses = query_batch(inputs, model)
    success = 0
    total = 0
    for example, response in zip(data, responses):
        hint_cards = parse_output(example[2], is_hint_text=True)
        guessed_cards = parse_output(response, hints=hints)
        prediction = hint_cards + guessed_cards
        total += 1
        if len(prediction) == 3:
            game = example[1]
            success += game.is_set(prediction)
            if not game.is_set(prediction):
                logging.warning("Input: " + str(example[0]))
                logging.warning("Guessed Cards: " + str(guessed_cards))
                logging.warning("Response: " + str(response))
                logging.warning("Prediction: " + str(prediction))
        else:
            logging.warning(
                f"Error in parsing less than three cards, num_cards: {len(prediction)}"
            )
            logging.warning("Input: " + str(example[0]))
            logging.warning("Response: " + str(response))
            logging.warning("Prediction: " + str(prediction))
    print(
        f"Success rate (game: {Game}, hints: {hints}): {success/total},"
        f" {success}/{total}"
    )


def evaluate_control(
    Game: SETGame = SETGame,
    model="gpt-4-0314",
    rounds: int = 100,
    seed: int = 42,
    cot: int = True,
    save_data: bool = True,
    load_data: bool = False,
):
    if load_data:
        data_type = "cf" if Game == CounterfactualSetGame else "real"
        path = f"set/data/{data_type}/control/cot_{cot}/data.pkl"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "rb") as handle:
            data = pickle.load(handle)
    else:
        data = prepare_control(Game, rounds=rounds, seed=seed, cot=cot)

    if save_data:
        data_type = "cf" if Game == CounterfactualSetGame else "real"
        path = f"set/data/{data_type}/control/cot_{cot}/data.pkl"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as handle:
            pickle.dump(data, handle)

    inputs = [example[0] for example in data]
    responses = query_batch(inputs, model)
    success = 0
    total = 0
    for example, response in zip(data, responses):
        prediction = parse_control(response)
        label = example[-1]
        success += label == prediction
        # print("Label: ", label, "Prediction: ", prediction)
        total += 1
        if not label == prediction:
            logging.warning("Input: " + str(example[0]))
            logging.warning("Response: " + str(response))
            logging.warning("True Label: " + str(label))
            logging.warning("Prediction: " + str(prediction))
    print(
        f"Control success rate (game: {Game}, hints: 3): {success/total},"
        f" {success}/{total}"
    )


if __name__ == "__main__":

    def unit_tests():
        game = SETGame(seed=15)
        board = game.reset()
        print(game.meta_info())
        print(game.rule_info())
        print(game.board_info())
        print(game.pick_info())
        sets, indices = game.find_sets()
        print(len(sets))
        print(sets[0])
        board, success = game.next(sets[0])
        print(game.meta_info())
        print(game.rule_info())
        print(game.board_info())
        print(game.pick_info())
        sets, indices = game.find_sets()
        example_set = sets[0]
        print("I'll give you two cards from a GAME-SET, you tell me the third one.")
        print("First card: ", example_set[0])
        print("Second card: ", example_set[1])
        print("Third card: ", example_set[2])
        print(len(sets))
        print(sets[0])
        print(sets[1])

    # unit_tests()

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="gpt-4-0314")
    parser.add_argument("--rounds", type=int, default=100)
    parser.add_argument("--hints", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--cot", type=str, default="False")
    parser.add_argument("--save_data", type=str, default="False")
    parser.add_argument("--save_interactions", type=str, default="False")
    parser.add_argument("--load_data", type=str, default="False")

    args = parser.parse_args()

    args.cot = args.cot == "True"
    args.save_data = args.save_data == "True"
    args.save_interactions = args.save_interactions == "True"
    args.load_data = args.load_data == "True"

    assert not (args.save_data and args.load_data)

    logging.warning(
        "Model: "
        + str(args.model)
        + "\nRounds: "
        + str(args.rounds)
        + "\nSeed: "
        + str(args.seed)
        + "\nCOT: "
        + str(args.cot)
    )

    MODEL_STR = args.model.replace("/", "_")

    from query_utils import query_batch

    evaluate_control(
        Game=SETGame,
        model=args.model,
        rounds=args.rounds,
        seed=args.seed,
        cot=args.cot,
        save_data=args.save_data,
        load_data=args.load_data,
    )
    evaluate_control(
        Game=CounterfactualSetGame,
        model=args.model,
        rounds=args.rounds,
        seed=args.seed,
        cot=args.cot,
        save_data=args.save_data,
        load_data=args.load_data,
    )
    evaluate(
        Game=SETGame,
        model=args.model,
        rounds=args.rounds,
        hints=2,
        seed=args.seed,
        cot=args.cot,
        save_data=args.save_data,
        load_data=args.load_data,
    )
    evaluate(
        Game=CounterfactualSetGame,
        model=args.model,
        rounds=args.rounds,
        hints=2,
        seed=args.seed,
        cot=args.cot,
        save_data=args.save_data,
        load_data=args.load_data,
    )
    evaluate(
        Game=SETGame,
        model=args.model,
        rounds=args.rounds,
        hints=1,
        seed=args.seed,
        cot=args.cot,
        save_data=args.save_data,
        load_data=args.load_data,
    )
    evaluate(
        Game=SETGame,
        model=args.model,
        rounds=args.rounds,
        hints=0,
        seed=args.seed,
        cot=args.cot,
        save_data=args.save_data,
        load_data=args.load_data,
    )
    evaluate(
        Game=CounterfactualSetGame,
        model=args.model,
        rounds=args.rounds,
        hints=1,
        seed=args.seed,
        cot=args.cot,
        save_data=args.save_data,
        load_data=args.load_data,
    )
    evaluate(
        Game=CounterfactualSetGame,
        model=args.model,
        rounds=args.rounds,
        hints=0,
        seed=args.seed,
        cot=args.cot,
        save_data=args.save_data,
        load_data=args.load_data,
    )
