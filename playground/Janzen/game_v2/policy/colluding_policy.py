from .base import Policy, ActionType
import functools

class ColludingPolicy(Policy):
    colluding_players = []

    def __init__(self, name, atype, strategy):
        super().__init__(name, atype, strategy)

    @classmethod
    def add_player_to_colluding(cls, player):
        cls.colluding_players.append(player)

    @classmethod
    def get_all_colluding_cards(cls):
        cards = {}
        for player in cls.colluding_players:
            cards[player.idx] = player.cards
        return cards

    def _get_action(self, *args, **kwargs):
        colluding_cards = ColludingPolicy.get_all_colluding_cards()
        strategy = functools.partial(self.strategy, colluding_cards=colluding_cards)
        return strategy(*args, **kwargs)

    def is_colluding_policy(self):
        return True
