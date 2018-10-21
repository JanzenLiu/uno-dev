from .base import PlayerType, Player
from ..card import CardColor


class PCFirstCardPlayer(Player):
    def __init__(self, name, idx, stream=True, filename=None, save_rewards=False):
        super().__init__(PlayerType.PC_FIRST_CARD, name, idx,
                         stream=stream, filename=filename, save_rewards=save_rewards)

    def get_play_from_playable(self, playable_cards, **info):
        assert isinstance(playable_cards, list) and len(playable_cards) > 0
        return playable_cards[0]

    def _play_new_playable(self, new_playable, **info):
        return True

    def _get_color(self, **info):
        for card in self.cards:
            if card.color != CardColor.WILD:
                return card.color
        return CardColor.RED
