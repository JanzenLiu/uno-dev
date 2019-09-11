from .base import Policy, ActionType
from .greedy_policy import GreedyGetPlayPolicy, GreedyGetColorPolicy, GreedyPlayNewPolicy
from .lr_policy import LRPolicy
from .keras_policy import KerasPolicy
from .colluding_policy import ColludingPolicy, NeighborColludingGetPlay, NeighborColludingGetColor
from .first_card_policy import FirstCardGetPlayPolicy, FirstCardGetColorPolicy, FirstCardPlayNewPolicy
from .first_two_greedy_policy import FirstTwoGreedyGetPlayPolicy, FirstTwoGreedyGetColorPolicy, FirstTwoGreedyPlayNewPolicy
from .probabilistic_fc_or_greedy_policy import ProbabilisticFCOrGreedyGetPlayPolicy, ProbabilisticFCOrGreedyGetColorPolicy, ProbabilisticFCOrGreedyPlayNewPolicy
from .weighted_fc_or_greedy_policy import WeightedFCOrGreedyGetPlayPolicy, WeightedFCOrGreedyGetColorPolicy, WeightedFCOrGreedyPlayNewPolicy