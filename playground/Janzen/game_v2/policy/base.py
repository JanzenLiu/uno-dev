from ..card import Card, CardColor
from enum import Enum, unique
import functools


@unique
class ActionType(Enum):
    GET_PLAY = 1
    GET_COLOR = 2
    PLAY_NEW = 3

    @staticmethod
    def from_string(string):
        assert isinstance(string, str)
        return ActionType[string.upper()]

    @staticmethod
    def option_set():
        return set([option.value for option in ActionType])

    @staticmethod
    def option_string():
        return "\n".join(["{}) {}".format(option.value, option.name) for option in ActionType])


class Policy(object):
    def __init__(self, name, atype, strategy):
        assert isinstance(name, str) and len(name) > 0
        assert callable(strategy)

        # init name
        self.name = name

        # init type
        self.atype = None  # to mute IDE warning
        self.check_action = None  # to mute IDE warning
        self.init_action_type(atype)

        # init strategy
        self.strategy = strategy

    def __repr__(self):
        return "{}()".format(type(self).__name__)

    def __str__(self):
        return "{}()".format(type(self).__name__)

    @staticmethod
    def _check_get_play_action(action):
        assert isinstance(action, tuple) and len(action) == 2
        assert isinstance(action[0], int) and action[0] >= 0
        assert isinstance(action[1], Card)

    @staticmethod
    def _check_get_color_action(action):
        assert isinstance(action, CardColor)

    @staticmethod
    def _check_play_new_action(action):
        assert isinstance(action, bool)

    def init_action_type(self, atype):
        # set action type
        if isinstance(atype, ActionType):
            self.atype = atype
        elif isinstance(atype, int):
            self.atype = ActionType(atype)
        elif isinstance(atype, str):
            self.atype = ActionType.from_string(atype)
        else:
            raise Exception("Unknown ActionType for Policy: {}. Valid ActionType: {}".format(
                atype, ActionType.option_string()))

        # set checker
        if self.atype == ActionType.GET_PLAY:
            self.check_action = Policy._check_get_play_action
        elif self.atype == ActionType.GET_COLOR:
            self.check_action = Policy._check_get_color_action
        elif self.atype == ActionType.PLAY_NEW:
            self.check_action = Policy._check_play_new_action
        else:
            raise Exception("Unknown ActionType for Policy: {}. Valid ActionType: {}".format(
                atype, ActionType.option_string()))

    def _get_action(self, *args, **kwargs):
        return self.strategy(*args, **kwargs)

    def get_action(self, *args, **kwargs):
        action = self._get_action(*args, **kwargs)
        self.check_action(action)
        return action


class ModelPolicy(Policy):
    def __init__(self, name, atype, model, strategy, classmap=None):
        assert classmap is None or isinstance(classmap, dict)
        super().__init__(name, atype, strategy)
        self.model = None  # to mute IDE warning
        self.classmap = None  # to mute IDE warning
        self.init_model(model, classmap)
        self.fix_param()

    def init_model(self, model, classmap):
        raise NotImplementedError

    def fix_param(self):
        self.strategy = functools.partial(self.strategy, model=self.model, classmap=self.classmap)
