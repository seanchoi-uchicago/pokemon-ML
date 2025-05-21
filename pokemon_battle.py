from dataclasses import dataclass
from typing import List, Dict, Optional
import random
import json
import os

# Load Pokemon and moves data
def load_pokemon_data():
    with open('src/collected-data/pokemon_data.json', 'r') as f:
        return json.load(f)

def load_moves_data():
    with open('src/collected-data/moves_data.json', 'r') as f:
        return json.load(f)

def load_types_data():
    with open('src/collected-data/types_data.json', 'r') as f:
        return json.load(f)

POKEMON_DATA = load_pokemon_data()
MOVES_DATA = load_moves_data()
TYPES_DATA = load_types_data()

@dataclass
class Move:
    name: str
    type: str
    power: int
    accuracy: int
    pp: int
    damage_class: str  # physical, special, or status

    @classmethod
    def from_data(cls, move_name: str):
        """Create a Move instance from the moves data."""
        move_data = MOVES_DATA[move_name]
        return cls(
            name=move_name,
            type=move_data['type'],
            power=move_data['power'] or 0,  # Some moves might not have power
            accuracy=move_data['accuracy'] or 100,  # Some moves might not have accuracy
            pp=move_data['pp'] or 20,  # Default PP if not specified
            damage_class=move_data['damage_class']
        )

@dataclass
class Pokemon:
    name: str
    level: int
    types: List[str]
    moves: List[Move]
    # Base stats
    hp: int
    attack: int
    defense: int
    special_attack: int
    special_defense: int
    speed: int
    # Current battle stats
    current_hp: int
    status: Optional[str] = None  # e.g., "poison", "burn", "sleep", etc.
    stat_stages: Dict[str, int] = None  # Tracks stat modifications (-6 to +6)

    @classmethod
    def from_data(cls, pokemon_name: str, level: int = 50):
        """Create a Pokemon instance from the Pokemon data."""
        pokemon_data = POKEMON_DATA[pokemon_name]
        stats = pokemon_data['base_stats']
        
        # Get up to 4 random moves from the Pokemon's movepool
        available_moves = pokemon_data['moves']
        selected_moves = random.sample(available_moves, min(4, len(available_moves)))
        moves = [Move.from_data(move_name) for move_name in selected_moves]
        
        # Create the Pokemon instance with current_hp set to max HP
        return cls(
            name=pokemon_name,
            level=level,
            types=pokemon_data['types'],
            moves=moves,
            hp=(stats['hp'] * 2 * level/100) + level + 10,
            attack=stats['attack'],
            defense=stats['defense'],
            special_attack=stats['special-attack'],
            special_defense=stats['special-defense'],
            speed=stats['speed'],
            current_hp=(stats['hp'] * 2 * level/100) + level + 10 # Initialize current_hp to max HP
        )

    def __post_init__(self):
        if self.stat_stages is None:
            self.stat_stages = {
                "attack": 0,
                "defense": 0,
                "special_attack": 0,
                "special_defense": 0,
                "speed": 0,
                "accuracy": 0,
                "evasion": 0
            }

    def is_fainted(self) -> bool:
        return self.current_hp <= 0

    def take_damage(self, damage: int):
        self.current_hp = max(0, self.current_hp - damage)

    def heal(self, amount: int):
        self.current_hp = min(self.hp, self.current_hp + amount)

class Team:
    def __init__(self, pokemon_list: List[Pokemon]):
        if len(pokemon_list) != 6:
            raise ValueError("A team must have exactly 6 Pokemon")
        self.pokemon = pokemon_list
        self.active_pokemon_index = 0

    @property
    def active_pokemon(self) -> Pokemon:
        return self.pokemon[self.active_pokemon_index]

    def switch_pokemon(self, new_index: int) -> bool:
        """Switch to a different Pokemon in the team."""
        if 0 <= new_index < len(self.pokemon):
            if not self.pokemon[new_index].is_fainted():
                self.active_pokemon_index = new_index
                return True
        return False

    def get_available_switches(self) -> List[int]:
        """Get indices of Pokemon that can be switched to."""
        return [i for i, p in enumerate(self.pokemon) if not p.is_fainted() and i != self.active_pokemon_index]

    def is_defeated(self) -> bool:
        """Check if all Pokemon in the team are fainted."""
        return all(p.is_fainted() for p in self.pokemon)

class Battle:
    def __init__(self, player_team: Team, opponent_team: Team):
        self.player_team = player_team
        self.opponent_team = opponent_team
        self.turn_count = 0
        self.last_move_used = None

    def calculate_damage(self, attacker: Pokemon, defender: Pokemon, move: Move) -> int:
        """Calculate damage for a move."""
        # physical/special
        level = attacker.level
        attack = attacker.attack if move.damage_class == "physical" else attacker.special_attack
        defense = defender.defense if move.damage_class == "physical" else defender.special_defense
        
        # stat changes
        if move.damage_class == "physical":
            attack = self.apply_stat_stages(attack, attacker.stat_stages["attack"])
            defense = self.apply_stat_stages(defense, defender.stat_stages["defense"])
        elif move.damage_class == "special":
            attack = self.apply_stat_stages(attack, attacker.stat_stages["special_attack"])
            defense = self.apply_stat_stages(defense, defender.stat_stages["special_defense"])
            
        # damage calc
        damage = ((2 * level / 5 + 2) * move.power * (attack / defense) / 50 + 2)
        
        # damage roll
        damage *= random.uniform(0.85, 1.00)

        #type effectiveness
        for type in defender.types:
            damage *= TYPES_DATA[move.type][type]
        
        return int(damage)

    def apply_stat_stages(self, stat: int, stage: int) -> int:
        """Apply stat stage modifications."""
        if stage > 0:
            return stat * (2 + stage) / 2
        elif stage < 0:
            return stat * 2 / (2 - stage)
        return stat

    def execute_move(self, attacker: Pokemon, defender: Pokemon, move: Move) -> bool:
        """Execute a move and return whether it was successful."""
        # Check if move hits
        if random.randint(1, 100) > move.accuracy:
            print(f"{attacker.name}'s {move.name} missed!")
            return False

        # Calculate and apply damage
        damage = self.calculate_damage(attacker, defender, move)
        defender.take_damage(damage)
        print(f"{attacker.name} used {move.name}!")
        print(f"It dealt {damage} damage to {defender.name}!")
        
        # Check if defender fainted
        if defender.is_fainted():
            print(f"{defender.name} fainted!")
        
        return True

    def execute_turn(self, player_action: tuple, opponent_action: tuple):
        """Execute a single turn of battle.
        
        Args:
            player_action: Tuple of (action_type, action_data)
                action_type can be 'move' or 'switch'
                action_data is either a Move object or a team index
            opponent_action: Same format as player_action
        """
        self.turn_count += 1
        print(f"\nTurn {self.turn_count}")

        # Handle switching first
        if player_action[0] == 'switch':
            self.player_team.switch_pokemon(player_action[1])
            print(f"Player switched to {self.player_team.active_pokemon.name}!")
        
        if opponent_action[0] == 'switch':
            self.opponent_team.switch_pokemon(opponent_action[1])
            print(f"Opponent switched to {self.opponent_team.active_pokemon.name}!")

        # If both players switched, end turn
        if player_action[0] == 'switch' and opponent_action[0] == 'switch':
            return

        # Determine turn order based on speed
        player_speed = self.player_team.active_pokemon.speed
        opponent_speed = self.opponent_team.active_pokemon.speed

        # Execute moves in order
        if player_speed >= opponent_speed:
            if player_action[0] == 'move':
                self.execute_move(self.player_team.active_pokemon, 
                                self.opponent_team.active_pokemon, 
                                player_action[1])
            if not self.opponent_team.active_pokemon.is_fainted() and opponent_action[0] == 'move':
                self.execute_move(self.opponent_team.active_pokemon, 
                                self.player_team.active_pokemon, 
                                opponent_action[1])
        else:
            if opponent_action[0] == 'move':
                self.execute_move(self.opponent_team.active_pokemon, 
                                self.player_team.active_pokemon, 
                                opponent_action[1])
            if not self.player_team.active_pokemon.is_fainted() and player_action[0] == 'move':
                self.execute_move(self.player_team.active_pokemon, 
                                self.opponent_team.active_pokemon, 
                                player_action[1])

    def is_battle_over(self) -> bool:
        """Check if the battle is over."""
        return self.player_team.is_defeated() or self.opponent_team.is_defeated()

    def get_winner(self) -> Optional[Team]:
        """Get the winner of the battle, or None if the battle isn't over."""
        if not self.is_battle_over():
            return None
        return self.opponent_team if self.player_team.is_defeated() else self.player_team

def main():
    # Create two teams of 6 Pokemon
    player_pokemon = [
        Pokemon.from_data("charizard"),
        Pokemon.from_data("blastoise"),
        Pokemon.from_data("venusaur"),
        Pokemon.from_data("pikachu"),
        Pokemon.from_data("snorlax"),
        Pokemon.from_data("gyarados")
    ]
    
    opponent_pokemon = [
        Pokemon.from_data("tyranitar"),
        Pokemon.from_data("metagross"),
        Pokemon.from_data("salamence"),
        Pokemon.from_data("garchomp"),
        Pokemon.from_data("dragonite"),
        Pokemon.from_data("hydreigon")
    ]
    
    player_team = Team(player_pokemon)
    opponent_team = Team(opponent_pokemon)
    
    # Print team information
    print("Battle Start!")
    print("\nPlayer's Team:")
    for i, pokemon in enumerate(player_team.pokemon):
        print(f"{i+1}. {pokemon.name}")
        print(f"   Types: {', '.join(pokemon.types)}")
        print(f"   Moves: {', '.join(move.name for move in pokemon.moves)}")
        print(f"   HP: {pokemon.hp}")
    
    print("\nOpponent's Team:")
    for i, pokemon in enumerate(opponent_team.pokemon):
        print(f"{i+1}. {pokemon.name}")
        print(f"   Types: {', '.join(pokemon.types)}")
        print(f"   Moves: {', '.join(move.name for move in pokemon.moves)}")
        print(f"   HP: {pokemon.hp}")
    
    # Create and run a battle
    battle = Battle(player_team, opponent_team)
    
    while not battle.is_battle_over():
        # For demonstration, we'll just use the first move of the active Pokemon
        player_move = battle.player_team.active_pokemon.moves[0]
        opponent_move = random.choice(battle.opponent_team.active_pokemon.moves)
        
        # Randomly decide whether to switch or use a move
        if random.random() < 0.2 and battle.player_team.get_available_switches():
            player_action = ('switch', random.choice(battle.player_team.get_available_switches()))
        else:
            player_action = ('move', player_move)
            
        if random.random() < 0.2 and battle.opponent_team.get_available_switches():
            opponent_action = ('switch', random.choice(battle.opponent_team.get_available_switches()))
        else:
            opponent_action = ('move', opponent_move)
        
        battle.execute_turn(player_action, opponent_action)
        
        # Print current HP of active Pokemon
        print("\nCurrent Status:")
        print(f"Player's {battle.player_team.active_pokemon.name}: {battle.player_team.active_pokemon.current_hp}/{battle.player_team.active_pokemon.hp} HP")
        print(f"Opponent's {battle.opponent_team.active_pokemon.name}: {battle.opponent_team.active_pokemon.current_hp}/{battle.opponent_team.active_pokemon.hp} HP")

    winner = battle.get_winner()
    print(f"\n{'Player' if winner == player_team else 'Opponent'} wins the battle!")

if __name__ == "__main__":
    main() 