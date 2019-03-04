import numpy as np
import random
from .base import PlayerType, Player
from ..card import CardColor


class PCRandomPlayer(Player):
    def __init__(self, name, idx, play_draw=1., stream=True, filename=None, save_rewards=False):
        assert (isinstance(play_draw, float) and 0 <= play_draw <= 1) or play_draw == 0 or play_draw == 1
        super().__init__(PlayerType.PC_RANDOM, name, idx,
                         stream=stream, filename=filename, save_rewards=save_rewards)
        self.probs_for_draw = [float(play_draw), float(1 - play_draw)]

    def _get_play_from_playable(self, playable_cards, **info):
        num_rounds_played = info.get("num_rounds_played", -1)
        assert isinstance(playable_cards, list) and len(playable_cards) > 0
        return random.Random(num_rounds_played).choice(playable_cards)

    def _play_new_playable(self, new_playable, **info):
        return bool(np.random.choice([True, False], p=self.probs_for_draw))  # to unify type

    def _get_color(self, **info):
        num_rounds_played = info.get("num_rounds_played", -1)
        return random.Random(num_rounds_played).choice([CardColor.RED, CardColor.GREEN, CardColor.BLUE, CardColor.YELLOW])
