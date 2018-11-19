import pandas as pd
import datetime
import sys
import os
import itertools
import math
try:
    from .game_v2 import *
except (ModuleNotFoundError if sys.version_info >= (3, 6) else SystemError) as e:
    from game_v2 import *



opponent_player = (PlayerType.PC_GREEDY, "NPC")


def make_players(total_num, first_pos, info_prob):
    assert isinstance(total_num, int) and 3 <= total_num <= 10
    assert isinstance(first_pos, int) and 0 <= first_pos <= (total_num - 1)
    players = [opponent_player] * total_num

    # since we only care about collusion with probability, we don't set a contrast group
    # actually info_prob = 1 is equivalent to a contrast group
    nc_greedy_get_play = NeighborColludingGetPlay("greedy", info_probability=info_prob)
    nc_greedy_get_color = NeighborColludingGetColor("greedy", info_probability=info_prob)
    colluding_player1 = (PlayerType.POLICY, "NC_GREEDY_1", dict(get_play=nc_greedy_get_play, get_color=nc_greedy_get_color))
    colluding_player2 = (PlayerType.POLICY, "NC_GREEDY_2", dict(get_play=nc_greedy_get_play, get_color=nc_greedy_get_color))

    players[first_pos] = colluding_player1
    players[(first_pos + 1) % total_num] = colluding_player2
    return players


if __name__ == "__main__":
    ts = datetime.datetime.today().strftime('%Y%m%d%H%M%S')  # time string
    out_folder = "local_collusion_result/greedy_probabilistic_collusion"
    os.makedirs(out_folder, exist_ok=True)
    end_condition = GameEndCondition.ROUND_10000

    for num_players in range(3, 11):

        out_file = "ProbNeighborCollusion_10000rounds_{}players_{}.csv".format(num_players, ts)
        out_path = os.path.join(out_folder, out_file)

        cols = list(itertools.chain(*[["p{}_type".format(i), "p{}_collusion_type".format(i),
                                       "p{}_num_wins".format(i), "p{}_cum_reward".format(i)]
                                      for i in range(num_players)])) + ["info_probability"]

        df = pd.DataFrame(columns=cols)  # keep the records

        min_pos = 0
        max_pos = (num_players - 1)
        middle_pos = math.floor((min_pos + max_pos) / 2)
        for pos in [min_pos, middle_pos, max_pos]:
            for info_prob in [x / 100.0 for x in range(0, 101, 10)]:
                print("Testing Case #{}_{}...with info probability {}...".format(num_players, pos, info_prob))
                game = Game(players=make_players(num_players, pos, info_prob), end_condition=end_condition, interval=0, verbose=False)
                game.run()

                # *** After game ***
                row = {}
                for i, player in enumerate(game.players):
                    assert isinstance(player, Player)

                    # update records
                    # player_type | player_params | num_wins | cum_rewards
                    offset = 4 * i
                    row.update({
                        cols[offset]: player.name,
                        cols[offset + 1]: "greedy" if player.is_policy() else "",
                        cols[offset + 2]: player.num_wins,
                        cols[offset + 3]: player.cumulative_reward
                    })
                    row.update({
                        "info_probability": info_prob,
                    })

                df = df.append(row, ignore_index=True)
                # *** END ***

                print()

        df.to_csv(out_path, index=False)
