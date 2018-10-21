import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import ast
import math
import os

# configs
csv_filename = "simulation_10000rounds_20181009143318"
dir_name = "local_graphs"
player_type_num = 5  # range(1, 6)
min_num_players = 2
max_num_players = 10
round_num = 10000


def draw_csv_subplot(subplot, y):
    subplot.plot(range(len(y)), y, marker="o", markersize=3)
    subplot.set_title("@ {} Players".format(len(y)), fontsize=8)
    subplot.xaxis.set_major_locator(MaxNLocator(integer=True))


if __name__ == "__main__":
    df = pd.read_csv("{}.csv".format(csv_filename))
    row_num_per_type = sum(range(min_num_players, max_num_players + 1))

    os.makedirs(dir_name, exist_ok=True)
    for player_type_idx in range(player_type_num):
        f_wr, ax_wr = plt.subplots(3, 3)
        f_reward, ax_reward = plt.subplots(3, 3)
        threshold = int(player_type_idx * row_num_per_type)
        player_df = df[threshold:threshold+row_num_per_type]
        player_type = player_df["player_type"].unique()[0]
        player_params = player_df["player_params"].unique()[0]
        output_type = "{}{}".format(player_type,
                                    "" if not isinstance(player_params, str)
                                    else "_{}".format(ast.literal_eval(player_params)["play_draw"]))

        for num_player in range(min_num_players, max_num_players + 1):
            start = sum(range(min_num_players, num_player))
            player_num_df = player_df[start:start+num_player]
            winning_rates = player_num_df["num_wins"] / round_num
            rewards = player_num_df["cum_reward"]

            subplot_row_idx = math.floor((num_player - 2) / 3)
            subplot_col_idx = (num_player - 2) % 3
            subplot_wr = ax_wr[subplot_row_idx, subplot_col_idx]
            subplot_reward = ax_reward[subplot_row_idx, subplot_col_idx]

            # reward and winning rate subplot common part
            draw_csv_subplot(subplot_wr, winning_rates)
            draw_csv_subplot(subplot_reward, rewards)

            # reward and winning rate subplot customized part
            subplot_wr.axhline(y=(1/len(winning_rates)), color="black", linestyle="--", linewidth=1)

        f_wr.suptitle("{} Winning Rate".format(output_type), fontsize=14)
        f_wr.tight_layout()
        f_wr.subplots_adjust(top=0.9)

        f_reward.suptitle("{} Cumulative Reward".format(output_type), fontsize=14)
        f_reward.tight_layout()
        f_reward.subplots_adjust(top=0.9)

        f_wr.savefig("{}/{}_{}_wr.png".format(dir_name, csv_filename, output_type))
        f_reward.savefig("{}/{}_{}_reward.png".format(dir_name, csv_filename, output_type))
