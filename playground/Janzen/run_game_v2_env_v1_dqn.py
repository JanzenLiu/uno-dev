import sys
try:
    from .game_v2 import *
except (ModuleNotFoundError if sys.version_info >= (3, 6) else SystemError) as e:
    from game_v2 import *
import random
import numpy as np
from collections import deque
from keras.layers import Dense
from keras.optimizers import Adam
from keras.models import Sequential
import logging
import argparse


class DQNAgent:
    def __init__(self, state_size, action_size, hidden_sizes,
                 discount_factor=0.99, learning_rate=0.001,  # 0.99, 0.001 originally
                 batch_size=256, train_start=100, fix_q_start=0,
                 epsilon=1.0, epsilon_min=0.005, epsilon_steps=50000,  # 1.0, 0.005, 50000
                 memory_size=10000):

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
        self.fix_q_start = fix_q_start
        self.training_rl = False

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
        # model.summary()
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
        memory_size = len(self.memory)
        if memory_size < self.train_start:
            return
        batch_size = min(self.batch_size, memory_size)
        mini_batch = random.sample(self.memory, batch_size)

        update_input = np.zeros((batch_size, self.state_size))
        update_target = np.zeros((batch_size, self.action_size))

        for i in range(batch_size):
            state, action, reward, next_state, done = mini_batch[i]
            target = reward

            if not done:
                if memory_size > self.fix_q_start:
                    if not self.training_rl:
                        print("starting fixed-q training.")
                        self.training_rl = True
                    target = reward + self.discount_factor * np.amax(self.target_model.predict(next_state)[0])
                else:
                    target = reward + self.discount_factor * reward

            update_input[i] = state
            update_target[i] = target

        self.model.fit(update_input, update_target, batch_size=batch_size, epochs=1, verbose=0)

    def load_model(self, name):
        self.model.load_weights(name)

    def save_model(self, name):
        self.model.save_weights(name)


if __name__ == "__main__":
    EPISODES = 10000

    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--hidden_sizes', nargs='*', type=int, default=[])
    parser.add_argument('--discount_factor', type=float, default=0.99)
    parser.add_argument('--learning_rate', type=float, default=0.001)
    parser.add_argument('--batch_size', type=int, default=256)
    parser.add_argument('--train_start', type=int, default=100)
    parser.add_argument('--fix_q_start', type=int, default=0)
    parser.add_argument('--epsilon', type=float, default=1.0)
    parser.add_argument('--epsilon_min', type=float, default=0.005)
    parser.add_argument('--epsilon_steps', type=int, default=50000)
    parser.add_argument('--log_id', '-i', type=int, required=True)
    args = parser.parse_args()
    kwargs = dict(args._get_kwargs())

    # initialize logger
    log_id = kwargs.pop('log_id')
    assert log_id < 1000
    filename = 'env-v1-dqn-{:0>3}.log'.format(log_id)
    logger = logging.Logger("DQNLogger")
    sh = logging.StreamHandler()
    fh = logging.FileHandler(filename)
    logger.addHandler(sh)
    logger.addHandler(fh)

    # log hyper-parameters
    for k, v, in kwargs.items():
        logger.info('{}={}'.format(k, v))

    # initialize agent
    env = make_env(version=1)
    state_size = env.state_space_dim
    action_size = env.action_space_dim
    agent = DQNAgent(state_size, action_size, **kwargs)

    for i in range(EPISODES):
        state, done = env.reset()
        reward = 0

        while not done:
            action = agent.get_action(state)
            next_state, reward, done = env.step(action)
            agent.replay_memory(state, action, reward, next_state, done)
            agent.train_replay()
            state = next_state

        agent.update_target_model()
        win = env.players[0].num_cards == 0
        if win:
            logger.info("Round {}: win".format(i))
        else:
            logger.info("Round {}: lose - {} cards left".format(i, env.players[0].num_cards))

    env.end_round()

    logger.info("win rate: {}, avg reward: {}".format(env.players[0].num_wins / EPISODES,
                                                      env.players[0].cumulative_reward / EPISODES))