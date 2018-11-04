import pandas as pd
import numpy as np
import keras as ks
import datetime
import pickle
import sys
import re
from sklearn.linear_model import LogisticRegression
from scipy import sparse
try:
    from .game_v2 import *
except (ModuleNotFoundError if sys.version_info >= (3, 6) else SystemError) as e:
    from game_v2 import *


ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
data_cols = [
    'DrawFourCard()',
    'DrawTwoCard(BLUE)', 'DrawTwoCard(GREEN)', 'DrawTwoCard(RED)', 'DrawTwoCard(YELLOW)',
    'NumberCard(BLUE, 0)', 'NumberCard(BLUE, 1)', 'NumberCard(BLUE, 2)', 'NumberCard(BLUE, 3)', 'NumberCard(BLUE, 4)',
    'NumberCard(BLUE, 5)', 'NumberCard(BLUE, 6)', 'NumberCard(BLUE, 7)', 'NumberCard(BLUE, 8)', 'NumberCard(BLUE, 9)',
    'NumberCard(GREEN, 0)', 'NumberCard(GREEN, 1)', 'NumberCard(GREEN, 2)', 'NumberCard(GREEN, 3)', 'NumberCard(GREEN, 4)',
    'NumberCard(GREEN, 5)', 'NumberCard(GREEN, 6)', 'NumberCard(GREEN, 7)', 'NumberCard(GREEN, 8)', 'NumberCard(GREEN, 9)',
    'NumberCard(RED, 0)', 'NumberCard(RED, 1)', 'NumberCard(RED, 2)', 'NumberCard(RED, 3)', 'NumberCard(RED, 4)',
    'NumberCard(RED, 5)', 'NumberCard(RED, 6)', 'NumberCard(RED, 7)', 'NumberCard(RED, 8)', 'NumberCard(RED, 9)',
    'NumberCard(YELLOW, 0)', 'NumberCard(YELLOW, 1)', 'NumberCard(YELLOW, 2)', 'NumberCard(YELLOW, 3)',
    'NumberCard(YELLOW, 4)', 'NumberCard(YELLOW, 5)', 'NumberCard(YELLOW, 6)', 'NumberCard(YELLOW, 7)',
    'NumberCard(YELLOW, 8)', 'NumberCard(YELLOW, 9)',
    'ReverseCard(BLUE)', 'ReverseCard(GREEN)', 'ReverseCard(RED)', 'ReverseCard(YELLOW)',
    'SkipCard(BLUE)', 'SkipCard(GREEN)', 'SkipCard(RED)', 'SkipCard(YELLOW)',
    'WildCard()',
    'color_BLUE', 'color_GREEN', 'color_RED', 'color_YELLOW',
    'to_draw',
    'type_DRAW_2', 'type_DRAW_4', 'type_NUMBER', 'type_REVERSE', 'type_SKIP', 'type_WILDCARD',
    'value_-1', 'value_0', 'value_1', 'value_2', 'value_3', 'value_4',
    'value_5', 'value_6', 'value_7', 'value_8', 'value_9'
]
classes = data_cols[:54]
num_data_cols = len(data_cols)


class LRPolicy(Policy):
    def __init__(self, name, model):
        super().__init__(name)

        with open(model, "rb") as f:
            self.model = pickle.load(f)
        assert isinstance(self.model, LogisticRegression)
        self.name_to_index = {name: i for i, name in enumerate(self.model.classes_)}

    def get_play_from_playable(self, playable_cards, **info):
        # =============
        # preprocessing
        # =============
        row_dict = {}

        play_state = info.get("play_state", None)
        if play_state is not None:
            row_dict["color_{}".format(play_state["color"].name)] = 1
            row_dict["type_{}".format(play_state["type"].name)] = 1
            row_dict["value_{}".format(int(play_state["value"]))] = 1

        for index, playable in playable_cards:
            card_name = ansi_escape.sub('', str(playable))
            row_dict[card_name] = row_dict.get(card_name, 0) + 1

        row_array = np.zeros((num_data_cols,), dtype=np.int64)
        for i, data_col in enumerate(data_cols):
            row_array[i] = row_dict.get(data_col, 0)
        row_array = row_array.reshape((1, -1))

        # ================
        # model prediction
        # ================
        pred = self.model.predict(row_array)[0]
        probs = self.model.predict_proba(row_array)[0]
        best_prob, best_play = 0, playable_cards[0]

        # ==============
        # postprocessing
        # ==============
        for index, playable in playable_cards:
            card_name = ansi_escape.sub('', str(playable))
            if card_name == pred:
                return index, playable

            prob = probs[self.name_to_index[card_name]]
            if prob > best_prob:
                best_prob, best_play = prob, (index, playable)

        print("Prediction not in Playables!")
        return best_play

    def play_new_playable(self, new_playable, **info):
        return GreedyPolicy.play_new_playable(new_playable, **info)

    def get_color(self, **info):
        return GreedyPolicy.get_color(**info)


class KerasPolicy(Policy):
    def __init__(self, name, model):
        super().__init__(name)

        self.model = ks.models.load_model(model)
        assert isinstance(self.model, ks.models.Model)
        self.name_to_index = {name: i for i, name in enumerate(data_cols)}

    def get_play_from_playable(self, playable_cards, **info):
        # =============
        # preprocessing
        # =============
        row_dict = {}

        play_state = info.get("play_state", None)
        if play_state is not None:
            row_dict["color_{}".format(play_state["color"].name)] = 1
            row_dict["type_{}".format(play_state["type"].name)] = 1
            row_dict["value_{}".format(int(play_state["value"]))] = 1

        for index, playable in playable_cards:
            card_name = ansi_escape.sub('', str(playable))
            row_dict[card_name] = row_dict.get(card_name, 0) + 1

        row_array = np.zeros((num_data_cols,), dtype=np.int64)
        for i, data_col in enumerate(data_cols):
            row_array[i] = row_dict.get(data_col, 0)
        row_array = sparse.csr_matrix(row_array)

        # ================
        # model prediction
        # ================
        probs = self.model.predict(row_array)[0]
        pred = classes[np.argmax(probs)]
        best_prob, best_play = 0, playable_cards[0]

        # ==============
        # postprocessing
        # ==============
        for index, playable in playable_cards:
            card_name = ansi_escape.sub('', str(playable))
            if card_name == pred:
                return index, playable

            prob = probs[self.name_to_index[card_name]]
            if prob > best_prob:
                best_prob, best_play = prob, (index, playable)

        print("Prediction not in Playables!")
        return best_play

    def play_new_playable(self, new_playable, **info):
        return GreedyPolicy.play_new_playable(new_playable, **info)

    def get_color(self, **info):
        return GreedyPolicy.get_color(**info)


if __name__ == "__main__":
    # ==============
    # target players
    # ==============
    target_players = [
        (PlayerType.POLICY, "NN[16]_GREEDY", dict(policy=KerasPolicy("nn_policy", "nn[16]_getplay4M.h5"))),
        (PlayerType.POLICY, "LR_GREEDY", dict(policy=LRPolicy("lr_policy", "lr_getplay4M.pkl"))),
    ]
    opponent_player = (PlayerType.PC_GREEDY, "NPC")

    # ===================
    # records preparation
    # ===================
    out_path = "GreedyImitation_10000rounds_{}.csv".format(datetime.datetime.today().strftime('%Y%m%d%H%M%S'))
    cols = ["player_type", "player_params", "num_players", "pos", "num_wins", "cum_reward"]
    df = pd.DataFrame(columns=cols)  # keep the records

    # ===========
    # other setup
    # ===========
    end_condition = GameEndCondition.ROUND_10000

    for target_player_tup in target_players:
        assert isinstance(target_player_tup, tuple)

        for num_players in range(2, 11):

            for pos in range(num_players):
                print("Testing {} ({}@{})...".format(target_player_tup[1], pos, num_players))

                players = [opponent_player]*pos + [target_player_tup] + [opponent_player]*(num_players-1-pos)
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
