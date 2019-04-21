import random
import logging
import argparse
import numpy as np
import sys
from collections import deque, OrderedDict
from keras.layers import Dense
from keras.optimizers import Adam
from keras.models import Sequential
from game_v2 import *


class DoubleDQNAgent:
    def __init__(self, state_size, action_size, hidden_sizes,
                 discount_factor=0.99, learning_rate=0.001,  # 0.99, 0.001 originally
                 batch_size=64, train_start=100,
                 epsilon=1.0, epsilon_min=0.005, epsilon_steps=1000,  # 1.0, 0.005, 50000
                 memory_size=1000):

        self.state_size = state_size
        self.action_size = action_size
        self.hidden_sizes = hidden_sizes

        self.discount_factor = discount_factor
        self.learning_rate = learning_rate
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = (self.epsilon - self.epsilon_min) / epsilon_steps
        self.batch_size = batch_size
        self.train_start = train_start

        self.memory_size = memory_size
        self.memory = deque(maxlen=memory_size)
        self.model = self.build_model()
        self.target_model = self.build_model()
        self.update_target_model()

    def build_model(self):
        model = Sequential()

        input_dim = self.state_size
        for dim in self.hidden_sizes:
            model.add(Dense(dim, input_dim=input_dim, activation='relu', kernel_initializer='he_uniform'))
            input_dim = dim
        model.add(Dense(self.action_size, input_dim=input_dim, activation='linear', kernel_initializer='he_uniform'))
        model.compile(loss='mse', optimizer=Adam(lr=self.learning_rate))
        return model

    def update_target_model(self):
        self.target_model.set_weights(self.model.get_weights())

    def get_action(self, state):
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        else:
            q_value = self.model.predict(state)
            return np.argmax(q_value[0])

    def replay_memory(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))
        if self.epsilon > self.epsilon_min:
            self.epsilon -= self.epsilon_decay

    def train_replay(self):
        # sample batch memory from all memory
        memory_size = len(self.memory)
        if memory_size < self.train_start:
            return
        batch_size = min(self.batch_size, memory_size)
        mini_batch = random.sample(self.memory, batch_size)

        update_input = np.zeros((batch_size, self.state_size))
        update_target = np.zeros((batch_size, self.action_size))

        for i in range(batch_size):
            state, action, reward, next_state, done = mini_batch[i]

            if not done:
                tmp_q_next = self.target_model.predict(next_state)
                q_next = tmp_q_next[0]
                tmp_q_eval4next = self.model.predict(next_state)
                q_eval4next = tmp_q_eval4next[0]
                max_act4next = np.argmax(q_eval4next)  # the action with highest q value evaluated by the eval net
                selected_q_next = q_next[max_act4next]
                target = reward + self.discount_factor * selected_q_next
            else:
                target = reward

            update_input[i] = state
            update_target[i] = target

        self.model.fit(update_input, update_target, batch_size=batch_size, epochs=1, verbose=0)

    def load_weights(self, name):
        self.model.load_weights(name)

    def save_weights(self, name):
        self.model.save_weights(name)

    def save_model(self, name):
        self.model.save(name)


if __name__ == "__main__":
    # parse arguments
    # example: `python3 run_game_v2_battle_dqn_local.py -n 64 64 -i 5`
    parser = argparse.ArgumentParser()
    parser.add_argument('--hidden_sizes', '-n', nargs='*', type=int, default=[])
    parser.add_argument('--discount_factor', type=float, default=0.99)
    parser.add_argument('--learning_rate', type=float, default=0.001)
    parser.add_argument('--batch_size', type=int, default=256)
    parser.add_argument('--train_start', type=int, default=100)
    parser.add_argument('--epsilon', type=float, default=1.0)
    parser.add_argument('--epsilon_min', type=float, default=0.005)
    parser.add_argument('--epsilon_steps', type=int, default=5000)
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
    filename = 'battle-ddqn-{:0>3}-local.log'.format(log_id)
    logger = logging.Logger("DoubleDQNLogger")
    sh = logging.StreamHandler()
    fh = logging.FileHandler(filename)
    logger.addHandler(sh)
    logger.addHandler(fh)

    model_path_wr = 'battle-ddqn-{:0>3}-best-wr-local.h5'.format(log_id)
    model_path_ar = 'battle-ddqn-{:0>3}-best-ar-local.h5'.format(log_id)

    logger.info('opponent=greedy')
    # log hyper-parameters
    for k, v, in kwargs.items():
        logger.info('{}={}'.format(k, v))

    # initialize agent
    state_version = kwargs.pop("state")
    reward_version = kwargs.pop("reward")
    env = BattleEnv(state_version=state_version, reward_version=reward_version)
    state_size = env.state_space_dim
    action_size = env.action_space_dim
    agent = DoubleDQNAgent(state_size, action_size, **kwargs)
    wins = []
    rewards = []
    max_window_wr = -sys.maxsize - 1
    max_window_ar = -sys.maxsize - 1

    state, done = env.start_round()

    for i in range(episodes):
        reward = 0

        while not done:
            action = agent.get_action(state)
            next_state, reward, done = env.step(action)
            agent.replay_memory(state, action, reward, next_state, done)
            agent.train_replay()
            state = next_state

        agent.update_target_model()
        win = env.ext_player.num_cards == 0
        wins.append(int(win))
        rewards.append(env.opp_player.loss if win else -env.ext_player.loss)

        if i >= 100:
            window_wr = sum(wins[-100:])
            window_ar = sum(rewards[-100:]) / 100
        else:
            window_wr = sum(wins) / (i + 1) * 100
            window_ar = sum(rewards) / (i + 1)

        if agent.epsilon > agent.epsilon_min:
            msg = " - epsilon={:.4f}".format(agent.epsilon)
        else:
            msg = ""

        msg += " - win rate: {}%, avg reward: {}".format(
            round(window_wr, 2),
            round(window_ar, 2)
        )

        if win:
            msg = "Round {}: win{}".format(i, msg)
        else:
            msg = "Round {}: lose - {} cards left{}".format(i, env.ext_player.num_cards, msg)

        if window_wr > max_window_wr:
            max_window_wr = window_wr
            agent.save_model(model_path_wr)
            msg += " (best wwr)"
        if window_ar > max_window_ar:
            max_window_ar = window_ar
            agent.save_model(model_path_ar)
            msg += " (best war)"

        logger.info(msg)

        if i < episodes - 1:
            state, done = env.reset()

    env.end_round()

    logger.info("best window win rate: {}\nbest window avg reward: {}".format(
        round(max_window_wr, 2),
        round(max_window_ar, 2)
    ))
