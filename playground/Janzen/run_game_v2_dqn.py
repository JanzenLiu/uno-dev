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


class DQNAgent:
    def __init__(self, state_size, action_size, hidden_sizes,
                 discount_factor=0.49, learning_rate=0.001,
                 batch_size=256, train_start=100, train_rl_start=1000,
                 epsilon=1.0, epsilon_min=0.005, epsilon_steps=2000):

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
        self.train_rl_start = train_rl_start
        self.training_rl = False

        self.memory = deque(maxlen=10000)
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
        model.summary()
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
                if memory_size > self.train_rl_start:
                    if not self.training_rl:
                        print("starting training RL.")
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
    EPISODES = 1000

    env = make_env(version=1)
    state_size = env.state_space_dim
    action_size = env.action_space_dim
    hidden_sizes = []
    agent = DQNAgent(state_size, action_size, hidden_sizes)

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
        print("Round {}: {} - {} cards left".format(i, 'win' if win else 'lose', env.players[0].num_cards))

    env.end_round()

    print(env.players[0].num_wins, env.players[0].cumulative_reward)
    print(env.players[1].num_wins, env.players[1].cumulative_reward)
