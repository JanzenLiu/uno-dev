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
    target_players = [
        (PlayerType.PC_GREEDY, "PC_GREEDY_1")
    ]
    opponent_player = (PlayerType.PC_RANDOM, "NPC", dict(play_draw=0))

    # ===================
    # records preparation
    # ===================
    final_csv_name = "greedy_playables_10000rounds_{}".format(datetime.datetime.today().strftime('%Y%m%d%H%M%S'))
    out_path = "local_result/{}.pkl".format(final_csv_name)
    # cols = ["player_type", "player_params", "num_players", "pos", "num_wins", "cum_reward"]
    # df = pd.DataFrame(columns=cols)  # keep the records
    playables_cols = ["play_state", "clockwise", "current_player", "num_cards_left", "next_player", "playable_cards", "chosen"]
    playables_df = pd.DataFrame(columns=playables_cols)

    # ===========
    # other setup
    # ===========
    end_condition = GameEndCondition.ROUND_10000
    min_num_players = 2
    max_num_players = 2
    num_backup_step = 3
    num_backup_points = range(min_num_players + num_backup_step - 1, max_num_players + 1, num_backup_step)

    for target_player_tup in target_players:
        assert isinstance(target_player_tup, tuple)

        for num_players in range(min_num_players, max_num_players + 1):

            for pos in range(num_players):
                print("Testing {} ({}@{})...".format(target_player_tup[1], pos, num_players))

                players = [opponent_player]*pos + [target_player_tup] + [opponent_player]*(num_players-1-pos)
                game = Game(players=players, end_condition=end_condition, interval=0, verbose=False, playables_df=playables_df,
                            playables_cols=["playable_cards", "chosen"])
                game.run()

                # *** After game ***
                target_player = game.players[pos]
                assert isinstance(target_player, Player)
                assert target_player.name == target_player_tup[1]

                # update records
                # player_type | player_params | num_players | pos | num_wins | cum_rewards
                # row = {
                #     cols[0]: target_player_tup[0].name,
                #     cols[1]: target_player_tup[2] if len(target_player_tup) == 3 else "",
                #     cols[2]: num_players,
                #     cols[3]: pos,
                #     cols[4]: target_player.num_wins,
                #     cols[5]: target_player.cumulative_reward
                # }
                # df = df.append(row, ignore_index=True)
                # *** END ***

                print()
            # backup current df
            # TODO: backup the whole df or just the part that has not been backuped yet?
            if num_players in num_backup_points:
                # out_path = "local_result/{}.pkl".format(final_csv_name)
                backup_path = "local_result/{}_up_to_{}.pkl".format(final_csv_name, num_players)
                playables_df.to_pickle(backup_path)

            #     df.to_csv(backup_path, index=False)

    # playables_df.to_csv(out_path, index=False)
    # df.to_csv(out_path, index=False)
    playables_df.to_pickle(out_path)
