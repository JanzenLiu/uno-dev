from .base import Controller
from .deck_controller import DeckController
from .flow_controller import FlowController
from .state_controller import StateController
from ..player import Player, PlayerType, construct_player
from ..card import Card, NumberCard, make_standard_deck, make_standard_unique_deck
import numpy as np
import gc


class EnvV1Controller(Controller):
    """
    Version 1 Environment Controller

    Always 2 players, the external agent is always at position 0 and the opponent is always GreedyPlayer.
    Always starts with clockwise flow and 7 first hand cards.
    Always uses the standard deck.
    """
    horizontal_rule_len = 60
    horizontal_rule = "-" * horizontal_rule_len
    num_players = 2
    num_first_hand = 7
    clockwise = True
    cards = make_standard_deck()
    state_space_dim = 135
    unique_cards = make_standard_unique_deck()
    action_names = [card.short_name for card in unique_cards] + [None]
    action_space_dim = len(action_names)
    action_space = list(range(action_space_dim))
    action_map = dict(zip(action_space, action_names))  # int -> card/None
    action_invmap = dict(zip(action_names, action_space))  # card/None -> int

    def __init__(self, stream=False, filename=None):
        super().__init__(stream=stream, filename=filename)

        # set players
        self.players = None
        self.ext_player = None  # external agent player
        self._init_players()

        # set subordinate controllers
        self.deck_controller = None
        self.flow_controller = None
        self.state_controller = None

        # set other attributes
        self.done = False

    def _init_players(self):
        self.players = [None] * 2
        self.players[0] = construct_player(PlayerType.PC_GREEDY, idx=0, name='Agent',
                                           stream=self.stream, filename=self.filename)  # Indeed use an external agent
        self.players[1] = construct_player(PlayerType.PC_GREEDY, idx=1, name='Greedy',
                                           stream=self.stream, filename=self.filename)
        self.ext_player = self.players[0]

    def _get_state(self):
        state = np.zeros(self.state_space_dim)

        # play state(dim=22)
        sc = self.state_controller
        state[0] = sc.current_to_draw  # to draw(dim=1)
        state[sc.current_color.value] = 1  # color(dim=4)
        state[sc.current_value + 6] = 1  # value(dim=11)
        state[sc.current_type.value + 16] = 1  # type(dim=6)

        # flow state(dim=2): clockwise(dim=2)
        state[int(self.flow_controller.clockwise) + 22] = 1

        # deck state(dim=55): used_pile size(dim=1) and cards in it(dim=54)
        state[24] = self.deck_controller.used_pile_size
        for card in self.deck_controller.used_pile:
            state[self.action_invmap[card.short_name] + 25] += 1

        # player state(dim=55): cards(dim=54) in hand and number of them(dim=1)
        state[79] = self.ext_player.num_cards
        for card in self.ext_player.cards:
            state[self.action_invmap[card.short_name] + 80] += 1

        # other player state(dim=1): #cards in each other player's hand
        state[134] = self.players[1].num_cards

        state = np.reshape(state, (1, -1))
        return state

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
            self.give_player_cards(player, self.state_controller.current_to_draw)
            self.state_controller.clear_to_draw()
        else:
            self.logger("Applying penalty: 1 card...")
            card = self.give_player_card(player)
            if self.state_controller.check_new_card_playable(card, player):
                if player.play_new_playable(card, play_state=self.state_controller.state_dict):
                    self.logger("Can play!")
                    self.player_play_card(player, (player.num_cards - 1, card))

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
        reward = np.full((self.action_space_dim,), -20)
        for i, card in playables:
            card_short_name = card.short_name
            card_id = self.action_invmap[card_short_name]
            reward[card_id] = card.score
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
                reward[self.action_invmap[card.short_name]] += self.players[1].loss
        else:
            prev_loss = ep.loss
            self.apply_penalty(ep)
            done = False
            reward[idx] = prev_loss - ep.loss

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
