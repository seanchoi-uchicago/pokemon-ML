import pygame
import os
import sys
import json
from PIL import Image
import time

# Get the absolute path to the project root directory
current_file = os.path.abspath(__file__)  # src/gui/pokemon_battle_gui.py
gui_dir = os.path.dirname(current_file)  # src/gui
src_dir = os.path.dirname(gui_dir)  # src
project_root = os.path.dirname(src_dir)  # project root

# Add the project root to Python path
sys.path.insert(0, project_root)

try:
    from pokemon_battle import Pokemon, Team, Battle, BattleMode, POKEMON_DATA
except ImportError as e:
    print(f"Error importing pokemon_battle: {e}")
    sys.exit(1)

class PokemonBattleGUI:
    def __init__(self):
        try:
            # Initialize Pygame
            pygame.init()
            
            # Set up the display with fixed size
            self.width = 1050
            self.height = 680  # 540 for image + 20px padding + 100 for log + 20px padding
            self.screen = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption("Pokémon Battle System")
            
            # Create a surface for the background
            self.background_surface = pygame.Surface((self.width, 540))
            
            # Initialize Pokémon data
            self.pokemon_data = POKEMON_DATA
            self.pokemon_list = sorted(self.pokemon_data.keys())
            
            # Initialize battle state
            self.battle = None
            self.player_team = None
            self.opponent_team = None
            self.battle_mode = "single"
            self.selected_pokemon = [""] * 12  # 6 for player, 6 for opponent
            self.current_view = "team_selection"  # or "battle"
            
            # Battle timing
            self.last_turn_time = 0
            self.turn_delay = 200  # 1 second between turns
            
            # Load fonts
            self.font = pygame.font.Font(None, 32)
            self.small_font = pygame.font.Font(None, 24)
            
            # Load sprites
            self.load_sprites()
            
            # Initialize battle log
            self.battle_log = []
            
            # Track if we need to redraw
            self.needs_redraw = True
            
            # Text input state
            self.active_input = None
            self.input_rects = []
            self.init_input_boxes()
            
        except Exception as e:
            print(f"Error initializing GUI: {e}")
            raise

    def init_input_boxes(self):
        """Initialize text input boxes for team selection."""
        self.input_rects = []
        box_width = 200
        box_height = 40
        spacing = 60
        
        # Player team input boxes
        for i in range(6):
            x = 50
            y = 150 + i * spacing
            rect = pygame.Rect(x, y, box_width, box_height)
            self.input_rects.append(rect)
        
        # Opponent team input boxes
        for i in range(6):
            x = self.width//2 + 50
            y = 150 + i * spacing
            rect = pygame.Rect(x, y, box_width, box_height)
            self.input_rects.append(rect)

    def load_sprites(self):
        """Load all Pokémon sprites."""
        self.sprites = {}
        sprite_dirs = {
            "front": os.path.join(src_dir, "setup", "data-collection", "sprites", "front"),
            "back": os.path.join(src_dir, "setup", "data-collection", "sprites", "back"),
            "background": os.path.join(src_dir, "setup", "data-collection", "sprites", "background")
        }
        
        # Load background first
        background_path = os.path.join(sprite_dirs["background"], "battle_background.jpg")
        if os.path.exists(background_path):
            try:
                self.background = pygame.image.load(background_path)
                # Scale background to exactly 1050x540
                self.background = pygame.transform.scale(self.background, (1050, 540))
            except Exception as e:
                self.background = None
        else:
            self.background = None
        
        # Load Pokémon sprites
        for view, dir_path in sprite_dirs.items():
            if view == "background":
                continue
                
            print(f"\nLoading {view} sprites from: {dir_path}")
            self.sprites[view] = {}
            
            # First, try to load Garchomp as the fallback sprite
            fallback_path = os.path.join(dir_path, "garchomp.png")
            fallback_sprite = None
            if os.path.exists(fallback_path):
                try:
                    fallback_sprite = pygame.image.load(fallback_path)
                    fallback_sprite = pygame.transform.scale(fallback_sprite, (150, 150))
                except Exception as e:
                    print(f"Error loading fallback sprite: {e}")
            
            # Now load all Pokémon sprites
            for pokemon in self.pokemon_list:
                sprite_path = os.path.join(dir_path, f"{pokemon.lower().replace(' ', '-')}.png")
                if os.path.exists(sprite_path):
                    try:
                        image = pygame.image.load(sprite_path)
                        image = pygame.transform.scale(image, (150, 150))
                        self.sprites[view][pokemon] = image
                    except Exception as e:
                        print(f"Error loading sprite for {pokemon}: {e}")
                        if fallback_sprite:
                            self.sprites[view][pokemon] = fallback_sprite
                        else:
                            print(f"No fallback sprite available for {pokemon}")
                else:
                    print(f"Sprite not found for {pokemon} at {sprite_path}")
                    if fallback_sprite:
                        self.sprites[view][pokemon] = fallback_sprite
                    else:
                        print(f"No fallback sprite available for {pokemon}")

    def draw_team_selection(self):
        """Draw the team selection screen."""
        # Clear screen
        self.screen.fill((255, 255, 255))
        
        # Draw title
        title = self.font.render("Select Your Teams", True, (0, 0, 0))
        self.screen.blit(title, (self.width//2 - title.get_width()//2, 20))
        
        # Draw battle mode selection
        mode_text = self.font.render(f"Battle Mode: {self.battle_mode.title()}", True, (0, 0, 0))
        self.screen.blit(mode_text, (20, 60))
        
        # Draw player team selection
        player_title = self.font.render("Player's Team", True, (0, 0, 0))
        self.screen.blit(player_title, (50, 100))
        
        # Draw opponent team selection
        opponent_title = self.font.render("Opponent's Team", True, (0, 0, 0))
        self.screen.blit(opponent_title, (self.width//2 + 50, 100))
        
        # Draw input boxes first
        for i, rect in enumerate(self.input_rects):
            # Draw input box
            color = (200, 200, 200) if self.active_input == i else (255, 255, 255)
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, (100, 100, 100), rect, 2)
            
            # Draw availability indicator
            pokemon_name = self.selected_pokemon[i].lower()
            if pokemon_name in self.pokemon_data:
                # Green circle for available Pokémon
                pygame.draw.circle(self.screen, (0, 255, 0), (rect.right + 20, rect.centery), 10)
            elif pokemon_name:  # Only show red if there's text
                # Red circle for unavailable Pokémon
                pygame.draw.circle(self.screen, (255, 0, 0), (rect.right + 20, rect.centery), 10)
        
        # Draw Start Battle button
        pygame.draw.rect(self.screen, (76, 175, 80), (self.width//2 - 100, 500, 200, 50))
        start_text = self.font.render("Start Battle", True, (255, 255, 255))
        self.screen.blit(start_text, (self.width//2 - start_text.get_width()//2, 510))
        
        # Draw instructions
        instructions = self.small_font.render("Click a box to type, press ENTER when done", True, (100, 100, 100))
        self.screen.blit(instructions, (20, 550))
        
        # Draw all text last to ensure visibility
        for i, rect in enumerate(self.input_rects):
            # Draw text
            text = self.small_font.render(self.selected_pokemon[i], True, (0, 0, 0))
            text_rect = text.get_rect(midleft=(rect.x + 10, rect.centery))
            self.screen.blit(text, text_rect)
            
            # Draw cursor if this is the active input
            if self.active_input == i:
                cursor_x = text_rect.right + 2
                cursor_y = text_rect.centery - 10
                pygame.draw.line(self.screen, (0, 0, 0), 
                               (cursor_x, cursor_y), 
                               (cursor_x, cursor_y + 20), 2)
        
        # Force redraw
        pygame.display.flip()

    def draw_battle(self):
        """Draw the battle screen."""
        if not self.needs_redraw:
            return
            
        # Draw background if available
        if self.background:
            self.background_surface.blit(self.background, (0, 0))
        else:
            # Fallback to drawing basic background
            self.background_surface.fill((255, 255, 255))  # White background as fallback
        
        # Draw active Pokémon
        if self.battle:
            # Player's Pokémon
            if self.battle.battle_mode == BattleMode.SINGLE:
                player_pokemon = [self.player_team.active_pokemon]
                opponent_pokemon = [self.opponent_team.active_pokemon]
            else:
                player_pokemon = self.player_team.active_pokemon
                opponent_pokemon = self.opponent_team.active_pokemon
            
            # Draw player's Pokémon
            for i, pokemon in enumerate(player_pokemon):
                if pokemon.name in self.sprites["back"]:
                    sprite = self.sprites["back"][pokemon.name]
                    # Position player's Pokémon on the left side, shifted 120 pixels right from previous position
                    x = 220 + i * 200  # Changed from 40 to 160
                    y = 300
                    self.background_surface.blit(sprite, (x, y))
                    # Draw name
                    name_text = self.small_font.render(pokemon.name, True, (0, 0, 0))
                    self.background_surface.blit(name_text, (x, y + 160))
                    # Draw HP
                    hp_text = self.small_font.render(f"HP: {pokemon.current_hp}/{pokemon.hp}", True, (0, 0, 0))
                    self.background_surface.blit(hp_text, (x, y + 180))
                else:
                    print(f"No back sprite found for {pokemon.name}")
            
            # Draw opponent's Pokémon
            for i, pokemon in enumerate(opponent_pokemon):
                if pokemon.name in self.sprites["front"]:
                    sprite = self.sprites["front"][pokemon.name]
                    # Position opponent's Pokémon on the right side
                    x = 620 + i * 200
                    y = 160
                    self.background_surface.blit(sprite, (x, y))
                    # Draw name
                    name_text = self.small_font.render(pokemon.name, True, (0, 0, 0))
                    self.background_surface.blit(name_text, (x, y + 160))
                    # Draw HP
                    hp_text = self.small_font.render(f"HP: {pokemon.current_hp}/{pokemon.hp}", True, (0, 0, 0))
                    self.background_surface.blit(hp_text, (x, y + 180))
                else:
                    print(f"No front sprite found for {pokemon.name}")
        
        # Blit the background surface to the screen
        self.screen.blit(self.background_surface, (0, 0))
        
        # Draw white rectangle between background and textbox
        pygame.draw.rect(self.screen, (255, 255, 255), (0, 540, 1050, 140))
        
        # Draw battle log below the background image
        log_surface = pygame.Surface((self.width - 40, 100))
        log_surface.fill((255, 255, 255))
        pygame.draw.rect(log_surface, (200, 200, 200), (0, 0, self.width - 40, 100), 2)  # Add border
        
        # Draw log title
        title_text = self.small_font.render("Battle Log", True, (0, 0, 0))
        log_surface.blit(title_text, (10, 5))
        
        # Draw log messages
        y = 30
        for message in self.battle_log[-4:]:  # Show last 4 messages
            text = self.small_font.render(message, True, (0, 0, 0))
            log_surface.blit(text, (10, y))
            y += 20
        
        # Position the log with 20px padding from image and bottom
        self.screen.blit(log_surface, (20, 560))  # 540 (image height) + 20 (padding)
        
        self.needs_redraw = False

    def handle_team_selection_events(self, event):
        """Handle events in team selection view."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            
            # Check if Start Battle button was clicked
            if 500 <= y <= 550 and self.width//2 - 100 <= x <= self.width//2 + 100:
                self.start_battle()
            
            # Handle input box clicks
            for i, rect in enumerate(self.input_rects):
                if rect.collidepoint(x, y):
                    self.active_input = i
                    self.needs_redraw = True
                    break
            else:
                self.active_input = None
                self.needs_redraw = True
            
            # Handle battle mode toggle
            if 60 <= y <= 90 and 20 <= x <= 200:
                self.battle_mode = "double" if self.battle_mode == "single" else "single"
                self.needs_redraw = True
        
        elif event.type == pygame.KEYDOWN:
            if self.active_input is not None:
                if event.key == pygame.K_RETURN:
                    self.active_input = None
                elif event.key == pygame.K_BACKSPACE:
                    self.selected_pokemon[self.active_input] = self.selected_pokemon[self.active_input][:-1]
                else:
                    # Only allow letters, numbers, and spaces
                    if event.unicode.isalnum() or event.unicode.isspace():
                        self.selected_pokemon[self.active_input] += event.unicode
                self.needs_redraw = True

    def start_battle(self):
        """Start a new battle with the selected teams."""
        try:
            print("Starting battle...")
            self.log_message("Starting battle...")
            
            # Get battle mode
            mode = BattleMode.DOUBLE if self.battle_mode == "double" else BattleMode.SINGLE
            self.log_message(f"Battle mode: {mode.value}")
            
            # Create teams
            player_pokemon = []
            opponent_pokemon = []
            
            # Set default Pokémon for player team
            default_player_pokemon = [
                "charizard",
                "blastoise",
                "venusaur",
                "pikachu",
                "snorlax",
                "gyarados"
            ]
            
            # Set default Pokémon for opponent team
            default_opponent_pokemon = [
                "tyranitar",
                "metagross",
                "salamence",
                "garchomp",
                "dragonite",
                "hydreigon"
            ]
            
            # Create player team
            for pokemon_name in default_player_pokemon:
                try:
                    pokemon = Pokemon.from_data(pokemon_name)
                    # Verify Pokémon has moves
                    if not pokemon.moves:
                        self.log_message(f"Error: {pokemon_name} has no moves!")
                        return
                    player_pokemon.append(pokemon)
                except Exception as e:
                    self.log_message(f"Error loading {pokemon_name}: {e}")
                    return
            
            # Create opponent team
            for pokemon_name in default_opponent_pokemon:
                try:
                    pokemon = Pokemon.from_data(pokemon_name)
                    # Verify Pokémon has moves
                    if not pokemon.moves:
                        self.log_message(f"Error: {pokemon_name} has no moves!")
                        return
                    opponent_pokemon.append(pokemon)
                except Exception as e:
                    self.log_message(f"Error loading {pokemon_name}: {e}")
                    return
            
            # Create teams and battle
            self.player_team = Team(player_pokemon, mode)
            self.opponent_team = Team(opponent_pokemon, mode)
            self.battle = Battle(self.player_team, self.opponent_team)
            
            # Switch to battle view
            self.current_view = "battle"
            
            # Log battle start
            self.log_message(f"Starting {mode.value.title()} Battle!")
            self.log_message("\nPlayer's Team:")
            for pokemon in self.player_team.pokemon:
                self.log_message(f"- {pokemon.name} (HP: {pokemon.hp})")
                self.log_message(f"  Moves: {', '.join(move.name for move in pokemon.moves)}")
            
            self.log_message("\nOpponent's Team:")
            for pokemon in self.opponent_team.pokemon:
                self.log_message(f"- {pokemon.name} (HP: {pokemon.hp})")
                self.log_message(f"  Moves: {', '.join(move.name for move in pokemon.moves)}")
            
        except Exception as e:
            print(f"Error starting battle: {e}")
            self.log_message(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()

    def battle_loop(self):
        """Execute one turn of the battle."""
        if not self.battle or self.battle.is_battle_over():
            winner = self.battle.get_winner() if self.battle else None
            if winner:
                self.log_message(f"\n{'Player' if winner == self.player_team else 'Opponent'} wins the battle!")
            return
        
        try:
            # Debug: Print active Pokémon at start of turn
            print("\n=== Start of Turn Debug ===")
            print("Player's Active Pokémon:")
            if self.battle.battle_mode == BattleMode.SINGLE:
                print(f"- {self.player_team.active_pokemon.name} (HP: {self.player_team.active_pokemon.current_hp}/{self.player_team.active_pokemon.hp})")
            else:
                for pokemon in self.player_team.active_pokemon:
                    print(f"- {pokemon.name} (HP: {pokemon.current_hp}/{pokemon.hp})")
            
            print("\nOpponent's Active Pokémon:")
            if self.battle.battle_mode == BattleMode.SINGLE:
                print(f"- {self.opponent_team.active_pokemon.name} (HP: {self.opponent_team.active_pokemon.current_hp}/{self.opponent_team.active_pokemon.hp})")
            else:
                for pokemon in self.opponent_team.active_pokemon:
                    print(f"- {pokemon.name} (HP: {pokemon.current_hp}/{pokemon.hp})")
            print("=== End of Turn Debug ===\n")
            
            # For demonstration, we'll just use the first move of each active Pokémon
            if self.battle.battle_mode == BattleMode.SINGLE:
                # Check for fainted Pokémon and switch them out
                # Check player's Pokémon
                if self.player_team.active_pokemon.current_hp <= 0:
                    # Find next available Pokémon
                    next_pokemon = None
                    next_index = None
                    for i, pokemon in enumerate(self.player_team.pokemon):
                        if pokemon.current_hp > 0:
                            next_pokemon = pokemon
                            next_index = i
                            break
                    
                    if next_pokemon:
                        self.log_message(f"\nPlayer's {self.player_team.active_pokemon.name} fainted!")
                        self.log_message(f"Player sent out {next_pokemon.name}!")
                        # Update the active Pokémon index directly
                        self.player_team.active_pokemon_index = next_index
                        # Force a redraw of the battle screen
                        self.needs_redraw = True
                        self.draw_battle()
                        pygame.display.flip()
                        # Add a small delay to show the switch
                        pygame.time.delay(500)
                        return
                    else:
                        self.log_message("\nPlayer has no more Pokémon!")
                        return
                
                # Check opponent's Pokémon
                if self.opponent_team.active_pokemon.current_hp <= 0:
                    # Find next available Pokémon
                    next_pokemon = None
                    next_index = None
                    for i, pokemon in enumerate(self.opponent_team.pokemon):
                        if pokemon.current_hp > 0:
                            next_pokemon = pokemon
                            next_index = i
                            break
                    
                    if next_pokemon:
                        self.log_message(f"\nOpponent's {self.opponent_team.active_pokemon.name} fainted!")
                        self.log_message(f"Opponent sent out {next_pokemon.name}!")
                        # Update the active Pokémon index directly
                        self.opponent_team.active_pokemon_index = next_index
                        # Force a redraw of the battle screen
                        self.needs_redraw = True
                        self.draw_battle()
                        pygame.display.flip()
                        # Add a small delay to show the switch
                        pygame.time.delay(500)
                        # Skip the rest of the turn after a switch
                        return
                    else:
                        self.log_message("\nOpponent has no more Pokémon!")
                        return
                
                # Verify active Pokémon have moves
                if not self.player_team.active_pokemon.moves:
                    self.log_message(f"Error: {self.player_team.active_pokemon.name} has no moves!")
                    return
                if not self.opponent_team.active_pokemon.moves:
                    self.log_message(f"Error: {self.opponent_team.active_pokemon.name} has no moves!")
                    return
                
                player_move = self.player_team.active_pokemon.moves[0]
                player_action = ('move', player_move)
                
                # Get opponent's action (in a real implementation, this would come from AI)
                opponent_move = self.opponent_team.active_pokemon.moves[0]
                opponent_action = ('move', opponent_move)
                
                self.log_message(f"Player's {self.player_team.active_pokemon.name} used {player_move.name}!")
                self.log_message(f"Opponent's {self.opponent_team.active_pokemon.name} used {opponent_move.name}!")
                
                self.battle.execute_turn(player_action, opponent_action)
                self.needs_redraw = True
                
                # Log current status
                self.log_message(f"\nPlayer's {self.player_team.active_pokemon.name}: "
                               f"{self.player_team.active_pokemon.current_hp}/{self.player_team.active_pokemon.hp} HP")
                self.log_message(f"Opponent's {self.opponent_team.active_pokemon.name}: "
                               f"{self.opponent_team.active_pokemon.current_hp}/{self.opponent_team.active_pokemon.hp} HP")
            else:
                # Double battle logic
                player_actions = []
                opponent_actions = []
                
                # Check for fainted Pokémon and switch them out
                for i in range(2):
                    # Check player's Pokémon
                    if self.player_team.active_pokemon[i].current_hp <= 0:
                        # Find next available Pokémon
                        next_pokemon = None
                        next_index = None
                        for j, pokemon in enumerate(self.player_team.pokemon):
                            if pokemon.current_hp > 0:
                                next_pokemon = pokemon
                                next_index = j
                                break
                        
                        if next_pokemon:
                            self.log_message(f"\nPlayer's {self.player_team.active_pokemon[i].name} fainted!")
                            self.log_message(f"Player sent out {next_pokemon.name}!")
                            # Update the active Pokémon index directly
                            self.player_team.active_pokemon_indices[i] = next_index
                            # Force a redraw of the battle screen
                            self.needs_redraw = True
                            self.draw_battle()
                            pygame.display.flip()
                            # Add a small delay to show the switch
                            pygame.time.delay(500)
                            # Skip the rest of the turn after a switch
                            return
                        else:
                            self.log_message("\nPlayer has no more Pokémon!")
                            return
                    
                    # Check opponent's Pokémon
                    if self.opponent_team.active_pokemon[i].current_hp <= 0:
                        # Find next available Pokémon
                        next_pokemon = None
                        next_index = None
                        for j, pokemon in enumerate(self.opponent_team.pokemon):
                            if pokemon.current_hp > 0:
                                next_pokemon = pokemon
                                next_index = j
                                break
                        
                        if next_pokemon:
                            self.log_message(f"\nOpponent's {self.opponent_team.active_pokemon[i].name} fainted!")
                            self.log_message(f"Opponent sent out {next_pokemon.name}!")
                            # Update the active Pokémon index directly
                            self.opponent_team.active_pokemon_indices[i] = next_index
                            # Force a redraw of the battle screen
                            self.needs_redraw = True
                            self.draw_battle()
                            pygame.display.flip()
                            # Add a small delay to show the switch
                            pygame.time.delay(500)
                            # Skip the rest of the turn after a switch
                            return
                        else:
                            self.log_message("\nOpponent has no more Pokémon!")
                            return
                
                # Execute moves for remaining Pokémon
                for i in range(2):
                    if not self.player_team.active_pokemon[i].moves:
                        self.log_message(f"Error: {self.player_team.active_pokemon[i].name} has no moves!")
                        return
                    if not self.opponent_team.active_pokemon[i].moves:
                        self.log_message(f"Error: {self.opponent_team.active_pokemon[i].name} has no moves!")
                        return
                    
                    player_move = self.player_team.active_pokemon[i].moves[0]
                    opponent_move = self.opponent_team.active_pokemon[i].moves[0]
                    
                    player_actions.append(('move', player_move, i))
                    opponent_actions.append(('move', opponent_move, i))
                
                self.battle.execute_turn(player_actions, opponent_actions)
                self.needs_redraw = True
                
                # Log current status
                self.log_message("\nCurrent Status:")
                self.log_message("Player's Pokemon:")
                for pokemon in self.player_team.active_pokemon:
                    self.log_message(f"  {pokemon.name}: {pokemon.current_hp}/{pokemon.hp} HP")
                self.log_message("Opponent's Pokemon:")
                for pokemon in self.opponent_team.active_pokemon:
                    self.log_message(f"  {pokemon.name}: {pokemon.current_hp}/{pokemon.hp} HP")
        except Exception as e:
            self.log_message(f"Error in battle loop: {str(e)}")
            import traceback
            traceback.print_exc()

    def log_message(self, message):
        """Add a message to the battle log."""
        print(message)
        self.battle_log.append(message)
        self.needs_redraw = True

    def run(self):
        """Main game loop."""
        running = True
        clock = pygame.time.Clock()
        
        while running:
            current_time = pygame.time.get_ticks()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif self.current_view == "team_selection":
                        self.handle_team_selection_events(event)
                elif self.current_view == "team_selection":
                    self.handle_team_selection_events(event)
            
            # Handle battle turns
            if self.current_view == "battle" and self.battle and not self.battle.is_battle_over():
                if current_time - self.last_turn_time >= self.turn_delay:
                    self.battle_loop()
                    self.last_turn_time = current_time
            
            # Draw current view
            if self.current_view == "team_selection":
                self.draw_team_selection()
            else:
                self.draw_battle()
            
            # Update display
            pygame.display.flip()
            
            # Cap the frame rate
            clock.tick(60)
        
        pygame.quit()

def main():
    try:
        app = PokemonBattleGUI()
        app.run()
    except Exception as e:
        print(f"Error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 