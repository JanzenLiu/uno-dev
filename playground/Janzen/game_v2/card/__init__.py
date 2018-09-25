import itertools
from .base import CardColor, CardType, Card, ActionCard, WeakActionCard, StrongActionCard
from .number_card import NumberCard
from .reverse_card import ReverseCard
from .skip_card import SkipCard
from .draw_two_card import DrawTwoCard
from .draw_four_card import DrawFourCard
from .wild_card import WildCard


def make_standard_deck():
    return list(itertools.chain(
        list(itertools.chain(  # for each color
            *(list(itertools.chain(
                [NumberCard(color, 0)],  # 1 x Number 0
                [NumberCard(color, num) for num in range(1, 10) for _ in range(2)],  # 2 x Number [1-9]
                [ReverseCard(color) for _ in range(2)],  # 2 x Reverse
                [SkipCard(color) for _ in range(2)],  # 2 x Skip
                [DrawTwoCard(color) for _ in range(2)]))  # 2 x Draw2
              for color in CardColor if color != CardColor.WILD)
        )),
        [WildCard() for _ in range(4)],  # 4 x Wildcard
        [DrawFourCard() for _ in range(4)]  # 4 x Draw4
    ))
