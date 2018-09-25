from .base import PlayerType, Player
from .human_player import HumanPlayer
from .pc_first_card_player import PCFirstCardPlayer


def construct_player(player_type, *args, **kwargs):
    assert isinstance(player_type, PlayerType)
    if player_type == PlayerType.HUMAN:
        player = HumanPlayer(*args, **kwargs)
    elif player_type == PlayerType.PC_FIRST_CARD:
        player = PCFirstCardPlayer(*args, **kwargs)
    else:
        raise Exception("Unknown Player Type Encountered while Creating Player")

    return player
