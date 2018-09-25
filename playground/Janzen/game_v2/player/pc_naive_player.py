from .base import PlayerType, Player
from ..card import CardColor


class PCNaivePlayer(Player):
    def __init__(self, name, idx):
        super().__init__(PlayerType.PC_NAIVE, name, idx)

    def get_play_from_playable(self, playable_cards, **info):
        assert isinstance(playable_cards, list) and len(playable_cards) > 0
        return playable_cards[0]

    def play_new_playable(self, new_playable, **info):
        return True

    def _get_color(self):
        for card in self.cards:
            if card.color != CardColor.WILD:
                return card.color
        return CardColor.RED
