import pandas as pd
import datetime
import sys
import os
import itertools
try:
    from .game_v2 import *
except (ModuleNotFoundError if sys.version_info >= (3, 6) else SystemError) as e:
    from game_v2 import *


nc_greedy_get_play = NeighborColludingGetPlay("greedy")
nc_greedy_get_color = NeighborColludingGetColor("greedy")
opponent_player = (PlayerType.PC_GREEDY, "NPC")
colluding_player1 = (PlayerType.POLICY, "NC_GREEDY_1", dict(get_play=nc_greedy_get_play, get_color=nc_greedy_get_color))
colluding_player2 = (PlayerType.POLICY, "NC_GREEDY_2", dict(get_play=nc_greedy_get_play, get_color=nc_greedy_get_color))


def make_players(n, p):
    assert isinstance(n, int) and 2 <= n <= 10
    assert isinstance(p, int) and 0 <= p <= n
    players = [opponent_player] * n

    # if p == n, all players are not colluding, and such a group is set for contrast
    if p != n:
        players[p] = colluding_player1
        players[(p + 1) % n] = colluding_player2
    return players


if __name__ == "__main__":
    ts = datetime.datetime.today().strftime('%Y%m%d%H%M%S')  # time string
    out_folder = "local_result"
    os.makedirs(out_folder, exist_ok=True)
    end_condition = GameEndCondition.ROUND_10000

    for num_players in range(3, 11):

        out_file = "NeighborCollusion_10000rounds_{}players_{}.csv".format(num_players, ts)
        out_path = os.path.join(out_folder, out_file)

        cols = list(itertools.chain(*[["p{}_type".format(i), "p{}_collusion_type".format(i),
                                       "p{}_num_wins".format(i), "p{}_cum_reward".format(i)]
                                      for i in range(num_players)]))
        df = pd.DataFrame(columns=cols)  # keep the records

        for pos in range(num_players + 1):
            print("Testing Case #{}_{}...".format(num_players, pos))
            game = Game(players=make_players(num_players, pos), end_condition=end_condition, interval=0, verbose=False)
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

            df = df.append(row, ignore_index=True)
            # *** END ***

            print()

        df.to_csv(out_path, index=False)
