from .base import CardType, WeakActionCard


class ReverseCard(WeakActionCard):
    def __init__(self, color):
        super().__init__(CardType.REVERSE, color)
        self.short_name = "R({})".format(self.color.name[0])

    def is_reverse(self):
        return True

    def _check_playable(self, current_color, current_value, current_type, current_to_draw):
        if current_to_draw > 0:
            return False
        else:
            return current_type == CardType.REVERSE or self.color == current_color
