from enum import Enum, unique
from ..card import CardColor, Card
from ..io import UnoLogger
from colorama import init
from colorama import Fore, Style


init()


@unique
class PlayerType(Enum):
    HUMAN = 1
    PC_NAIVE = 2

    @staticmethod
    def option_set():
        return set([option.value for option in PlayerType])

    @staticmethod
    def option_string():
        return "\n".join(["{}) {}".format(option.value, option.name) for option in PlayerType])


class Player(object):
    def __init__(self, ptype, name, idx):
        assert isinstance(ptype, PlayerType)
        assert isinstance(name, str)
        assert isinstance(idx, int) and idx >= 0
        self.type = ptype
        self.name = name
        self.idx = idx
        self.cards = []
        self.cumulative_score = 0
        self.logger = UnoLogger("{}[{} {}]{}".format(Fore.CYAN, type(self).__name__, self.name, Style.RESET_ALL))

    def __repr__(self):
        return "{}({})".format(self.type.name, self.format_attribute())

    def __str__(self):
        return "{}({})".format(self.type.name, self.format_attribute())

    def format_attribute(self, show_cards=False):
        attr_strings = [
            "name={}".format(self.name),
            "pos={}".format(self.idx),
            "cumulative_score={}".format(self.cumulative_score),
            "num_cards={}".format(self.num_cards)
        ]
        if show_cards:
            attr_strings.append("cards={}".format(self.cards))
        return ", ".join(attr_strings)

    @property
    def num_cards(self):
        return len(self.cards)

    @property
    def score(self):
        score = 0
        for card in self.cards:
            score += card.score
        return score

    def count_score(self):
        self.cumulative_score += self.score

    def is_human(self):
        return False  # to override

    def get_card(self, card):
        assert isinstance(card, Card)
        self.cards.append(card)
        self.logger("Draws 1 card.")

    def get_cards(self, cards):
        assert isinstance(cards, list)
        for card in cards:
            assert isinstance(card, Card)
            self.cards.append(card)
        self.logger("Draws {} card.".format(len(cards)))

    def clear_cards(self):
        self.cards = []

    def play_card(self, index):
        assert 0 <= index < self.num_cards
        card = self.cards.pop(index)
        self.logger("Plays {} ({} cards left).".format(card, self.num_cards))
        if self.is_uno():
            self.logger("Calls UNO!")
        return card

    def _get_playable(self, current_color, current_value, current_type, current_to_draw):
        playable_cards = [(i, card) for i, card in enumerate(self.cards)
                          if card.check_playable(current_color,
                                                 current_value,
                                                 current_type,
                                                 current_to_draw)]
        return playable_cards

    @staticmethod
    def filter_draw_four(playable_cards):
        # If playable_cards include no NumberCard or WeakActionCard, all cards are playable
        # If playable_cards include NumberCard or (and) WeakActionCard, DrawFourCard needs to be removed
        num_strict_matching = 0
        draw_four_indices = []
        for (idx, (i, card)) in enumerate(playable_cards):
            if card.is_number() or card.is_weak_action():
                num_strict_matching += 1
            elif card.is_draw4():
                draw_four_indices.append(idx)

        if num_strict_matching > 0:
            for i in sorted(draw_four_indices, reverse=True):
                del playable_cards[i]

        return playable_cards

    def get_playable(self, current_color, current_value, current_type, current_to_draw):
        return self.filter_draw_four(self._get_playable(current_color, current_value, current_type, current_to_draw))

    def get_play_from_playable(self, playable_cards, **info):
        raise NotImplementedError

    def check_new_card_playable(self, current_color, current_value, current_type, current_to_draw, new_card=None):
        if new_card is None:
            new_card = self.cards[-1]
        assert isinstance(new_card, Card)

        if not new_card.is_draw4():
            return new_card.check_playable(current_color, current_value, current_type, current_to_draw)
        else:
            for card in self.cards:
                if (card.is_number() or card.is_weak_action()) and \
                        card.check_playable(current_color, current_value, current_type, current_to_draw):
                    return False
            return True

    def play_new_playable(self, new_playable, **info):
        raise NotImplementedError

    def get_play(self, current_color, current_value, current_type, current_to_draw, **info):
        playable_cards = self.get_playable(current_color, current_value, current_type, current_to_draw)
        if len(playable_cards) == 0:
            play = None
        else:
            play = self.get_play_from_playable(playable_cards, **info)

        if play is None:
            self.logger("Has no playable cards or decides not to play.")
        return play

    def _get_color(self):
        raise NotImplementedError

    def get_color(self):
        color = self._get_color()
        assert isinstance(color, CardColor)
        self.logger("Selects color {}".format(color(color)))
        return color

    def is_done(self):
        return self.num_cards == 0

    def is_uno(self):
        return self.num_cards == 1
