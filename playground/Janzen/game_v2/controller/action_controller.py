import time
from .base import Controller
from .deck_controller import DeckController
from .flow_controller import FlowController
from .state_controller import StateController
from ..player import Player
from ..card import Card, NumberCard


class ActionController(Controller):
    def __init__(self, cards, players, num_first_hand=7, clockwise=True, interval=1):
        assert isinstance(cards, list)
        assert isinstance(players, list)
        assert isinstance(num_first_hand, int) and 1 <= num_first_hand <= (len(cards) - 1) / len(players)
        assert isinstance(interval, (int, float)) or interval > 0
        super().__init__()
        self.players = players
        self.deck_controller = DeckController(cards)
        self.flow_controller = FlowController(players, clockwise)
        self.state_controller = StateController()
        self.num_first_hand = num_first_hand
        self.interval = interval

    def format_attribute(self):
        return ", ".join([
            self.state_controller.format_attribute(),
            self.flow_controller.format_attribute(),
            self.deck_controller.format_attribute()
        ])

    def sleep(self):
        time.sleep(self.interval)

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
                if player.play_new_playable(card):
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
            color = player.get_color()
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

    def run(self):
        # Do the important thing for three times
        self.deck_controller.shuffle()
        self.deck_controller.shuffle()
        self.deck_controller.shuffle()
        self.sleep()
        self.distribute_first_hand()
        self.sleep()
        self.draw_initial_card()
        self.sleep()

        player = None
        while not self.flow_controller.is_player_done():
            self.flow_controller.to_next_player()
            player = self.flow_controller.current_player
            self.logger("Switch to player {}.".format(player))
            # self.sleep()

            play = player.get_play(
                self.state_controller.current_color,
                self.state_controller.current_value,
                self.state_controller.current_type,
                self.state_controller.current_to_draw
            )
            if play is not None:
                self.player_play_card(player, play)
            else:
                self.apply_penalty(player)
                self.sleep()
            # self.log_state()
            self.logger("-----------------------------------------------------------")

        assert isinstance(player, Player)
        self.logger("{} wins!".format(player.name))
        self.sleep()
        self.logger("calculating score for players...")
        self.sleep()
        for player in self.players:
            player.count_score()

        msg = ["presenting score of players...",
               "-----------------------------------------------------------"]
        for index, player in enumerate(self.players):
            msg.append("{}: {} (cumulative_score={})".format(player.name,
                                                             player.score,
                                                             player.cumulative_score))
        msg.append("-----------------------------------------------------------")
        self.logger("\n".join(msg))
        self.sleep()

        self.logger("clearing cards for players...")
        for player in self.players:
            player.clear_cards()
        return player  # return winner
