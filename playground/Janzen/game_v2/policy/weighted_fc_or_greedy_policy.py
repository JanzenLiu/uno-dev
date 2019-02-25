from .base import Policy, ActionType
from ..card import Card, CardColor
import numpy as np


# a new weighted scoring scheme to combine FirstCard and Greedy
# alpha * FC + (1 - alpha) * Greedy
# temporary method:
# current restriction: sum of all FC scores and sum of all Greedy scores equal
# FC scores is an arithmetic progression
# alternative method:
# use ranks to replace scores then weight them
def weighted_fc_or_greedy_get_play(playable_cards, **info):
    assert isinstance(playable_cards, list) and len(playable_cards) > 0
    fc_weight = info.get("fc_weight", 0.5)

    weighted_scores = []
    score_sum = 0
    card_num = len(playable_cards)
    for index, card in playable_cards:
        assert isinstance(card, Card)
        weighted_scores.append((1 - fc_weight) * card.score)
        score_sum += card.score

    common_difference = (2 * score_sum / (card_num * (card_num - 1)) if card_num > 1 else 0)
    for score_index, weighted_score in enumerate(weighted_scores):
        weighted_scores[score_index] = (weighted_score + fc_weight * (card_num - 1 - score_index) * common_difference)

    best_index = int(np.argmax(weighted_scores))
    return playable_cards[best_index]


def weighted_fc_or_greedy_get_color(**info):
    weighted_color_scores = {}
    cards = info.get("cards", [])
    fc_weight = info.get("fc_weight", 0.5)

    score_sum = 0
    color_card_num = 0
    for card in cards:
        if not card.is_strong_action():
            score_sum += card.score
            color_card_num += 1

    common_difference = (2 * score_sum / (color_card_num * (color_card_num - 1)) if color_card_num > 1 else 0)
    color_card_index = 0
    for card in cards:
        if not card.is_strong_action():
            color = card.color
            greedy_score = card.score * (1 - fc_weight)
            fc_score = (color_card_num - 1 - color_card_index) * common_difference * fc_weight
            weighted_score = (greedy_score + fc_score)
            if color not in weighted_color_scores:
                weighted_color_scores[color] = weighted_score
            else:
                weighted_color_scores[color] += weighted_score
            color_card_index += 1

    if len(weighted_color_scores) > 0:
        best_color = sorted(weighted_color_scores.items(), key=lambda x: x[1], reverse=True)[0][0]
    else:
        best_color = CardColor.RED

    return best_color


def weighted_fc_or_greedy_play_new(new_playable, **info):
    return True


class WeightedFCOrGreedyGetPlayPolicy(Policy):
    def __init__(self, fc_weight=0.5):
        assert 0 <= fc_weight <= 1
        super().__init__(name="default", atype=ActionType.GET_PLAY, strategy=weighted_fc_or_greedy_get_play)
        self.fc_weight = fc_weight

    def _get_action(self, *args, **kwargs):
        return self.strategy(fc_weight=self.fc_weight, *args, **kwargs)


class WeightedFCOrGreedyGetColorPolicy(Policy):
    def __init__(self, fc_weight=0.5):
        assert 0 <= fc_weight <= 1
        super().__init__(name="default", atype=ActionType.GET_COLOR, strategy=weighted_fc_or_greedy_get_color)
        self.fc_weight = fc_weight

    def _get_action(self, *args, **kwargs):
        return self.strategy(fc_weight=self.fc_weight, *args, **kwargs)


class WeightedFCOrGreedyPlayNewPolicy(Policy):
    def __init__(self):
        super().__init__(name="default", atype=ActionType.PLAY_NEW, strategy=weighted_fc_or_greedy_play_new)


