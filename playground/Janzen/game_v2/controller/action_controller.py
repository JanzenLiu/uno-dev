import time
from .base import Controller
from .deck_controller import DeckController
from .flow_controller import FlowController
from .state_controller import StateController
from ..player import Player
from ..card import Card, NumberCard


class ActionController(Controller):

    horizontal_rule_len = 60

    def __init__(self, cards, players, num_first_hand=7, clockwise=True, interval=1, stream=True, filename=None):
        assert isinstance(cards, list)
        assert isinstance(players, list)
        assert isinstance(num_first_hand, int) and 1 <= num_first_hand <= (len(cards) - 1) / len(players)
        assert isinstance(interval, (int, float)) or interval > 0
        super().__init__(stream=stream, filename=filename)
        self.players = players
        self.deck_controller = DeckController(cards, stream=stream, filename=filename)
        self.flow_controller = FlowController(players, clockwise, stream=stream, filename=filename)
        self.state_controller = StateController(stream=stream, filename=filename)
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

    def update_loss(self):
        self.logger("calculating loss for players...")
        for player in self.players:
            player.count_loss()

        msg = ["presenting loss of players...",
               "-" * self.horizontal_rule_len]
        for index, player in enumerate(self.players):
            assert isinstance(player, Player)
            msg.append("{}: {} (cumulative_loss={})".format(player.name,
                                                            player.loss,
                                                            player.cumulative_loss))
        msg.append("-" * self.horizontal_rule_len)
        self.logger("\n".join(msg))

    def update_reward(self):
        self.logger("calculating reward for players...")
        winner_idx = self.flow_controller.current_player.idx
        loss_sum = 0
        for player in self.players:
            if player.idx != winner_idx:
                player.add_reward(-1 * player.loss)
                loss_sum += player.loss
        self.flow_controller.current_player.add_reward(loss_sum)

        msg = ["presenting reward of players...",
               "-" * self.horizontal_rule_len]
        for index, player in enumerate(self.players):
            assert isinstance(player, Player)
            msg.append("{}: {} (cumulative_reward={})".format(player.name,
                                                              player.loss*-1 if player.idx != winner_idx else loss_sum,
                                                              player.cumulative_reward))
        msg.append("-" * self.horizontal_rule_len)
        self.logger("\n".join(msg))

    def update_records(self):
        self.logger("updating win/loss records for players...")
        winner_idx = self.flow_controller.current_player.idx
        for player in self.players:
            player.add_record(player.idx == winner_idx)

        msg = ["presenting records of players...",
               "-" * self.horizontal_rule_len]
        for index, player in enumerate(self.players):
            assert isinstance(player, Player)
            msg.append("{}: {}/{} (winning rate={}%)".format(player.name,
                                                             player.num_wins,
                                                             player.num_rounds,
                                                             round(player.win_rate * 100, 1)))
        msg.append("-" * self.horizontal_rule_len)
        self.logger("\n".join(msg))

    def run(self):
        for player in self.players:
            player.start_round()

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
                self.state_controller.current_to_draw,
                next_player=self.flow_controller.next_player()
            )
            if play is not None:
                self.player_play_card(player, play)
            else:
                self.apply_penalty(player)
                self.sleep()
            # self.log_state()
            self.logger("-"*self.horizontal_rule_len)

        assert isinstance(player, Player)
        self.logger("{} wins!".format(player.name))
        self.sleep()

        self.update_loss()
        self.sleep()
        self.update_reward()
        self.sleep()
        self.update_records()
        self.sleep()

        self.logger("clearing cards for players...")
        for player in self.players:
            player.end_round()
        return player  # return winner
