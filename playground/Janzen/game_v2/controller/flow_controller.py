from .base import Controller
from ..player import Player


# Adapted from https://gist.github.com/nichochar/87e18f9eb72f114853eb
class Node(object):
    def __init__(self, next_node=None, prev_node=None, data=None):
        super().__init__()
        self.next_node = next_node
        self.prev_node = prev_node
        self.data = data

    def __repr__(self):
        return "Node({})".format(self.data)

    def __str__(self):
        return "Node({})".format(self.data)


class LinkedList(object):
    def __init__(self, lst):
        self.first_node = node = Node(data=lst[0])
        for elem in lst[1:-1]:
            new_node = Node(prev_node=node, data=elem)
            node.next_node = new_node
            node = new_node
        self.last_node = Node(next_node=self.first_node, prev_node=node, data=lst[-1])
        self.first_node.prev_node = self.last_node
        node.next_node = self.last_node


class FlowController(Controller):
    def __init__(self, players, clockwise=True):
        for player in players:
            assert isinstance(player, Player)
        super().__init__()
        self.num_players = len(players)
        self.player_loop = LinkedList(players)
        self.current_player_node = self.player_loop.first_node
        self.current_player = self.current_player_node.data
        self.clockwise = clockwise
        self.skip = -1

    def format_attribute(self):
        return ", ".join([
            "num_players={}".format(self.num_players),
            "clockwise={}".format(self.clockwise),
            "skip={}".format(self.skip),
            "current_player={}".format(self.current_player)
        ])

    def reverse(self):
        if self.num_players == 2:
            self.add_skip(1)
        else:
            self.clockwise = not self.clockwise

    def clear_skip(self):
        self.skip = 0

    def set_skip(self, num):
        assert isinstance(num, int) and num >= 0
        self.skip = num

    def add_skip(self, num=1):
        assert isinstance(num, int) and num > 0
        self.skip += num

    def to_next_player(self, skip=None):
        if skip is None:
            skip = self.skip

        assert isinstance(skip, int) and skip >= -1
        for i in range(skip + 1):
            if self.clockwise:
                self.current_player_node = self.current_player_node.next_node
            else:
                self.current_player_node = self.current_player_node.prev_node
        self.current_player = self.current_player_node.data
        self.clear_skip()

    def is_player_done(self, player=None):
        if player is None:
            player = self.current_player
        assert isinstance(player, Player)
        return player.is_done()
