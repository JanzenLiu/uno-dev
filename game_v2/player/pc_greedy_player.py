from .base import PlayerType, Player
from ..card import CardColor, Card


class PCGreedyPlayer(Player):
    def __init__(self, name, idx, stream=True, filename=None, save_rewards=False, save_actions=False):
        super().__init__(PlayerType.PC_GREEDY, name, idx,
                         stream=stream, filename=filename,
                         save_rewards=save_rewards, save_actions=save_actions)

    def _get_play_from_playable(self, playable_cards, **info):
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

    def _play_new_playable(self, new_playable, **info):
        return True

    def _get_color(self, **info):
        color_scores = {}

        for card in self.cards:
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

        assert isinstance(best_color, CardColor)
        return best_color
