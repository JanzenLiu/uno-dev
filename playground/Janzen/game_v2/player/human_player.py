from .base import PlayerType, Player
from ..io import get_input
from ..card import CardColor, Card


card_input_msg = "Please Select a Card to Play, Input one of the given Number as Your Choice:\n"
card_input_err = "Sorry, Your Input is Invalid, Try Again."
instant_play_msg = "The New Card is Playable, Do You Want to Play it Immediately? (y/n)\n"
instant_play_err = "Sorry, Your Input is Invalid, Try Again."
color_input_msg = "\n".join(["Please Select Color, Input One Number from 1 to 4:", CardColor.option_string()])
color_input_err = "Sorry, Your Input is Invalid, Try Again."


class HumanPlayer(Player):
    def __init__(self, name, idx, stream=True, filename=None, save_rewards=False):
        super().__init__(PlayerType.HUMAN, name, idx,
                         stream=stream, filename=filename, save_rewards=save_rewards)

    def is_human(self):
        return True

    def get_play_from_playable(self, playable_cards, **info):
        assert isinstance(playable_cards, list) and len(playable_cards) > 0
        choice_dict = {index: card for index, card in playable_cards}
        choice_set = choice_dict.keys()
        choice_msg = ["-1) Not Play"]
        choice_msg += ["{})  {}".format(index, card) for index, card in playable_cards]
        choice_msg.append("# Your current cards: {}, total: {}".format(self.cards, self.num_cards))
        msg = "{}{}".format(card_input_msg, "\n".join(choice_msg))

        return get_input(msg,
                         card_input_err,
                         parser=int,
                         checker=lambda x: x in choice_set or x == -1,
                         constructor=lambda x: None if x == -1 else (x, choice_dict[x]))

    def play_new_playable(self, new_playable, **info):
        assert isinstance(new_playable, Card)
        msg = "{}y) Yes, Play {}\nn) No".format(instant_play_msg, new_playable)

        return get_input(msg,
                         instant_play_err,
                         checker=lambda x: x == 'y' or x == 'n',
                         constructor=lambda x: x == 'y')

    def _get_color(self):
        msg = "{}\n{}".format(color_input_msg,
                              "# Your current cards: {}, total: {}".format(self.cards, self.num_cards))
        return get_input(msg,
                         color_input_err,
                         parser=int,
                         checker=lambda x: 1 <= x <= 4,
                         constructor=CardColor)
