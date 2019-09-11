from .base import Controller
from .deck_controller import DeckController
from .flow_controller import FlowController
from .state_controller import StateController
from ..player import Player, PlayerType, construct_player
from ..card import Card, NumberCard, make_standard_deck, make_standard_unique_deck
import numpy as np
import gc


class BattleEnv(Controller):
    horizontal_rule_len = 60
    horizontal_rule = "-" * horizontal_rule_len
    num_players = 2
    num_first_hand = 7
    clockwise = True
    cards = make_standard_deck()
    unique_cards = make_standard_unique_deck()
    action_names = [card.short_name for card in unique_cards] + [None]
    action_space_dim = len(action_names)
    action_space = list(range(action_space_dim))
    action_map = dict(zip(action_space, action_names))  # int -> card/None
    action_invmap = dict(zip(action_names, action_space))  # card/None -> int
    state_version_to_dim = {"1d_1": 135, "2d_1": (5, 58)}
    reward_versions = {"score_1", "score_1.1", "count_1", "count_1.1", "final_1", "final_1.1", "type_1"}

    def __init__(self, state_version="1d_1", reward_version="score_1",
                 agent_pos=0, opponent_type=PlayerType.PC_GREEDY, low_dim=False, stream=False, filename=None):
        assert isinstance(state_version, str)
        assert isinstance(reward_version, str)
        assert isinstance(agent_pos, int) and 0 <= agent_pos <= 1
        assert isinstance(opponent_type, PlayerType)

        super().__init__(stream=stream, filename=filename)
        cls = self.__class__

        # set state scheme
        # TODO: add feature names
        if state_version not in cls.state_version_to_dim:
            raise ValueError("Unknown state_verison: {}".format(state_version))
        self.state_version = state_version
        self.state_space_dim = cls.state_version_to_dim[state_version]

        # set reward scheme
        if reward_version not in cls.reward_versions:
            raise ValueError("Unknown reward_verison: {}".format(reward_version))
        self.reward_version = reward_version

        # set players
        self.agent_pos = agent_pos
        self.opponent_type = opponent_type
        self.players = None
        self.ext_player = None  # external agent player
        self.opp_player = None  # opponent player
        self._init_players()

        # set subordinate controllers
        self.deck_controller = None
        self.flow_controller = None
        self.state_controller = None

        # set other attributes
        self.done = False
        self.low_dim = low_dim

    def _init_players(self):
        ap = self.agent_pos  # agent position
        op = 1 - self.agent_pos  # opponent position
        ot = self.opponent_type
        self.players = [None] * 2
        self.players[ap] = construct_player(PlayerType.PC_GREEDY, idx=ap, name='Agent',
                                            stream=self.stream, filename=self.filename)  # Indeed use an external agent
        self.players[op] = construct_player(ot, idx=op, name=ot.name,
                                            stream=self.stream, filename=self.filename)
        self.ext_player = self.players[ap]
        self.opp_player = self.players[op]

    def _get_state(self):
        # TODO: update this method to add a new version of state
        entire_state = None
        sc = self.state_controller
        dc = self.deck_controller
        ep = self.ext_player
        op = self.opp_player
        ctd = sc.current_to_draw
        ccv = sc.current_color.value
        cv = sc.current_value
        ctv = sc.current_type.value
        cw = self.flow_controller.clockwise
        playables = ep.get_playable(sc.current_color, sc.current_value, sc.current_type, sc.current_to_draw)

        if self.state_version.startswith("1d"):
            if self.low_dim:
                entire_state = np.zeros(self.state_space_dim)
                state = entire_state
            else:
                entire_state = np.zeros((1, self.state_space_dim))
                state = entire_state[0]

            # ================
            # common 1D states
            # ================
            # play state(dim=22)
            state[0] = ctd  # to draw(dim=1),        #0
            state[ccv] = 1  # color(dim=4),      #1 - #4
            state[cv + 6] = 1  # value(dim=11),       #5 - #15
            state[ctv + 16] = 1  # type(dim=6),   #16 - #21

            # flow state(dim=2): clockwise(dim=2)
            state[int(cw) + 22] = 1  # #22 - #23

            # player state(dim=110): cards(dim=54) in hand, number of them(dim=1) and valid actions(dim=55)
            state[24] = ep.num_cards  # #24
            for card in ep.cards:     # #25 - #78
                state[self.action_invmap[card.short_name] + 25] += 1
            if len(playables) == 0:
                state[133] = 1  # no playable, only "None" is valid
            else:
                for i, card in playables:
                    state[self.action_invmap[card.short_name] + 79] += 1  # #79 - #132

            # opponent state(dim=1): #cards in each other player's hand
            state[134] = op.num_cards

        if self.state_version == "2d_1":
            entire_state = np.zeros(self.state_space_dim)

            # play and flow state
            # (0 - 9, Reverse, Skip, DrawTwo) * RGBY, Wild, DrawFour
            state = entire_state[0]
            state[55] = ctd
            state[56] = int(cw)
            state[(ccv - 1) * 13: ccv * 13] = 1
            if cv > -1:
                state[cv: 40 + cv: 13] = 1
            if ctv == 1:
                state[10:50:13] = 1
            elif ctv == 2:
                state[11:51:13] = 1
            elif ctv == 4:
                state[12:52:13] = 1
            elif ctv == 3:
                state[52] = 1
            elif ctv == 5:
                state[53] = 1

            # player state
            state = entire_state[1]
            state[57] = ep.num_cards
            for card in ep.cards:
                state[self.action_invmap[card.short_name]] += 1

            state = entire_state[2]
            if len(playables) == 0:
                state[54] = 1  # no playable, only "None" is valid
            else:
                for i, card in playables:
                    state[self.action_invmap[card.short_name]] += 1

            # opponent state
            state = entire_state[3]
            state[57] = op.num_cards

            # deck state
            state = entire_state[4]
            state[57] = len(dc.used_pile)
            for card in dc.used_pile:
                state[self.action_invmap[card.short_name]] += 1

        return entire_state

    def format_attribute(self):
        return ", ".join([
            self.state_controller.format_attribute(),
            self.flow_controller.format_attribute(),
            self.deck_controller.format_attribute()
        ])

    def log_state(self):
        self.logger("Current play state: ({}).".format(self.state_controller.format_attribute()))
        self.logger("Current flow state: ({}).".format(self.flow_controller.format_attribute()))
        self.logger("Current deck state: ({}).".format(self.deck_controller.format_attribute()))

    def give_player_card(self, player):
        assert isinstance(player, Player)
        card = self.deck_controller.draw_card()
        player.get_card(card)
        return card

    def give_player_cards(self, player, num_cards):
        assert isinstance(player, Player)
        cards = self.deck_controller.draw_cards(num_cards)
        player.get_cards(cards)
        return cards

    def player_play_card(self, player, play):
        index, card = play
        player.play_card(index)
        self.deck_controller.discard_card(card)
        self.state_controller.accept_card(card, player, self.flow_controller)

    def apply_penalty(self, player=None):
        if player is None:
            player = self.flow_controller.current_player

        assert isinstance(player, Player)
        if self.state_controller.current_to_draw > 0:
            self.logger("Applying penalty: {} cards...".format(self.state_controller.current_to_draw))
            cards = self.give_player_cards(player, self.state_controller.current_to_draw)
            self.state_controller.clear_to_draw()
            return cards
        else:
            self.logger("Applying penalty: 1 card...")
            card = self.give_player_card(player)
            if self.state_controller.check_new_card_playable(card, player):
                if player.play_new_playable(card, play_state=self.state_controller.state_dict):
                    self.logger("Can play!")
                    self.player_play_card(player, (player.num_cards - 1, card))
                    return []
            return [card]

    def draw_initial_card(self):
        self.logger("Drawing initial cards...")
        card = self.deck_controller.draw_card()
        assert isinstance(card, Card)

        while card.is_draw4():
            self.logger("Oops, It\'s a Draw4 card ({}), let\'s try again.".format(card))
            card = self.deck_controller.draw_card()
            assert isinstance(card, Card)

        self.logger("{} is drawn as the initial card.".format(card))
        if card.is_number():
            # set current color and number
            assert isinstance(card, NumberCard)
            self.state_controller.set_color(card.color)
            self.state_controller.set_value(card.num)

        elif card.is_reverse():
            # the direction is reversed, and the current color is determined by the card
            self.flow_controller.reverse()
            self.state_controller.set_color(card.color)
            self.state_controller.set_value(-1)

        elif card.is_skip():
            # the first player is skipped, and the current color is determined by the card
            self.flow_controller.add_skip(1)
            self.state_controller.set_color(card.color)
            self.state_controller.set_value(-1)

        elif card.is_wildcard():
            # the first player determine the current color and begin playing
            player = self.flow_controller.current_player
            assert isinstance(player, Player)
            color = player.get_color(play_state=self.state_controller.state_dict,
                                     next_player=self.flow_controller.next_player())
            self.state_controller.set_color(color)
            self.state_controller.set_value(-1)

        elif card.is_draw2():
            # the first player draw 2 cards, and the current color is determined by the card
            self.state_controller.add_to_draw(2)
            self.state_controller.set_color(card.color)
            self.state_controller.set_value(-1)
            self.apply_penalty()
            self.flow_controller.to_next_player()

        else:
            # raise Error
            raise Exception("Unknown Card Type of the Initial Card")

        self.state_controller.set_type(card.card_type)
        self.log_state()

    def distribute_first_hand(self):
        self.logger("Distributing first hand cards ({} for each player)...".format(self.num_first_hand))
        for player in self.players:
            self.give_player_cards(player, self.num_first_hand)

    def start_round(self):
        self.deck_controller = DeckController(self.cards, stream=self.stream, filename=self.filename)
        self.flow_controller = FlowController(self.players, self.clockwise, stream=self.stream, filename=self.filename)
        self.state_controller = StateController(stream=self.stream, filename=self.filename)

        for player in self.players:
            player.start_round()

        for _ in range(3):
            self.deck_controller.shuffle()  # do the important thing for three times

        self.distribute_first_hand()
        self.draw_initial_card()

        ep = self.ext_player
        sc = self.state_controller
        fc = self.flow_controller
        fc.to_next_player()
        done = False

        # let other player(s) play (very unlikely but possible)
        while not (fc.current_player == ep or done):
            player = fc.current_player
            self.logger("Switch to player {}.".format(player))

            play = player.get_play(
                sc.current_color,
                sc.current_value,
                sc.current_type,
                sc.current_to_draw,
                next_player=fc.next_player()
            )
            if play is not None:
                self.player_play_card(player, play)
                done = fc.is_player_done()
            else:
                self.apply_penalty(player)
            fc.to_next_player()
            self.logger(self.horizontal_rule)

        assert fc.current_player == ep
        self.done = done
        self.logger("Switch to player {}.".format(fc.current_player))
        return self._get_state(), done

    def step(self, action):
        # TODO: update this method to add a new version of reward
        rv = self.reward_version
        sc = self.state_controller
        fc = self.flow_controller
        ep = self.ext_player
        idx = self.action_space.copy()

        # check it is the external agent player's turn to play and the round hasn't finished yet
        assert fc.current_player == ep and not fc.is_player_done()

        # parse action
        action_name = self.action_map[action]
        playables = ep.get_playable(sc.current_color, sc.current_value, sc.current_type, sc.current_to_draw)
        play = None
        if self.low_dim:
            reward = 0
        else:
            reward = np.full((self.action_space_dim,), 0)

        for i, card in playables:
            card_short_name = card.short_name
            card_id = self.action_invmap[card_short_name]

            # --- case switching ---
            if self.low_dim:
                if action_name == card_short_name:
                    play = i, card
                    if rv == "score_1":
                        reward += card.score
                    elif rv == "score_1.1":
                        reward += card.score * 0.1
                    elif rv == "count_1":
                        reward += 1
                    elif rv == "count_1.1":
                        reward += 0.1
                    elif rv == "final_1":
                        reward += 0
                    elif rv == "final_1.1":
                        reward += 0
                    elif rv == "type_1":
                        if card.is_number():
                            reward += 1
                        elif card.is_weak_action():
                            reward += 2
                        else:
                            reward += 3
                    break
            else:
                if rv == "score_1":
                    reward[card_id] = card.score
                elif rv == "score_1.1":
                    reward[card_id] = card.score * 0.1
                elif rv == "count_1":
                    reward[card_id] = 1
                elif rv == "count_1.1":
                    reward[card_id] = 0.1
                elif rv == "final_1":
                    reward[card_id] = 0
                elif rv == "final_1.1":
                    reward[card_id] = 0
                elif rv == "type_1":
                    if card.is_number():
                        reward[card_id] = 1
                    elif card.is_weak_action():
                        reward[card_id] = 2
                    else:
                        reward[card_id] = 3
            # ----------------------

            if card_id in idx:
                idx.remove(card_id)
            if card_short_name == action_name:
                play = i, card

        # apply agent's action
        if play is not None:
            self.player_play_card(ep, play)
            done = fc.is_player_done()
            if done:
                card = play[1]
                i = self.action_invmap[card.short_name]

                # --- case switching ---
                if self.low_dim:
                    if rv == "score_1":
                        reward += self.opp_player.loss
                    elif rv == "score_1.1":
                        reward += self.opp_player.loss
                    elif rv == "count_1":
                        reward += self.opp_player.num_cards
                    elif rv == "count_1.1":
                        reward += self.opp_player.num_cards
                    elif rv == "final_1":
                        reward = 10
                    elif rv == "final_1.1":
                        reward = 10
                    elif rv == "type_1":
                        reward = 10
                else:
                    if rv == "score_1":
                        reward[i] += self.opp_player.loss
                    elif rv == "score_1.1":
                        reward[i] += self.opp_player.loss
                    elif rv == "count_1":
                        reward[i] += self.opp_player.num_cards
                    elif rv == "count_1.1":
                        reward[i] += self.opp_player.num_cards
                    elif rv == "final_1":
                        reward[i] = 10
                    elif rv == "final_1.1":
                        reward[i] = 10
                    elif rv == "type_1":
                        reward[i] = 10
                # ----------------------
        else:
            drawn_cards = self.apply_penalty(ep)
            done = False

            # --- case switching ---
            if self.low_dim:
                if rv == "score_1":
                    reward = -sum([c.score for c in drawn_cards])
                elif rv == "score_1.1":
                    reward = -sum([c.score for c in drawn_cards]) * 0.1
                elif rv == "count_1":
                    reward = -len(drawn_cards)
                elif rv == "count_1.1":
                    reward = -len(drawn_cards) * 0.1
                elif rv == "final_1":
                    reward = 0
                elif rv == "final_1.1":
                    reward = 0
                elif rv == "type_1":
                    reward = -len(drawn_cards)
            else:
                if rv == "score_1":
                    reward[idx] = -sum([c.score for c in drawn_cards])
                elif rv == "score_1.1":
                    reward[idx] = -sum([c.score for c in drawn_cards]) * 0.1
                elif rv == "count_1":
                    reward[idx] = -len(drawn_cards)
                elif rv == "count_1.1":
                    reward[idx] = -len(drawn_cards) * 0.1
                elif rv == "final_1":
                    reward[idx] = 0
                elif rv == "final_1.1":
                    reward[idx] = 0
                elif rv == "type_1":
                    reward[idx] = -len(drawn_cards)
            # ----------------------

        fc.to_next_player()
        self.logger(self.horizontal_rule)

        # let other player(s) play
        while not (fc.current_player == ep or done):
            player = fc.current_player
            self.logger("Switch to player {}.".format(player))

            play = player.get_play(
                sc.current_color,
                sc.current_value,
                sc.current_type,
                sc.current_to_draw,
                next_player=fc.next_player()
            )
            if play is not None:
                self.player_play_card(player, play)
                done = fc.is_player_done()
                # if done:
                #     reward[:] = -100
            else:
                self.apply_penalty(player)  # done must remain False in this case
            fc.to_next_player()
            self.logger(self.horizontal_rule)

        self.done = done
        self.logger("Switch to player {}.".format(fc.current_player))
        return self._get_state(), reward, done

    def end_round(self):
        if self.done:
            total_loss = 0
            for player in self.players:
                total_loss += player.loss
            for player in self.players:
                if player.num_cards == 0:  # winner
                    player.add_record(True)
                    player.add_reward(total_loss - player.loss)
                else:  # loser(s)
                    player.add_record(False)
                    player.add_reward(-player.loss)

        for player in self.players:
            player.end_round()

        self.deck_controller = None
        self.flow_controller = None
        self.state_controller = None

        gc.collect()

    def reset(self):
        self.end_round()
        return self.start_round()
