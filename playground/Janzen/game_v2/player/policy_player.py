from .base import PlayerType, Player
from ..card import CardColor, Card
import pickle


class Policy(object):
    def __init__(self, name):
        assert isinstance(name, str) and len(name) > 0
        self.name = name

    def __repr__(self):
        return "{}()".format(type(self).__name__)

    def __str__(self):
        return "{}()".format(type(self).__name__)

    def get_play_from_playable(self, playable_cards, **info):
        # Returns best_index, best_card
        raise NotImplementedError

    def play_new_playable(self, new_playable, **info):
        # Returns True or False
        raise NotImplementedError

    def get_color(self, **info):
        # Return best_color
        raise NotImplementedError


class GreedyPolicy(Policy):
    def __init__(self, name):
        super().__init__(name)

    @staticmethod
    def get_play_from_playable(playable_cards, **info):
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

    @staticmethod
    def play_new_playable(new_playable, **info):
        return True

    @staticmethod
    def get_color(**info):
        color_scores = {}
        cards = info.get("cards", [])

        for card in cards:
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


class PolicyPlayer(Player):
    def __init__(self, name, idx, policy,
                 stream=True, filename=None,
                 save_rewards=False, save_actions=False):
        assert isinstance(policy, Policy)

        super().__init__(PlayerType.POLICY, name, idx,
                         stream=stream, filename=filename,
                         save_rewards=save_rewards, save_actions=save_actions)
        self.policy = policy

    def _get_play_from_playable(self, playable_cards, **info):
        return self.policy.get_play_from_playable(playable_cards, **info)

    def _play_new_playable(self, new_playable, **info):
        return self.policy.play_new_playable(new_playable, **info)

    def _get_color(self, **info):
        return self.policy.get_color(cards=self.cards, **info)
