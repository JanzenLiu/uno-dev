import random
from .base import PlayerType, Player
from ..card import CardColor


class PCRandomPlayer(Player):
    def __init__(self, name, idx):
        super().__init__(PlayerType.PC_RANDOM, name, idx)

    def get_play_from_playable(self, playable_cards, **info):
        assert isinstance(playable_cards, list) and len(playable_cards) > 0
        return random.choice(playable_cards)

    def play_new_playable(self, new_playable, **info):
        return random.choice([True, False])

    def _get_color(self):
        return random.choice([CardColor.RED, CardColor.GREEN, CardColor.BLUE, CardColor.YELLOW])
