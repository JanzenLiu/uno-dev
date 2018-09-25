import sys
try:
    from .game_v2 import Game, GameEndCondition, PlayerType, Player
except (ModuleNotFoundError if sys.version_info >= (3, 6) else SystemError) as e:
    from game_v2 import Game, GameEndCondition, PlayerType, Player


if __name__ == "__main__":
    players = [
        (PlayerType.PC_FIRST_CARD, "PC_FIRSTCARD_1"),
        (PlayerType.PC_RANDOM, "PC_RANDOM_1", dict(play_draw=1)),
        (PlayerType.PC_RANDOM, "PC_RANDOM_2", dict(play_draw=.5)),
        (PlayerType.PC_RANDOM, "PC_RANDOM_3", dict(play_draw=0)),
        (PlayerType.PC_GREEDY, "PC_GREEDY_1")
    ]
    end_condition = GameEndCondition.ROUND_1000

    game = Game(players=players, end_condition=end_condition, interval=0)
    game.run()
