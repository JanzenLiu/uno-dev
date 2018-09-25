from enum import Enum, unique
from .player import PlayerType, Player, HumanPlayer, PCNaivePlayer
from .card import Card, make_standard_deck
from .controller import ActionController
from .io import get_input, UnoLogger
from colorama import init
from colorama import Fore, Style


init()


@unique
class GameEndCondition(Enum):
    ROUND_1 = 1
    ROUND_3 = 2
    ROUND_5 = 3
    SCORE_200 = 4
    SCORE_500 = 5
    SCORE_1000 = 6

    @staticmethod
    def option_set():
        return set([option.value for option in GameEndCondition])

    @staticmethod
    def option_string():
        return "\n".join(["{}) {}".format(option.value, option.name) for option in GameEndCondition])


nplayers_input_msg = "Please Input a Number as the Number of Players: 2-10"
nplayers_input_err = "Sorry, Your Input is Invalid, Try Again."
ptype_input_msg = "Please Select Type of Player #{}, Input One Number from 1 to 2:\n" + PlayerType.option_string()
ptype_input_err = "Sorry, Your Input is Invalid, Try Again."
pname_input_msg = "Please Input the Name for Player #{} (Max Length: 20)"
pname_input_err = "Sorry, Your Input is Invalid, Try Again."


class Game(object):
    def __init__(self, cards=None, players=None, end_condition=GameEndCondition.ROUND_1, interval=1):
        assert isinstance(end_condition, GameEndCondition)
        assert isinstance(interval, (int, float)) or interval > 0
        # set logger
        self.logger = UnoLogger("{}{}{}".format(Fore.LIGHTMAGENTA_EX, "[Game]", Style.RESET_ALL))

        # set players
        self.num_players = 0
        self.players = []
        self._init_players(players)

        # set cards
        self.cards = []
        self._init_cards(cards)

        # set state
        self.num_rounds_played = 0

        # set controllers
        self.end_condition = end_condition
        self.interval = interval
        self.action_controller = None

    @staticmethod
    def get_num_players():
        return get_input(nplayers_input_msg,
                         nplayers_input_err,
                         parser=int,
                         checker=lambda x: 2 <= x <= 10)

    @staticmethod
    def get_player_type(index):
        msg = ptype_input_msg.format(index + 1)
        return get_input(msg,
                         ptype_input_err,
                         parser=int,
                         checker=lambda x: x in PlayerType.option_set(),
                         constructor=PlayerType)

    @staticmethod
    def get_player_name(index):
        msg = pname_input_msg.format(index + 1)
        return get_input(msg,
                         pname_input_err,
                         checker=lambda x: 0 < len(x) <= 20)

    @staticmethod
    def _init_player(player_type, player_name, i):
        assert isinstance(player_type, PlayerType)
        assert isinstance(player_name, str) and 0 < len(player_name) <= 20
        if player_type == PlayerType.HUMAN:
            player = HumanPlayer(player_name, i)
        elif player_type == PlayerType.PC_NAIVE:
            player = PCNaivePlayer(player_name, i)
        else:
            raise Exception("Unknown Player Type Encountered while Creating Player")

        return player

    def _init_players(self, players):
        self.players = []

        if isinstance(players, list):
            assert isinstance(players[0], tuple)
            assert 2 <= len(players) <= 10

            self.num_players = len(players)
            for i, tup in enumerate(players):
                player = Game._init_player(tup[0], tup[1], i)
                self.players.append(player)
                self.logger("Player created from list: {}".format(player))

        elif players is None or isinstance(players, int):
            if players is None:
                self.num_players = Game.get_num_players()
            else:
                assert 2 <= players <= 10
                self.num_players = players

            for i in range(self.num_players):
                player = Game._init_player(Game.get_player_type(i), Game.get_player_name(i), i)
                self.players.append(player)
                self.logger("Player created from input: {}".format(player))
        else:
            raise Exception("Unknown Players Config Encountered while Creating Game")

    def _init_cards(self, cards):
        if isinstance(cards, list):
            assert len(cards) > 0
            for card in cards:
                assert isinstance(card, Card)
            self.cards = cards
        elif cards is None:
            self.cards = make_standard_deck()
        elif isinstance(cards, int):
            assert 1 <= cards <= 2
            self.cards = []
            for _ in range(cards):
                self.cards += make_standard_deck()

    def _is_end_by_round(self, rounds):
        assert isinstance(rounds, int) and rounds > 0
        return self.num_rounds_played >= rounds

    def _is_end_by_score(self, max_score):
        assert isinstance(max_score, int) and max_score > 0
        for player in self.players:
            assert isinstance(player, Player)
            if player.cumulative_score >= max_score:
                return True
        return False

    def is_end(self):
        if self.end_condition == GameEndCondition.ROUND_1:
            return self._is_end_by_round(1)
        elif self.end_condition == GameEndCondition.ROUND_3:
            return self._is_end_by_round(3)
        elif self.end_condition == GameEndCondition.ROUND_5:
            return self._is_end_by_round(5)
        elif self.end_condition == GameEndCondition.SCORE_200:
            return self._is_end_by_score(200)
        elif self.end_condition == GameEndCondition.SCORE_500:
            return self._is_end_by_score(500)
        elif self.end_condition == GameEndCondition.SCORE_1000:
            return self._is_end_by_score(1000)
        else:
            raise Exception("Unknown End Condition Encountered while Checking Game End")

    def run(self):
        while not self.is_end():
            self.action_controller = ActionController(self.cards, self.players, interval=self.interval)
            self.action_controller.run()
            self.num_rounds_played += 1

        self.logger("Game Over after {} rounds".format(self.num_rounds_played))