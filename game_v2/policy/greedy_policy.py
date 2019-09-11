from .base import Policy, ActionType
from ..card import Card, CardColor


def greedy_get_play(playable_cards, **info):
    assert isinstance(playable_cards, list) and len(playable_cards) > 0
    best_index, best_card = playable_cards[0]

    assert isinstance(best_card, Card)
    best_score = best_card.score

    for index, card in playable_cards[1:]:
        assert isinstance(card, Card)
        if card.score > best_score:
            best_index, best_card = index, card
            best_score = card.score

    return best_index, best_card


def greedy_get_color(**info):
    color_scores = {}
    cards = info.get("cards", [])

    for card in cards:
        if not card.is_strong_action():
            color = card.color
            score = card.score
            if color not in color_scores:
                color_scores[color] = score
            else:
                color_scores[color] += score

    if len(color_scores) > 0:
        best_color = sorted(color_scores.items(), key=lambda x: x[1], reverse=True)[0][0]
    else:
        best_color = CardColor.RED

    return best_color


def greedy_play_new(new_playable, **info):
        return True


class GreedyGetPlayPolicy(Policy):
    def __init__(self):
        super().__init__(name="default", atype=ActionType.GET_PLAY, strategy=greedy_get_play)


class GreedyGetColorPolicy(Policy):
    def __init__(self):
        super().__init__(name="default", atype=ActionType.GET_COLOR, strategy=greedy_get_color)


class GreedyPlayNewPolicy(Policy):
    def __init__(self):
        super().__init__(name="default", atype=ActionType.PLAY_NEW, strategy=greedy_play_new)
