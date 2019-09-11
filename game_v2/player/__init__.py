from .base import PlayerType, Player
from .human_player import HumanPlayer
from .pc_first_card_player import PCFirstCardPlayer
from .pc_random_player import PCRandomPlayer
from .pc_greedy_player import PCGreedyPlayer
from .policy_player import PolicyPlayer


def construct_player(player_type, *args, **kwargs):
    assert isinstance(player_type, PlayerType)
    if player_type == PlayerType.HUMAN:
        player = HumanPlayer(*args, **kwargs)
    elif player_type == PlayerType.PC_FIRST_CARD:
        player = PCFirstCardPlayer(*args, **kwargs)
    elif player_type == PlayerType.PC_RANDOM:
        player = PCRandomPlayer(*args, **kwargs)
    elif player_type == PlayerType.PC_GREEDY:
        player = PCGreedyPlayer(*args, **kwargs)
    elif player_type == PlayerType.POLICY:
        player = PolicyPlayer(*args, **kwargs)
    else:
        raise Exception("Unknown Player Type Encountered while Creating Player")

    return player
