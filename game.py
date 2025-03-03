import pygame
import random

# Game constants and configurations
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
CARD_WIDTH, CARD_HEIGHT = 50, 70

# Card ranks in play and total cards
RANKS = list(range(2, 9))          # [2,3,4,5,6,7,8]
CARDS_PER_RANK = 6
TOTAL_CARDS = CARDS_PER_RANK * len(RANKS)  # 42 cards total
PLAYERS_COUNT = 3
CARDS_PER_PLAYER = TOTAL_CARDS // PLAYERS_COUNT  # 14 each

# Colors (RGB)
GREEN_TABLE = (34, 139, 34)   # table background
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (180, 180, 180)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 200)
RED = (200, 0, 0)

# Positions for AI card placeholder stacks and pile
AI1_POS = (50, 50)  # top-left corner for AI1's cards
AI2_POS = (SCREEN_WIDTH - 50 - CARD_WIDTH, 50)  # top-right for AI2's cards
PILE_POS = ((SCREEN_WIDTH // 2) - (CARD_WIDTH // 2), 
            (SCREEN_HEIGHT // 2) - (CARD_HEIGHT // 2))

# Define a Player class to hold player info
class Player:
    def __init__(self, name, is_ai):
        self.name = name
        self.is_ai = is_ai
        self.hand = []  # list of card ranks in player's hand

# Initialize Pygame and create window
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Bluff Card Game")
clock = pygame.time.Clock()

# Load fonts for text
font_small = pygame.font.Font(None, 24)   # for card ranks and small labels
font_large = pygame.font.Font(None, 36)   # for general messages
font_huge = pygame.font.Font(None, 64)    # for winner announcement

# Create card face surfaces for each rank (white card with rank number)
card_face = {}
for rank in RANKS:
    surf = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
    surf.fill(WHITE)
    pygame.draw.rect(surf, BLACK, surf.get_rect(), 2)  # black border
    text = font_small.render(str(rank), True, BLACK)
    text_rect = text.get_rect(center=(CARD_WIDTH//2, CARD_HEIGHT//2))
    surf.blit(text, text_rect)
    card_face[rank] = surf

# Create card back surface (for hidden cards)
card_back = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
card_back.fill(BLUE)
pygame.draw.rect(card_back, BLACK, card_back.get_rect(), 2)
back_text = font_small.render("X", True, WHITE)  # 'X' to mark back
back_text_rect = back_text.get_rect(center=(CARD_WIDTH//2, CARD_HEIGHT//2))
card_back.blit(back_text, back_text_rect)

# Define buttons as rectangles for confirm, call, and reset
confirm_button = pygame.Rect(SCREEN_WIDTH//2 - 60, SCREEN_HEIGHT - 40, 120, 30)
call_button = pygame.Rect(50, SCREEN_HEIGHT - 40, 100, 30)
reset_button = pygame.Rect(SCREEN_WIDTH//2 - 50, SCREEN_HEIGHT//2 + 50, 100, 30)

# Game state variables
players = []
current_player = 0         # index of current player's turn
current_rank = RANKS[0]    # current required rank to play (cycles through RANKS)
pile = []                  # face-down pile of played cards (list of ranks)
selected_indices = []      # indices of cards selected by human player
last_action_msg = ""       # message describing the last action for display
game_over = False
winner = None

# Function to reset and start a new game
def reset_game():
    global players, current_player, current_rank, pile, selected_indices
    global last_action_msg, game_over, winner
    # Create and shuffle the deck of 42 cards
    deck = []
    for rank in RANKS:
        deck += [rank] * CARDS_PER_RANK
    random.shuffle(deck)
    # Initialize players and deal cards
    players = [
        Player("You", is_ai=False),
        Player("AI 1", is_ai=True),
        Player("AI 2", is_ai=True)
    ]
    for i, player in enumerate(players):
        hand_cards = deck[i*CARDS_PER_PLAYER : (i+1)*CARDS_PER_PLAYER]
        player.hand = sorted(hand_cards)  # sort hand by rank for convenience
    # Choose a random starting player and starting rank 2
    current_player = random.randrange(PLAYERS_COUNT)
    current_rank = RANKS[0]   # starting at 2
    pile = []
    selected_indices = []
    last_action_msg = f"{players[current_player].name} starts. Rank {current_rank} to play."
    game_over = False
    winner = None

# Call reset_game once to start the first game
reset_game()

# Helper function for AI to decide what cards to play on its turn
def ai_play_turn(player_index, required_rank):
    """Select cards for AI player to play. Returns list of actual card ranks played."""
    player = players[player_index]
    hand = player.hand
    actual_cards = []  # cards AI will actually play from its hand
    declared = required_rank  # AI will declare the required rank
    
    # Check if AI has any card of the required rank
    has_required = required_rank in hand
    will_bluff = False
    if has_required:
        # AI has at least one required-rank card; decide randomly if to bluff
        # (e.g., 30% chance to bluff even if it can play honestly)
        if random.random() < 0.3:
            will_bluff = True
    else:
        # AI does not have the required rank, so it must bluff
        will_bluff = True

    if not will_bluff:
        # Play honestly: use one (sometimes two) of the required rank
        count_required = hand.count(required_rank)
        # If AI has multiple of the rank, it might play 2 at once (50% chance)
        cards_to_play = 1
        if count_required > 1 and random.random() < 0.5:
            cards_to_play = 2
        # Remove that many required-rank cards from hand
        for _ in range(cards_to_play):
            if required_rank in hand:
                hand.remove(required_rank)
                actual_cards.append(required_rank)
    else:
        # Bluffing: choose a card (or two) of some other rank to play
        # Pick a rank from hand that is not the required rank
        other_ranks = [r for r in hand if r != required_rank]
        if not other_ranks:
            # If somehow all cards are of the required rank (rare), just use one of them
            other_ranks = hand[:]
        # Choose the rank the AI has the most of, to discard heavier
        if other_ranks:
            rank_to_play = max(set(other_ranks), key=other_ranks.count)
        else:
            rank_to_play = required_rank  # fallback (though this case is unlikely)
        # Decide to play one or two of that rank
        count_available = hand.count(rank_to_play)
        cards_to_play = 1
        if count_available > 1 and random.random() < 0.5:
            cards_to_play = 2
        for _ in range(cards_to_play):
            # Remove the chosen rank card from hand to play
            if rank_to_play in hand:
                hand.remove(rank_to_play)
                actual_cards.append(rank_to_play)
    # Now actual_cards contains the ranks AI is throwing (maybe not the same as declared)
    return actual_cards

# Helper function for AI to decide whether to call bluff on someone else's play
def ai_decide_call(ai_index, declared_rank, count_played):
    """Return True if AI player at ai_index will call bluff on a play of 'count_played' cards of 'declared_rank'."""
    ai_hand = players[ai_index].hand
    ai_count = ai_hand.count(declared_rank)  # how many of declared rank AI holds
    total_rank_cards = CARDS_PER_RANK  # total number of cards of that rank in game (6)
    # If the play is impossible given what AI holds (holds + played > 6), definitely call
    if ai_count + count_played > total_rank_cards:
        return True
    # Otherwise decide based on suspicion factors
    # Calculate probability of calling (base on how many played and how many AI has)
    call_prob = 0.0
    if ai_count + count_played == total_rank_cards:
        # All cards of that rank would be accounted for between AI and played cards
        if count_played >= 2:
            call_prob = 0.5  # suspicious if multiple cards claimed and AI has the rest
        else:
            call_prob = 0.2  # slightly suspicious even if one card (AI holds most of them)
    else:
        # There are still unaccounted cards potentially with the third player
        if count_played >= 3:
            call_prob = 0.3  # a big play (3+) is somewhat risky, call with some chance
        elif count_played == 2:
            call_prob = 0.1  # 2 cards might raise a little suspicion
        else:
            call_prob = 0.0  # single card and nothing impossible, likely no call
    # Randomize the call decision against the probability threshold
    return (random.random() < call_prob)

# Function to handle moving a card image smoothly from one point to another (animation)
def animate_card_move(start_pos, end_pos, card_surf):
    """Animate a card moving from start_pos to end_pos."""
    steps = 15  # number of animation steps (frames)
    dx = (end_pos[0] - start_pos[0]) / steps
    dy = (end_pos[1] - start_pos[1]) / steps
    x, y = start_pos
    for _ in range(steps):
        # Clear and redraw the scene behind the moving card
        draw_game_state()  
        # Draw the moving card at the current interpolated position
        screen.blit(card_surf, (x, y))
        pygame.display.flip()
        clock.tick(60)  # maintain frame rate
        # Increment position
        x += dx
        y += dy

# Function to draw all game elements on the screen (called each frame)
def draw_game_state():
    # Fill background
    screen.fill(GREEN_TABLE)
    # Draw pile (if any cards in pile)
    if pile:
        screen.blit(card_back, PILE_POS)  # show one card back
        # Display number of cards in pile on top of the card
        pile_count_text = font_small.render(str(len(pile)), True, YELLOW)
        pile_text_rect = pile_count_text.get_rect(center=(PILE_POS[0] + CARD_WIDTH//2, PILE_POS[1] + CARD_HEIGHT//2))
        screen.blit(pile_count_text, pile_text_rect)
    # Draw players' cards and info
    # Human (player 0) - show all cards
    user = players[0]
    hand = user.hand
    # Determine spacing for user's hand so it spans nicely
    if hand:
        margin = min(50, (SCREEN_WIDTH - 100) // len(hand))
    else:
        margin = 50
    start_x = (SCREEN_WIDTH - (CARD_WIDTH + margin*(len(hand)-1) )) // 2 if hand else SCREEN_WIDTH//2
    for idx, card_rank in enumerate(hand):
        # If this card is selected, raise it up a bit
        x = start_x + idx * margin
        y = SCREEN_HEIGHT - CARD_HEIGHT - 20
        if idx in selected_indices:
            y -= 10  # raise selected card
        # Draw the card face (since user can see own cards)
        screen.blit(card_face[card_rank], (x, y))
    # Draw user's label or card count (optional, since they see their hand, but we can show count)
    user_label = font_small.render(f"You: {len(hand)} cards", True, YELLOW if current_player == 0 else WHITE)
    user_label_rect = user_label.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - CARD_HEIGHT - 40))
    screen.blit(user_label, user_label_rect)
    # AI1 (player 1) - show card backs and count
    ai1 = players[1]
    ai1_count = len(ai1.hand)
    # Draw up to 3 overlapping card backs as a placeholder for AI's hand
    overlap = 10  # overlap offset in pixels
    for i in range(min(3, ai1_count)):
        screen.blit(card_back, (AI1_POS[0] + i*overlap, AI1_POS[1]))
    # AI1 label with count
    ai1_label = font_small.render(f"AI 1: {ai1_count} cards", True, YELLOW if current_player == 1 else WHITE)
    # Place the label above AI1's cards
    ai1_label_rect = ai1_label.get_rect(topleft=(AI1_POS[0], AI1_POS[1] - 20))
    screen.blit(ai1_label, ai1_label_rect)
    # AI2 (player 2) - show card backs and count
    ai2 = players[2]
    ai2_count = len(ai2.hand)
    for i in range(min(3, ai2_count)):
        # Overlap to the left for AI2 (so cards fan leftwards)
        screen.blit(card_back, (AI2_POS[0] - i*overlap, AI2_POS[1]))
    ai2_label = font_small.render(f"AI 2: {ai2_count} cards", True, YELLOW if current_player == 2 else WHITE)
    # Place the label above AI2's cards (align right with cards)
    ai2_label_rect = ai2_label.get_rect(topright=(AI2_POS[0] + CARD_WIDTH, AI2_POS[1] - 20))
    screen.blit(ai2_label, ai2_label_rect)
    # Draw the current required rank at top-center
    rank_text = font_large.render(f"Current Rank: {current_rank}", True, WHITE)
    rank_rect = rank_text.get_rect(midtop=(SCREEN_WIDTH//2, 10))
    screen.blit(rank_text, rank_rect)
    # Draw last action/status message (if any)
    if last_action_msg:
        action_text = font_large.render(last_action_msg, True, WHITE)
        action_rect = action_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 10))
        screen.blit(action_text, action_rect)
    # If game is over, draw winner announcement and reset button
    if game_over and winner is not None:
        win_text = font_huge.render(f"{winner} wins!", True, YELLOW)
        win_rect = win_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        screen.blit(win_text, win_rect)
        # Draw reset button
        pygame.draw.rect(screen, GRAY, reset_button)
        reset_label = font_small.render("Reset", True, BLACK)
        reset_label_rect = reset_label.get_rect(center=reset_button.center)
        screen.blit(reset_label, reset_label_rect)
    else:
        # If game not over, draw action buttons (Confirm on user's turn, Call on AI's turn)
        if players[current_player].is_ai:
            # It's an AI turn that has played, maybe allow call button if in call phase
            if waiting_for_call and players[current_player].is_ai:
                pygame.draw.rect(screen, RED, call_button)
                call_text = font_small.render("Call Bluff", True, WHITE)
                call_text_rect = call_text.get_rect(center=call_button.center)
                screen.blit(call_text, call_text_rect)
        else:
            # It's the human's turn, show confirm button
            pygame.draw.rect(screen, GRAY, confirm_button)
            conf_text = font_small.render("Confirm", True, BLACK)
            conf_text_rect = conf_text.get_rect(center=confirm_button.center)
            screen.blit(conf_text, conf_text_rect)

# Variables to manage call timing on AI turns
waiting_for_call = False
call_timer_start = 0
potential_caller_index = None
potential_caller_call = False

# Main game loop
running = True
while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            if game_over:
                # If game over, only respond to Reset button
                if reset_button.collidepoint(mouse_pos):
                    reset_game()
                continue  # skip other interactions when game is over
            # If not game over:
            current_player_obj = players[current_player]
            if current_player_obj.is_ai:
                # If it's AI's turn and we're in the call waiting phase, allow human to click "Call Bluff"
                if waiting_for_call and call_button.collidepoint(mouse_pos):
                    # Human calls bluff on AI's play
                    caller_index = 0  # human
                    waiting_for_call = False  # end call waiting phase
                    # Determine outcome of call
                    accused_index = current_player  # AI who just played
                    # Check if the AI was bluffing (compare actual cards vs declared rank)
                    # last_play_info holds what AI actually played
                    liar = False
                    if last_play_info:
                        declared = last_play_info['declared']
                        actual_cards = last_play_info['cards']
                        # If any actual card is not of the declared rank, it was a bluff
                        if any(card != declared for card in actual_cards):
                            liar = True
                    # Prepare message about call result
                    if liar:
                        last_action_msg = f"You called bluff on {players[accused_index].name}! It WAS a bluff."
                    else:
                        last_action_msg = f"You called bluff on {players[accused_index].name}, but they were honest."
                    # Split the pile between the two players (accused and caller)
                    total_cards = len(pile)
                    half = total_cards // 2
                    # If odd number of cards, let caller take the extra one (arbitrary choice)
                    for i in range(total_cards):
                        if i < half:
                            players[accused_index].hand.append(pile[i])
                        else:
                            players[caller_index].hand.append(pile[i])
                    # Clear the pile on table
                    pile.clear()
                    # Sort hands (optional, to keep order tidy after adding cards)
                    players[accused_index].hand.sort()
                    players[caller_index].hand.sort()
                    # Animate cards splitting (optional simple animation: one card to each in alternation)
                    # We'll simulate by moving a few representative cards for visual effect
                    cards_to_animate = min(4, total_cards)  # animate at most 4 cards for brevity
                    for j in range(cards_to_animate):
                        if j % 2 == 0:
                            # move card to accused player's area
                            target_idx = accused_index
                        else:
                            # move card to caller's area
                            target_idx = caller_index
                        # Determine target position (center of player's area)
                        if target_idx == 0:   # user
                            target_pos = (SCREEN_WIDTH//2, SCREEN_HEIGHT - CARD_HEIGHT - 20)
                        elif target_idx == 1: # AI1
                            target_pos = AI1_POS
                        else:                 # AI2
                            target_pos = AI2_POS
                        animate_card_move(PILE_POS, target_pos, card_back)
                    # Determine next player (regardless of call outcome, move to next in turn order)
                    current_player = (accused_index + 1) % PLAYERS_COUNT
                    # Advance rank in sequence
                    rank_index = RANKS.index(current_rank)
                    current_rank = RANKS[(rank_index + 1) % len(RANKS)]
                    # After call resolution, check win condition for any player
                    for player in players:
                        if len(player.hand) <= 5:
                            game_over = True
                            winner = player.name
                    # End of call resolution
            else:
                # It's the human's turn: allow card selection and confirm play
                # Check if a card in user's hand was clicked
                user_hand = players[0].hand
                # Compute card positions similar to draw_game_state to determine which card was clicked
                if user_hand:
                    margin = min(50, (SCREEN_WIDTH - 100) // len(user_hand))
                else:
                    margin = 50
                start_x = (SCREEN_WIDTH - (CARD_WIDTH + margin*(len(user_hand)-1))) // 2 if user_hand else SCREEN_WIDTH//2
                card_clicked = False
                for idx, card_rank in enumerate(user_hand):
                    card_x = start_x + idx * margin
                    card_y = SCREEN_HEIGHT - CARD_HEIGHT - 20
                    card_rect = pygame.Rect(card_x, card_y, CARD_WIDTH, CARD_HEIGHT)
                    # If this card was raised (selected), adjust rect position to match
                    if idx in selected_indices:
                        card_rect.y -= 10
                    if card_rect.collidepoint(mouse_pos):
                        card_clicked = True
                        # Toggle selection of this card
                        if idx in selected_indices:
                            # Deselect if already selected
                            selected_indices.remove(idx)
                        else:
                            # If selecting a new card, ensure it matches rank of any already selected cards
                            if not selected_indices:
                                # No selection yet, select this card
                                selected_indices.append(idx)
                            else:
                                # There is an existing selection; check rank
                                first_sel_rank = user_hand[selected_indices[0]]
                                if card_rank == first_sel_rank:
                                    selected_indices.append(idx)  # same rank, allow adding
                                else:
                                    # Different rank – reset selection to this single card
                                    selected_indices.clear()
                                    selected_indices.append(idx)
                        break
                # If not clicking on a card, check if Confirm button was clicked
                if not card_clicked and confirm_button.collidepoint(mouse_pos):
                    if selected_indices:
                        # Human confirms playing selected cards
                        # Determine actual cards and declared rank (which is current_rank)
                        selected_indices.sort()
                        actual_cards = [user_hand[i] for i in selected_indices]
                        declared = current_rank
                        # Remove these cards from user's hand
                        # Remove in reverse order to avoid index shifting
                        for i in sorted(selected_indices, reverse=True):
                            user_hand.pop(i)
                        selected_indices.clear()
                        # Add to pile
                        pile.extend(actual_cards)
                        # Record last play info for potential bluff checking
                        last_play_info = {'player': 0, 'declared': declared, 'cards': actual_cards.copy()}
                        # Compose message about the play
                        last_action_msg = f"You played {len(actual_cards)} card(s) of {declared}."
                        # Animate cards moving to pile
                        # Compute original positions of the cards that were played for animation
                        start_positions = []
                        if actual_cards:
                            margin = min(50, (SCREEN_WIDTH - 100) // (len(user_hand) + len(actual_cards)))
                            start_x = (SCREEN_WIDTH - (CARD_WIDTH + margin*(len(user_hand)+len(actual_cards)-1))) // 2
                        else:
                            margin = 50
                            start_x = SCREEN_WIDTH//2
                        # Note: We compute as if cards were still in hand (approximate positions)
                        for card_rank in actual_cards:
                            # The first selected index's original x position (they were contiguous rank)
                            # For simplicity, animate all from the position of the first selected card
                            break
                        if actual_cards:
                            # Use the first removed card's slot as animation start
                            first_idx = (start_x + (len(user_hand)) * margin) if user_hand else start_x
                            first_card_pos = (first_idx, SCREEN_HEIGHT - CARD_HEIGHT - 20)
                            animate_card_move(first_card_pos, PILE_POS, card_face[actual_cards[0]])
                        # After human plays, check if AI players call bluff
                        caller_index = None
                        # Let both AIs consider calling; pick the first that decides to call
                        ai_indices = [1, 2]
                        random.shuffle(ai_indices)  # randomize order of who gets to react first
                        for ai_idx in ai_indices:
                            if ai_decide_call(ai_idx, declared, len(actual_cards)):
                                caller_index = ai_idx
                                break
                        if caller_index is not None:
                            # An AI called bluff on the user
                            accused_index = 0  # user is the one who just played
                            # Check if user was bluffing (did all actual cards match declared rank?)
                            liar = False
                            if any(card != declared for card in actual_cards):
                                liar = True
                            if liar:
                                last_action_msg = f"{players[caller_index].name} calls bluff! You were BLUFFING."
                            else:
                                last_action_msg = f"{players[caller_index].name} calls bluff, but you were honest."
                            # Split the pile between user (accused) and AI caller
                            total_cards = len(pile)
                            half = total_cards // 2
                            for j in range(total_cards):
                                if j < half:
                                    players[accused_index].hand.append(pile[j])
                                else:
                                    players[caller_index].hand.append(pile[j])
                            pile.clear()
                            players[accused_index].hand.sort()
                            players[caller_index].hand.sort()
                            # Animate a few cards moving from center pile to each player
                            cards_to_animate = min(4, total_cards)
                            for j in range(cards_to_animate):
                                if j % 2 == 0:
                                    target_idx = accused_index
                                else:
                                    target_idx = caller_index
                                if target_idx == 0:
                                    target_pos = (SCREEN_WIDTH//2, SCREEN_HEIGHT - CARD_HEIGHT - 20)
                                elif target_idx == 1:
                                    target_pos = AI1_POS
                                else:
                                    target_pos = AI2_POS
                                animate_card_move(PILE_POS, target_pos, card_back)
                            # Next player is still the one after the user (even though call interrupted)
                            current_player = (accused_index + 1) % PLAYERS_COUNT
                            # Advance rank
                            rank_index = RANKS.index(current_rank)
                            current_rank = RANKS[(rank_index + 1) % len(RANKS)]
                            # Check win condition for any player
                            for player in players:
                                if len(player.hand) <= 5:
                                    game_over = True
                                    winner = player.name
                        else:
                            # No AI called the bluff, play stands
                            # Check if user now has <=5 cards (win condition)
                            if len(players[0].hand) <= 5:
                                game_over = True
                                winner = players[0].name
                            # Advance to next turn if game not over
                            if not game_over:
                                current_player = (current_player + 1) % PLAYERS_COUNT
                                # Advance rank in sequence
                                rank_index = RANKS.index(current_rank)
                                current_rank = RANKS[(rank_index + 1) % len(RANKS)]
            # End of MOUSEBUTTONDOWN handling

    # If game is over, just update display (reset happens via button event above)
    if game_over:
        draw_game_state()
        pygame.display.flip()
        clock.tick(30)
        continue

    # If it's an AI player's turn (and not currently waiting for call resolution)
    if not players[current_player].is_ai:
        # Human player's turn: just wait for user input (handled in events above)
        pass
    else:
        # AI player's turn logic
        if not waiting_for_call:
            # Simulate a short "thinking" delay for the AI
            pygame.time.delay(500)
            # AI selects and plays cards
            actual_cards = ai_play_turn(current_player, current_rank)
            # The AI declares the current_rank (may or may not match actual_cards)
            declared = current_rank
            # Update pile with these cards
            pile.extend(actual_cards)
            # Record last play info (for checking bluff later)
            last_play_info = {'player': current_player, 'declared': declared, 'cards': actual_cards.copy()}
            # Compose action message
            last_action_msg = f"{players[current_player].name} plays {len(actual_cards)} card(s) of {declared}."
            # Animate AI's card moving to pile (use one card back as representation)
            start_pos = AI1_POS if current_player == 1 else AI2_POS
            animate_card_move(start_pos, PILE_POS, card_back)
            # Set up call phase for human/other AI to possibly call bluff
            waiting_for_call = True
            call_timer_start = pygame.time.get_ticks()
            # Identify the other AI (aside from current player) who could call
            potential_caller_index = 1 if current_player == 2 else 2  # the AI that is not current (since current is either 1 or 2)
            # Determine in advance if that AI intends to call (will execute after short delay if user doesn't call)
            potential_caller_call = ai_decide_call(potential_caller_index, declared, len(actual_cards))
        else:
            # Already waiting for call (which means an AI just played and we gave time for user to call)
            # Check if the call waiting period has expired
            if pygame.time.get_ticks() - call_timer_start > 1000:  # 1 second window for user to call
                # Time up, resolve whether the other AI calls or not
                caller_index = None
                if potential_caller_call:
                    caller_index = potential_caller_index
                waiting_for_call = False  # end call phase
                if caller_index is not None:
                    # Other AI calls bluff on the AI that just played
                    accused_index = current_player
                    liar = False
                    # Check if the accused AI lied about their cards
                    if last_play_info:
                        declared = last_play_info['declared']
                        actual_cards = last_play_info['cards']
                        if any(card != declared for card in actual_cards):
                            liar = True
                    if liar:
                        last_action_msg = f"{players[caller_index].name} calls bluff on {players[accused_index].name}! Bluff confirmed."
                    else:
                        last_action_msg = f"{players[caller_index].name} calls bluff on {players[accused_index].name}, but it was truthful."
                    # Split pile between the AI who played and the AI who called
                    total_cards = len(pile)
                    half = total_cards // 2
                    for i in range(total_cards):
                        if i < half:
                            players[accused_index].hand.append(pile[i])
                        else:
                            players[caller_index].hand.append(pile[i])
                    pile.clear()
                    players[accused_index].hand.sort()
                    players[caller_index].hand.sort()
                    # Quick animation of cards moving from pile to each AI (two moves to illustrate)
                    animate_card_move(PILE_POS, AI1_POS if accused_index == 1 else AI2_POS, card_back)
                    animate_card_move(PILE_POS, AI1_POS if caller_index == 1 else AI2_POS, card_back)
                    # Next player is the one after the accused (current_player) in turn order
                    current_player = (accused_index + 1) % PLAYERS_COUNT
                    # Advance rank
                    rank_index = RANKS.index(current_rank)
                    current_rank = RANKS[(rank_index + 1) % len(RANKS)]
                else:
                    # No one called within the window
                    # No call scenario: check if current AI (who just played) won by reducing hand
                    if len(players[current_player].hand) <= 5:
                        game_over = True
                        winner = players[current_player].name
                    # Advance to next turn if game continues
                    if not game_over:
                        current_player = (current_player + 1) % PLAYERS_COUNT
                        rank_index = RANKS.index(current_rank)
                        current_rank = RANKS[(rank_index + 1) % len(RANKS)]
    # Draw the current game state
    draw_game_state()
    pygame.display.flip()
    clock.tick(60)

# Quit Pygame when loop ends
pygame.quit()
