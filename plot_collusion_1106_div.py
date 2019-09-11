import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import os


input_folder = "local_result"
graph_folder = "local_graphs"
file_template = "NeighborCollusion_10000rounds_{}players_{}.csv"
alpha = .5


def plot_collusion(ts, show=False):
    name = None
    f_wr, ax_wr = plt.subplots(3, 3, figsize=(20, 12))
    f_reward, ax_reward = plt.subplots(3, 3, figsize=(20, 12))

    for n_players in range(3, 11):
        file = file_template.format(n_players, ts)
        path = os.path.join(input_folder, file)
        df = pd.read_csv(path)
        irow = (n_players - 3) // 3
        icol = (n_players - 3) % 3

        ref_row = df.loc[n_players]
        ref_wins = np.array([ref_row['p{}_num_wins'.format(pos)] for pos in range(n_players)]) / 10000
        ref_rewards = np.array([ref_row['p{}_cum_reward'.format(pos)] for pos in range(n_players)]) / 10000

        subplot_wr = ax_wr[irow, icol]
        subplot_wr.plot(ref_wins, label="w/o collusion", color='g')
        subplot_reward = ax_reward[irow, icol]
        subplot_reward.plot(ref_rewards, label="w/o collusion", color='g')

        for i, row in df.iterrows():
            if i == n_players:
                continue
            if name is None:
                name = row["p0_collusion_type"]

            wins = np.array([row['p{}_num_wins'.format(pos)] for pos in range(n_players)]) / 10000
            rewards = np.array([row['p{}_cum_reward'.format(pos)] for pos in range(n_players)]) / 10000
            colluding_pos = [i, (i + 1) % n_players]
            colluding_wins = [wins[pos] for pos in colluding_pos]
            colluding_rewards = [rewards[pos] for pos in colluding_pos]

            if i != n_players - 1:
                non_colluding_pos_p1 = list(range(colluding_pos[0] + 1))
                non_colluding_pos_p2 = list(range(colluding_pos[1], n_players))
                non_colluding_wins_p1 = wins[:colluding_pos[0] + 1]
                non_colluding_wins_p2 = wins[colluding_pos[1]:]
                non_colluding_rewards_p1 = rewards[:colluding_pos[0] + 1]
                non_colluding_rewards_p2 = rewards[colluding_pos[1]:]

                subplot_wr.plot(non_colluding_pos_p1, non_colluding_wins_p1, color='b', alpha=alpha)
                subplot_wr.plot(non_colluding_pos_p2, non_colluding_wins_p2, color='b', alpha=alpha)
                subplot_wr.plot(colluding_pos, colluding_wins, color='r')
                subplot_reward.plot(non_colluding_pos_p1, non_colluding_rewards_p1, color='b', alpha=alpha)
                subplot_reward.plot(non_colluding_pos_p2, non_colluding_rewards_p2, color='b', alpha=alpha)
                subplot_reward.plot(colluding_pos, colluding_rewards, color='r')
            else:
                subplot_wr.plot(wins, color='b', alpha=alpha)
                subplot_reward.plot(rewards, color='b', alpha=alpha)

            subplot_wr.scatter(colluding_pos, colluding_wins, color='r', s=20, zorder=10)
            subplot_reward.scatter(colluding_pos, colluding_rewards, color='r', s=20, zorder=10)

        subplot_wr.axhline(y=1/n_players, color="black", linestyle="--", linewidth=1)
        subplot_wr.xaxis.set_major_locator(MaxNLocator(integer=True))
        subplot_wr.set_title("@ {} Players".format(n_players), fontsize=16)
        subplot_reward.axhline(y=0, color="black", linestyle="--", linewidth=1)
        subplot_reward.xaxis.set_major_locator(MaxNLocator(integer=True))
        subplot_reward.set_title("@ {} Players".format(n_players), fontsize=16)

    f_wr.suptitle("Average Wins", fontsize=20)
    f_wr.tight_layout()
    f_wr.subplots_adjust(top=0.9)
    f_wr.delaxes(ax_wr[2][2])
    f_reward.suptitle("Average Reward", fontsize=20)
    f_reward.tight_layout()
    f_reward.subplots_adjust(top=0.9)
    f_reward.delaxes(ax_reward[2][2])

    f_wr.savefig(os.path.join(graph_folder, "collusion_{}_wr.png".format(name)))
    f_reward.savefig(os.path.join(graph_folder, "collusion_{}_reward.png".format(name)))

    if show:
        plt.show()


if __name__ == "__main__":
    plot_collusion("20181106030413")  # Greedy
    plot_collusion("20181106093945")  # FirstCard
