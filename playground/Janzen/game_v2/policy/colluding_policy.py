from .base import Policy, ActionType
from .greedy_policy import greedy_get_play, greedy_get_color
from ..player import Player
from ..card import Card


# number card: 4 * (1 * 0 + 2 * (1 + 2 + 3 + 4 + 5 + 6 + 7 + 8 + 9)) = 360
# reverse card: 4 * 2 * 20 = 160
# skip card: 4 * 2 * 20 = 160
# draw2 card: 4 * 2 * 20 = 160
# draw4 card: 4 * 50 = 200
# wild card: 4 * 50 = 200
# sum = 360 + 160 + 160 + 160 + 200 + 200 = 1240
# therefore, score expectation of a card in a standard deck is 1240/108
_avg_score = 1240 / 108


# nc stands for neighbor collusion
def _default_nc_greedy_get_play(playable_cards, next_player_cards, num_cards_left, **info):
    assert isinstance(num_cards_left, int) and num_cards_left > 0
    assert isinstance(playable_cards, list) and len(playable_cards) > 0
    assert isinstance(next_player_cards, list) and len(next_player_cards) > 0

    # only one card left and it's playable, so just play it, and then the team will win
    if num_cards_left == 1:
        return playable_cards[0]

    best_play = None
    best_score = - 2 * _avg_score

    for index, card in playable_cards:
        assert isinstance(card, Card)
        if card.is_number():
            # this will be the best play if the partner has no valid cards to play
            best_play = index, card
            best_score = card.score - _avg_score

            # then see whether the partner has valid cards to play in actuality
            for next_card in next_player_cards:
                assert isinstance(next_card, Card)
                if next_card.check_playable(card.color, card.num, card.card_type, 0):
                    score = card.score + next_card.score
                    if score > best_score:
                        best_play = index, card
                        best_score = score

        elif card.is_reverse() or card.is_skip():
            if card.score > best_score:
                best_play = index, card
                best_score = card.score

        elif card.is_wildcard():
            best_next_score = max([next_card.score for next_card in next_player_cards])
            score = card.score + best_next_score
            if score > best_score:
                best_play = index, card
                best_score = score

        elif card.is_draw2():
            # expected reward = 20 - 2 * _avg_score > -_avg_score, so consider this case
            score = card.score - 2 * _avg_score
            if score > best_score:
                best_play = index, card
                best_score = score

        elif card.is_draw4():
            # expected reward = 50 - 4 * _avg_score > -_avg_score, so consider this case
            score = card.score - 4 * _avg_score
            if score > best_score:
                best_play = index, card
                best_score = score

        else:
            # raise Error
            raise Exception("Unknown Card Type Encountered while Getting Collusion Play")

    return best_play


def _default_nc_greedy_get_color(next_player_cards, **info):
    return greedy_get_color(cards=next_player_cards)


class ColludingPolicy(Policy):
    def __init__(self, name, atype, strategy):
        super().__init__(name, atype, strategy)
        self.players = set()

    def add_player(self, player):
        assert isinstance(player, Player) and player.is_policy()
        if not self.is_player_in(player):
            self.players.add(player)

    def add_players(self, players):
        for player in players:
            self.add_player(player)

    def is_player_in(self, player):
        assert isinstance(player, Player)
        return player in self.players

    @property
    def all_player_cards(self):
        return [(player, player.cards) for player in self.players]

    def is_colluding_policy(self):
        return True


class NeighborColludingGetPlay(ColludingPolicy):
    def __init__(self, name, strategy=_default_nc_greedy_get_play, solo_strategy=greedy_get_play):
        assert callable(solo_strategy)
        super().__init__(name, ActionType.GET_PLAY, strategy)
        self.solo_strategy = solo_strategy

    def _get_action(self, next_player=None, *args, **kwargs):
        assert isinstance(next_player, Player) or next_player is None
        if self.is_player_in(next_player):
            return self.strategy(next_player_cards=next_player.cards, *args, **kwargs)
        else:
            return self.solo_strategy(*args, **kwargs)


class NeighborColludingGetColor(ColludingPolicy):
    def __init__(self, name, strategy=_default_nc_greedy_get_color, solo_strategy=greedy_get_color):
        assert callable(solo_strategy)
        super().__init__(name, ActionType.GET_COLOR, strategy)
        self.solo_strategy = solo_strategy

    def _get_action(self, next_player=None, *args, **kwargs):
        assert isinstance(next_player, Player) or next_player is None
        if self.is_player_in(next_player):
            return self.strategy(next_player_cards=next_player.cards, *args, **kwargs)
        else:
            return self.solo_strategy(*args, **kwargs)
