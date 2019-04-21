from .base import Policy, ActionType
from ..card import Card, CardColor, make_standard_unique_deck
import numpy as np
import copy
import random


state_space_dim = 135
unique_cards = make_standard_unique_deck()
action_names = [card.short_name for card in unique_cards] + [None]
action_space_dim = len(action_names)
action_space = list(range(action_space_dim))
action_map = dict(zip(action_space, action_names))  # int -> card/None
action_invmap = dict(zip(action_names, action_space))  # card/None -> int


def rand_max(iterable, key=None):
    """
    A max function that tie breaks randomly instead of first-wins as in
    built-in max().
    :param iterable: The container to take the max from
    :param key: A function to compute tha max from. E.g.:
      >>> rand_max([-2, 1], key=lambda x:x**2
      -2
      If key is None the identity is used.
    :return: The entry of the iterable which has the maximum value. Tie
    breaks are random.
    """
    if key is None:
        key = lambda x: x

    max_v = -np.inf
    max_l = []

    for item, value in zip(iterable, [key(i) for i in iterable]):
        if value == max_v:
            max_l.append(item)
        elif value > max_v:
            max_l = [item]
            max_v = value

    return random.choice(max_l)


# =======================
# For node selection step
# =======================
class UCB1(object):
    """
    Tree policy
    The typical bandit upper confidence bounds algorithm.
    """
    def __init__(self, c):
        self.c = c

    def __call__(self, action_node):
        if self.c == 0:  # assert that no nan values are returned
                        # for action_node.n = 0
            return action_node.q

        return (action_node.q +
                self.c * np.sqrt(2 * np.log(action_node.parent.n) /
                                 action_node.n))


# ===================
# For simulation step
# ===================
def random_terminal_roll_out(state_node):
    """
    Estimate the reward with the sum of a rollout till a terminal state.
    Typical for terminal-only-reward situations such as games with no
    evaluation of the board as reward.

    :param state_node:
    :return:
    """
    def stop_terminal(state):
        return state.is_terminal()

    return _roll_out(state_node, stop_terminal)


def _roll_out(state_node, stopping_criterion):
    reward = 0
    state = state_node
    while not stopping_criterion(state):
        #random
        action = random.choice(state.actions)
        state = state.children[action].sample_state()
    reward += state.get_reward()
    return reward


# ========================
# For backpropagation step
# ========================
def monte_carlo_backpropagate(node):
    """
    A monte carlo update as in classical UCT.

    See feldman amd Domshlak (2014) for reference.
    :param node: The node to start the backup from
    """
    r = node.reward
    while node is not None:
        node.n += 1
        node.q = ((node.n - 1)/node.n) * node.q + 1/node.n * r
        node = node.parent


# =========
# For graph
# =========
class Node(object):
    def __init__(self, parent):
        self.parent = parent
        self.children = {}
        # average score of the node
        self.q = 0
        # number of rounds that the node is visited
        self.n = 0


class ActionNode(Node):
    """
    A node holding an action in the tree.
    """
    def __init__(self, parent, action):
        super(ActionNode, self).__init__(parent)
        self.action = action
        self.n = 0

    def sample_state(self):
        """
        Samples a state from this action and adds it to the tree if the
        state never occurred before.

        :param real_world: If planning in belief states are used, this can
        be set to True if a real world action is taken. The belief is than
        used from the real world action instead from the belief state actions.
        :return: The state node, which was sampled.
        """
        state_node = self.parent.perform(self, self.action)

        if state_node not in self.children:
            self.children[state_node] = state_node

        return self.children[state_node]


class StateNode(Node):
    """
    A node holding a state in the tree.
    """

    def __init__(self, parent, state, game):
        super(StateNode, self).__init__(parent)
        self.state = state
        self.reward = 0
        self.game = game

        sc = game.state_controller
        ep = game.ext_player
        playables = ep.get_playable(sc.current_color, sc.current_value, sc.current_type, sc.current_to_draw)
        if len(playables) > 0:
            self.actions = []
            for action in playables:
                action_idx = game.action_invmap[action[1].short_name]
                self.actions.append(action_idx)
                self.children[action_idx] = ActionNode(self, action_idx)
        else:
            self.actions = [54]
            self.children[54] = ActionNode(self, 54) # None

    def reset(self, game_bak):
        self.game = game_bak

    @property
    def untried_actions(self):
        """
        All actions which have never be performed
        :return: A list of the untried actions.
        """
        return [a for a in self.children if self.children[a].n == 0]

    @untried_actions.setter
    def untried_actions(self, value):
        raise ValueError("Untried actions can not be set.")

    def get_reward(self):
        if self.game.ext_player.num_cards == 0:
            return 1
        else:
            return 0

    def perform(self, parent, action):
        sc = self.game.state_controller
        fc = self.game.flow_controller
        ep = self.game.ext_player
        idx = self.game.action_space.copy()

        # print("fc.current_player: ", fc.current_player)
        # print("fc.is_player_done():", fc.is_player_done())
        # print("self.game.done:", self.game.done)
        # assert not fc.is_player_done()

        done = False
        if fc.current_player == ep:
            action_name = self.game.action_map[action]
            playables = ep.get_playable(sc.current_color, sc.current_value, sc.current_type, sc.current_to_draw)
            play = None

            for i, card in playables:
                card_short_name = card.short_name
                card_id = self.game.action_invmap[card_short_name]

                if card_id in idx:
                    idx.remove(card_id)
                if card_short_name == action_name:
                    play = i, card

            # apply agent's action
            if play is not None:
                self.game.player_play_card(ep, play)
                done = fc.is_player_done()
            else:
                drawn_cards = self.game.apply_penalty(ep)
                done = False

            fc.to_next_player()
            self.game.logger(self.game.horizontal_rule)

        # let other player(s) play
        while not (fc.current_player == ep or done):
            player = fc.current_player
            self.game.logger("Switch to player {}.".format(player))

            play = player.get_play(
                sc.current_color,
                sc.current_value,
                sc.current_type,
                sc.current_to_draw,
                next_player=fc.next_player()
            )
            if play is not None:
                self.game.player_play_card(player, play)
                done = fc.is_player_done()
                # if done:
                #     reward[:] = -100
            else:
                self.game.apply_penalty(player)  # done must remain False in this case
            fc.to_next_player()
            self.game.logger(self.game.horizontal_rule)


        # s_
        s_ = self.game._get_state()
        self.game.done = done
        # action
        # playables = ep.get_playable(sc.current_color, sc.current_value, sc.current_type, sc.current_to_draw)

        return StateNode(parent, s_, self.game)

    def is_terminal(self):
        return self.game.done


def mcts_get_play(playable_cards, **info):
    assert isinstance(playable_cards, list) and len(playable_cards) > 0
    mcts_iter = info.get("mcts_iter", 100)
    tree_policy = info.get("tree_policy")
    default_policy = info.get("default_policy")
    backup = info.get("backup")
    game = info.get("game")
    game_bak = info.get("game_bak")

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
    state[int(info.get("clockwise", None)) + 22] = 1  # #22 - #23

    # player state(dim=110): cards(dim=54) in hand, number of them(dim=1) and valid actions can play(dim=55)
    player = info.get("current_player", None)
    state[24] = info.get("num_cards_left", None)  # #24
    for card in player.cards:  # #25 - #78
        state[action_invmap[card.short_name] + 25] += 1

    if len(playable_cards) == 0:
        state[133] = 1
    else:
        for i, card in playable_cards:
            state[action_invmap[card.short_name] + 79] += 1  # #79 - #132

    # other player state(dim=1): #cards in each other player's hand
    state[134] = info.get("next_player", None).num_cards

    state = np.reshape(state, (1, -1))

    # ===========
    # tree search
    # ===========
    root = StateNode(None, state, game)

    if root.parent is not None:
        raise ValueError("Root's parent must be None.")

    for _ in range(mcts_iter):
        # selection
        node = _get_next_node(root, tree_policy)
        # simulation
        node.reward = default_policy(node)
        # back
        backup(node)

        root.reset(copy.deepcopy(game_bak))

    action_id = rand_max(root.children.values(), key=lambda x: x.q).action

    # ==============
    # postprocessing
    # ==============
    action_name = action_map[action_id]  # action_map
    play = None
    for i, card in playable_cards:
        card_short_name = card.short_name
        if card_short_name == action_name:
            play = i, card

    return play


def _expand(state_node):
    action = random.choice(state_node.untried_actions)
    # action = state_node.untried_actions[0]
    return state_node.children[action].sample_state()


def _best_child(state_node, tree_policy):
    best_action_node = rand_max(state_node.children.values(),
                                      key=tree_policy)
    return best_action_node.sample_state()


def _get_next_node(state_node, tree_policy):
    while not state_node.is_terminal():
        if state_node.untried_actions:
            return _expand(state_node)
        else:
            state_node = _best_child(state_node, tree_policy)
    return state_node


class MCTSGetPlayPolicy(Policy):
    def __init__(self, game, mcts_iter=100, tree_policy=UCB1(c=1.41), default_policy=random_terminal_roll_out,
                              backup=monte_carlo_backpropagate):
        assert mcts_iter >= 0
        super().__init__(name="default", atype=ActionType.GET_PLAY, strategy=mcts_get_play)
        self.mcts_iter = mcts_iter
        self.tree_policy = tree_policy
        self.default_policy = default_policy
        self.backup = backup
        self.game = game
        self.game_bak = copy.deepcopy(self.game)

    def _get_action(self, *args, **kwargs):
        return self.strategy(mcts_iter=self.mcts_iter, tree_policy=self.tree_policy, default_policy=self.default_policy,
                             backup=self.backup, game=self.game, game_bak=self.game_bak, *args, **kwargs)


