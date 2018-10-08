import random
from .base import Controller
from ..card import Card


class DeckController(Controller):
    def __init__(self, cards, copy=True, stream=True, filename=None):
        super().__init__(stream=stream, filename=filename)
        assert isinstance(cards, list)
        assert len(cards) > 0
        for card in cards:
            assert isinstance(card, Card)
        self.deck_size = len(cards)
        self.draw_pile = cards.copy() if copy else cards
        self.used_pile = []

    @property
    def draw_pile_size(self):
        return len(self.draw_pile)

    @property
    def used_pile_size(self):
        return len(self.used_pile)

    def format_attribute(self):
        return ", ".join([
            "deck_size={}".format(self.deck_size),
            "draw_pile_size={}".format(self.draw_pile_size),
            "used_pile_size={}".format(self.used_pile_size)
        ])

    def shuffle(self):
        self.logger("Shuffling the draw pile...")
        random.shuffle(self.draw_pile)

    def regenerate_draw_pile(self):
        assert self.draw_pile_size == 0  # only enable regeneration of draw pile while it is run out
        self.logger("Regenerating the draw pile...")
        self.draw_pile = self.used_pile
        self.used_pile = []
        self.logger("Done. New draw pilie size: {}".format(self.draw_pile_size))

    def _draw_card(self):
        # TODO: to consider the case that both draw_pile and used_pile is empty
        assert self.draw_pile_size > 0

        # get top card and remove it from the data structure
        card = self.draw_pile.pop(0)

        # regenerate draw pile and shuffle if no cards left after this draw
        if self.draw_pile_size == 0:
            self.regenerate_draw_pile()
            self.shuffle()

        return card

    def draw_card(self):
        # add log: drawing
        card = self._draw_card()
        # add log: number of card(s) drawn
        # add log: current draw pile size
        return card

    def draw_cards(self, num_cards):
        assert isinstance(num_cards, int) and num_cards >= 1

        # repeat calling self.draw_card() for num_cards times
        # add log: drawing
        cards = [self._draw_card() for _ in range(num_cards)]
        # add log: number of cards drawn
        return cards

    def _discard_card(self, card):
        assert isinstance(card, Card)
        self.used_pile.append(card)

    def discard_card(self, card):
        self._discard_card(card)
        # add log: discarded card
        # add log: current used pile size

    def discard_cards(self, cards):
        assert isinstance(cards, list)
        for card in cards:
            self._discard_card(card)
        # add log: discarded cards
        # add log: current used pile size
