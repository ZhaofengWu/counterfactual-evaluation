"""Generate chess dataset. """


from __future__ import annotations

import math
import pathlib
import random
import os
import sys
from typing import Sequence, Union, Optional, Tuple
import io
from copy import deepcopy

import chess
import chess.pgn
from tqdm import tqdm

random.seed(0)


class Opening:
    def __init__(
        self,
        opening: Union[str, chess.pgn.Game, Sequence[chess.Move]]
    ):
        if not opening:
            raise ValueError("Opening must be non-empty.")
        if isinstance(opening, str):
            self.game = self._from_pgn(opening)
        elif isinstance(opening, chess.pgn.Game):
            self.game = deepcopy(opening)
        elif isinstance(opening[0], chess.Move):
            self.game = self._from_moves(opening)
        else:
            raise ValueError("input opening must be a string, sequence of moves or sequence of move notation")

    @staticmethod
    def _from_pgn(opening_text: str):
        pgn = io.StringIO(opening_text)
        return chess.pgn.read_game(pgn)

    @staticmethod
    def _from_moves(opening_moves: Sequence[chess.Move]):
        game = chess.pgn.Game()
        node = game
        for move in opening_moves:
            node = node.add_variation(move)
        return game

    def as_text(self, board: Union[chess.Board, ChessVariant], inline=False):
        """
        A chess.Board object must be passed in to determine the text
        """
        if isinstance(board, ChessVariant):
            board = board.init_board()
        self.game.setup(board=board)
        columns = None if inline else 80
        exporter = chess.pgn.StringExporter(columns=columns, headers=False,
                                            variations=False, comments=False)
        pgn_string = self.game.accept(exporter)
        return pgn_string

    def as_moves(self):
        return [deepcopy(m) for m in self.game.mainline_moves()]


class ChessVariant:
    """Abstract class for a chess variant game"""
    _description: int = NotImplementedError
    def __init__(self, layout: str ='rnbqkbnr'):
        self.layout = layout

    @property
    def description(self):
        return self._description

    def init_board(self) -> chess.Board:
        board = chess.Board(
            f'{self.layout}/pppppppp/8/8/8/8/PPPPPPPP/{self.layout.upper()}')
        return board

    def is_valid_opening(self, opening: Union[str, chess.pgn.Game, Sequence[chess.Move], Opening]):
        if not isinstance(opening, Opening):
            opening = Opening(opening)
        board = self.init_board()
        valid = True
        for move in opening.as_moves():
            if move not in board.legal_moves:
                valid = False
                break
            board.push(move)
        return valid

    def is_interesting_move(self, board: chess.Board, move: chess.Move):
        """is a move not just pushing a random pawn"""
        turn = board.turn
        old_right = board.has_castling_rights(turn)
        board.push(move)
        new_right = board.has_castling_rights(turn)
        board.pop()
        is_bon_cloud = old_right != new_right and not board.is_castling(turn)

        bad_moves = [
            chess.Move(from_square=chess.B1, to_square=chess.A3),
            chess.Move(from_square=chess.G1, to_square=chess.H3),
            chess.Move(from_square=chess.B8, to_square=chess.A6),
            chess.Move(from_square=chess.G8, to_square=chess.H6),
        ]

        interesting = not board.is_irreversible(move) or board.is_capture(move) or board.is_castling(move)
        interesting = interesting and not is_bon_cloud and move not in bad_moves

        return interesting

    @staticmethod
    def _make_move_illegal(board: chess.Board, candidate: chess.Move):
        """modify a candidate move such that it's no longer legal"""
        not_found = True
        toggle_start = random.random() < 0.0
        trial = 0
        max_trail = 1000
        while not_found:
            from_square, to_square = candidate.from_square, candidate.to_square
            if toggle_start:
                square = from_square
            else:
                square = to_square
            file, rank = chess.square_file(square), chess.square_rank(square)
            file += random.randint(-1, 1)
            rank += random.randint(-1, 1)
            file = max(min(file, 7), 0)
            rank = max(min(rank, 7), 0)
            if toggle_start:
                move = chess.Move(from_square=chess.square(file, rank), to_square=to_square)
            else:
                move = chess.Move(from_square=from_square, to_square=chess.square(file, rank))
            if move not in list(board.legal_moves):
                not_found = False
            trial += 1
            if trial >= max_trail:
                raise RuntimeError("maximum trials reached")
        return move

    @staticmethod
    def _sample_jump_move(board: chess.Board):
        """Sample an illegal move that skips to jump into own pieces"""

        not_found = True
        trial = 0
        max_trail = 2000
        while not_found:
            """sample a piece and make moves as if there is nothing blocking it"""
            piece_type = random.choice([chess.KNIGHT, chess.BISHOP, chess.QUEEN])
            piece_color = board.turn
            squares = board.pieces(piece_type, piece_color)
            if len(squares):
                empty_board = chess.Board(fen=None)
                empty_board.set_piece_at(random.choice(list(squares)), chess.Piece(piece_type, chess.WHITE))
                legal_moves = list(empty_board.legal_moves)
                move = random.choice(legal_moves)
                if move not in board.legal_moves:
                    not_found = False
            trial += 1
            if trial >= max_trail:
                raise RuntimeError("maximum trials reached")
        return move

    def _sample_illegal_move(self, board: chess.Board, interesting_ratio: float = 0.75):
        legal_moves = list(board.legal_moves)
        if random.random() < 1 - interesting_ratio and legal_moves:
            move = random.choice(legal_moves)
            return self._make_move_illegal(board, move)
        elif random.random() < 0.8 and legal_moves:
            legal_moves = [m for m in legal_moves if self.is_interesting_move(board, m)]
            move = random.choice(legal_moves)
            return self._make_move_illegal(board, move)
        else:
            return self._sample_jump_move(board)

    def sample_legal_opening(
        self,
        num_moves: int,
        also_legal: Optional[ChessVariant] = None,
        also_illegal: Optional[ChessVariant] = None,
        interesting_ratio: float = 0.4
    ) -> Tuple[chess.Move]:
        """
        Args:
            num_moves: number of move rounds to sample.
            also_legal: a ChessVariant where sampled opening is supposed to be also valid for
            also_illegal: a ChessVariant where sampled opening is supposed to be also invalid for
            interesting_ratio: the rate where we bias sampling to an intersting move that's not pawn push
        """
        not_found = True
        max_trials = 2000
        trial_idx = 0
        while not_found:
            board = self.init_board()
            legal_board = also_legal.init_board() if also_legal else None
            illegal_board = also_illegal.init_board() if also_illegal else None
            opening = []
            contains_illegal = False
            for i in range(num_moves * 2):
                legal_moves = set(board.legal_moves)
                if also_legal:
                    legal_moves = set(legal_moves & set(legal_board.legal_moves))
                legal_moves = list(legal_moves)
                if not legal_moves:
                    break
                else:
                    if i == 0 and random.random() < 0.5:
                        legal_moves = [
                            chess.Move.from_uci("d2d4"),
                            chess.Move.from_uci("e2e4"),
                        ]
                    if i == 1 and random.random() < 0.5:
                        legal_moves = [
                            chess.Move.from_uci("c7c5"),
                            chess.Move.from_uci("d7d5"),
                            chess.Move.from_uci("e7e5"),
                            chess.Move.from_uci("d7d6"),
                            chess.Move.from_uci("e7e6"),
                        ]
                    if (i and random.random() < interesting_ratio) or \
                            (i and random.random() < interesting_ratio * 0.25):
                        legal_moves = [m for m in legal_moves if self.is_interesting_move(board, m)]
                        if not legal_moves:
                            break
                    move = random.choice(legal_moves)
                    board.push(move)
                    # print(board)
                    if also_legal:
                        legal_board.push(move)
                    if also_illegal:
                        if move not in illegal_board.legal_moves:
                            contains_illegal = True
                        else:
                            illegal_board.push(move)
                        #     print(illegal_board)
                    opening.append(move)
            if len(opening) == 2 * num_moves:
                not_found = False
            if also_illegal and not contains_illegal:
                not_found = True
            trial_idx += 1
            if trial_idx >= max_trials:
                raise RuntimeError("maximum trials reached")

        return tuple(opening)

    def sample_illegal_opening(
        self,
        num_moves: int,
        also_illegal: Optional[ChessVariant] = None,
        interesting_ratio: float = 0.5
    ) -> Tuple[chess.Move]:
        """
        Args:
            num_moves: number of move rounds to sample.
            also_illegal: a ChessVariant where sampled opening is supposed to be also invalid for
            interesting_ratio: the rate where we bias sampling to an intersting move that's not pawn push
        """
        not_found = True
        max_trials = 2000
        trial_idx = 0
        illegal_index = random.randint(2, num_moves * 2 - 1)
        while not_found:
            board = self.init_board()
            illegal_board = also_illegal.init_board() if also_illegal else None
            opening = []
            contains_illegal = False
            for i in range(num_moves * 2):
                legal_moves = list(board.legal_moves)
                if i == 0 and random.random() < 0.5:
                    legal_moves = [
                        chess.Move.from_uci("d2d4"),
                        chess.Move.from_uci("e2e4"),
                    ]
                if i == 1 and random.random() < 0.5:
                    legal_moves = [
                        chess.Move.from_uci("c7c5"),
                        chess.Move.from_uci("d7d5"),
                        chess.Move.from_uci("e7e5"),
                        chess.Move.from_uci("d7d6"),
                        chess.Move.from_uci("e7e6"),
                    ]
                if not legal_moves:
                    illegal_index = i
                if i == illegal_index:
                    move = self._sample_illegal_move(board)
                else:
                    if (i and random.random() < interesting_ratio) or \
                            (i and random.random() < interesting_ratio * 0.25):
                        legal_moves = [m for m in legal_moves if self.is_interesting_move(board, m)]
                    if not legal_moves:
                        break
                    move = random.choice(legal_moves)
                board.push(move)

                if also_illegal:
                    if move not in illegal_board.legal_moves:
                        contains_illegal = True
                    else:
                        illegal_board.push(move)
                    #     print(illegal_board)
                opening.append(move)
            if len(opening) == 2 * num_moves:
                not_found = False
            if also_illegal and not contains_illegal:
                not_found = True
            trial_idx += 1
            if trial_idx >= max_trials:
                raise RuntimeError("maximum trials reached")

        return tuple(opening)


class Chess(ChessVariant):
    _description = "normal chess"


class KnightBishopSwappedChess(ChessVariant):
    _description = "knight and bishoped are swapped"

    def __init__(self):
        super().__init__("rbnqknbr")


class Sampler:
    def __init__(
        self,
        real_world_legal: bool,
        counter_factual_legal: bool
    ):
        """
        Sample openings based on desired criteria
        Args:
            real_world_legal: True if desired openings should be legal for real world case, False for illegal
            counter_factual_legal: True if desired openings should be legal for counterfactual case, False for illegal
        """
        self.real_world_legal = real_world_legal
        self.counter_factual_legal = counter_factual_legal

    def sample(self, num_samples: int, num_moves: int, interesting_ratio: float = 0.5):
        openings = set()
        real_world_chess = Chess()
        counter_factual_chess = KnightBishopSwappedChess()
        with tqdm(total=num_samples,
                  desc=f"Generating openings that's {'legal' if self.real_world_legal else 'illegal'} for real world & "
                       f"{'legal' if self.counter_factual_legal else 'illegal'} for counter factual") as pbar:
            while len(openings) < num_samples:
                if self.real_world_legal and self.counter_factual_legal:
                    opening = real_world_chess.sample_legal_opening(
                        num_moves, also_legal=counter_factual_chess, interesting_ratio=interesting_ratio)
                elif self.real_world_legal and not self.counter_factual_legal:
                    opening = real_world_chess.sample_legal_opening(
                        num_moves, also_illegal=counter_factual_chess, interesting_ratio=interesting_ratio)
                elif not self.real_world_legal and self.counter_factual_legal:
                    opening = counter_factual_chess.sample_legal_opening(
                        num_moves, also_illegal=real_world_chess, interesting_ratio=interesting_ratio)
                else:
                    opening = real_world_chess.sample_illegal_opening(
                        num_moves, also_illegal=counter_factual_chess, interesting_ratio=interesting_ratio * 0.25)
                openings.add(Opening(opening))
                pbar.n = len(openings)
                pbar.refresh()
        return openings

    def sample_and_save(
            self, num_samples: int, num_moves: int, save_dir: Union[str, pathlib.Path], interesting_ratio: float = 0.5):
        openings = self.sample(num_samples, num_moves, interesting_ratio)
        suffix = f"_{'T' if self.real_world_legal else 'F'}_{'T' if self.counter_factual_legal else 'F'}.txt"
        pathlib.Path(save_dir).mkdir(exist_ok=True, parents=True)
        real_world_file = open(os.path.join(save_dir, f"real_world" + suffix), 'w')
        counter_factual_file = open(os.path.join(save_dir, f"counter_factual" + suffix), 'w')
        real_world_cls = Chess
        counter_factual_cls = KnightBishopSwappedChess
        for opening in openings:
            real_world_file.write(opening.as_text(real_world_cls(), inline=True) + "\n")
            counter_factual_file.write(opening.as_text(counter_factual_cls(), inline=True) + "\n")
        real_world_file.close()
        counter_factual_file.close()


def test():
    real_world_chess = Chess()
    counter_factual_chess = KnightBishopSwappedChess()
    opening = real_world_chess.sample_legal_opening(5, also_illegal=counter_factual_chess)
    opening = Opening(opening)
    assert real_world_chess.is_valid_opening(opening)
    assert not counter_factual_chess.is_valid_opening(opening)

    opening = real_world_chess.sample_legal_opening(5, also_legal=counter_factual_chess)
    opening = Opening(opening)
    assert real_world_chess.is_valid_opening(opening)
    assert counter_factual_chess.is_valid_opening(opening)

    opening = real_world_chess.sample_illegal_opening(5, also_illegal=counter_factual_chess)
    opening = Opening(opening)
    assert not real_world_chess.is_valid_opening(opening)
    assert not counter_factual_chess.is_valid_opening(opening)


def main(num_moves=4):
    """
    sample a balanced dataset where half the of samples are yes and half of the samples are no, for both real world and
    counter factual.

    T_T means opening that's legal for both real-world and counter-factual; it doesn't have bishop or knight moves
    T_F means opening that's legal for real-world but illegal for counterfactual
    F_T means opening that's illegal for real-world but legal for counterfactual
    F_F means opening that's illegal for both real-world and counter-factual; it has a lot of bizarre moves

    We mix T_T, T_F, F_T, F_F by 0%, 50%, 50%, 0% of the total openings. This guarantees we 50% yes and 50% no for
    both real-world and counterfactual cases. This also guarantees we don't have too many bizarre moves that's less
    meaningful for LLMs
    """
    num_moves = int(num_moves)
    if num_moves % 2:
        raise ValueError('number of moves must be multiple of 4 to be fair')

    num_samples = 400
    num_turns = num_moves // 2  # one turn is 2 moves
    num_samples_tt = int(num_samples * 0.0)
    num_samples_tf = int(num_samples * 0.5)
    num_samples_ft = int(num_samples * 0.5)
    num_samples_ff = int(num_samples * 0.0)
    save_dir = f'chess/data/chess_{num_moves}_move'
    Sampler(True, True).sample_and_save(num_samples_tt, num_turns, save_dir)
    Sampler(True, False).sample_and_save(num_samples_tf, num_turns, save_dir)
    Sampler(False, True).sample_and_save(num_samples_ft, num_turns, save_dir)
    Sampler(False, False).sample_and_save(num_samples_ff, num_turns, save_dir)


if __name__ == "__main__":
    try:
        main(
            *sys.argv[1:]
        )  # pylint: disable=no-value-for-parameter,too-many-function-args
    except Exception as e:
        import pdb
        import traceback

        if not isinstance(e, (pdb.bdb.BdbQuit, KeyboardInterrupt)):
            print("\n" + ">" * 100 + "\n")
            traceback.print_exc()
            print()
            pdb.post_mortem()
