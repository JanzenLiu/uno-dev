from .base import Policy, ActionType
from ..card import Card, CardColor


# hybrid of greedy and first card
# greedily choose the card with the higher score in the first two cards
def first_two_greedy_get_play(playable_cards, **info):
    assert isinstance(playable_cards, list) and len(playable_cards) > 0
    if len(playable_cards) == 1:
        return playable_cards[0]

    _, first_card = playable_cards[0]
    _, second_card = playable_cards[1]
    assert isinstance(first_card, Card) and isinstance(second_card, Card)

    if first_card.score >= second_card.score:
        return playable_cards[0]
    else:
        return playable_cards[1]


def first_two_greedy_get_color(**info):
    color_scores = {}
    cards = info.get("cards", [])

    color_counter = 0
    for card in cards and color_counter < 2:
        if not card.is_strong_action():
            color = card.color
            score = card.score
            color_counter += 1
            if color not in color_scores:
                color_scores[color] = score
            else:
                color_scores[color] += score

    if len(color_scores) > 0:
        best_color = sorted(color_scores.items(), key=lambda x: x[1], reverse=True)[0][0]
    else:
        best_color = CardColor.RED

    return best_color


def first_two_greedy_play_new(new_playable, **info):
    return True


class FirstTwoGreedyGetPlayPolicy(Policy):
    def __init__(self):
        super().__init__(name="default", atype=ActionType.GET_PLAY, strategy=first_two_greedy_get_play)


class FirstTwoGreedyGetColorPolicy(Policy):
    def __init__(self):
        super().__init__(name="default", atype=ActionType.GET_COLOR, strategy=first_two_greedy_get_color)


class FirstTwoGreedyPlayNewPolicy(Policy):
    def __init__(self):
        super().__init__(name="default", atype=ActionType.PLAY_NEW, strategy=first_two_greedy_play_new)