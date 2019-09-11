from enum import Enum, unique
from colorama import init
from colorama import Fore, Back, Style


init()

colormap = {
    "WILD": Fore.BLACK + Back.WHITE,
    "RED": Fore.LIGHTRED_EX,
    "GREEN": Fore.LIGHTGREEN_EX,
    "BLUE": Fore.LIGHTBLUE_EX,
    "YELLOW": Fore.LIGHTYELLOW_EX
}


@unique
class CardColor(Enum):
    WILD = 0  # just a conceptual type
    RED = 1
    GREEN = 2
    BLUE = 3
    YELLOW = 4

    def __call__(self, string):
        return "{}{}{}".format(colormap[self.name], string, Style.RESET_ALL)

    @staticmethod
    def option_set(ignore_wild=True):
        options = set([option.value for option in CardColor])
        if ignore_wild:
            options.remove(CardColor.WILD)
        return options

    @staticmethod
    def option_string(ignore_wild=True):
        if ignore_wild:
            return "\n".join(["{}) {}".format(option.value, option(option.name))
                              for option in CardColor if option != CardColor.WILD])
        else:
            return "\n".join(["{}) {}".format(option.value, option(option.name))
                              for option in CardColor])

@unique
class CardType(Enum):
    ABSTRACT = -1  # just a conceptual type
    NUMBER = 0
    REVERSE = 1
    SKIP = 2
    WILDCARD = 3
    DRAW_2 = 4
    DRAW_4 = 5


class Card(object):
    def __init__(self, card_type, color, score):
        assert isinstance(card_type, CardType)
        assert isinstance(color, CardColor)
        assert isinstance(score, int)
        self.card_type = card_type
        self.color = color
        self.score = score
        self.short_name = None  # to be overriden

    def __repr__(self):
        return self.color("{}({})".format(type(self).__name__, self.format_attribute()))

    def __str__(self):
        return self.color("{}({})".format(type(self).__name__, self.format_attribute()))

    def format_attribute(self):
        pass

    def check_playable(self, current_color, current_value, current_type, current_to_draw):
        assert isinstance(current_color, CardColor) and current_color != CardColor.WILD
        assert isinstance(current_value, int) and -1 <= current_value <= 9
        assert isinstance(current_type, CardType) and current_type != CardType.ABSTRACT
        assert isinstance(current_to_draw, int) and current_to_draw >= 0
        return self._check_playable(current_color, current_value, current_type, current_to_draw)

    def _check_playable(self, current_color, current_value, current_type, current_to_draw):
        return False  # to override

    # =============
    # Type Checkers
    # =============
    # to override
    def is_number(self):
        return False

    def is_reverse(self):
        return False

    def is_skip(self):
        return False

    def is_wildcard(self):
        return False

    def is_draw2(self):
        return False

    def is_draw4(self):
        return False

    def is_action(self):
        return False

    def is_weak_action(self):
        return False

    def is_strong_action(self):
        return False

    def is_draw_action(self):
        return False


class ActionCard(Card):
    def __init__(self, card_type, color, score):
        assert card_type != CardType.NUMBER
        super().__init__(card_type, color, score)

    def is_action(self):
        return True


class WeakActionCard(ActionCard):
    def __init__(self, card_type, color):
        assert color != CardColor.WILD  # might be extended?
        super().__init__(card_type, color, 20)

    def format_attribute(self):
        return self.color.name

    def is_weak_action(self):
        return True


class StrongActionCard(ActionCard):
    def __init__(self, card_type):
        super().__init__(card_type, CardColor.WILD, 50)

    def format_attribute(self):
        return ""

    def is_strong_action(self):
        return True
