from .base import Controller
from .flow_controller import FlowController
from ..card import CardType, CardColor, Card, NumberCard
from ..player import Player


class StateController(Controller):
    def __init__(self, stream=True, filename=None):
        super().__init__(stream=stream, filename=filename)
        self.current_color = None
        self.current_value = None
        self.current_type = None
        self.current_to_draw = 0

    @property
    def state_dict(self):
        return {
            "color": self.current_color,
            "value": self.current_value,
            "type": self.current_type,
            "to_draw": self.current_to_draw
        }

    def format_attribute(self):
        color = self.current_color
        return ", ".join([
            "color={}".format(color(color) if isinstance(color, CardColor) else None),
            "value={}".format(self.current_value),
            "type={}".format(self.current_type),
            "to_draw={}".format(self.current_to_draw)
        ])

    def set_color(self, color):
        assert isinstance(color, CardColor)
        self.current_color = color

    def set_value(self, value):
        assert isinstance(value, int) and -1 <= value <= 9
        self.current_value = value

    def set_type(self, ctype):
        assert isinstance(ctype, CardType)
        self.current_type = ctype

    def clear_to_draw(self):
        self.current_to_draw = 0

    def add_to_draw(self, num):
        assert isinstance(num, int)
        self.current_to_draw += num

    def check_card_playable(self, card):
        assert isinstance(card, Card)
        return card.check_playable(self.current_color,
                                   self.current_value,
                                   self.current_type,
                                   self.current_to_draw)

    def check_new_card_playable(self, card, player):
        assert isinstance(player, Player)
        return player.check_new_card_playable(self.current_color,
                                              self.current_value,
                                              self.current_type,
                                              self.current_to_draw,
                                              card)

    def accept_card(self, card, player, flow_controller):
        assert isinstance(card, Card)
        assert isinstance(player, Player)
        assert isinstance(flow_controller, FlowController)

        new_color = card.color
        new_value = -1
        new_type = card.card_type
        new_to_draw = 0

        if card.is_number():
            assert isinstance(card, NumberCard)
            new_value = card.num

        elif card.is_reverse():
            flow_controller.reverse()

        elif card.is_skip():
            flow_controller.add_skip()

        elif card.is_wildcard():
            new_color = player.get_color(play_state=self.state_dict)
            assert isinstance(new_color, CardColor)

        elif card.is_draw2():
            assert self.current_to_draw == 0 or self.current_type == CardType.DRAW_2
            new_to_draw = self.current_to_draw + 2

        elif card.is_draw4():
            new_color = player.get_color(play_state=self.state_dict)
            new_to_draw = self.current_to_draw + 4
            assert isinstance(new_color, CardColor)
            # add log: color selected

        else:
            # raise Error
            raise Exception("Unknown Card Type Encountered while Applying State Change")

        self.current_color = new_color
        self.current_value = new_value
        self.current_type = new_type
        self.current_to_draw = new_to_draw
