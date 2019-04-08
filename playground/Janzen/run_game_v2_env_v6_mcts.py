import sys
try:
    from .game_v2 import *
except (ModuleNotFoundError if sys.version_info >= (3, 6) else SystemError) as e:
    from game_v2 import *
import random
import numpy as np
from collections import defaultdict
import logging
import argparse


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
    def get_action(self, state):
        if np.random.rand() <= self.epsilon:
            # take random action
            action = np.random.choice(self.actions)
        else:
            # take action according to the q function table
            next_state = self.possible_next_state(state)
            action = self.arg_max(next_state)
        return int(action)

    # compute arg_max if multiple candidates exit, pick one randomly
    @staticmethod
    def arg_max(next_state):
        max_index_list = []
        max_value = next_state[0]
        for index, value in enumerate(next_state):
            if value > max_value:
                max_index_list.clear()
                max_value = value
                max_index_list.append(index)
            elif value == max_value:
                max_index_list.append(index)
        return random.choice(max_index_list)

    # get the possible next states
    def possible_next_state(self, state):
        col, row = state
        next_state = [0.0] * 4

        if row != 0:
            next_state[0] = self.value_table[str([col, row - 1])]
        else:
            next_state[0] = self.value_table[str(state)]
        if row != self.height - 1:
            next_state[1] = self.value_table[str([col, row + 1])]
        else:
            next_state[1] = self.value_table[str(state)]
        if col != 0:
            next_state[2] = self.value_table[str([col - 1, row])]
        else:
            next_state[2] = self.value_table[str(state)]
        if col != self.width - 1:
            next_state[3] = self.value_table[str([col + 1, row])]
        else:
            next_state[3] = self.value_table[str(state)]

        return next_state


# main loop
if __name__ == "__main__":
    # parse arguments
    # example: `python3 run_game_v2_env_v6_mcts.py -i 5`
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
            action = agent.get_action(next_state)

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

