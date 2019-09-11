import pandas as pd
import numpy as np
import keras as ks
import datetime
import pickle
import sys
from sklearn.linear_model import LogisticRegression
try:
    from .game_v2 import *
except (ModuleNotFoundError if sys.version_info >= (3, 6) else SystemError) as e:
    from game_v2 import *


shared_keys = ['color', 'to_draw', 'type', 'value', 'card_color', 'card_type', 'card_score']


def append_state_to_dict(state, data_dict):
    data_dict['color'].append(state['color'].value)
    data_dict['type'].append(state['type'].value)
    data_dict['to_draw'].append(state['to_draw'])
    data_dict['value'].append(state['value'])


def append_card_info_to_dict(available_card, data_dict):
    data_dict['card_color'].append(available_card.color.value)
    data_dict['card_type'].append(available_card.card_type.value)
    data_dict['card_score'].append(available_card.score)


def standardize_df(raw_df):
    possibilities = ["color_{}".format(index) for index in range(1, 5)] + \
                    ["card_color_{}".format(index) for index in range(5)] + \
                    ["card_type_{}".format(index) for index in range(6)] + \
                    ["type_{}".format(index) for index in range(6)] + ['card_score', 'to_draw', "value"]
    differences = [key for key in possibilities if key not in raw_df.columns]
    for key in differences:
        raw_df.insert(0, key, int(0))
    assert len([key for key in possibilities if key not in raw_df.columns]) == 0
    return raw_df


def transform_data_matrix(raw_df):
    raw_df = pd.get_dummies(raw_df, columns=['color', 'card_color', 'card_type', 'type'])
    raw_df = standardize_df(raw_df)
    assert len(raw_df.columns) == 24
    raw_df.sort_index(axis=1, inplace=True)

    # convert to matrix
    data = raw_df.values
    return data


def prepare_model_data(play_state, possible_cards):
    data_dict = {key: [] for key in shared_keys}
    for (_, playable_card) in possible_cards:
        append_state_to_dict(play_state, data_dict)
        append_card_info_to_dict(playable_card, data_dict)

    data_df = pd.DataFrame.from_dict(data_dict)
    return transform_data_matrix(data_df)


class LRPolicy(Policy):
    def __init__(self, name, model):
        super().__init__(name)

        with open(model, "rb") as f:
            self.model = pickle.load(f)
        assert isinstance(self.model, LogisticRegression)

    def get_play_from_playable(self, playable_cards, **info):
        # =============
        # preprocessing
        # =============
        current_state = info.get("play_state", None)
        transformed_data = prepare_model_data(current_state, playable_cards)

        # ================
        # model prediction
        # ================
        best_index = np.argmax(self.model.predict_proba(transformed_data)[:,1])
        return playable_cards[best_index]

    def play_new_playable(self, new_playable, **info):
        return GreedyPolicy.play_new_playable(new_playable, **info)

    def get_color(self, **info):
        return GreedyPolicy.get_color(**info)


class KerasPolicy(Policy):
    def __init__(self, name, model):
        super().__init__(name)

        self.model = ks.models.load_model(model)
        assert isinstance(self.model, ks.models.Model)

    def get_play_from_playable(self, playable_cards, **info):
        # =============
        # preprocessing
        # =============
        current_state = info.get("play_state", None)
        transformed_data = prepare_model_data(current_state, playable_cards)

        # ================
        # model prediction
        # ================
        best_index = np.argmax(self.model.predict(x=np.array(transformed_data))[:,1])
        return playable_cards[best_index]

    def play_new_playable(self, new_playable, **info):
        return GreedyPolicy.play_new_playable(new_playable, **info)

    def get_color(self, **info):
        return GreedyPolicy.get_color(**info)


if __name__ == "__main__":
    # ==============
    # target players
    # ==============
    target_players = [
        (PlayerType.POLICY, "NN[16]_GREEDY", dict(policy=KerasPolicy("nn_policy", "nn[16]_getplay4M_1c1r.h5"))),
        (PlayerType.POLICY, "LR_GREEDY", dict(policy=LRPolicy("lr_policy", "lr_getplay4M_1c1r.pkl"))),
    ]
    opponent_player = (PlayerType.PC_GREEDY, "NPC")

    # ===================
    # records preparation
    # ===================
    out_path = "local_imitation/GreedyImitation_1000rounds_{}_1c1r.csv".format(datetime.datetime.today().strftime('%Y%m%d%H%M%S'))
    cols = ["player_type", "player_params", "num_players", "pos", "num_wins", "cum_reward"]
    df = pd.DataFrame(columns=cols)  # keep the records

    # ===========
    # other setup
    # ===========
    end_condition = GameEndCondition.ROUND_1000

    for target_player_tup in target_players:
        assert isinstance(target_player_tup, tuple)

        for num_players in range(2, 11):

            for pos in range(num_players):
                print("Testing {} ({}@{})...".format(target_player_tup[1], pos, num_players))

                players = [opponent_player] * pos + [target_player_tup] + [opponent_player] * (num_players - 1 - pos)
                game = Game(players=players, end_condition=end_condition, interval=0, verbose=False)
                game.run()

                # *** After game ***
                target_player = game.players[pos]
                assert isinstance(target_player, Player)
                assert target_player.name == target_player_tup[1]

                # update records
                # player_type | player_params | num_players | pos | num_wins | cum_rewards
                row = {
                    cols[0]: target_player_tup[0].name,
                    cols[1]: target_player_tup[2] if len(target_player_tup) == 3 else "",
                    cols[2]: num_players,
                    cols[3]: pos,
                    cols[4]: target_player.num_wins,
                    cols[5]: target_player.cumulative_reward
                }
                df = df.append(row, ignore_index=True)
                # *** END ***

                print()

    df.to_csv(out_path, index=False)
