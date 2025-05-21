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

class Battle:
    def __init__(self, player_pokemon: Pokemon, opponent_pokemon: Pokemon):
        self.player_pokemon = player_pokemon
        self.opponent_pokemon = opponent_pokemon
        self.turn_count = 0

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

    def execute_turn(self, player_move: Move, opponent_move: Move):
        """Execute a single turn of battle."""
        self.turn_count += 1
        print(f"\nTurn {self.turn_count}")

        # Determine turn order based on speed
        first = self.player_pokemon if self.player_pokemon.speed >= self.opponent_pokemon.speed else self.opponent_pokemon
        second = self.opponent_pokemon if first == self.player_pokemon else self.player_pokemon

        # Execute moves in order
        first_move = player_move if first == self.player_pokemon else opponent_move
        second_move = opponent_move if first == self.player_pokemon else player_move

        self.execute_move(first, second, first_move)
        if not second.is_fainted():
            self.execute_move(second, first, second_move)

    def is_battle_over(self) -> bool:
        """Check if the battle is over."""
        return self.player_pokemon.is_fainted() or self.opponent_pokemon.is_fainted()

    def get_winner(self) -> Optional[Pokemon]:
        """Get the winner of the battle, or None if the battle isn't over."""
        if not self.is_battle_over():
            return None
        return self.opponent_pokemon if self.player_pokemon.is_fainted() else self.player_pokemon

def main():
    # Create Pokemon from the data
    pokemon1 = Pokemon.from_data("calyrex-shadow")
    pokemon2 = Pokemon.from_data("charizard")
    
    # Print Pokemon information
    print("Battle Start!")

    print("\n")
    print(pokemon1.name, ":")
    print(f"Types: {', '.join(pokemon1.types)}")
    print(f"Moves: {', '.join(move.name for move in pokemon1.moves)}")
    print(f"HP: {pokemon1.hp}")
    
    print("\n")
    print(pokemon1.name, ":")
    print(f"Types: {', '.join(pokemon2.types)}")
    print(f"Moves: {', '.join(move.name for move in pokemon2.moves)}")
    print(f"HP: {pokemon2.hp}")
    
    # Create and run a battle
    battle = Battle(pokemon1, pokemon2)
    
    while not battle.is_battle_over():
        player_move = battle.player_pokemon.moves[0]

        opponent_move = random.choice(battle.opponent_pokemon.moves)
        
        battle.execute_turn(player_move, opponent_move)
        
        # Print current HP
        print("\n")
        print(pokemon1.name, f" HP: {battle.player_pokemon.current_hp}/{battle.player_pokemon.hp}")
        print(pokemon2.name, f" HP: {battle.opponent_pokemon.current_hp}/{battle.opponent_pokemon.hp}")

    winner = battle.get_winner()
    print(f"\n{winner.name} wins the battle!")

if __name__ == "__main__":
    main() 