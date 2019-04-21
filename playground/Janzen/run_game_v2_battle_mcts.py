from __future__ import division
import random
import logging
import argparse
import numpy as np
import pickle
import sys
import time
from collections import defaultdict, OrderedDict
try:
    from .game_v2 import *
except (ModuleNotFoundError if sys.version_info >= (3, 6) else SystemError) as e:
    from game_v2 import *
import copy


# ===================
# For general purpose
# ===================
def save_pickle(obj, path):
    with open(path, "wb") as f:
        pickle.dump(obj, f)


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


# =========
# For agent
# =========
class MCTSAgent(object):
    """
    The central MCTS class, which performs the tree search. It gets a
    tree policy, a default policy, and a backup strategy.
    See e.g. Browne et al. (2012) for a survey on monte carlo tree search
    """

    def __init__(self, tree_policy, default_policy, backup, game):
        self.tree_policy = tree_policy
        self.default_policy = default_policy
        self.backup = backup
        self.game = game
        self.game_bak = copy.deepcopy(self.game)

    def get_action(self, s, n=1000):
        """
        Run the monte carlo tree search.

        :param root: The StateNode
        :param n: The number of roll-outs to be performed
        :return: best action
        """

        root = StateNode(None, s, self.game)

        if root.parent is not None:
            raise ValueError("Root's parent must be None.")

        for _ in range(n):
            # print("get_action loop")
            # selection
            node = _get_next_node(root, self.tree_policy)
            # print("after _get_next_node")
            # simulation
            node.reward = self.default_policy(node)
            # print("after simulation")
            # back
            self.backup(node)
            # print("after backpropagation")

            root.reset(copy.deepcopy(self.game_bak))

        return rand_max(root.children.values(), key=lambda x: x.q).action


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


if __name__ == "__main__":
    # parse arguments
    # example: `python3 run_game_v2_battle_dqn_local.py -n 64 64 -i 5`
    parser = argparse.ArgumentParser()
    # parser.add_argument('--epsilon', type=float, default=1.0)
    # parser.add_argument('--epsilon_min', type=float, default=0.005)
    # parser.add_argument('--epsilon_steps', type=int, default=5000)
    parser.add_argument('--log_id', '-i', type=int, required=True)
    parser.add_argument('--episodes', type=int, default=1000)
    parser.add_argument('--state', type=str, default="1d_1")
    parser.add_argument('--reward', type=str, default="score_1")
    parser.add_argument('--mcts_iter', '-n', type=int, default=1000)
    args = parser.parse_args()
    kwargs = OrderedDict(sorted(args._get_kwargs(), key=lambda x: x[0]))

    episodes = kwargs.pop('episodes')

    # initialize logger
    log_id = kwargs.pop('log_id')
    mcts_iter = kwargs.get('mcts_iter')
    assert log_id < 1000
    filename = 'battle-mcts-{:0>3}-local.log'.format(log_id)
    logger = logging.Logger("MCTSLogger")
    sh = logging.StreamHandler()
    fh = logging.FileHandler(filename)
    logger.addHandler(sh)
    logger.addHandler(fh)

    # model_path_wr = 'battle-mcts-{:0>3}-best-wr-local.pkl'.format(log_id)
    # model_path_ar = 'battle-mcts-{:0>3}-best-ar-local.pkl'.format(log_id)

    # log hyper-parameters
    logger.info('opponent=greedy')
    for k, v, in kwargs.items():
        logger.info('{}={}'.format(k, v))

    # initialize agent
    state_version = kwargs.pop("state")
    reward_version = kwargs.pop("reward")
    env = BattleEnv(state_version=state_version, reward_version=reward_version)
    state_size = env.state_space_dim
    action_size = env.action_space_dim

    state, done = env.start_round()

    wins = []
    rewards = []
    max_window_wr = -sys.maxsize - 1
    max_window_ar = -sys.maxsize - 1

    for i in range(episodes):
        begin = time.time()
        reward = 0

        while not done:
            game_copy = copy.deepcopy(env)
            agent = MCTSAgent(tree_policy=UCB1(c=1.41), default_policy=random_terminal_roll_out,
                              backup=monte_carlo_backpropagate, game=game_copy)
            action = agent.get_action(state, n=mcts_iter)
            # print("action got", action)
            next_state, reward, done = env.step(action)
            state = next_state

        win = env.ext_player.num_cards == 0
        # print("ext_player num_cards: {}; opp_player num_cards: {}".format(env.ext_player.num_cards, env.opp_player.num_cards))
        wins.append(int(win))
        rewards.append(env.opp_player.loss if win else -env.ext_player.loss)

        if i >= 100:
            window_wr = sum(wins[-100:])
            window_ar = sum(rewards[-100:]) / 100
        else:
            window_wr = sum(wins) / (i + 1) * 100
            window_ar = sum(rewards) / (i + 1)

        msg = "win rate: {}%, avg reward: {}".format(
            round(window_wr, 2),
            round(window_ar, 2)
        )

        if win:
            msg = "Round {}: win - {}".format(i, msg)
        else:
            msg = "Round {}: lose - {} cards left{} - ".format(i, env.ext_player.num_cards, msg)

        if window_wr > max_window_wr:
            max_window_wr = window_wr
            # save_pickle(state, model_path_wr)
            msg += " (best wwr)"
        if window_ar > max_window_ar:
            max_window_ar = window_ar
            # save_pickle(state, model_path_ar)
            msg += " (best war)"

        logger.info(msg)
        duration = time.time() - begin
        print("duration: {}".format(duration))

        if i < episodes - 1:
            state, done = env.reset()

    env.end_round()

    logger.info("best window win rate: {}\nbest window avg reward: {}".format(
        round(max_window_wr, 2),
        round(max_window_ar, 2)
    ))