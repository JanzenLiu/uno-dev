import pandas as pd
import datetime
import sys
try:
    from .game_v2 import *
except (ModuleNotFoundError if sys.version_info >= (3, 6) else SystemError) as e:
    from game_v2 import *


if __name__ == "__main__":
    # ==============
    # target players
    # ==============
    nc_greedy_get_play = NeighborColludingGetPlay("greedy")
    nc_greedy_get_color = NeighborColludingGetColor("greedy")
    colluding_players = [
        (PlayerType.POLICY, "NC_GREEDY_1", dict(get_play=nc_greedy_get_play, get_color=nc_greedy_get_color)),
        (PlayerType.POLICY, "NC_GREEDY_2", dict(get_play=nc_greedy_get_play, get_color=nc_greedy_get_color)),
    ]
    opponent_player = (PlayerType.PC_GREEDY, "NPC")

    # ===========
    # other setup
    # ===========
    end_condition = GameEndCondition.ROUND_10000

    num_players = 3
    for pos in range(num_players):
        print("Testing Case #{}...".format(pos))

        players = colluding_players.copy()
        players.insert(pos, opponent_player)
        game = Game(players=players, end_condition=end_condition, interval=0, verbose=False)
        game.run()
