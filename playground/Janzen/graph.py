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
        playables = game.ep.get_playable(sc.current_color, sc.current_value, sc.current_type, sc.current_to_draw)
        self.actions = playables

        for action in self.actions:
            self.children[action] = ActionNode(self, action)

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
        if self.ext_player.num_cards == 0:
            return 1
        else:
            return 0

    def perform(self, parent, action):
        sc = self.game.state_controller
        fc = self.game.flow_controller
        ep = self.game.ext_player
        idx = self.game.action_space.copy()

        assert fc.current_player == ep and not fc.is_player_done()

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
        # action
        # playables = ep.get_playable(sc.current_color, sc.current_value, sc.current_type, sc.current_to_draw)

        return StateNode(parent, s_, self.game)

    def is_terminal(self):
        return self.game.done

