"""
This script is used to collect data for "imitating" a GreedyPlayer
"""


import datetime
import pickle
import sys
try:
    from .game_v2 import *
except (ModuleNotFoundError if sys.version_info >= (3, 6) else SystemError) as e:
    from game_v2 import *


def save_pickle(obj, path):
    with open(path, "wb") as f:
        pickle.dump(obj, f)


if __name__ == "__main__":
    # records preparation
    iden = datetime.datetime.today().strftime('%Y%m%d%H%M%S')
    get_play_path = "actions_get_play_{}.pkl".format(iden)
    get_color_path = "actions_get_color_{}.pkl".format(iden)
    play_new_path = "actions_play_new_{}.pkl".format(iden)
    get_play_actions = []
    get_color_actions = []
    play_new_actions = []

    # game configuration
    end_condition = GameEndCondition.ROUND_1000
    num_players = 10

    # target players
    players = [(PlayerType.PC_GREEDY, "PC_GREEDY_{}".format(i), dict(save_actions=True)) for i in range(num_players)]

    # game
    game = Game(players=players, end_condition=end_condition, interval=0, verbose=False)
    game.run()

    # *** After game ***
    print("classifying actions...")
    for pos in range(num_players):
        player = game.players[pos]
        assert isinstance(player, Player)
        assert player.name == "PC_GREEDY_{}".format(pos)
        for round_actions in player.actions:
            for action in round_actions:
                x = action[2]
                if isinstance(x, bool):
                    play_new_actions.append(action)
                elif isinstance(x, int):
                    get_play_actions.append(action)
                elif isinstance(x, CardColor):
                    get_color_actions.append(action)
                else:
                    # raise Exception("Unknown action saved: {}".format(action))
                    pass

    print("saving actions")
    save_pickle(get_play_actions, get_play_path)
    save_pickle(get_color_actions, get_color_path)
    save_pickle(play_new_actions, play_new_path)

    # *** END ***
