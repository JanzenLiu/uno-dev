import sys
try:
    from .game_v2 import *
except (ModuleNotFoundError if sys.version_info >= (3, 6) else SystemError) as e:
    from game_v2 import *


if __name__ == "__main__":
    players = [
        (PlayerType.PC_FIRST_CARD, "FC_1"),
        (PlayerType.PC_RANDOM, "RANDOM_1", dict(play_draw=1)),
        (PlayerType.PC_GREEDY, "GREEDY_1"),
        (PlayerType.PC_FIRST_CARD, "FC_2"),
        (PlayerType.PC_RANDOM, "RANDOM_2", dict(play_draw=1)),
        (PlayerType.PC_GREEDY, "GREEDY_2"),
        (PlayerType.PC_FIRST_CARD, "FC_3"),
        (PlayerType.PC_RANDOM, "RANDOM_3", dict(play_draw=1)),
    ]

    end_condition = GameEndCondition.ROUND_1000
    game = Game(players=players, interval=0, verbose=False, demo=1000)
    game.run()

