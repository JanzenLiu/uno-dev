import pandas as pd
import datetime
import sys
try:
    from .game_v2 import *
except (ModuleNotFoundError if sys.version_info >= (3, 6) else SystemError) as e:
    from game_v2 import *


if __name__ == "__main__":
    # ===================
    # records preparation
    # ===================
    out_path = "simulation_2players_{}.csv".format(datetime.datetime.today().strftime('%Y%m%d%H%M%S'))
    cols = ["player_type", "player_params", "num_rounds", "num_wins", "cum_reward"]
    df = pd.DataFrame(columns=cols)  # keep the records

    # =======
    # players
    # =======
    opponents = [(PlayerType.PC_GREEDY, "NPC")]
    target_players = [
        (PlayerType.PC_FIRST_CARD, "PC_FIRSTCARD_1"),
        (PlayerType.PC_RANDOM, "PC_RANDOM_1", dict(play_draw=1)),
        (PlayerType.PC_RANDOM, "PC_RANDOM_2", dict(play_draw=.5)),
        (PlayerType.PC_RANDOM, "PC_RANDOM_3", dict(play_draw=0)),
        (PlayerType.PC_GREEDY, "PC_GREEDY_1")
    ]

    for target_player_tup in target_players:
        assert isinstance(target_player_tup, tuple)
        print("Testing {}...".format(target_player_tup[1]))
        players = [target_player_tup] + opponents
        end_condition = GameEndCondition.ROUND_10000
        game = Game(players=players, end_condition=end_condition, interval=0, verbose=False)
        game.run()
        print()

        target_player = game.players[0]
        assert isinstance(target_player, Player)
        assert target_player.name == target_player_tup[1]

        # update records
        # player_type | player_params | num_rounds | num_wins | win_rate | cum_rewards
        row = {
            cols[0]: target_player_tup[0].name,
            cols[1]: target_player_tup[2] if len(target_player_tup) == 3 else "",
            cols[2]: target_player.num_rounds,
            cols[3]: target_player.num_wins,
            cols[4]: target_player.cumulative_reward
        }
        df = df.append(row, ignore_index=True)

    df.to_csv(out_path, index=False)
