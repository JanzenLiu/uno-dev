import numpy as np
import random
from .base import PlayerType, Player
from ..card import CardColor


class PCRandomPlayer(Player):
    def __init__(self, name, idx, play_draw=1.):
        assert (isinstance(play_draw, float) and 0 <= play_draw <= 1) or play_draw == 0 or play_draw == 1
        super().__init__(PlayerType.PC_RANDOM, name, idx)
        self.probs_for_draw = [float(play_draw), float(1 - play_draw)]

    def get_play_from_playable(self, playable_cards, **info):
        assert isinstance(playable_cards, list) and len(playable_cards) > 0
        print(playable_cards)
        return random.choice(playable_cards)

    def play_new_playable(self, new_playable, **info):
        return np.random.choice([True, False], p=self.probs_for_draw)

    def _get_color(self):
        return np.random.choice([CardColor.RED, CardColor.GREEN, CardColor.BLUE, CardColor.YELLOW])
