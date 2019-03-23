def train_replay(self):
    # # sample batch memory from all memory
    # memory_size = len(self.memory)
    # if memory_size < self.train_start:
    #     return
    # batch_size = min(self.batch_size, memory_size)
    # mini_batch = random.sample(self.memory, batch_size)

    update_input = np.zeros((batch_size, self.state_size))
    update_target = np.zeros((batch_size, self.action_size))

    for i in range(batch_size):
        state, action, reward, next_state, done = mini_batch[i]

        if not done:
            target = reward + self.discount_factor * np.amax(self.target_model.predict(next_state)[0])
        else:
            target = reward

        update_input[i] = state
        update_target[i] = target

    self.model.fit(update_input, update_target, batch_size=batch_size, epochs=1, verbose=0)


# DDQN
def learn(self):
    # if self.memory_counter > self.memory_size:
    #     sample_index = np.random.choice(self.memory_size, size=self.batch_size)
    # else:
    #     sample_index = np.random.choice(self.memory_counter, size=self.batch_size)
    # batch_memory = self.memory[sample_index, :]

    # 这一段和 DQN 不一样
    q_next, q_eval4next = self.sess.run(
        [self.q_next, self.q_eval],
        feed_dict={self.s_: batch_memory[:, -self.n_features:],  # next observation
                   self.s: batch_memory[:, -self.n_features:]})  # next observation
    q_eval = self.sess.run(self.q_eval, {self.s: batch_memory[:, :self.n_features]})
    q_target = q_eval.copy()
    batch_index = np.arange(self.batch_size, dtype=np.int32)
    eval_act_index = batch_memory[:, self.n_features].astype(int)
    reward = batch_memory[:, self.n_features + 1]

    if self.double_q:  # 如果是 Double DQN
        max_act4next = np.argmax(q_eval4next, axis=1)  # q_eval 得出的最高奖励动作
        selected_q_next = q_next[batch_index, max_act4next]  # Double DQN 选择 q_next 依据 q_eval 选出的动作
    else:  # 如果是 Natural DQN
        selected_q_next = np.max(q_next, axis=1)  # natural DQN

    q_target[batch_index, eval_act_index] = reward + self.gamma * selected_q_next

    # 这下面和 DQN 一样:
    _, self.cost = self.sess.run([self._train_op, self.loss],
                                 feed_dict={self.s: batch_memory[:, :self.n_features],
                                            self.q_target: q_target})
    # self.cost_his.append(self.cost)
    # self.epsilon = self.epsilon + self.epsilon_increment if self.epsilon < self.epsilon_max else self.epsilon_max
    # self.learn_step_counter += 1

