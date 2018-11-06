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


def get_best_score_from_raw_playable(raw_playable_cards):
    filtered_playable_cards = Player.filter_draw_four(raw_playable_cards)
    filtered_best_score = -_avg_score  # no card can be played
    if len(filtered_playable_cards) > 0:
        filtered_best_score = max([card.score for index, card in filtered_playable_cards])
    return filtered_best_score


# nc stands for neighbor collusion
# ================
# greedy collusion
# ================
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
            next_player_playable_cards = [(i, next_card) for i, next_card in enumerate(next_player_cards)
                                          if next_card.check_playable(card.color, card.num, card.card_type, 0)]
            filtered_best_next_score = get_best_score_from_raw_playable(next_player_playable_cards)
            score = card.score + filtered_best_next_score
            if score > best_score:
                best_play = index, card
                best_score = score

        elif card.is_reverse() or card.is_skip():
            if card.score > best_score:
                best_play = index, card
                best_score = card.score

        elif card.is_wildcard():
            next_player_cards_with_index = [(i, next_card) for i, next_card in enumerate(next_player_cards)]
            filtered_best_next_score = get_best_score_from_raw_playable(next_player_cards_with_index)
            score = card.score + filtered_best_next_score
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

    # if current player does not play a card, and next player plays the card with highest score
    if "play_state" in info:
        play_state = info["play_state"]
        next_player_playable_cards = [(i, next_card) for i, next_card in enumerate(next_player_cards)
                                      if next_card.check_playable(play_state["color"], play_state["value"],
                                                                  play_state["type"], play_state["to_draw"])]
        filtered_best_next_score = get_best_score_from_raw_playable(next_player_playable_cards)
        if -_avg_score + filtered_best_next_score > best_score:
            best_play = None
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
