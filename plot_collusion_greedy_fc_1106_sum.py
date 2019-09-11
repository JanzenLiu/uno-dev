import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import ast
import math
import os

# configs
csv_greedy_filename = "NeighborCollusion_10000rounds_{}players_20181106030413"
csv_fc_filename = "NeighborCollusion_10000rounds_{}players_20181106093945"
min_num_players = 2
max_num_players = 10
round_num = 10000

dir_name = "local_graphs/collusion_greedy_and_first_card"
os.makedirs(dir_name, exist_ok=True)


def calculate_wr_and_reward(settings, setting_columns, first_pos, total_num):
    first_winning_rate = settings[setting_columns[first_pos * 4 + 2]].values[0] / 10000.0
    first_reward = settings[setting_columns[first_pos * 4 + 3]].values[0]
    if first_pos == total_num - 1:
        second_winning_rate = settings[setting_columns[2]].values[0] / 10000.0
        second_reward = settings[setting_columns[3]].values[0]
    else:
        second_winning_rate = settings[setting_columns[first_pos * 4 + 6]].values[0] / 10000.0
        second_reward = settings[setting_columns[first_pos * 4 + 7]].values[0]

    return first_winning_rate, first_reward, second_winning_rate, second_reward


def update_wr_reward_list(settings, columns, current_first_player_pos, current_player_num, sum_wr_list,
                          sum_rewards_list):
    first_winning_rate, first_reward, second_winning_rate, second_reward = calculate_wr_and_reward(settings, columns,
                                                                                                   current_first_player_pos,
                                                                                                   current_player_num)
    sum_wr_list.append(first_winning_rate + second_winning_rate)
    sum_rewards_list.append(first_reward + second_reward)


def draw_csv_subplot(subplot, y_with_greedy_collusion, y_with_fc_collusion, y_without_collusion):
    subplot.plot(range(len(y_with_greedy_collusion)), y_with_greedy_collusion, marker="o", c="r", markersize=3)
    subplot.plot(range(len(y_with_fc_collusion)), y_with_fc_collusion, marker="o", c="g", markersize=3)
    subplot.plot(range(len(y_without_collusion)), y_without_collusion, marker="o", c="b", markersize=3)
    subplot.set_title("@ {} Players".format(len(y_with_greedy_collusion)), fontsize=8)
    subplot.xaxis.set_major_locator(MaxNLocator(integer=True))


def adjust_figure(fig, ax, title, save_fig_name):
    fig.suptitle(title, fontsize=14)
    fig.delaxes(ax[2][2])
    fig.legend(['Greedy Collusion', 'First Card Collusion', 'No Collusion'], bbox_to_anchor=(1, 0.315))
    ax[2][1].set_xlabel('index of the first player in the pair', position=(0.5, 0.5))
    fig.tight_layout()
    fig.subplots_adjust(top=0.87)
    fig.savefig(save_fig_name)


if __name__ == "__main__":
    f_wr, ax_wr = plt.subplots(3, 3)
    f_reward, ax_reward = plt.subplots(3, 3)
    for player_num in range(3, 11):
        df_greedy = pd.read_csv("local_collusion_result/greedy/{}.csv".format(csv_greedy_filename.format(player_num)))
        df_fc = pd.read_csv("local_collusion_result/first_card/{}.csv".format(csv_fc_filename.format(player_num)))
        subplot_row_idx = math.floor((player_num - 3) / 3)
        subplot_col_idx = (player_num - 3) % 3
        subplot_wr = ax_wr[subplot_row_idx, subplot_col_idx]
        subplot_reward = ax_reward[subplot_row_idx, subplot_col_idx]

        sum_winning_rates_with_greedy_collusion = []
        sum_winning_rates_with_fc_collusion = []
        sum_winning_rates_without_collusion = []
        sum_rewards_with_greedy_collusion = []
        sum_rewards_with_fc_collusion = []
        sum_rewards_without_collusion = []

        column_names = df_greedy.columns

        # contrast without collusion
        contrast_setting = df_greedy.loc[[player_num]]

        for first_player_pos in range(player_num):
            # first_player column num in df_greedy: first_player_pos * 4 + first_player_pos * 4 + 3
            # second_player column num in df_greedy: (first_player_pos+1) * 4 + (first_player_pos+1) * 4 + 3 OR 0 - 3
            current_greedy_setting = df_greedy.loc[[first_player_pos]]
            update_wr_reward_list(current_greedy_setting, column_names, first_player_pos, player_num,
                                  sum_winning_rates_with_greedy_collusion, sum_rewards_with_greedy_collusion)

            current_fc_setting = df_fc.loc[[first_player_pos]]
            update_wr_reward_list(current_fc_setting, column_names, first_player_pos, player_num,
                                  sum_winning_rates_with_fc_collusion, sum_rewards_with_fc_collusion)

            update_wr_reward_list(contrast_setting, column_names, first_player_pos, player_num,
                                  sum_winning_rates_without_collusion, sum_rewards_without_collusion)

        draw_csv_subplot(subplot_wr, sum_winning_rates_with_greedy_collusion, sum_winning_rates_with_fc_collusion,
                         sum_winning_rates_without_collusion)
        draw_csv_subplot(subplot_reward, sum_rewards_with_greedy_collusion, sum_rewards_with_fc_collusion,
                         sum_rewards_without_collusion)

    adjust_figure(f_wr, ax_wr, "Collusion Sum Winning Rate",
                  "{}/{}_wr.pdf".format(dir_name, "sum_winning_rate_20181106"))
    adjust_figure(f_reward, ax_reward, "Collusion Sum Cumulative Reward",
                  "{}/{}_reward.pdf".format(dir_name, "sum_reward_20181106"))
