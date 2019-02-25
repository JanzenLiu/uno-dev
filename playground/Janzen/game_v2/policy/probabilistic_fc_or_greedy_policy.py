from .base import Policy, ActionType
from numpy.random import choice
from .greedy_policy import greedy_get_play, greedy_get_color
from .first_card_policy import first_card_get_play, first_card_get_color


def probabilistic_fc_or_greedy_get_play(playable_cards, **info):
    fc_prob = info.get("fc_prob", 0.5)
    return choice([first_card_get_play, greedy_get_play], p=[fc_prob, 1-fc_prob])(playable_cards, **info)


def probabilistic_fc_or_greedy_get_color(**info):
    fc_prob = info.get("fc_prob", 0.5)
    return choice([first_card_get_color, greedy_get_color], p=[fc_prob, 1-fc_prob])(**info)


def probabilistic_fc_or_greedy_play_new(new_playable, **info):
    return True


class ProbabilisticFCOrGreedyGetPlayPolicy(Policy):
    def __init__(self, fc_prob=0.5):
        assert 0 <= fc_prob <= 1
        super().__init__(name="default", atype=ActionType.GET_PLAY, strategy=probabilistic_fc_or_greedy_get_play)
        self.fc_prob = fc_prob

    def _get_action(self, *args, **kwargs):
        return self.strategy(fc_prob=self.fc_prob, *args, **kwargs)

class ProbabilisticFCOrGreedyGetColorPolicy(Policy):
    def __init__(self, fc_prob=0.5):
        assert 0 <= fc_prob <= 1
        super().__init__(name="default", atype=ActionType.GET_COLOR, strategy=probabilistic_fc_or_greedy_get_color)
        self.fc_prob = fc_prob

    def _get_action(self, *args, **kwargs):
        return self.strategy(fc_prob=self.fc_prob, *args, **kwargs)


class ProbabilisticFCOrGreedyPlayNewPolicy(Policy):
    def __init__(self):
        super().__init__(name="default", atype=ActionType.PLAY_NEW, strategy=probabilistic_fc_or_greedy_play_new)
