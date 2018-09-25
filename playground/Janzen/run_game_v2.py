try:
    from .game_v2 import Game, GameEndCondition, PlayerType
except SystemError:
    from game_v2 import Game, GameEndCondition, PlayerType


if __name__ == "__main__":
    players = [(PlayerType.HUMAN, "Janzen"), (PlayerType.PC_NAIVE, "PC1")]
    end_condition = GameEndCondition.ROUND_1

    game = Game(players=players, end_condition=end_condition, interval=2)
    game.run()
