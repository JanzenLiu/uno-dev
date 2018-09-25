from .base import CardType, StrongActionCard


class DrawFourCard(StrongActionCard):
    def __init__(self):
        super().__init__(CardType.DRAW_4)

    def is_draw4(self):
        return True

    def is_draw_action(self):
        return True

    def _check_playable(self, current_color, current_value, current_type, current_to_draw):
        return True
