from .base import Policy, ActionType
from ..card import CardColor


def first_card_get_play(playable_cards, **info):
    assert isinstance(playable_cards, list) and len(playable_cards) > 0
    return playable_cards[0]


def first_card_get_color(**info):
    cards = info.get("cards", [])

    for card in cards:
        if card.color != CardColor.WILD:
            return card.color
    return CardColor.RED


def first_card_play_new(new_playable, **info):
        return True


class FirstCardGetPlayPolicy(Policy):
    def __init__(self):
        super().__init__(name="default", atype=ActionType.GET_PLAY, strategy=first_card_get_play)


class FirstCardGetColorPolicy(Policy):
    def __init__(self):
        super().__init__(name="default", atype=ActionType.GET_COLOR, strategy=first_card_get_color)


class FirstCardPlayNewPolicy(Policy):
    def __init__(self):
        super().__init__(name="default", atype=ActionType.PLAY_NEW, strategy=first_card_play_new)
