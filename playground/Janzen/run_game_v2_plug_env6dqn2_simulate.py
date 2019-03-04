import pandas as pd
import numpy as np
import datetime
import sys
try:
    from .game_v2 import *
except (ModuleNotFoundError if sys.version_info >= (3, 6) else SystemError) as e:
    from game_v2 import *


state_space_dim = 135
unique_cards = make_standard_unique_deck()
action_names = [card.short_name for card in unique_cards] + [None]
action_space_dim = len(action_names)
action_space = list(range(action_space_dim))
action_map = dict(zip(action_space, action_names))  # int -> card/None
action_invmap = dict(zip(action_names, action_space))  # card/None -> int


def dqn_get_play(model, classmap, playable_cards, **info):
    # =============
    # preprocessing
    # =============
    # make model input from the given parameters
    state = np.zeros(state_space_dim)

    # play state(dim=22)
    play_state = info.get("play_state", None)
    state[0] = play_state["to_draw"]  # to draw(dim=1),        #0
    state[play_state["color"].value] = 1  # color(dim=4),      #1 - #4
    state[play_state["value"] + 6] = 1  # value(dim=11),       #5 - #15
    state[play_state["type"].value + 16] = 1  # type(dim=6),   #16 - #21

    # flow state(dim=2): clockwise(dim=2)
    # state[int(info.get("clockwise", None)) + 22] = 1  # #22 - #23
    clockwise = info.get("clockwise", None)
    if clockwise is not None:
        state[int(clockwise) + 22] = 1

    # player state(dim=110): cards(dim=54) in hand, number of them(dim=1) and valid actions can play(dim=55)
    player = info.get("current_player", None)
    state[24] = info.get("num_cards_left", None)  # #24
    for card in player.cards:                     # #25 - #78
        state[action_invmap[card.short_name] + 25] += 1

    if len(playable_cards) == 0:
        state[133] = 1
    else:
        for i, card in playable_cards:
            state[action_invmap[card.short_name] + 79] += 1  # #79 - #132

    # other player state(dim=1): #cards in each other player's hand
    state[134] = info.get("next_player", None).num_cards

    state = np.reshape(state, (1, -1))

    # ================
    # model prediction
    # ================
    q_value = model.predict(state)
    action_id = np.argmax(q_value[0])

    # ==============
    # postprocessing
    # ==============
    action_name = classmap[action_id]  # action_map
    play = None
    for i, card in playable_cards:
        card_short_name = card.short_name
        if card_short_name == action_name:
            play = i, card

    return play


if __name__ == "__main__":
    # =======
    # players
    # =======
    target_player_tup = (
        PlayerType.POLICY,
        "ENV6_DQN2",
        dict(get_play=KerasPolicy(name="dqn_policy", atype="get_play",
                                  model="env-v6-dqn-002-local.h5",
                                  strategy=dqn_get_play, classmap=action_map))
    )
    opponent_player = (PlayerType.PC_RANDOM, "NPC", dict(play_draw=0))

    # ===================
    # records preparation
    # ===================
    out_path = "local_result/Env6Dqn2_10000rounds_{}.csv".format(datetime.datetime.today().strftime('%Y%m%d%H%M%S'))
    cols = ["player_type", "player_params", "num_players", "pos", "num_wins", "cum_reward"]
    df = pd.DataFrame(columns=cols)  # keep the records

    # ===========
    # other setup
    # ===========
    end_condition = GameEndCondition.ROUND_10000

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
