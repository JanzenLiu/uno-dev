
# coding: utf-8

# In[1]:


from enum import Enum, unique
import itertools
import random
from colorama import init
from colorama import Fore, Back, Style

init()


# TODO: put into OutputController
Colormap = {
    'r': Fore.RED,
    'g': Fore.GREEN,
    'b': Fore.BLUE,
    'y': Fore.YELLOW,
    'w': Fore.BLACK + Back.WHITE,
}
def colored(content, color='w'):
    color = color.lower()
    assert color in list(Colormap.keys())
    return Colormap[color] + content + Style.RESET_ALL


def add_label(obj, content):
    basename = type(obj).__bases__[0].__name__
    classname = type(obj).__name__ if basename == 'object' else basename
    return '[{}] {}'.format(classname, content)


@unique
class CardType(Enum):
    ABSTRACT = -1  # just a conceptual type
    NUMBER = 0
    REVERSE = 1
    SKIP = 2
    WILDCARD = 3
    DRAW_2 = 4
    DRAW_4 = 5


@unique
class CardColor(Enum):
    WILD = 0  # just a conceptual type
    RED = 1
    GREEN = 2
    BLUE = 3
    YELLOW = 4


# TODO: to seperate out a card checker class
class Card(object):
    # TODO: add format_property methods, and unify __repr__ method
    # TODO: rename property card_type to type
    def __init__(self, card_type, color):
        self.card_type = card_type
        self.color = color

    def __repr__(self):
        if self.is_number():
            return colored("{}({}, {})".format(type(self).__name__, self.color.name, self.num), self.color.name[0])
        elif self.is_weak_action():
            return colored("{}({})".format(type(self).__name__, self.color.name), self.color.name[0])
        else:
            return colored("{}()".format(type(self).__name__))


    # =============
    # Type Checkers
    # =============
    def is_number(self):
        return self.card_type == CardType.NUMBER

    def is_reverse(self):
        return self.card_type == CardType.REVERSE

    def is_skip(self):
        return self.card_type == CardType.SKIP

    def is_wildcard(self):
        return self.card_type == CardType.WILDCARD

    def is_draw2(self):
        return self.card_type == CardType.DRAW_2

    def is_draw4(self):
        return self.card_type == CardType.DRAW_4

    def is_action(self):
        return self.card_type != CardType.NUMBER

    def is_weak_action(self):
        # TODO: to use type checking instead
        return self.card_type == CardType.REVERSE or \
               self.card_type == CardType.SKIP or \
               self.card_type == CardType.DRAW_2

    def is_strong_action(self):
        # TODO: to use type checking instead
        return self.card_type == CardType.WILDCARD or self.card_type == CardType.DRAW_4

    def is_draw_action(self):
        return self.card_type == CardType.DRAW_2 or self.card_type == CardType.DRAW_4


class NumberCard(Card):
    def __init__(self, color, num):
        assert isinstance(color, CardColor) and color != CardColor.WILD  # might be extended?
        assert isinstance(num, int) and 0 <= num <= 9

        super().__init__(CardType.NUMBER, color)
        self.num = num


class WeakActionCard(Card):
    def __init__(self, card_type, color):
        assert isinstance(card_type, CardType)  # to refine
        assert isinstance(color, CardColor) and color != CardColor.WILD  # might be extended?

        super().__init__(card_type, color)


class ReverseCard(WeakActionCard):
    def __init__(self, color):
        super().__init__(CardType.REVERSE, color)


class SkipCard(WeakActionCard):
    def __init__(self, color):
        super().__init__(CardType.SKIP, color)


class DrawTwoCard(WeakActionCard):
    def __init__(self, color):
        super().__init__(CardType.DRAW_2, color)


class StrongActionCard(Card):
    def __init__(self, card_type):
        assert isinstance(card_type, CardType)  # to refine

        super().__init__(card_type, CardColor.WILD)


class WildCard(StrongActionCard):
    def __init__(self):
        super().__init__(CardType.WILDCARD)


class DrawFourCard(StrongActionCard):
    def __init__(self):
        super().__init__(CardType.DRAW_4)


color_input_msg = "Please Select Color, Input One Number from 1 to 4:\n1)RED 2)GREEN 3)BLUE 4)YELLOW"
color_input_err = "Sorry, Your Input is Invalid, Try Again."


def get_color_input():
        while True:
            try:
                print(color_input_msg)
                color = int(input())
                if 1 <= color <= 4:
                    break
                else:
                    print(color_input_err)
            except ValueError:
                print(color_input_err)

        return CardColor(color)


def check_card_playable(card, current_color, current_value, current_type, current_to_draw):
    assert isinstance(card, Card)
    assert isinstance(current_color, CardColor) and current_color != CardColor.WILD
    assert isinstance(current_value, int) and -1 <= current_value <= 9
    assert isinstance(current_type, CardType) and current_type != CardType.ABSTRACT
    assert isinstance(current_to_draw, int) and current_to_draw >= 0

    # ============================
    # Penalty hasn't been executed
    # ============================
    if current_to_draw > 0:
        # Need a draw action card to get over the penalty
        if current_type == CardType.DRAW_2:
            return card.is_draw2() or card.is_draw4()
        elif current_type == CardType.DRAW_4:
            return card.is_draw4()

    # =========================
    # Penalty has been executed
    # =========================
    if card.is_number():
        # if previous card is Number: same color or same number
        # if previous card is Reverse: same color
        # if previous card is Skip: same color
        # if previous card is Wild: same color
        # if previous card is Draw2: same color (and already executed)
        # if previous card is Draw4: same color (and already executed)
        assert isinstance(card, NumberCard)
        return card.color == current_color or card.num == current_value

    elif card.is_reverse():
        # if previous card is Number: same color
        # if previous card is Reverse: always valid
        # if previous card is Skip: same color
        # if previous card is Wild: same color
        # if previous card is Draw2: same color (and already executed)
        # if previous card is Draw4: same color (and already executed)
        assert isinstance(card, ReverseCard)
        return current_type == CardType.REVERSE or card.color == current_color

    elif card.is_skip():
        # if previous card is Number: same color
        # if previous card is Reverse: same color
        # if previous card is Skip: always valid
        # if previous card is Wild: same color
        # if previous card is Draw2: same color (and already executed)
        # if previous card is Draw4: same color (and already executed)
        assert isinstance(card, SkipCard)
        return current_type == CardType.SKIP or card.color == current_color

    elif card.is_wildcard():
        # if previous card is Number: always valid
        # if previous card is Reverse: always valid
        # if previous card is Skip: always valid
        # if previous card is Wild: always valid
        # if previous card is Draw2: (already executed)
        # if previous card is Draw4: (already executed)
        assert isinstance(card, WildCard)
        return True

    elif card.is_draw2():
        # if previous card is Number: always valid
        # if previous card is Reverse: always valid
        # if previous card is Skip: always valid
        # if previous card is Wild: always valid
        # if previous card is Draw2: always valid
        # if previous card is Draw4: (already executed)
        assert isinstance(card, DrawTwoCard)
        return current_type == CardType.DRAW_2 or card.color == current_color

    elif card.is_draw4():
        # if previous card is Number: always valid
        # if previous card is Reverse: always valid
        # if previous card is Skip: always valid
        # if previous card is Wild: always valid
        # if previous card is Draw2: always valid
        # if previous card is Draw4: always valid
        assert isinstance(card, DrawFourCard)
        return True

    else:
        # raise Error
        raise Exception("Unknown Card Type Encountered While Checking Validity")


def accept_card(card, current_color, current_value, current_type, current_to_draw):
    assert isinstance(card, Card)
    assert isinstance(current_color, CardColor) and current_color != CardColor.WILD
    assert isinstance(current_value, int) and -1 <= current_value <= 9
    assert isinstance(current_type, CardType) and current_type != CardType.ABSTRACT
    assert isinstance(current_to_draw, int) and current_to_draw >= 0

    new_color = card.color
    new_value = -1
    new_type = card.card_type
    new_to_draw = 0

    if card.is_number():
        assert isinstance(card, NumberCard)
        new_value = card.num

    elif card.is_reverse():
        pass  # should not be passed if a flow_controller is given

    elif card.is_skip():
        pass  # should not be passed if a flow_controller is given

    elif card.is_wildcard():
        new_color = get_color_input()

    elif card.is_draw2():
        assert current_to_draw == 0 or current_type == CardType.DRAW_2
        new_to_draw = current_to_draw + 2

    elif card.is_draw4():
        new_color = get_color_input()
        new_to_draw = current_to_draw + 4

    else:
        # raise Error
        raise Exception("Unknown Card Type Encountered while Applying State Change")

    return new_color, new_value, new_type, new_to_draw


# Cards with Color, For Each Color 4*(1+9*2+2+2+2):
# 0       : 1
# 1-9     : 2
# Reverse : 2
# Skip    : 2
# Draw2   : 2
#
# Cards without Color:
# Wildcard: 4
# Draw4   : 4
# TODO: to make those number customizable
def make_standard_deck():
    return list(itertools.chain(
        list(itertools.chain(  # for each color
            *(list(itertools.chain(
                [NumberCard(color, 0)],  # 1 x Number 0
                [NumberCard(color, num) for num in range(1, 10) for _ in range(2)],  # 2 x Number [1-9]
                [ReverseCard(color) for _ in range(2)],  # 2 x Reverse
                [SkipCard(color) for _ in range(2)],  # 2 x Skip
                [DrawTwoCard(color) for _ in range(2)]))  # 2 x Draw2
              for color in CardColor if color != CardColor.WILD)
        )),
        [WildCard() for _ in range(4)],  # 4 x Wildcard
        [DrawFourCard() for _ in range(4)]  # 4 x Draw4
    ))


def state_accept_card(self, card):
    self.current_color, self.current_value, self.current_type, self.current_to_draw = \
        accept_card(card, self.current_color, self.current_value, self.current_type, self.current_to_draw)


# In[5]:


@unique
class PlayerType(Enum):
    HUMAN = 1
    PC_NAIVE = 2


class Player(object):
    def __init__(self, ptype, name, idx):
        assert isinstance(ptype, PlayerType)
        assert name is not None
        assert idx is not None
        self.type = ptype
        self.name = name
        self.idx = idx  # add default setting, if not given, set it according to global counter
        self.cards = []
        self.cumulative_score = 0

    @property
    def num_cards(self):
        return len(self.cards)

    @property
    def score(self):
        score = 0
        for card in self.cards:
            if card.is_number():
                assert isinstance(card, NumberCard)
                score += card.num
            elif card.is_reverse():
                score += 20
            elif card.is_skip():
                score += 20
            elif card.is_draw2():
                score += 20
            elif card.is_wildcard():
                score += 50
            elif card.is_draw4():
                score += 50
            else:
                raise Exception("Unknown Card Type Encountered while Calculating Score")
        return score

    def count_score(self):
        self.cumulative_score += self.score

    def is_human(self):
        return self.type == PlayerType.HUMAN

    def get_card(self, card):
        assert isinstance(card, Card)
        print(add_label(self, '{} gets card: {}.'.format(self.name, card)))
        self.cards.append(card)

    def get_cards(self, cards):
        assert isinstance(cards, list)
        for card in cards:
            self.get_card(card)

    def clear_cards(self):
        self.cards = []

    def play_card(self, index):
        assert 0 <= index < self.num_cards
        card = self.cards.pop(index)
        print(add_label(self, '{} plays {}.'.format(self.name, card)))
        return card

    def get_playable(self, current_color, current_value, current_type, current_to_draw):
        print(add_label(self, '{} is looking for possible play under ({}, {}, type {}, to draw {})'.format(
            self.name,
            current_color.name,
            current_value,
            current_type.name,
            current_to_draw
        )))
        playable_cards = [(i, card) for i, card in enumerate(self.cards)
                         if check_card_playable(card,
                                               current_color,
                                               current_value,
                                               current_type,
                                               current_to_draw)]
        # If playable_cards include no NumberCard or WeakActionCard, all cards are playable
        # If playable_cards include NumberCard or (and) WeakActionCard, DrawFourCard needs to be removed
        matching_card_indices = []
        draw_four_indices = []
        for (idx, (i, card)) in enumerate(playable_cards):
            if card.is_number() or card.is_weak_action():
                matching_card_indices.append(idx)
            elif card.is_draw4():
                draw_four_indices.append(idx)

        if len(matching_card_indices) > 0 and len(draw_four_indices) > 0:
            for i in sorted(draw_four_indices, reverse=True):
                del playable_cards[i]

        return playable_cards

    # @abstractmethod
    def get_play(self, current_color, current_value, current_type, current_to_draw):
        pass

    def is_done(self):
        return self.num_cards == 0

    def __repr__(self):
        return "Player({}, \"{}\", pos {}, {})".format(self.type.name, self.name, self.idx, self.cards)

    def __str__(self):
        return "Player({}, \"{}\", pos {}, {})".format(self.type.name, self.name, self.idx, self.cards)


# In[6]:


class PCNaivePlayer(Player):
    def __init__(self, name, idx):
        super().__init__(PlayerType.PC_NAIVE, name, idx)

    def get_play(self, current_color, current_value, current_type, current_to_draw):
        plays = self.get_playable(current_color, current_value, current_type, current_to_draw)

        if len(plays) == 0:
            print(add_label(self, '{} has no valid plays.'.format(self.name)))
            return None
        else:
            print(add_label(self, '{}\'s possible plays: {}.'.format(self.name, plays)))
            print(add_label(self, '{} chooses to play: {}'.format(self.name, plays[0])))
            return plays[0]


# In[7]:


card_input_msg = "Please Select a Card to Play, Input one of the given Number as Your Choice:\n"
card_input_err = "Sorry, Your Input is Invalid, Try Again."


class HumanPlayer(Player):
    def __init__(self, name, idx):
        super().__init__(PlayerType.HUMAN, name, idx)

    @staticmethod
    def get_play_input(plays):
        choice_dict = {index: card for index, card in plays}
        choice_set = choice_dict.keys()
        choice_msg = ["-1) Not Play"]
        choice_msg += ["{}){}".format(index, card) for index, card in plays]
        msg = "{}{}".format(card_input_msg, " ".join(choice_msg))
        while True:
            try:
                print(msg)
                choice = int(input())
                if choice in choice_set or choice == -1:
                    break
                else:
                    print(card_input_err)
            except ValueError:
                print(card_input_err)

        if choice == -1:
            return None
        else:
            return choice, choice_dict[choice]

    def get_play(self, current_color, current_value, current_type, current_to_draw):
        plays = self.get_playable(current_color, current_value, current_type, current_to_draw)

        if len(plays) == 0:
            print(add_label(self, '{} has no valid plays.'.format(self.name)))
            return None
        else:
            print(add_label(self, '{}\'s possible plays: {}.'.format(self.name, plays)))
            play = HumanPlayer.get_play_input(plays)
            print(add_label(self, '{} chooses to play: {}'.format(self.name, play)))
            return play


# In[8]:


# TODO: to write a function connect_nodes(next_node, prev_node)
# TODO: to enable removing nodes for the LinkedList
# Adapted from https://gist.github.com/nichochar/87e18f9eb72f114853eb
class Node(object):
    def __init__(self, next_node=None, prev_node=None, data=None):
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


# In[9]:


class DeckController(object):
    def __init__(self, cards, copy=True):
        assert isinstance(cards, list)
        assert len(cards) > 0
        self.deck_size = len(cards)
        self.draw_pile = cards.copy() if copy else cards
        self.used_pile = []

    @property
    def draw_pile_size(self):
        return len(self.draw_pile)

    @property
    def used_pile_size(self):
        return len(self.used_pile)

    def shuffle(self):
        print(add_label(self, 'Shuffling draw pile...'))
        random.shuffle(self.draw_pile)

    def regenerate_draw_pile(self):
        print(add_label(self, 'Regenerating draw pile...'))
        self.draw_pile = self.used_pile
        self.used_pile = []
        print(add_label(self, '{} cards in the draw pile now.'.format(self.draw_pile_size)))

    def draw_card(self):
        # TODO: to consider the case that both draw_pile and used_pile is empty
        assert self.draw_pile_size > 0

        # get top card and remove it from the data structure
        print(add_label(self, 'Drawing card...'))
        card = self.draw_pile.pop(0)
        print(add_label(self, '{} drawn. Draw pile: {} cards'.format(card, self.draw_pile_size)))

        # regenerate draw pile and shuffle if no cards left after this draw
        if self.draw_pile_size == 0:
            self.regenerate_draw_pile()
            self.shuffle()

        return card

    def draw_cards(self, num_cards):
        assert isinstance(num_cards, int) and num_cards >= 1

        # repeat calling self.draw_card() for num_cards times
        cards = [self.draw_card() for _ in range(num_cards)]
        return cards

    def discard_card(self, card):
        assert isinstance(card, Card)
        self.used_pile.append(card)
        print(add_label(self, '{} discarded. Discard pile: {} cards'.format(card, self.used_pile_size)))

    def discard_cards(self, cards):
        assert isinstance(cards, list)
        for card in cards:
            self.discard_card(card)


# In[10]:


class StateController(object):
    # TODO: to seperate State out as a class
    def __init__(self):
        self.current_color = None
        self.current_value = None
        self.current_type = None
        self.current_to_draw = 0

    def set_color(self, color):
        assert isinstance(color, CardColor)
        self.current_color = color

    def set_value(self, value):
        assert isinstance(value, int) and -1 <= value <= 9
        self.current_value = value

    def set_type(self, ctype):
        assert isinstance(ctype, CardType)
        self.current_type = ctype

    def clear_to_draw(self):
        self.current_to_draw = 0

    def add_to_draw(self, num):
        assert isinstance(num, int)
        self.current_to_draw += num

    def check_card_playable(self, card):
        return check_card_playable(card,
                                   self.current_color,
                                   self.current_value,
                                   self.current_type,
                                   self.current_to_draw)

    # def get_playable(self, cards):
    #     assert isinstance(cards, list)
    #     return [card for card in cards
    #             if check_card_playable(card,
    #                                    self.current_color,
    #                                    self.current_value,
    #                                    self.current_type,
    #                                    self.current_to_draw)]

    def accept_card(self, card, player, flow_controller):
        assert isinstance(card, Card)
        assert isinstance(player, Player)
        assert isinstance(flow_controller, FlowController)

        new_color = card.color
        new_value = -1
        new_type = card.card_type
        new_to_draw = 0

        if card.is_number():
            assert isinstance(card, NumberCard)
            new_value = card.num

        elif card.is_reverse():
            flow_controller.reverse()

        elif card.is_skip():
            flow_controller.add_skip()

        elif card.is_wildcard():
            if player.is_human():
                new_color = get_color_input()
            else:
                new_color = CardColor(random.randint(1, 4))  # TODO: to enhance
            print(add_label(self, 'Player {} selects color {}'.format(player.name, colored(new_color.name, new_color.name[0]))))

        elif card.is_draw2():
            assert self.current_to_draw == 0 or self.current_type == CardType.DRAW_2
            new_to_draw = self.current_to_draw + 2

        elif card.is_draw4():
            if player.is_human():
                new_color = get_color_input()
            else:
                new_color = CardColor(random.randint(1, 4))  # TODO: to enhance
            new_to_draw = self.current_to_draw + 4
            print(add_label(self, 'Player {} selects color {}'.format(player.name, colored(new_color.name, new_color.name[0]))))

        else:
            # raise Error
            raise Exception("Unknown Card Type Encountered while Applying State Change")

        self.current_color = new_color
        self.current_value = new_value
        self.current_type = new_type
        self.current_to_draw = new_to_draw

    def check_action_validity(self, action):
        # TODO: to support multiple cards as an action
        pass


# In[11]:


# TODO: to enable removing nodes for the FlowController
class FlowController(object):
    def __init__(self, players, clockwise=True):
        self.player_loop = LinkedList(players)
        self.current_player_node = self.player_loop.first_node
        self.current_player = self.current_player_node.data
        self.clockwise = clockwise
        self.skip = -1

    def reverse(self):
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
        # TODO: to check whether the player in under the supervision of this instance
        if player is None:
            player = self.current_player
        assert isinstance(player, Player)
        return player.is_done()


# In[12]:


class ActionController(object):
    def __init__(self, cards, players, clockwise=True):
        self.players = players
        self.deck_controller = DeckController(cards)
        self.flow_controller = FlowController(players, clockwise)
        self.state_controller = StateController()
        self.num_first_hand = 7  # TODO: to put it in config or make it customizable

    def __str__(self):
        return "ActionController(color={}, value={}, to_draw={}, clockwise={}, skip={})".format(
            self.state_controller.current_color.name,
            self.state_controller.current_value,
            self.state_controller.current_to_draw,
            self.flow_controller.clockwise,
            self.flow_controller.skip
        )

    @staticmethod
    def get_color_input():
        return get_color_input()

    def apply_penalty(self, player=None):
        if player is None:
            player = self.flow_controller.current_player

        assert isinstance(player, Player)
        if self.state_controller.current_to_draw > 0:
            self.give_player_cards(player, self.state_controller.current_to_draw)
            self.state_controller.clear_to_draw()
        else:
            card = self.give_player_card(player)
            if self.state_controller.check_card_playable(card):
                # TODO: to make this play optional
                print(add_label(self, 'The new card is playable, so play it immediately'))
                self.player_play_card(player, (player.num_cards - 1, card))

    def draw_initial_card(self):
        print(add_label(self, 'Drawing initial card...'))
        card = self.deck_controller.draw_card()
        assert isinstance(card, Card)

        while card.is_draw4():
            print(add_label(self, 'Oops, It\'s a Draw4 Card, Let\'s Try Again'))
            card = self.deck_controller.draw_card()
            assert isinstance(card, Card)

        print(add_label(self, '{} drawed as the initial card.'.format(card)))
        if card.is_number():
            # set current color and number
            assert isinstance(card, NumberCard)
            self.state_controller.set_color(card.color)
            self.state_controller.set_value(card.num)

        elif card.is_reverse():
            # the direction is reversed, and the current color is determined by the card
            assert isinstance(card, ReverseCard)
            self.flow_controller.reverse()
            self.state_controller.set_color(card.color)
            self.state_controller.set_value(-1)

        elif card.is_skip():
            # the first player is skipped, and the current color is determined by the card
            assert isinstance(card, SkipCard)
            self.flow_controller.add_skip(1)
            self.state_controller.set_color(card.color)
            self.state_controller.set_value(-1)

        elif card.is_wildcard():
            # the first player determine the current color and begin playing
            assert isinstance(card, WildCard)
            color = ActionController.get_color_input()
            self.state_controller.set_color(color)
            self.state_controller.set_value(-1)

        elif card.is_draw2():
            # the first player draw 2 cards, and the current color is determined by the card
            assert isinstance(card, DrawTwoCard)
            self.state_controller.add_to_draw(2)
            self.state_controller.set_color(card.color)
            self.state_controller.set_value(-1)
            self.apply_penalty()
            self.flow_controller.to_next_player()

        else:
            # raise Error
            raise Exception("Unknown Card Type of the Initial Card")

        self.state_controller.set_type(card.card_type)

    def distribute_first_hand(self):
        print(add_label(self, 'Distributing first hand cards...'))
        for _ in range(self.num_first_hand):
            for player in self.players:
                self.give_player_card(player)

    def player_play_card(self, player, play):
        index, card = play
        player.play_card(index)
        self.deck_controller.discard_card(card)
        self.state_controller.accept_card(card, player, self.flow_controller)

    def give_player_card(self, player):
        card = self.deck_controller.draw_card()
        player.get_card(card)
        return card

    def give_player_cards(self, player, num_cards):
        cards = self.deck_controller.draw_cards(num_cards)
        player.get_cards(cards)
        return cards

    def run(self):
        # Do the important thing for three times
        self.deck_controller.shuffle()
        self.deck_controller.shuffle()
        self.deck_controller.shuffle()
        self.distribute_first_hand()
        self.draw_initial_card()

        player = None
        while not self.flow_controller.is_player_done():
            self.flow_controller.to_next_player()
            player = self.flow_controller.current_player
            print(add_label(self, 'Switch to {}'.format(player)))

            play = player.get_play(
                self.state_controller.current_color,
                self.state_controller.current_value,
                self.state_controller.current_type,
                self.state_controller.current_to_draw
            )
            if play is not None:
                self.player_play_card(player, play)
            else:
                print(add_label(self, '{} plays no card.'.format(player.name)))
                self.apply_penalty(player)

        assert isinstance(player, Player)
        print(add_label(self, '{} wins in this round.'.format(player.name)))
        print(add_label(self, 'Calculaing scores.'))
        for player in self.players:
            player.count_score()

        print(add_label(self, 'Present cumulative scores for each player'))
        print("-----------------------------------------------------------")
        for index, player in enumerate(self.players):
            print("pos {} - name {}: {}".format(index, player.name, player.cumulative_score))


# In[13]:


nplayers_input_msg = "Please Input a Number as the Number of Players: 2-10"
nplayers_input_err = "Sorry, Your Input is Invalid, Try Again."
ptype_input_msg = "Please Select Type of Player #{}, Input One Number from 1 to 2:\n1)HUMAN 2)PC_NAIVE"
ptype_input_err = "Sorry, Your Input is Invalid, Try Again."
pname_input_msg = "Please Input the Name for Player #{} (Max Length: 20)"
pname_input_err = "Sorry, Your Input is Invalid, Try Again."


class Game(object):
    def __init__(self):
        self.num_players = 0
        self.players = []
        self.cards = []
        self.action_controller = None

    @staticmethod
    def get_num_players():
        while True:
            try:
                print(nplayers_input_msg)
                num = int(input())
                if 2 <= num <= 10:
                    break
                else:
                    print(nplayers_input_err)
            except ValueError:
                print(nplayers_input_err)

        return num

    @staticmethod
    def get_player_type(index):
        msg = ptype_input_msg.format(index + 1)
        while True:
            try:
                print(msg)
                ptype = int(input())
                if 1 <= ptype <= 2:
                    break
                else:
                    print(ptype_input_err)
            except ValueError:
                print(ptype_input_err)

        return PlayerType(ptype)

    @staticmethod
    def get_player_name(index):
        msg = pname_input_msg.format(index + 1)
        while True:
            print(msg)
            name = input()
            if 0 < len(name) <= 20:
                break
            else:
                print(pname_input_err)

        return name

    def run(self):
        # =====================
        # Get Number of Players
        # =====================
        self.num_players = Game.get_num_players()
        print(add_label(self, 'Number of Player Set: {}\n'.format(self.num_players)))

        # ===============
        # Get Player Info
        # ===============
        for i in range(self.num_players):
            player_type = Game.get_player_type(i)
            player_name = Game.get_player_name(i)

            if player_type == PlayerType.HUMAN:
                player = HumanPlayer(player_name, i)
            elif player_type == PlayerType.PC_NAIVE:
                player = PCNaivePlayer(player_name, i)
            else:
                raise Exception("Unknown Player Type Encountered while Creating Player")

            self.players.append(player)
            print(add_label(self, 'Player created: {}\n'.format(player)))

        # =====================================
        # Initialize Cards and ActionController
        # =====================================
        self.cards = make_standard_deck()
        self.action_controller = ActionController(self.cards, self.players)

        # ====
        # Play
        # ====
        self.action_controller.run()

        print(add_label(self, 'Game over.'))


# In[14]:


if __name__ == "__main__":
    game = Game()
    game.run()
