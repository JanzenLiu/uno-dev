from .base import CardType, WeakActionCard


class DrawTwoCard(WeakActionCard):
    def __init__(self, color):
        super().__init__(CardType.DRAW_2, color)
        self.short_name = "D2({})".format(self.color.name[0])

    def is_draw2(self):
        return True

    def is_draw_action(self):
        return True

    def _check_playable(self, current_color, current_value, current_type, current_to_draw):
        if current_to_draw > 0:
            return current_type == CardType.DRAW_2
        else:
            return current_type == CardType.DRAW_2 or self.color == current_color
