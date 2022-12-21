import pygame
import os
import random

# define global final variables
WIDTH = 1270  # screen width, height
HEIGHT = 640
WINDOW_OFFSET_X = 5
WINDOW_OFFSET_Y = 30  # no idea why but this works
FPS = 30
CLOCK = pygame.time.Clock()
SLOT_COLOR = (70, 0, 0)
HAND_Y_LOC = 450
HAND_CARD_DIMS = [150, 180]
POWER_LOC = [1110, 600]
DISCARD_PILE_LOC = [0, HAND_Y_LOC]
END_TURN_RECT = (WIDTH - 230, POWER_LOC[1] - 110, 230, 100)
LINEUP_NUM = 6
LINEUP_Y = 50
LINEUP_X_START = 120
LINEUP_X_END = 1140
SLOT_HEIGHT = 200
SLOT_WIDTH = (LINEUP_X_END - LINEUP_X_START) / LINEUP_NUM
CUSHION = 10

LOC_SLOT_HEIGHT = SLOT_HEIGHT
LOC_SLOT_WIDTH = int(SLOT_WIDTH)
LOC_SLOT_X = LINEUP_X_START
LOC_SLOT_Y = LINEUP_Y + SLOT_HEIGHT + CUSHION

SELECT_Y = 260
SELECT_WIDTH = SLOT_WIDTH + 15
SELECT_X_START = LINEUP_X_START
SELECT_GAP = 25
TURN_CHANGE_LOC = [380, 300]
YES_RECT = (WIDTH - 250, 400, 125, 70)
NO_RECT = (WIDTH - 125, 400, 125, 70)
REPLACE_TEXT_LOC = [450, 360]
DISCARD_TEXT_LOC = [420, 120]
DISPLAY_DISCARD = [int(WIDTH * 1 / 12), int(HEIGHT * 1 / 8), int(WIDTH * 5 / 6), int(HEIGHT * 3 / 4)]

# global variables that might change
global status, running  # status: home screen, game screen
# running is true while game window is open
global start_button, pass_button, yes_button, no_button
global screen  # pygame screen
global p1, p2
global lineup, discard_slot  # discard slot: slot displaying the top card of the discard pile
global curr_player, game_winner  # curr player: player who can take actions
global turn_change_text_counter, end_game_text_counter  # to count down how long text appears on the screen
global curr_screen, screen_counter, display_discard, card_trashed, return_function
# curr_screen: whether a player has to choose to discard cards, replace the lineup, etc., or if they can currently buy
# cards and take actions
# screen_counter: number of cards to be discarded/trashed until we go back to the default screen
# display_discard: true if the discard pile is currently being displayed (when the user clicks on it)
# card_trashed: when a card is trashed, this variable stores the card
# return function: sometimes a function has to be called after a card is trashed; if so, that function is stored here
global trash_pile
global deck
global log

# log of game events
# format: list of lists of tuples; one list for each turn, and one tuple for each event
# (event type, card involved, player, [targets])
# event type: 'buy', 'play' for card played, or 'ability'


# to do later: re-implement 2-player play (discard slot corresponds to the current player)
# TODO: card text on mouse over

# end the turn. most of this is handled by calling the player.pass_turn function.
# called when we detect that the player has clicked the "end turn" button or pressed the spacebar.
def end_turn():
    global curr_player
    global log

    curr_player.pass_turn()

    # each turn has a new list of actions in the log
    log.append([])


# for each slot in the lineup, add a card to it (that fits that slot's restrictions).
# a lot of this is handled in the slot.add_card function.
# called at the beginning of the game, or when a player chooses to replace the lineup
# todo: move the end_game check to a different function
def fill_lineup():
    global lineup
    global deck

    for c in range(len(lineup)):
        if len(deck) == 0:
            # the game ends when the lineup must be filled when there are no cards left
            end_game()

        else:
            # remove the card from the deck and add it to the lineup
            # lineup[c] is a slot
            lineup[c].add_card()


# for each slot in the lineup, put it back in the deck, then refill the lineup.
# called when the player clicks the "yes" button to replace the lineup.
def yes_replace():
    # empty the lineup
    for slot in lineup:
        if slot.card is not None:  # we don't want to add none back in the deck
            deck.append(slot.card)
            slot.card = None

    # refill the lineup
    fill_lineup()
    new_turn()


# start a new turn, changing the current player and going back to the default screen.
# called after the player chooses whether or not to replace the lineup.
def new_turn():
    global turn_change_text_counter
    global curr_screen
    global curr_player

    turn_change_text_counter = 20  # counts how long "Player 1 Turn" appears on the screen
    curr_screen = "default"  # the default screen where players play cards
    # curr_player = curr_player.opponent


# button class, which holds a rect to be displayed on the screen and a function to execute when clicked.
class Button:
    def __init__(self, rect, function, image=None, color=SLOT_COLOR, text=""):
        self.rect = pygame.Rect(rect)
        self.function = function  # on click, execute this function
        self.img = image  # display this image on the button
        self.color = color  # if there's no image, the button is this color
        self.font = pygame.font.Font('freesansbold.ttf', 16)  # font for the text on the button
        self.text = self.font.render(text, True, pygame.Color('White'))  # render white text on the button

    def draw(self):
        global screen

        if self.img:
            pygame.transform.scale(self.img, (self.rect[1], self.rect[2]))
            screen.blit(self.img, self.rect[0], self.rect[1])

        else:
            # fill the area behind this button with black
            screen.fill(pygame.Color("black"), self.rect)
            # button color is slightly smaller than the black to create a black border
            screen.fill(self.color, self.rect.inflate(-4, -4))

        # draw the text in the center of the button
        text_rect = self.text.get_rect(center=self.rect.center)
        screen.blit(self.text, text_rect)

    def update(self, surface):
        pass  # check hover? idk what goes here

    # called every frame. checks if the player clicked on this button, and if so, the function is executed.
    def check_event(self, event):
        # if self.function.__name__ == "trash" and event.type == pygame.MOUSEBUTTONUP:
        #     print("rect: " + str(self.rect))
        #     print("click position: " + str(event.pos))
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.rect.collidepoint(event.pos):
            # if self.function.__name__ == "discard":
            #     print("rect: " + str(self.rect))
            #     print("going to discard")

            # print("function: " + self.function.__name__)
            self.function()


# class holding basic information about a card. each card in the game will have a subclass of this.
class Card:

    def __init__(self, card_type, cost, power, owned_by=None):
        self.type = card_type  # basic, action, innovation, etc
        self.cost = cost  # how much energy this card costs
        self.power = power  # amount of power gained when this is played
        self.player = owned_by  # the player that owns this card
        self.slot = None  # the slot in the lineup representing this card
        self.button = None  # clickable rectangle representing the card on the screen
        self.select_button = None  # for selecting the card on a discard/trash screen, etc.
        self.vps = self.cost / 2  # how many victory points this card gives at the end of the game

    def __str__(self):
        return type(self).__name__  # make customizable

    # the current player buys this card, calling the player.buy function.
    # called when this card is clicked on in the lineup.
    def buy(self):
        global curr_player
        global lineup
        global log

        # print("card object: " + str(self))
        # print("name: " + self.name)
        # print("owned by: " + str(self.owned_by))
        # print("slot: " + str(self.slot))

        # if the player has enough power to buy
        if curr_player.power >= self.cost:
            # print("power: " + str(curr_player.power))
            # print("cost: " + str(self.cost))
            self.player = curr_player  # the current player now owns the card
            self.button.function = None  # the function needs to be removed because otherwise it will be called when
            # the card is clicked on in the discard pile

            curr_player.buy(self)

            self.slot.remove()  # the slot will remove this card and replace it with a new one, if possible.
            self.slot = None

        log[-1].append(('buy', self, curr_player, []))  # add to the log that this card was bought

    # add this card to a slot in the lineup.
    # called from the slot.add_card function.
    def add(self, slot):
        self.slot = slot
        # create a new button which will cause the player to buy this card when it is clicked on
        self.button = Button(slot.rect, self.buy, color=SLOT_COLOR, text=str(self))

    # everything was handled in the player draw function
    def draw(self, hand_size):
        pass

    # the card is played and has its effect
    # called when the card is clicked on from the hand
    def play(self):
        player = self.player
        # print("playing card, owned by " + str(self.player) + ", card name: " + str(self))
        if player == curr_player:
            play_valid = True

            # if this is an action card, the player must have an action available to play this card.
            if self.type != "basic" and self.type != "innovation" and player.actions <= 0:
                play_valid = False

            if play_valid:
                player.play(self)
                self.take_effect()

            # self.button = None

        else:
            print("stop playing my cards its not your turn")

    # the card has its effect. if it is an innovation, it goes into play. for every non-innovation card, this function
    # is overwritten in the corresponding subclass.
    # called from the self.play function
    def take_effect(self):
        if self.type == "innovation":
            empty_slot = False
            # find an empty slot to put the innovation
            for slot in self.player.loc_list:
                if slot.card is None:
                    slot.card = self
                    empty_slot = True
                    break

            if not empty_slot:
                pass  # player has to select a innovation to replace

    # remove this card from the hand and add it to the discard pile.
    # called when the player clicks on this card from the discard screen (prompted by a card's effect)
    def discard(self):
        global screen_counter
        global deck

        print("discarding card: " + str(self))
        self.player.hand.remove(self)
        self.player.add_to_discard(self)
        screen_counter -= 1

    # remove this card from the hand, deck, and/or discard pile, and add it to the trash pile.
    # called when the player clicks on this card from the trash screen, either when in the hand or discard pile
    # (prompted by a card's effect)
    def trash(self):
        global screen_counter
        global deck
        global trash_pile
        global curr_screen
        global card_trashed

        # print("trashing card: " + str(self) + ", trash counter: " + str(screen_counter))
        # print("curr_screen: " + str(curr_screen))

        # store the trashed card for functions that need it
        card_trashed = self

        # if we trash cards from different places, put that here
        # remove the card from the hand, deck, and/or discard pile
        if self.player is not None:
            if self in self.player.hand:
                self.player.hand.remove(self)
            if self in self.player.discard_pile:
                self.player.discard_pile.remove(self)
                if self == discard_slot.card:
                    discard_slot.card = None
                    # todo: update discard slot to a different card
        if self in deck:
            deck.remove(self)

        trash_pile.append(self)
        self.button = None

        # decrement the "number of cards to be trashed"
        screen_counter -= 1


# basic card that starts in the player's hand
# card text: {no effect}
class Space(Card):
    def __init__(self, player):
        super().__init__("basic", 1, 0, owned_by=player)


# basic card that starts in the player's hand.
# card text: gain 1 energy.
class Crystal(Card):
    def __init__(self, player):
        super().__init__("basic", 1, 1, owned_by=player)


# action card, costs 2 energy.
# card text: Draw a card. You may shuffle your discard pile.
class Barter(Card):
    def __init__(self):
        super().__init__("action", 2, 0)

    def take_effect(self):
        self.player.draw_card()
        self.player.shuffle_discard()  # TODO: change to a may


# action card, costs 2 energy.
# card text: gain 1 energy, gain 2 actions
class Catalyst(Card):
    def __init__(self):
        super().__init__("action", 2, 1)

    def take_effect(self):
        self.player.actions += 2


# action card, costs 2 energy.
# card text: Draw a card.
# You may trash an action or location in your hand or discard pile. If you do, draw 2 additional cards.
class Sacrifice(Card):
    def __init__(self):
        super().__init__("action", 2, 0)

    def take_effect(self):
        global return_function  # this function is executed after the trashing occurs

        self.player.draw_card()
        self.player.trash_cards(1)
        # when the trashing is done, check if the trashed card was an action
        return_function = self.draw_condition

    def draw_condition(self):
        # print("draw condition")
        if card_trashed.type == "action" or card_trashed.type == "innovation":
            # print("gottem")
            self.player.draw_cards(2)


# action card, costs 2 energy.
# card text: gain 1 energy. You may trash a card in your hand or discard pile.
class Scrap(Card):
    def __init__(self):
        super().__init__("action", 2, 1)

    def take_effect(self):
        self.player.trash_cards(1)  # todo: change to a may


# action card, costs 3 energy.
# card text: gain 1 energy and draw a card.
class FavorableExchange(Card):
    def __init__(self):
        super().__init__("action", 5, 2)

    def take_effect(self):
        self.player.draw_card()


# action card, costs 7 energy.
# card text: gain 2 energy. put a random card with cost 4 or less from the deck into your discard pile.
class HiredBandit(Card):
    def __init__(self):
        super().__init__("action", 7, 2)

    def take_effect(self):
        self.player.get_card(4)


# action card, costs 7 energy.
# card text: gain 1 energy, draw a card. attack: your opponent discards a card.
class WeaponHeist(Card):
    def __init__(self):
        super().__init__("attack", 7, 1)

    def take_effect(self):
        self.player.draw_card()
        self.player.opponent.discard_cards(1)


# action card, costs 3 energy.
# card text: gain 1 energy. Attack: your opponent discards a card
class Pistol(Card):
    def __init__(self):
        super().__init__("attack", 3, 1)

    def take_effect(self):
        self.player.opponent.discard_cards(1)


# action card, costs 3 energy.
# card text: gain 2 energy.
class FuelCell(Card):
    def __init__(self):
        super().__init__("action", 3, 2)

    def take_effect(self):
        pass


# action card, costs 4 energy.
# card text: gain 2 energy Defense: you may discard this card to avoid an attack.
# If you do, trash a card from your hand or discard pile.
class MakeshiftBarrier(Card):
    def __init__(self):
        super().__init__("defense", 4, 2)

    def defend(self):
        pass

    # todo: implement defenses


# location card, costs 2 energy.
# card text:
# You may look at and buy the top card of the main deck.
# Destroy this location to draw a card.
class Spyglass(Card):
    def __init__(self):
        super().__init__("innovation", 2, 0)


# action card, costs 2 energy.
# card text: Gain an opponent's power this turn
class AppliedReconnaissance(Card):
    def __init__(self):
        super().__init__("action", 2, 0)

    # todo: implement
    def take_effect(self):
        pass


# action card, costs 4 energy.
# card text:
# if you've played a 2- cost card this turn, draw a card
# if you've played a 3-6 cost card this turn, draw a card
# if you've played a 7+ cost card this turn, draw a card
class ReadTheMaps(Card):
    def __init__(self):
        super().__init__("action", 4, 0)

    def take_effect(self):
        global log

        cost0_2 = False
        cost3_6 = False
        cost7_10 = False

        turn_events = log[-1]  # everything that happened this turn
        for i in range(len(turn_events)):
            event = turn_events[i]
            if event[0] == 'play':  # if this event was a card play
                if event[1].cost <= 2:
                    cost0_2 = True
                elif event[1].cost <= 6:
                    cost3_6 = True
                else:
                    cost7_10 = True
            if cost0_2 and cost3_6 and cost7_10:
                break

        if cost0_2:
            self.player.draw_card()
        if cost3_6:
            self.player.draw_card()
        if cost7_10:
            self.player.draw_card()


# action card, costs 1 energy.
# card text: Give 2 spaces to your opponent, then trash this card.
class Jinx(Card):
    def __init__(self):
        super().__init__("action", 1, 0)

    def take_effect(self):
        # add a space to the opponent's deck
        self.player.opponent.deck.append(Space(self.player.opponent))
        self.player.opponent.deck.append(Space(self.player.opponent))
        self.trash()


# display the discard pile. if curr_screen == "trash", this also allows the player to trash cards from the discard pile.
# called when the player clicks on the discard pile
def show_discard():
    global display_discard
    global screen

    display_discard = True


# player class, which holds a hand, deck, discard pile, current amount of power, etc.
class Player:

    def __init__(self, player_num):
        self.hand = []
        # create the starting deck
        self.deck = [Space(self), Space(self), Space(self),
                     Crystal(self), Crystal(self), Crystal(self), Crystal(self),
                     Crystal(self), Crystal(self), Crystal(self)]

        # list of slots that can contain locations.
        self.loc_list = [Slot(0, 100, pygame.Rect(LOC_SLOT_X, LOC_SLOT_Y, LOC_SLOT_WIDTH, LOC_SLOT_HEIGHT)),
                         Slot(0, 100, pygame.Rect(LOC_SLOT_X, LOC_SLOT_Y, LOC_SLOT_WIDTH, LOC_SLOT_HEIGHT)),
                         Slot(0, 100, pygame.Rect(LOC_SLOT_X, LOC_SLOT_Y, LOC_SLOT_WIDTH, LOC_SLOT_HEIGHT))]
        self.discard_pile = []
        random.shuffle(self.deck)
        self.is_p1 = player_num % 2

        # draw a 5 card starting hand
        for c in range(5):
            self.draw_card()

        self.power = 0
        self.opponent = None

        self.actions_per_turn = 2  # number of actions per turn (default: 2)
        self.actions = self.actions_per_turn  # number of actions currently available

        self.discard_pile_top = None  # top card of the discard pile, which is shown at all times

    def __str__(self):
        if self.is_p1:
            return "Player 1"
        else:
            return "Player 2"

    # update the buttons of the cards in hand so they are centered on the screen.
    # called from the self.draw_card and self.play_card functions.
    # todo: call when a card in trashed
    def update_hand(self):
        hand_size = len(self.hand)

        for c in range(hand_size):
            self.hand[c].button.rect = \
                pygame.Rect((WIDTH / 2 - (HAND_CARD_DIMS[0] * ((hand_size / 2.0) - c))),
                            DISCARD_PILE_LOC[1], HAND_CARD_DIMS[0], HAND_CARD_DIMS[1])
            # this works don't question it
            if self.hand[c].player is None:
                raise Exception

    # draw multiple cards. called from some take_effect functions
    def draw_cards(self, num):
        for i in range(num):
            self.draw_card()

    # draw a card.
    # called from card.take_effect functions, the self.draw_cards function, as well as in self.__init__
    # function to start the game.
    def draw_card(self):
        global curr_player

        # if there are no cards from the deck to draw, shuffle in the discard pile.
        if len(self.deck) == 0:
            self.shuffle_discard()

        # if there are now cards in the deck, draw.
        if len(self.deck) != 0:
            card = self.deck.pop()  # get the next card from the deck
            self.hand.append(card)
            hand_size = len(self.hand)

            # i'll be honest, i have no idea why there's a try except statement here
            try:
                if self == curr_player:
                    card.button = Button((WIDTH / 2 + (SLOT_WIDTH * (hand_size / 2.0 - 0.5)),
                                          HAND_Y_LOC, SLOT_WIDTH, SLOT_HEIGHT), card.play, color=SLOT_COLOR,
                                         text=str(card))
                    self.update_hand()
            except NameError:
                card.button = Button((WIDTH / 2 + (SLOT_WIDTH * (hand_size / 2.0 - 0.5)),
                                      HAND_Y_LOC, SLOT_WIDTH, SLOT_HEIGHT), card.play, color=SLOT_COLOR, text=str(card))
                self.update_hand()

    # shuffle the discard pile into the deck.
    # called from the self.draw_card function and from some card.take_effect functions.
    def shuffle_discard(self):
        global discard_slot

        self.deck = self.discard_pile
        self.discard_pile = []
        random.shuffle(self.deck)

        if self.is_p1:
            discard_slot.card = None

    # end the turn.
    # called from the end_turn function.
    def pass_turn(self):
        global log
        global screen
        global turn_change_text_counter
        global curr_screen

        # print("current turn: " + str(self))
        # print("starting turn of: " + str(self.opponent))

        # all cards played this turn and all cards left in hand go to the discard pile
        for element in log[-1]:
            if element[0] == 'play' and element[1].type != "innovation":
                self.add_to_discard(element[1])
        for card in self.hand:
            self.add_to_discard(card)

        self.hand = []
        self.power = 0

        # draw a new hand of 5
        while len(self.hand) < 5:
            self.draw_card()

        if len(deck) == 0:
            end_game()

        curr_screen = "replace"

        self.actions = self.actions_per_turn

    # adds this card to the discard pile, and shows it with a button on top of the discard pile.
    # called from the card.discard function and the self.pass_turn function
    def add_to_discard(self, card):
        global discard_slot
        global curr_player

        self.discard_pile.append(card)

        if self == curr_player:
            if discard_slot.card is not None:
                discard_slot.card.button = None
                # new top card of the discard pile, so we create a new button and get rid of the old one

            discard_slot.card = card
            # button that displays the discard pile when clicked
            card.button = Button(
                (DISCARD_PILE_LOC[0], DISCARD_PILE_LOC[1], HAND_CARD_DIMS[0], HAND_CARD_DIMS[1]),
                show_discard, color=SLOT_COLOR, text=str(card))
            # this button is clickable when on the trash screen, and trashes the card
            card.select_button = Button((0, 0, HAND_CARD_DIMS[0], HAND_CARD_DIMS[1]),
                                        card.trash, color=SLOT_COLOR, text=str(card))

    # adds a card from the lineup to the discard pile.
    # called from the card.buy function.
    def buy(self, card):
        self.add_to_discard(card)
        self.power -= card.cost

    def play(self, card):
        global log

        if card.type != "basic" and card.type != "innovation":
            self.actions -= 1

            print("taking action, current actions: " + str(self.actions))

        self.power += card.power
        self.hand.remove(card)

        if card.type == "innovation":
            function = None  # this should be defined when the innovation is constructed
            rect = (LOC_SLOT_X, LOC_SLOT_Y, LOC_SLOT_WIDTH, LOC_SLOT_HEIGHT)
            print(rect)
            card.button = Button(rect, function, color=SLOT_COLOR, text=str(card))

        self.update_hand()  # since we removed a card from the hand, we need to update the visuals

        log[-1].append(('play', card, self, []))

    def get_card(self, num):
        global deck

        print("getting card")

        random.shuffle(deck)

        c = 0
        added = False
        while not added and c < len(deck):
            card = deck[c]
            if card.cost <= num:
                self.add_to_discard(card)
                added = True
                deck.pop(c)

            c += 1

        print("added: " + str(added))

    # choose a card from hand or discard pile to get rid of
    def trash_cards(self, num):
        global curr_screen
        global screen_counter

        if len(self.hand) != 0:
            curr_screen = "trash"
            screen_counter = num

            print("starting trash")

            c = 0
            for card in self.hand:
                x_pos = (SELECT_GAP + SELECT_WIDTH) * c + SELECT_X_START
                y_pos = SELECT_Y
                card.select_button = Button((x_pos, y_pos, SELECT_WIDTH, SLOT_HEIGHT), card.trash, color=SLOT_COLOR,
                                            text=str(card))
                c += 1

    # choose and discard
    def discard_cards(self, num):
        global curr_screen
        global screen_counter

        curr_screen = "discard"
        screen_counter = num

        c = 0
        for card in self.hand:
            x_pos = (SELECT_GAP + SELECT_WIDTH) * c + SELECT_X_START
            y_pos = SELECT_Y
            card.select_button = Button((x_pos, y_pos, SELECT_WIDTH, SLOT_HEIGHT), card.discard, color=SLOT_COLOR,
                                        text=str(card))
            c += 1


class Power:

    def __init__(self, name, effect):
        self.name = name
        self.effect = effect


class Slot:

    def __init__(self, min_cost, max_cost, rect):
        self.min = min_cost
        self.max = max_cost
        self.card = None
        self.rect = rect

    def __str__(self):
        if self.min == 0:
            min_text = "no minimum"
        else:
            min_text = "min cost: " + str(self.min) + "\n"
        if self.max == 100:
            max_text = "no maximum"
        else:
            max_text = "max cost: " + str(self.max) + "\n"

        return "Slot\n" + min_text + max_text

    def remove(self):
        self.card = None

        self.add_card()

    def add_card(self):
        added = False
        skipped_card = False

        c = 0
        while not added and c < len(deck):
            card = deck[c]
            if card is None:
                print("index: " + str(c))
                print("deck length: " + str(len(deck)))
                for i in range(len(deck)):
                    print(deck[i])
            if self.min <= card.cost <= self.max:
                self.card = card
                card.add(self)
                added = True
                deck.pop(c)
            else:
                skipped_card = True

            c += 1

        if not added:
            print("no valid cards in deck :(")

        if skipped_card:
            random.shuffle(deck)  # if we don't shuffle here, the next card added is always a card that doesn't fit
            # in the current slot, and we want it to be random


def end_game():
    global status
    global p1
    global p2
    global end_game_text_counter
    global game_winner

    p1_vps = 0
    p2_vps = 0

    for card in p1.deck:
        p1_vps += card.vps
    for card in p1.discard_pile:
        p1_vps += card.vps

    for card in p2.deck:
        p2_vps += card.vps
    for card in p2.discard_pile:
        p2_vps += card.vps

    if p1_vps > p2_vps:
        game_winner = "1"
    else:
        game_winner = "2"

    end_game_text_counter = 70


def initialize():
    global running
    global status
    global start_button
    global screen
    global turn_change_text_counter
    global end_game_text_counter
    global screen_counter
    global curr_screen
    global display_discard

    pygame.init()
    os.environ['SDL_VIDEO_WINDOW_POS'] = '%i,%i' % (WINDOW_OFFSET_X, WINDOW_OFFSET_Y)

    status = "home"
    running = True

    screen = pygame.display.set_mode([500, 500])
    screen.fill((0, 0, 0))

    pygame.display.set_mode((WIDTH, HEIGHT))

    start_button = Button((0, 0, 350, 100), start_game, color=(100, 30, 0), text="Play!")
    start_button.rect.center = (screen.get_rect().centerx, screen.get_rect().centery)

    turn_change_text_counter = 0
    end_game_text_counter = 0
    screen_counter = 0
    curr_screen = "default"
    display_discard = False


def mouse_up(button, pos):
    # print("clicky")
    pass


def key_up(key):
    global curr_screen

    print("key up")

    if key == pygame.K_SPACE:
        print("space bar up")
        if curr_screen == "default":
            end_turn()


def start_game():
    global status
    global p1
    global p2
    global deck
    global lineup
    global curr_player
    global screen
    global discard_slot
    global pass_button
    global yes_button
    global no_button
    global trash_pile
    global return_function
    global log

    status = "game"

    # define the players
    p1 = Player(1)
    p2 = Player(2)
    p1.opponent = p2
    p2.opponent = p1

    # add the cards to the communal deck
    deck = []

    for i in range(6):
        deck.append(Barter())

    for i in range(5):
        deck.append(Scrap())

    for i in range(1):
        deck.append(FavorableExchange())

    for i in range(1):
        deck.append(HiredBandit())

    for i in range(1):
        deck.append(WeaponHeist())

    for i in range(1):
        deck.append(Pistol())

    for i in range(5):
        deck.append(FuelCell())

    for i in range(1):
        deck.append(MakeshiftBarrier())

    for i in range(1):
        deck.append(Spyglass())

    for i in range(1):
        deck.append(Sacrifice())

    for i in range(7):
        deck.append(ReadTheMaps())

    # the lineup contains 6 slots, some of which will reliably have cards of certain costs.
    lineup = [Slot(0, 2, pygame.Rect((LINEUP_X_START, LINEUP_Y, SLOT_WIDTH, SLOT_HEIGHT))),
              Slot(0, 100, pygame.Rect((LINEUP_X_START + SLOT_WIDTH, LINEUP_Y, SLOT_WIDTH, SLOT_HEIGHT))),
              Slot(3, 6, pygame.Rect((LINEUP_X_START + (SLOT_WIDTH * 2), LINEUP_Y, SLOT_WIDTH, SLOT_HEIGHT))),
              Slot(3, 6, pygame.Rect((LINEUP_X_START + (SLOT_WIDTH * 3), LINEUP_Y, SLOT_WIDTH, SLOT_HEIGHT))),
              Slot(0, 100, pygame.Rect((LINEUP_X_END - (SLOT_WIDTH * 2), LINEUP_Y, SLOT_WIDTH, SLOT_HEIGHT))),
              Slot(7, 100, pygame.Rect((LINEUP_X_END - SLOT_WIDTH, LINEUP_Y, SLOT_WIDTH, SLOT_HEIGHT)))]

    discard_slot = Slot(0, 100, pygame.Rect(DISCARD_PILE_LOC[0], DISCARD_PILE_LOC[1], HAND_CARD_DIMS[0],
                                            HAND_CARD_DIMS[1]))

    trash_pile = []

    random.shuffle(deck)

    fill_lineup()

    # randomly determine starting player
    starting_player = random.randrange(1)

    if starting_player == 0:
        curr_player = p1
    else:
        curr_player = p2

    pass_button = Button(END_TURN_RECT, end_turn, color=(100, 70, 0), text="End Turn")

    yes_button = Button(YES_RECT, yes_replace, color=(0, 100, 0), text="yes")
    no_button = Button(NO_RECT, new_turn, color=(100, 0, 0), text="no")

    return_function = None

    log = [[]]


# check for clicks
def handle_events():
    global running
    global lineup
    global status
    global p1
    global p2
    global yes_button
    global no_button
    global display_discard

    for e in pygame.event.get():
        if e.type == pygame.QUIT:  # when you click x, exit the program
            running = False
        elif e.type == pygame.KEYUP:
            # print('key pressed')
            key_up(e.key)  # if a key was pressed, do the associated action
        elif e.type == pygame.MOUSEBUTTONUP:
            mouse_up(e.button, e.pos)  # if the mouse was clicked, do the associated action

        if status == "home":
            start_button.check_event(e)

        if status == "game":
            if display_discard:
                # print("clicky")
                display_rect = pygame.Rect(DISPLAY_DISCARD)

                # if the player clicks outside the display discard window, close the window
                if e.type == pygame.MOUSEBUTTONUP and not display_rect.collidepoint(e.pos):
                    print("exiting display discard")
                    display_discard = False

                if curr_screen == "trash":
                    # print("trashing from discard pile")
                    for card in curr_player.discard_pile:
                        card.select_button.check_event(e)

            elif curr_screen == "default":
                for slot in lineup:
                    if slot.card is not None:
                        slot.card.button.check_event(e)
                    # if slot == lineup[0]:
                    #     print("checking events")
                for card in curr_player.hand:
                    card.button.check_event(e)

                if discard_slot.card is not None:
                    # print("discard slot card: " + str(discard_slot.card))
                    # print("function: " + str(discard_slot.card.button.function))
                    if discard_slot.card.button.function is not None:
                        discard_slot.card.button.check_event(e)

                    # if e.type == pygame.MOUSEBUTTONUP:
                    #     print("button: " + str(discard_slot.card.button))
                    #     print("function: " + str(discard_slot.card.button.function))

                pass_button.check_event(e)

            # if e.type == pygame.MOUSEBUTTONUP:
            #     print("function: " + str(pass_button.function))

            elif curr_screen == "replace":
                yes_button.check_event(e)
                no_button.check_event(e)

            elif curr_screen == "discard":
                # TODO: change to accommodate curr player discard
                for card in curr_player.opponent.hand:
                    card.select_button.check_event(e)

            elif curr_screen == "trash":
                for card in curr_player.hand:
                    card.select_button.check_event(e)
                for card in curr_player.discard_pile:
                    card.select_button.check_event(e)
                    # print("card name: " + str(card))

                if discard_slot.card is not None:
                    # print("discard slot card: " + str(discard_slot.card))
                    # print("function: " + str(discard_slot.card.button.function))
                    if discard_slot.card.button.function is not None:
                        discard_slot.card.button.check_event(e)


# update the game elements each frame
def update():
    global start_button
    global screen
    global lineup
    global status
    global turn_change_text_counter
    global end_game_text_counter
    global curr_screen
    global screen_counter
    global display_discard

    if status == "home":
        start_button.update(screen)

    if status == "game":
        for slot in lineup:
            if slot.card is not None:
                slot.card.button.update(screen)
        # print("current player: " + str(curr_player))
        for card in curr_player.hand:
            card.button.update(screen)
        if discard_slot.card is not None:
            discard_slot.card.button.update(screen)

        if curr_screen == "replace":
            yes_button.update(screen)
            no_button.update(screen)

        if (not curr_player.hand) and curr_player.power == 0:
            # change this condition
            pass_button.color = (0, 180, 0)
        else:
            pass_button.color = (170, 150, 0)

        pass_button.update(screen)

        if turn_change_text_counter > 0:
            turn_change_text_counter -= 1

        if end_game_text_counter > 0:
            end_game_text_counter -= 1

            if end_game_text_counter == 0:
                status = "home"

        if screen_counter == 0 and (curr_screen == "discard" or curr_screen == "trash"):
            curr_screen = "default"
            display_discard = False

            if return_function is not None:
                print("executing return function")
                return_function()
            print("returning to default screen")


# display text and buttons
def draw():
    global screen
    global curr_player
    global turn_change_text_counter
    global screen_counter
    global display_discard

    screen.fill((0, 0, 0))

    if status == "home":
        start_button.draw()

    if status == "game":
        power_font = pygame.font.Font('freesansbold.ttf', 32)
        text = power_font.render("Power: " + str(curr_player.power), True, pygame.Color('White'))
        screen.blit(text, POWER_LOC)

        for slot in lineup:
            if slot.card is not None:
                slot.card.button.draw()
        for slot in curr_player.loc_list:
            if slot.card is not None:
                slot.card.button.draw()
        for card in curr_player.hand:
            card.button.draw()
        if discard_slot.card is not None:
            discard_slot.card.button.draw()

        pass_button.draw()

        if end_game_text_counter > 0:
            turn_change_font = pygame.font.Font('freesansbold.ttf', 80)
            text = turn_change_font.render("Player " + game_winner + " Wins!", True, pygame.Color('White'))
            screen.blit(text, TURN_CHANGE_LOC)

        elif turn_change_text_counter > 0:
            if curr_player.is_p1:
                player_num = '1'
            else:
                player_num = '2'
            turn_change_font = pygame.font.Font('freesansbold.ttf', 80)
            text = turn_change_font.render("Player " + player_num + " Turn", True, pygame.Color('White'))
            screen.blit(text, TURN_CHANGE_LOC)

        # show replace screen text (asking whether the player wants to replace the lineup)
        if curr_screen == "replace":
            yes_button.draw()
            no_button.draw()
            replace_font = pygame.font.Font('freesansbold.ttf', 35)
            text = replace_font.render("Replace this lineup?", True, pygame.Color('White'))
            screen.blit(text, REPLACE_TEXT_LOC)

        if curr_screen == "discard" or display_discard or curr_screen == "trash":
            screen.fill((100, 100, 100, 100), special_flags=pygame.BLEND_ADD)

        if curr_screen == "discard":
            discard_font = pygame.font.Font('freesansbold.ttf', 50)
            if screen_counter >= 2:
                discard_text = "Discard " + str(screen_counter) + " cards:"
            else:
                discard_text = "Discard a card:"
            text = discard_font.render(discard_text, True, pygame.Color('Black'))
            screen.blit(text, DISCARD_TEXT_LOC)

            # TODO: change to accommodate current player discarding
            for card in curr_player.opponent.hand:
                if card.button is not None:
                    card.select_button.draw()
                # else:
                #     print("card has no button: " + str(card))

        # TODO: change to a may
        if curr_screen == "trash":
            trash_font = pygame.font.Font('freesansbold.ttf', 50)
            if screen_counter >= 2:
                trash_text = "Trash " + str(screen_counter) + " cards:"
            else:
                trash_text = "Trash a card:"
            text = trash_font.render(trash_text, True, pygame.Color('Black'))
            screen.blit(text, DISCARD_TEXT_LOC)

            for card in curr_player.hand:
                if card.button is not None:
                    card.select_button.draw()

        if display_discard:
            pygame.draw.rect(screen, (169, 169, 169), DISPLAY_DISCARD)

            # display the cards in the discard pile
            select_index = [DISPLAY_DISCARD[0] + CUSHION, DISPLAY_DISCARD[1] + CUSHION]
            for card in curr_player.discard_pile:
                # print(select_index)
                card.select_button.rect = pygame.Rect(select_index[0], select_index[1], card.select_button.rect.width,
                                                      card.select_button.rect.height)
                card.select_button.draw()

                select_index[0] += HAND_CARD_DIMS[0] + CUSHION
                if select_index[0] >= DISPLAY_DISCARD[2]:
                    select_index[1] += HAND_CARD_DIMS[1] + CUSHION
                    select_index[0] = DISPLAY_DISCARD[0] + CUSHION


def main_loop():
    global running

    while running:
        pygame.display.set_caption('Build decker')  # text at the top of the window
        handle_events()  # detect inputs
        update()  # update the screen to the next frame
        draw()  # display everything on the screen for the next frame
        pygame.display.flip()
        CLOCK.tick(FPS)


if __name__ == "__main__":
    initialize()
    main_loop()
    pygame.quit()
