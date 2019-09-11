import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import math
import os
import numpy as np
from scipy.interpolate import spline

# configs
csv_greedy_filename = "ProbNeighborCollusion_10000rounds_{}players_20181120005240"
round_num = 10000
dir_name = "test/local_graphs/probabilistic_collusion"
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


def draw_csv_subplot(subplot, y_min, y_middle, y_max, num_players):
    x = list(range(0, 101, 10))

    subplot.plot(x, y_min, marker="o", c="r", markersize=5, lw=2)
    subplot.plot(x, y_middle, marker="x", c="g", markersize=5, lw=2)
    subplot.plot(x, y_max, marker="*", c="b", markersize=5, lw=2)

    #     x_smooth = np.linspace(min(x), max(x), 200)
    #     y_min_smooth = spline(x, y_min, x_smooth)
    #     y_mid_smooth = spline(x, y_middle, x_smooth)
    #     y_max_smooth = spline(x, y_max, x_smooth)

    #     subplot.plot(x_smooth, y_min_smooth, marker="o", c="r", markersize=5, markevery=10)
    #     subplot.plot(x_smooth, y_mid_smooth, marker="x", c="g", markersize=5, markevery=10)
    #     subplot.plot(x_smooth, y_max_smooth, marker="*", c="b", markersize=5, markevery=10)

    subplot.set_title("@ {} Players".format(num_players), fontsize=12)


def adjust_figure(fig, ax, title, save_fig_name):
    fig.suptitle(title, fontsize=20)
    fig.delaxes(ax[2][2])
    fig.legend(['min (0)', 'middle', 'max'], bbox_to_anchor=(0.89, 0.3),
               title='index of the 1st player in pair', fontsize=12)
    ax[2][1].set_xlabel('knowledge percentage available in collusion (%)', position=(0.5, 0.5))
    fig.tight_layout()
    fig.set_size_inches(12, 9)
    fig.subplots_adjust(top=0.9)
    fig.savefig(save_fig_name)


f_wr, ax_wr = plt.subplots(3, 3, figsize=(12, 9))
f_reward, ax_reward = plt.subplots(3, 3, figsize=(12, 9))
for player_num in range(3, 11):
    df_greedy = pd.read_csv(
        "local_collusion_result/greedy_probabilistic_collusion/{}.csv".format(csv_greedy_filename.format(player_num)))
    subplot_row_idx = math.floor((player_num - 3) / 3)
    subplot_col_idx = (player_num - 3) % 3
    subplot_wr = ax_wr[subplot_row_idx, subplot_col_idx]
    subplot_reward = ax_reward[subplot_row_idx, subplot_col_idx]

    sum_winning_rates_min_pos = []
    sum_winning_rates_middle_pos = []
    sum_winning_rates_max_pos = []
    sum_rewards_min_pos = []
    sum_rewards_middle_pos = []
    sum_rewards_max_pos = []

    column_names = df_greedy.columns

    min_pos = 0
    max_pos = (player_num - 1)
    middle_pos = math.floor((min_pos + max_pos) / 2)
    for first_player_pos_base, first_player_pos in enumerate([min_pos, middle_pos,
                                                              max_pos]):  # every player_num has three different player pos settings: min, middle, max
        for prob_row_offset in range(11):
            current_greedy_setting = df_greedy.loc[[first_player_pos_base * 11 + prob_row_offset]]

            if first_player_pos_base == 0:  # min
                update_wr_reward_list(current_greedy_setting, column_names, first_player_pos, player_num,
                                      sum_winning_rates_min_pos, sum_rewards_min_pos)
            elif first_player_pos_base == 1:  # middle
                update_wr_reward_list(current_greedy_setting, column_names, first_player_pos, player_num,
                                      sum_winning_rates_middle_pos, sum_rewards_middle_pos)
            else:  # max
                update_wr_reward_list(current_greedy_setting, column_names, first_player_pos, player_num,
                                      sum_winning_rates_max_pos, sum_rewards_max_pos)

    draw_csv_subplot(subplot_wr, sum_winning_rates_min_pos, sum_winning_rates_middle_pos,
                     sum_winning_rates_max_pos, player_num)
    draw_csv_subplot(subplot_reward, sum_rewards_min_pos, sum_rewards_middle_pos,
                     sum_rewards_max_pos, player_num)

adjust_figure(f_wr, ax_wr, "Probabilistic Neighbor Collusion Sum Winning Rate",
              "{}/{}_wr_11points.pdf".format(dir_name, "sum_winning_rate_20181120"))
adjust_figure(f_reward, ax_reward, "Probabilistic Neighbor Collusion Sum Cumulative Reward",
              "{}/{}_reward_11points.pdf".format(dir_name, "sum_reward_20181120"))