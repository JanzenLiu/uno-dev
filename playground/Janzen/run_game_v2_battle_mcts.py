import random
import logging
import argparse
import numpy as np
import pickle
import sys
from collections import defaultdict, OrderedDict
try:
    from .game_v2 import *
except (ModuleNotFoundError if sys.version_info >= (3, 6) else SystemError) as e:
    from game_v2 import *
from .graph import StateNode
from .mcts_utill import rand_max, UCB1, random_terminal_roll_out, monte_carlo_backpropagate
import copy


def save_pickle(obj, path):
    with open(path, "wb") as f:
        pickle.dump(obj, f)


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
            # selection
            node = _get_next_node(root, self.tree_policy)
            # simulation
            node.reward = self.default_policy(node)
            # back
            self.backup(node)

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
    args = parser.parse_args()
    kwargs = OrderedDict(sorted(args._get_kwargs(), key=lambda x: x[0]))

    episodes = kwargs.pop('episodes')

    # initialize logger
    log_id = kwargs.pop('log_id')
    assert log_id < 1000
    filename = 'battle-mcts-{:0>3}-local.log'.format(log_id)
    logger = logging.Logger("MCTSLogger")
    sh = logging.StreamHandler()
    fh = logging.FileHandler(filename)
    logger.addHandler(sh)
    logger.addHandler(fh)

    model_path_wr = 'battle-mcts-{:0>3}-best-wr-local.pkl'.format(log_id)
    model_path_ar = 'battle-mcts-{:0>3}-best-ar-local.pkl'.format(log_id)

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

    game_copy = copy.deepcopy(env)
    agent = MCTSAgent(tree_policy=UCB1(c=1.41), default_policy=random_terminal_roll_out,
                      backup=monte_carlo_backpropagate, game=game_copy)
    wins = []
    rewards = []
    max_window_wr = -sys.maxsize - 1
    max_window_ar = -sys.maxsize - 1

    state, done = env.start_round()

    for i in range(episodes):
        reward = 0

        while not done:
            action = agent.get_action(state, n=1000)
            next_state, reward, done = env.step(action)
            state = next_state

        win = env.ext_player.num_cards == 0
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
            msg = "Round {}: win{}".format(i, msg)
        else:
            msg = "Round {}: lose - {} cards left{}".format(i, env.ext_player.num_cards, msg)

        if window_wr > max_window_wr:
            max_window_wr = window_wr
            save_pickle(state, model_path_wr)
            msg += " (best wwr)"
        if window_ar > max_window_ar:
            max_window_ar = window_ar
            save_pickle(state, model_path_ar)
            msg += " (best war)"

        logger.info(msg)

        if i < episodes - 1:
            state, done = env.reset()

    env.end_round()

    logger.info("best window win rate: {}\nbest window avg reward: {}".format(
        round(max_window_wr, 2),
        round(max_window_ar, 2)
    ))
