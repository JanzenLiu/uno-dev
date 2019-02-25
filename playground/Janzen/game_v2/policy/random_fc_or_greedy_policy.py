from .base import Policy, ActionType
import random
from .greedy_policy import greedy_get_play, greedy_get_color
from .first_card_policy import first_card_get_play, first_card_get_color


def random_fc_or_greedy_get_play(playable_cards, **info):
    return random.choice(greedy_get_play, first_card_get_play)(playable_cards, **info)


def random_fc_or_greedy_get_color(**info):
    return random.choice(greedy_get_color, first_card_get_color)(**info)


def random_fc_or_greedy_play_new(new_playable, **info):
        return True


class RandomFCOrGreedyGetPlayPolicy(Policy):
    def __init__(self):
        super().__init__(name="default", atype=ActionType.GET_PLAY, strategy=random_fc_or_greedy_get_play)


class RandomFCOrGreedyGetColorPolicy(Policy):
    def __init__(self):
        super().__init__(name="default", atype=ActionType.GET_COLOR, strategy=random_fc_or_greedy_get_color)


class RandomFCOrGreedyPlayNewPolicy(Policy):
    def __init__(self):
        super().__init__(name="default", atype=ActionType.PLAY_NEW, strategy=random_fc_or_greedy_play_new)
