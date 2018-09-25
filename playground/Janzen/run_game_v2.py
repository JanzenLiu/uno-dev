import sys
try:
    from .game_v2 import Game, GameEndCondition, PlayerType
except (ModuleNotFoundError if sys.version_info >= (3, 6) else SystemError) as e:
    from game_v2 import Game, GameEndCondition, PlayerType


if __name__ == "__main__":
    game = Game(interval=2)
    game.run()
