from .base import Policy, ActionType
from .greedy_policy import greedy_get_play, greedy_get_color
from ..player import Player
from ..card import Card, CardColor
import random


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
    best_score = - 2 * _avg_score  # the case neither the current player and the partner play any cards

    for index, card in playable_cards:
        assert isinstance(card, Card)
        if card.is_number():
            # then see whether the partner has valid cards to play in actuality
            next_player_playable_cards = [(i, next_card) for i, next_card in enumerate(next_player_cards)
                                          if next_card.check_playable(card.color, card.num, card.card_type, 0)]
            filtered_best_next_score = get_best_score_from_raw_playable(next_player_playable_cards)
            score = card.score + filtered_best_next_score
            if score > best_score:
                best_play = index, card
                best_score = score

        elif card.is_reverse() or card.is_skip():
            # TODO: to refine
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


def _default_nnc_greedy_get_play(playable_cards, num_cards_left, next_partner_cards, **info):
    assert isinstance(num_cards_left, int) and num_cards_left > 0
    assert isinstance(playable_cards, list) and len(playable_cards) > 0
    assert isinstance(next_partner_cards, list) and len(next_partner_cards) > 0

    # only one card left and it's playable, so just play it, and then the team will win
    if num_cards_left    == 1:
        return playable_cards[0]

    best_play = None
    best_score = - 2 * _avg_score  # the case neither the current player and the partner play any cards

    for index, card in playable_cards:
        assert isinstance(card, Card)
        if card.is_number() or card.is_reverse() or card.is_skip() or card.is_draw2():
            # then see whether the partner has valid cards to play in actuality
            # for non-neighboring case, simply checking color is enough
            next_partner_playable_cards = [(i, next_card) for i, next_card in enumerate(next_partner_cards)
                                           if next_card.color == card.color or next_card.is_strong_action()]
            filtered_best_next_score = get_best_score_from_raw_playable(next_partner_playable_cards)
            score = card.score + filtered_best_next_score
            if score > best_score:
                best_play = index, card
                best_score = score

        elif card.is_wildcard() or card.is_draw4():
            next_partner_cards_with_index = [(i, next_card) for i, next_card in enumerate(next_partner_cards)]
            filtered_best_next_score = get_best_score_from_raw_playable(next_partner_cards_with_index)
            score = card.score + filtered_best_next_score
            if score > best_score:
                best_play = index, card
                best_score = score

        else:
            # raise Error
            raise Exception("Unknown Card Type Encountered while Getting Collusion Play")

    # if current player does not play a card, and next player plays the card with highest score
    if "play_state" in info:
        play_state = info["play_state"]
        next_partner_playable_cards = [(i, next_card) for i, next_card in enumerate(next_partner_cards)
                                       if next_card.color == play_state["color"] or next_card.is_strong_action()]
        filtered_best_next_score = get_best_score_from_raw_playable(next_partner_playable_cards)
        if -_avg_score + filtered_best_next_score > best_score:
            best_play = None
    return best_play


def _default_nnc_greedy_get_color(next_partner_cards, **info):
    return greedy_get_color(cards=next_partner_cards)


# ====================
# first card collusion
# ====================
def _default_nc_first_card_get_play(playable_cards, next_player_cards, num_cards_left, **info):
    assert isinstance(num_cards_left, int) and num_cards_left > 0
    assert isinstance(playable_cards, list) and len(playable_cards) > 0
    assert isinstance(next_player_cards, list) and len(next_player_cards) > 0

    # only one card left and it's playable, so just play it, and then the team will win
    if num_cards_left == 1:
        return playable_cards[0]

    selected_play = None
    for index, card in playable_cards:
        assert isinstance(card, Card)
        # confirm whether next player can also play if this current card is played
        if card.is_number():
            next_player_playable_cards = [(i, next_card) for i, next_card in enumerate(next_player_cards)
                                          if next_card.check_playable(card.color, card.num, card.card_type, 0)]
            filtered_next_playable_cards = Player.filter_draw_four(next_player_playable_cards)
            if len(filtered_next_playable_cards) > 0:
                selected_play = index, card
                break

        elif card.is_wildcard():
            selected_play = index, card
            break

    if selected_play is None:
        # No card can allow next player to play too
        selected_play = playable_cards[0]

    return selected_play


def _default_nc_first_card_get_color(next_player_cards, **info):
    current_player_cards = info.get("cards", [])
    current_first_color = None
    colluding_first_color = None
    for card in current_player_cards:
        if card.color != CardColor.WILD:
            if current_first_color is not None:
                current_first_color = card.color
            # TODO: refactor
            if card.is_number():
                # only number cards in this case allow next player to play
                next_player_playable_cards = [(i, next_card) for i, next_card in enumerate(next_player_cards)
                                              if next_card.check_playable(card.color, card.num, card.card_type, 0)]
                filtered_next_playable_cards = Player.filter_draw_four(next_player_playable_cards)
                if len(filtered_next_playable_cards) > 0:
                    colluding_first_color = card.color
                    break

    if colluding_first_color is not None:
        return colluding_first_color
    elif current_first_color is not None:
        return current_first_color
    else:
        return CardColor.RED


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

    def get_partner(self, exclude=None):
        assert isinstance(exclude, Player) or exclude is None
        return [player for player in self.players if player != exclude]

    @staticmethod
    def keep_by_probability(next_player_cards, info_probability):
        # helper function to adjust knowledge accessible by partner
        # order of cards need to be preserved
        total_num = len(next_player_cards)
        kept_num = round(total_num * info_probability)
        target_indices = random.sample(range(total_num), kept_num)
        target_indices.sort()
        available_cards = list(map(next_player_cards.__getitem__, target_indices))
        return available_cards


class NeighborColludingGetPlay(ColludingPolicy):
    def __init__(self, name, strategy=_default_nc_greedy_get_play,
                 nn_strategy=_default_nnc_greedy_get_play, info_probability=1):
        # nn stands for non-neighbor
        assert callable(nn_strategy)
        super().__init__(name, ActionType.GET_PLAY, strategy)
        self.nn_strategy = nn_strategy
        self.info_probability = info_probability  # if 1, full knowledge

    def _get_action(self, current_player=None, next_player=None, *args, **kwargs):
        assert isinstance(current_player, Player) or current_player is None
        assert isinstance(next_player, Player) or next_player is None
        available_next_player_cards = ColludingPolicy.keep_by_probability(next_player.cards, self.info_probability)
        if self.is_player_in(next_player) and len(available_next_player_cards) > 0:
            return self.strategy(next_player_cards=available_next_player_cards, *args, **kwargs)
        else:
            # assume only two colluding players so far, so only one partner
            partner = list(self.get_partner(exclude=current_player))[0]
            return self.nn_strategy(next_partner_cards=partner.cards, *args, **kwargs)


class NeighborColludingGetColor(ColludingPolicy):
    def __init__(self, name, strategy=_default_nc_greedy_get_color,
                 nn_strategy=_default_nnc_greedy_get_color, info_probability=1):
        assert callable(nn_strategy)
        super().__init__(name, ActionType.GET_COLOR, strategy)
        self.nn_strategy = nn_strategy
        self.info_probability = info_probability  # if 1, full knowledge

    def _get_action(self, current_player=None, next_player=None, *args, **kwargs):
        assert isinstance(current_player, Player) or current_player is None
        assert isinstance(next_player, Player) or next_player is None
        available_next_player_cards = ColludingPolicy.keep_by_probability(next_player.cards, self.info_probability)
        if self.is_player_in(next_player) and len(available_next_player_cards) > 0:
            return self.strategy(next_player_cards=available_next_player_cards, *args, **kwargs)
        else:
            # assume only two colluding players so far, so only one partner
            partner = list(self.get_partner(exclude=current_player))[0]
            return self.nn_strategy(next_partner_cards=partner.cards, *args, **kwargs)
