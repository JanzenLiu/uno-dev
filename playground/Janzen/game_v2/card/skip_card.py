from .base import CardType, WeakActionCard


class SkipCard(WeakActionCard):
    def __init__(self, color):
        super().__init__(CardType.SKIP, color)

    def is_skip(self):
        return True

    def _check_playable(self, current_color, current_value, current_type, current_to_draw):
        if current_to_draw > 0:
            return False
        else:
            return current_type == CardType.SKIP or self.color == current_color
