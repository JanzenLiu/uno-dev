from .base import PlayerType, Player
from ..policy import ActionType, Policy, GreedyGetPlayPolicy, GreedyGetColorPolicy, GreedyPlayNewPolicy, ColludingPolicy


class PolicyPlayer(Player):
    def __init__(self, name, idx,
                 get_play=GreedyGetPlayPolicy(),
                 get_color=GreedyGetColorPolicy(),
                 play_new=GreedyPlayNewPolicy(),
                 stream=True, filename=None,
                 save_rewards=False, save_actions=False):
        assert isinstance(get_play, Policy) and get_play.atype == ActionType.GET_PLAY
        assert isinstance(get_color, Policy) and get_color.atype == ActionType.GET_COLOR
        assert isinstance(play_new, Policy) and play_new.atype == ActionType.PLAY_NEW

        super().__init__(PlayerType.POLICY, name, idx,
                         stream=stream, filename=filename,
                         save_rewards=save_rewards, save_actions=save_actions)
        self.get_play_policy = get_play
        self.get_color_policy = get_color
        self.play_new_policy = play_new

        if get_play.is_colluding_policy():
            assert isinstance(get_play, ColludingPolicy)
            get_play.add_player(self)

        if get_color.is_colluding_policy():
            assert isinstance(get_color, ColludingPolicy)
            get_color.add_player(self)

        if play_new.is_colluding_policy():
            assert isinstance(play_new, ColludingPolicy)
            play_new.add_player(self)

    def format_attribute(self, show_cards=False):
        attr_strings = [
            "name={}".format(self.name),
            "pos={}".format(self.idx),
            "cumulative_loss={}".format(self.cumulative_loss),
            "cumulative_reward={}".format(self.cumulative_reward),
            "num_cards={}".format(self.num_cards),
            "get_play_policy={}".format(self.get_play_policy),
            "get_color_policy={}".format(self.get_color_policy),
            "play_new_policy={}".format(self.play_new_policy)
        ]
        if show_cards:
            attr_strings.append("cards={}".format(self.cards))
        return ", ".join(attr_strings)

    def format_policy(self):
        policy_strings = [
            "get_play_policy={}".format(self.get_play_policy),
            "get_color_policy={}".format(self.get_color_policy),
            "play_new_policy={}".format(self.play_new_policy)
        ]
        return ", ".join(policy_strings)

    def _get_play_from_playable(self, playable_cards, **info):
        return self.get_play_policy.get_action(playable_cards=playable_cards,
                                               num_cards_left=self.num_cards,
                                               current_player=self,
                                               **info)

    def _play_new_playable(self, new_playable, **info):
        return self.play_new_policy.get_action(new_playable=new_playable, current_player=self, **info)

    def _get_color(self, **info):
        return self.get_color_policy.get_action(cards=self.cards, current_player=self, **info)

    def is_policy(self):
        return True
