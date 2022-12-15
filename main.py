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
global turn_change_counter, end_game_counter  # to count down how long text appears on the screen
global curr_screen, screen_counter, display_discard
# curr_screen: whether a player has to choose to discard cards, replace the lineup, etc., or if they can currently buy
# cards and take actions
# screen_counter: number of cards to be discarded/trashed until we go back to the default screen
global trash_pile
global deck


# to do later: re-implement 2-player play (discard slot corresponds to the current player)
# TODO: implement innovations
# TODO: card text on mouse over

def end_turn():
    global curr_player

    curr_player.pass_turn()


def fill_lineup():
    global lineup
    global deck

    d = 0

    for c in range(len(lineup)):
        if len(deck) == 0:
            end_game()

        lineup[c].add_card()
        # remove the card from the deck and add it to the lineup

        d += 1
        d %= len(deck)


def yes_replace():
    for slot in lineup:
        deck.append(slot.card)
        slot.card = None

    fill_lineup()
    new_turn()


def new_turn():
    global turn_change_counter
    global curr_screen
    global curr_player

    turn_change_counter = 20
    curr_screen = "default"
    # curr_player = curr_player.opponent


class Button:
    def __init__(self, rect, function, image=None, color=SLOT_COLOR, text=""):
        self.rect = pygame.Rect(rect)
        self.function = function
        self.img = image
        self.color = color
        self.font = pygame.font.Font('freesansbold.ttf', 16)
        self.text = self.font.render(text, True, pygame.Color('White'))

    def draw(self):
        global screen

        if self.img:
            pygame.transform.scale(self.img, (self.rect[1], self.rect[2]))
            screen.blit(self.img, self.rect[0], self.rect[1])

        else:
            screen.fill(pygame.Color("black"), self.rect)
            screen.fill(self.color, self.rect.inflate(-4, -4))

        text_rect = self.text.get_rect(center=self.rect.center)
        screen.blit(self.text, text_rect)

    def update(self, surface):
        pass  # check hover? idk what goes here

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


class Card:

    def __init__(self, card_type, cost, power, owned_by=None):
        self.type = card_type
        self.cost = cost
        self.power = power  # amount of power gained when this is played
        self.player = owned_by  # the player that owns this card
        self.slot = None  # the slot in the lineup representing this card
        self.button = None  # clickable rectangle representing the card on the screen
        self.select_button = None  # for selecting the card on a discard/trash screen, etc.
        self.vps = self.cost / 2

    def __str__(self):
        return type(self).__name__  # make customizable

    def buy(self):
        global curr_player
        global lineup

        # print("card object: " + str(self))
        # print("name: " + self.name)
        # print("owned by: " + str(self.owned_by))
        # print("slot: " + str(self.slot))

        # if the player has enough power to buy
        if curr_player.power >= self.cost:
            # print("power: " + str(curr_player.power))
            # print("cost: " + str(self.cost))
            self.player = curr_player
            self.button.function = None

            curr_player.buy(self)

            self.slot.remove()
            self.slot = None

    def add(self, slot):
        self.slot = slot
        self.button = Button(slot.rect, self.buy, color=SLOT_COLOR, text=str(self))

    # everything was handled in the player draw function
    def draw(self, hand_size):
        pass

    # the card is played and has its effect
    def play(self):
        player = self.player
        # print("playing card, owned by " + str(self.player) + ", card name: " + str(self))
        if player == curr_player:
            play_valid = True

            if self.type != "basic" and self.type != "innovation" and player.actions <= 0:
                play_valid = False

            if play_valid:
                player.play(self)
                self.take_effect()

            # self.button = None

        else:
            print("stop playing my cards its not your turn")

    # define this in subclasses
    def take_effect(self):
        pass

    def discard(self):
        global screen_counter
        global deck

        print("discarding card: " + str(self))
        self.player.hand.remove(self)
        self.player.add_to_discard(self)
        screen_counter -= 1

    def trash(self):
        global screen_counter
        global deck
        global trash_pile
        global curr_screen

        print("trashing card: " + str(self) + ", trash counter: " + str(screen_counter))
        # print("curr_screen: " + str(curr_screen))

        # if we trash cards from different places, put that here
        if self.player is not None:
            if self in self.player.hand:
                self.player.hand.remove(self)
            if self in self.player.discard_pile:
                self.player.discard_pile.remove(self)
        if self in deck:
            deck.remove(self)

        trash_pile.append(self)
        self.button = None

        screen_counter -= 1


class Space(Card):
    def __init__(self, player):
        super().__init__("basic", 1, 0, owned_by=player)


class Crystal(Card):
    def __init__(self, player):
        super().__init__("basic", 1, 1, owned_by=player)


class Barter(Card):
    def __init__(self):
        super().__init__("regular", 2, 0)

    def take_effect(self):
        self.player.draw_card()
        self.player.shuffle_discard()  # TODO: change to a may
        # todo: edit text (replace a card or shuffle discard)


class Catalyst(Card):
    def __init__(self):
        super().__init__("regular", 2, 1)

    def take_effect(self):
        self.player.actions += 2


class Sacrifice(Card):
    def __init__(self):
        super().__init__("regular", 2, 0)

    def take_effect(self):
        self.player.draw_card()
        self.player.trash_cards(1)
        # todo: edit text (if you trashed an action, draw 2)


class Scrap(Card):
    def __init__(self):
        super().__init__("regular", 2, 1)

    def take_effect(self):
        self.player.trash_cards(1)


class FavorableExchange(Card):
    def __init__(self):
        super().__init__("regular", 5, 2)

    def take_effect(self):
        self.player.draw_card()


class HiredBandit(Card):
    def __init__(self):
        super().__init__("regular", 7, 2)

    def take_effect(self):
        self.player.get_card(4)


class WeaponHeist(Card):
    def __init__(self):
        super().__init__("attack", 7, 1)

    def take_effect(self):
        self.player.draw_card()
        self.player.opponent.discard_cards(1)


class Pistol(Card):
    def __init__(self):
        super().__init__("attack", 3, 1)

    def take_effect(self):
        self.player.opponent.discard_cards(1)


class FuelCell(Card):
    def __init__(self):
        super().__init__("regular", 3, 2)

    def take_effect(self):
        pass


class MakeshiftBarrier(Card):
    def __init__(self):
        super().__init__("defense", 4, 2)

    def defend(self):
        pass

    # todo: find a way for defenses to work


class Spyglass(Card):
    def __init__(self):
        super().__init__("innovation", 2, 0)

    def take_effect(self):
        empty_slot = False
        for slot in self.player.loc_list:
            if slot.card is None:
                slot.card = self
                empty_slot = True
                break

        if not empty_slot:
            pass  # player has to select a innovation to replace


class AppliedReconnaissance(Card):
    def __init__(self):
        super().__init__("regular", 2, 0)

    def take_effect(self):
        pass


class ReadTheMaps(Card):
    def __init__(self):
        super().__init__("regular", 4, 0)

    def take_effect(self):
        pass
        # TODO: draw cards on conditions


class Jinx(Card):
    def __init__(self):
        super().__init__("regular", 0, 0)

    def take_effect(self):
        # TODO: give op 2 spaces
        self.trash()


# player class, which holds a hand, deck, discard pile, current amount of power, etc.
def show_discard():
    global display_discard
    global screen

    display_discard = True


class Player:

    def __init__(self, player_num):
        self.hand = []
        # create the starting deck
        self.deck = [Space(self), Space(self), Space(self),
                     Crystal(self), Crystal(self), Crystal(self), Crystal(self),
                     Crystal(self), Crystal(self), Crystal(self)]

        self.loc_list = [Slot(0, 100, pygame.Rect(LOC_SLOT_X, LOC_SLOT_Y, LOC_SLOT_WIDTH, LOC_SLOT_HEIGHT)),
                         Slot(0, 100, pygame.Rect(LOC_SLOT_X, LOC_SLOT_Y, LOC_SLOT_WIDTH, LOC_SLOT_HEIGHT)),
                         Slot(0, 100, pygame.Rect(LOC_SLOT_X, LOC_SLOT_Y, LOC_SLOT_WIDTH, LOC_SLOT_HEIGHT))]
        self.discard_pile = []
        self.played = []  # card played this turn, get discarded at the end of the turn
        random.shuffle(self.deck)
        self.is_p1 = player_num % 2

        # draw a 5 card starting hand
        for c in range(5):
            self.draw_card()

        self.power = 0
        self.opponent = None

        self.actions = 2

        self.discard_pile_top = None

    def __str__(self):
        if self.is_p1 == 1:
            return "Player 1"
        else:
            return "Player 2"

    # update the buttons of the cards in hand, so they are in the right place
    def update_hand(self):
        hand_size = len(self.hand)

        for c in range(hand_size):
            self.hand[c].button.rect = \
                pygame.Rect((WIDTH / 2 - (HAND_CARD_DIMS[0] * ((hand_size / 2.0) - c))),
                            DISCARD_PILE_LOC[1], HAND_CARD_DIMS[0], HAND_CARD_DIMS[1])
            # this works don't question it
            if self.hand[c].player is None:
                raise Exception

    def draw_card(self):
        global curr_player

        if len(self.deck) == 0:
            self.shuffle_discard()

        card = self.deck.pop()

        hand_size = len(self.hand)

        self.hand.append(card)

        try:
            if self == curr_player:
                card.button = Button((WIDTH / 2 + (SLOT_WIDTH * (hand_size / 2.0 - 0.5)),
                                      HAND_Y_LOC, SLOT_WIDTH, SLOT_HEIGHT), card.play, color=SLOT_COLOR, text=str(card))
                self.update_hand()
        except NameError:
            card.button = Button((WIDTH / 2 + (SLOT_WIDTH * (hand_size / 2.0 - 0.5)),
                                  HAND_Y_LOC, SLOT_WIDTH, SLOT_HEIGHT), card.play, color=SLOT_COLOR, text=str(card))
            self.update_hand()

    def shuffle_discard(self):
        global discard_slot

        self.deck = self.discard_pile
        self.discard_pile = []
        random.shuffle(self.deck)

        if self.is_p1:
            discard_slot.card = None

    def pass_turn(self):
        global screen
        global turn_change_counter
        global curr_screen

        # print("current turn: " + str(self))
        # print("starting turn of: " + str(self.opponent))

        # all cards played this turn and all cards left in hand go to the discard pile
        for card in self.played:
            self.add_to_discard(card)
        for card in self.hand:
            self.add_to_discard(card)

        self.hand = []
        self.played = []
        self.power = 0

        # draw a new hand of 5
        while len(self.hand) < 5:
            self.draw_card()

        if len(deck) == 0:
            end_game()

        curr_screen = "replace"

        self.actions = 2

    def add_to_discard(self, card):
        global discard_slot
        global curr_player

        self.discard_pile.append(card)

        if self == curr_player:
            if discard_slot.card is not None:
                discard_slot.card.button = None
                # new top card of the discard pile, so we create a new button and get rid of the old one

            discard_slot.card = card
            card.button = Button(
                (DISCARD_PILE_LOC[0], DISCARD_PILE_LOC[1], HAND_CARD_DIMS[0], HAND_CARD_DIMS[1]),
                show_discard, color=SLOT_COLOR, text=str(card))
            card.select_button = Button((0, 0, HAND_CARD_DIMS[0], HAND_CARD_DIMS[1]),
                                        card.trash, color=SLOT_COLOR, text=str(card))

    def buy(self, card):
        self.add_to_discard(card)
        self.power -= card.cost

    def play(self, card):
        if card.type != "basic" and card.type != "innovation":
            self.actions -= 1

            print("taking action, current actions: " + str(self.actions))

        self.power += card.power
        self.hand.remove(card)
        self.played.append(card)

        if card.type == "innovation":
            function = None  # this should be defined when the innovation is constructed
            rect = (LOC_SLOT_X, LOC_SLOT_Y, LOC_SLOT_WIDTH, LOC_SLOT_HEIGHT)
            print(rect)
            card.button = Button(rect, function, color=SLOT_COLOR, text=str(card))

        self.update_hand()  # since we removed a card from the hand, we need to update the visuals

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
    global end_game_counter
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

    end_game_counter = 70


def initialize():
    global running
    global status
    global start_button
    global screen
    global turn_change_counter
    global end_game_counter
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

    turn_change_counter = 0
    end_game_counter = 0
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

    status = "game"

    # add the cards to the communal deck
    deck = []

    for i in range(4):
        deck.append(Barter())

    for i in range(8):
        deck.append(Scrap())

    for i in range(6):
        deck.append(FavorableExchange())

    for i in range(3):
        deck.append(HiredBandit())

    for i in range(3):
        deck.append(WeaponHeist())

    for i in range(4):
        deck.append(Pistol())

    for i in range(6):
        deck.append(FuelCell())

    for i in range(3):
        deck.append(MakeshiftBarrier())

    for i in range(4):
        deck.append(Spyglass())

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

    p1 = Player(1)
    p2 = Player(2)
    p1.opponent = p2
    p2.opponent = p1

    starting_player = random.randrange(1)

    if starting_player == 0:
        curr_player = p1
    else:
        curr_player = p2

    pass_button = Button(END_TURN_RECT, end_turn, color=(100, 70, 0), text="End Turn")

    yes_button = Button(YES_RECT, yes_replace, color=(0, 100, 0), text="yes")
    no_button = Button(NO_RECT, new_turn, color=(100, 0, 0), text="no")


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
                if e.type == pygame.MOUSEBUTTONUP and not display_rect.collidepoint(e.pos):
                    print("exiting display discard")
                    display_discard = False

                if curr_screen == "trash":
                    print("trashing in from discard pile")
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
    global turn_change_counter
    global end_game_counter
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

        if turn_change_counter > 0:
            turn_change_counter -= 1

        if end_game_counter > 0:
            end_game_counter -= 1

            if end_game_counter == 0:
                status = "home"

        if screen_counter == 0 and (curr_screen == "discard" or curr_screen == "trash"):
            curr_screen = "default"
            display_discard = False
            # print("returning to default screen")


# display text and buttons
def draw():
    global screen
    global curr_player
    global turn_change_counter
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

        if end_game_counter > 0:
            turn_change_font = pygame.font.Font('freesansbold.ttf', 80)
            text = turn_change_font.render("Player " + game_winner + " Wins!", True, pygame.Color('White'))
            screen.blit(text, TURN_CHANGE_LOC)

        elif turn_change_counter > 0:
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
