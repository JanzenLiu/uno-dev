from __future__ import absolute_import
from __future__ import division
import sys
try:
    from .game_v2 import *
except (ModuleNotFoundError if sys.version_info >= (3, 6) else SystemError) as e:
    from game_v2 import *
import numpy as np
from collections import defaultdict
import logging
import argparse
import random
import copy


def monte_carlo(node):
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
    action = state_node.actions
    while not stopping_criterion(state):
        #random
        action = random.choice(state.actions)
        state = state.children[action].sample_state()
    reward += state.get_reward()
    return reward


class UCB1(object):
    """
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


class Node(object):
    def __init__(self, parent):
        self.parent = parent
        self.children = {}
        # 胜利
        self.q = 0
        # 总局数
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

    def __str__(self):
        return "Action: {}".format(self.action)


class StateNode(Node):
    """
    A node holding a state in the tree.
    """

    def __init__(self, parent, state, env):
        super(StateNode, self).__init__(parent)
        self.state = state
        self.reward = 0
        self.env = env

        next_move_types, next_moves = env.get_next_moves()
        self.actions = get_actions(next_moves, game.actions_lookuptable, game)

        for action in self.actions:
            self.children[action] = ActionNode(self, action)

    def reset(self, env_bak):
        self.env = env_bak

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
        # if self.game.playrecords.winner == 0:
        #    return 0
        if self.game.playrecords.winner == 1:
            return 1
        else:
            return 0

    def perform(self, parent, action):
        if action in [429, 430]:
            action_id = action
        else:
            action_id = self.actions.index(action)

        while (self.game.i <= 2):
            self.game.get_next_moves()
            self.game.last_move_type, self.game.last_move, self.game.end, self.game.yaobuqi = self.game.players[
                self.game.i].play(self.game.last_move_type, self.game.last_move, self.game.playrecords, action_id)
            if self.game.yaobuqi:
                self.game.yaobuqis.append(self.game.i)
            else:
                self.game.yaobuqis = []
            # 都要不起
            if len(self.game.yaobuqis) == 2:
                self.game.yaobuqis = []
                self.game.last_move_type = self.game.last_move = "start"
            if self.game.end:
                self.game.playrecords.winner = self.game.i + 1
                break
            self.game.i = self.game.i + 1
        # 一轮结束
        self.game.i = 0

        # s_
        s_ = get_state(self.game.playrecords, player=1)
        # action
        next_move_types, next_moves = self.game.get_next_moves()
        actions = get_actions(next_moves, self.game.actions_lookuptable, self.game)
        s_ = combine(s_, actions)

        return StateNode(parent, s_, self.game)

    def is_terminal(self):
        return self.env.done

    def __str__(self):
        return "State: {}".format(self.state)


class MCTS(object):
    """
    The central MCTS class, which performs the tree search. It gets a
    tree policy, a default policy, and a backup strategy.
    See e.g. Browne et al. (2012) for a survey on monte carlo tree search
    """

    def __init__(self, tree_policy, default_policy, backup, env):
        self.tree_policy = tree_policy
        self.default_policy = default_policy
        self.backup = backup
        self.env = env
        self.env_bak = copy.deepcopy(self.env)

    def __call__(self, s, n=1000):
        """
        Run the monte carlo tree search.

        :param root: The StateNode
        :param n: The number of roll-outs to be performed
        :return:
        """

        root = StateNode(None, s, self.env)

        if root.parent is not None:
            raise ValueError("Root's parent must be None.")

        for _ in range(n):
            # selection
            node = _get_next_node(root, self.tree_policy)
            # simulation
            node.reward = self.default_policy(node)
            # print(node.reward)
            # back
            self.backup(node)

            root.reset(copy.deepcopy(self.env_bak))

        # for i in root.children:
        #    print(root.children[i].__dict__)
        #    for j in root.children[i].children:
        #        print(root.children[i].children[j].__dict__)
        #    print("=======")
        return rand_max(root.children.values(), key=lambda x: x.q).action, rand_max(root.children.values(),
                                                                                    key=lambda x: x.q).q


def _expand(state_node):
    action = random.choice(state_node.untried_actions)
    action = state_node.untried_actions[0]
    # print(action)
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


# Monte Carlo Agent which learns every episodes from the sample
class MCAgent:
    def __init__(self, actions,
                 discount_factor=0.9, learning_rate=0.01,
                 epsilon=0.1):
        self.actions = actions

        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.samples = []
        self.value_table = defaultdict(float)

    # append sample to memory(state, reward, done)
    def save_sample(self, state, reward, done):
        self.samples.append([state, reward, done])

    # for every episode, agent updates q function of visited states
    def update(self):
        G_t = 0
        visit_state = []
        for reward in reversed(self.samples):
            state = str(reward[0])
            if state not in visit_state:
                visit_state.append(state)
                G_t = self.discount_factor * (reward[1] + G_t)
                value = self.value_table[state]
                self.value_table[state] = (value +
                                           self.learning_rate * (G_t - value))

    # get action for the state according to the q function table
    # agent pick action of epsilon-greedy policy
    def get_action(self, state, env):
        if np.random.rand() <= self.epsilon:
            # take random action
            best_action = np.random.choice(self.actions)
        else:
            env_copy = copy.deepcopy(env)
            mcts = MCTS(tree_policy=UCB1(c=1.41),
                        default_policy=random_terminal_roll_out,
                        backup=monte_carlo,
                        env=env_copy)
            best_action, _ = mcts(state, n=2000)
        return int(best_action)


# main loop
if __name__ == "__main__":
    # parse arguments
    # example: `python3 run_game_v2_env_v6_mc.py -i 5`
    parser = argparse.ArgumentParser()
    parser.add_argument('--discount_factor', type=float, default=0.99)
    parser.add_argument('--learning_rate', type=float, default=0.001)
    parser.add_argument('--epsilon', type=float, default=1.0)
    parser.add_argument('--log_id', '-i', type=int, required=True)
    parser.add_argument('--episodes', type=int, default=1000)
    args = parser.parse_args()
    kwargs = dict(args._get_kwargs())

    episodes = kwargs.pop('episodes')

    # initialize logger
    log_id = kwargs.pop('log_id')
    assert log_id < 1000
    filename = 'env-v6-mcts-{:0>3}-local.log'.format(log_id)
    logger = logging.Logger("MCTSLogger")
    sh = logging.StreamHandler()
    fh = logging.FileHandler(filename)
    logger.addHandler(sh)
    logger.addHandler(fh)

    # log hyper-parameters
    for k, v, in kwargs.items():
        logger.info('{}={}'.format(k, v))

    # initialize agent
    env = make_env(version=6)
    actions = env.action_space
    agent = MCAgent(actions=actions)

    for episode in range(episodes):
        state, done = env.reset()
        action = agent.get_action(state)

        while True:
            # forward to next state. reward is number and done is boolean
            next_state, reward, done = env.step(action)
            agent.save_sample(next_state, reward, done)

            # get next action
            action = agent.get_action(next_state, env)

            # at the end of each episode, update the q function table
            if done:
                win = env.players[0].num_cards == 0
                epsilon_string = " - win rate: {}%, avg reward: {}".format(
                    round(env.players[0].num_wins / (episode + 1) * 100, 2),
                    round(env.players[0].cumulative_reward / (episode + 1), 2)
                )

                if win:
                    logger.info("Round {}: win{}".format(episode, epsilon_string))
                else:
                    logger.info("Round {}: lose - {} cards left{}".format(episode, env.players[0].num_cards, epsilon_string))

                agent.update()
                agent.samples.clear()
                break

    env.end_round()
    logger.info("win rate: {}, avg reward: {}".format(env.players[0].num_wins / episodes,
                                                      env.players[0].cumulative_reward / episodes))

