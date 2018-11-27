from .base import Policy, ActionType
from .greedy_policy import GreedyGetPlayPolicy, GreedyGetColorPolicy, GreedyPlayNewPolicy
from .lr_policy import LRPolicy
# from .keras_policy import KerasPolicy
from .colluding_policy import ColludingPolicy, NeighborColludingGetPlay, NeighborColludingGetColor
from .first_card_policy import FirstCardGetPlayPolicy, FirstCardGetColorPolicy, FirstCardPlayNewPolicy
