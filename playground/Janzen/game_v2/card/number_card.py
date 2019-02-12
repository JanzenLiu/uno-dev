from .base import CardType, CardColor, Card


class NumberCard(Card):
    def __init__(self, color, num):
        assert color != CardColor.WILD
        assert isinstance(num, int) and 0 <= num <= 9
        super().__init__(CardType.NUMBER, color, num)
        self.num = num
        self.short_name = "N({}{})".format(self.color.name[0], self.num)

    def format_attribute(self):
        return "{}, {}".format(self.color.name, self.num)

    def is_number(self):
        return True

    def _check_playable(self, current_color, current_value, current_type, current_to_draw):
        if current_to_draw > 0:
            return False
        else:
            return self.color == current_color or self.num == current_value
