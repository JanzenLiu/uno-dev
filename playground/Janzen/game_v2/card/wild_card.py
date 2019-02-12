from .base import CardType, StrongActionCard


class WildCard(StrongActionCard):
    def __init__(self):
        super().__init__(CardType.WILDCARD)
        self.short_name = "W()"

    def is_wildcard(self):
        return True

    def _check_playable(self, current_color, current_value, current_type, current_to_draw):
        return current_to_draw == 0
