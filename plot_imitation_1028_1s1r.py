import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from matplotlib.ticker import MaxNLocator


input_folder = "local_result"
graph_folder = "local_graphs"
num_rounds = 10000  # rounds per configuration


if __name__ == "__main__":
    df_pc = pd.read_csv(os.path.join(input_folder, "simulation_10000rounds_20181009143318.csv"))
    df_imit = pd.read_csv(os.path.join(input_folder, "GreedyImitation_10000rounds_20181028002208.csv"))

    df_greedy = df_pc.iloc[-54:].reset_index(drop=True)
    df_nn = df_imit.iloc[:54].reset_index(drop=True)
    df_lr = df_imit.iloc[54:].reset_index(drop=True)

    f_wr, ax_wr = plt.subplots(3, 3, figsize=(20, 12))
    f_reward, ax_reward = plt.subplots(3, 3, figsize=(20, 12))

    start = 0
    for num_players in range(2, 11):
        end = start + num_players
        subdf_greedy = df_greedy.iloc[start:end]
        subdf_nn = df_nn.iloc[start:end]
        subdf_lr = df_lr.iloc[start:end]

        positions = np.arange(0, num_players)
        rewards_greedy = subdf_greedy['cum_reward'].values
        rewards_nn = subdf_nn['cum_reward'].values
        rewards_lr = subdf_lr['cum_reward'].values
        wins_greedy = subdf_greedy['num_wins'].values
        wins_nn = subdf_nn['num_wins'].values
        wins_lr = subdf_lr['num_wins'].values

        rewards_greedy = rewards_greedy / num_rounds
        rewards_nn = rewards_nn / num_rounds
        rewards_lr = rewards_lr / num_rounds
        wins_greedy = wins_greedy / num_rounds
        wins_nn = wins_nn / num_rounds
        wins_lr = wins_lr / num_rounds

        irow = (num_players - 2) // 3
        icol = (num_players - 2) % 3

        subplot_wr = ax_wr[irow, icol]
        subplot_wr.plot(positions, wins_greedy, marker='o', label="Greedy")
        subplot_wr.plot(positions, wins_nn, marker='o', label="NN[16]")
        subplot_wr.plot(positions, wins_lr, marker='o', label="LR")
        subplot_wr.set_title("@ {} Players".format(num_players), fontsize=16)
        subplot_wr.xaxis.set_major_locator(MaxNLocator(integer=True))
        subplot_wr.legend(fontsize=14)
        subplot_wr.axhline(y=(1/num_players), color="black", linestyle="--", linewidth=1)
        f_wr.suptitle("Winning Rate", fontsize=20)
        f_wr.tight_layout()
        f_wr.subplots_adjust(top=0.9)

        subplot_reward = ax_reward[irow, icol]
        subplot_reward.plot(positions, rewards_greedy, marker='o', label="Greedy")
        subplot_reward.plot(positions, rewards_nn, marker='o', label="NN[16]")
        subplot_reward.plot(positions, rewards_lr, marker='o', label="LR")
        subplot_reward.set_title("@ {} Players".format(num_players), fontsize=16)
        subplot_reward.xaxis.set_major_locator(MaxNLocator(integer=True))
        subplot_reward.legend(fontsize=14)
        subplot_reward.axhline(y=0, color="black", linestyle="--", linewidth=1)
        f_reward.suptitle("Average Reward", fontsize=20)
        f_reward.tight_layout()
        f_reward.subplots_adjust(top=0.9)

        start = end

    f_wr.savefig(os.path.join(graph_folder, "imitation_wr.png"))
    f_reward.savefig(os.path.join(graph_folder, "imitation_reward.png"))
