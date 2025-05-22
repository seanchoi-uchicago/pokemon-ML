from dataclasses import dataclass
from typing import List, Dict, Optional, Union
import random
import json
import os
from enum import Enum

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

class BattleMode(Enum):
    SINGLE = "single"
    DOUBLE = "double"

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
    def __init__(self, pokemon_list: List[Pokemon], battle_mode: BattleMode):
        if len(pokemon_list) != 6:
            raise ValueError("A team must have exactly 6 Pokemon")
        self.pokemon = pokemon_list
        self.battle_mode = battle_mode
        self.active_pokemon_indices = [0] if battle_mode == BattleMode.SINGLE else [0, 1]

    @property
    def active_pokemon(self) -> Union[Pokemon, List[Pokemon]]:
        if self.battle_mode == BattleMode.SINGLE:
            return self.pokemon[self.active_pokemon_indices[0]]
        return [self.pokemon[i] for i in self.active_pokemon_indices]

    def switch_pokemon(self, position: int, new_index: int) -> bool:
        """Switch to a different Pokemon in the team.
        
        Args:
            position: 0 for single battle or left position in double battle, 1 for right position in double battle
            new_index: Index of the Pokemon to switch to
        """
        if 0 <= new_index < len(self.pokemon) and position in [0, 1]:
            if not self.pokemon[new_index].is_fainted() and new_index not in self.active_pokemon_indices:
                if self.battle_mode == BattleMode.SINGLE:
                    self.active_pokemon_indices[0] = new_index
                else:
                    self.active_pokemon_indices[position] = new_index
                return True
        return False

    def get_available_switches(self) -> List[int]:
        """Get indices of Pokemon that can be switched to."""
        return [i for i, p in enumerate(self.pokemon) 
                if not p.is_fainted() and i not in self.active_pokemon_indices]

    def is_defeated(self) -> bool:
        """Check if all Pokemon in the team are fainted."""
        return all(p.is_fainted() for p in self.pokemon)

class Battle:
    def __init__(self, player_team: Team, opponent_team: Team):
        if player_team.battle_mode != opponent_team.battle_mode:
            raise ValueError("Both teams must use the same battle mode")
        self.player_team = player_team
        self.opponent_team = opponent_team
        self.battle_mode = player_team.battle_mode
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

    def execute_turn(self, player_actions: Union[tuple, List[tuple]], opponent_actions: Union[tuple, List[tuple]]):
        """Execute a single turn of battle.
        
        Args:
            player_actions: For single battle: tuple of (action_type, action_data)
                          For double battle: list of two tuples (action_type, action_data, target_position)
            opponent_actions: Same format as player_actions
        """
        self.turn_count += 1
        print(f"\nTurn {self.turn_count}")

        if self.battle_mode == BattleMode.SINGLE:
            # Handle switching first
            if player_actions[0] == 'switch':
                self.player_team.switch_pokemon(0, player_actions[1])
                print(f"Player switched to {self.player_team.active_pokemon.name}!")
            
            if opponent_actions[0] == 'switch':
                self.opponent_team.switch_pokemon(0, opponent_actions[1])
                print(f"Opponent switched to {self.opponent_team.active_pokemon.name}!")

            # If both players switched, end turn
            if player_actions[0] == 'switch' and opponent_actions[0] == 'switch':
                return

            # Determine turn order based on speed
            player_speed = self.player_team.active_pokemon.speed
            opponent_speed = self.opponent_team.active_pokemon.speed

            # Execute moves in order
            if player_speed >= opponent_speed:
                if player_actions[0] == 'move':
                    self.execute_move(self.player_team.active_pokemon, 
                                    self.opponent_team.active_pokemon, 
                                    player_actions[1])
                if not self.opponent_team.active_pokemon.is_fainted() and opponent_actions[0] == 'move':
                    self.execute_move(self.opponent_team.active_pokemon, 
                                    self.player_team.active_pokemon, 
                                    opponent_actions[1])
            else:
                if opponent_actions[0] == 'move':
                    self.execute_move(self.opponent_team.active_pokemon, 
                                    self.player_team.active_pokemon, 
                                    opponent_actions[1])
                if not self.player_team.active_pokemon.is_fainted() and player_actions[0] == 'move':
                    self.execute_move(self.player_team.active_pokemon, 
                                    self.opponent_team.active_pokemon, 
                                    player_actions[1])
        else:  # Double battle
            # Handle switching first
            for i, action in enumerate(player_actions):
                if action[0] == 'switch':
                    self.player_team.switch_pokemon(i, action[1])
                    print(f"Player switched to {self.player_team.active_pokemon[i].name}!")
            
            for i, action in enumerate(opponent_actions):
                if action[0] == 'switch':
                    self.opponent_team.switch_pokemon(i, action[1])
                    print(f"Opponent switched to {self.opponent_team.active_pokemon[i].name}!")

            # Get all active Pokemon and their speeds
            active_pokemon = [
                (self.player_team.active_pokemon[0], player_actions[0], 'player', 0),
                (self.player_team.active_pokemon[1], player_actions[1], 'player', 1),
                (self.opponent_team.active_pokemon[0], opponent_actions[0], 'opponent', 0),
                (self.opponent_team.active_pokemon[1], opponent_actions[1], 'opponent', 1)
            ]

            # Sort by speed
            active_pokemon.sort(key=lambda x: x[0].speed, reverse=True)

            # Execute moves in order
            for pokemon, action, team, position in active_pokemon:
                if action[0] == 'move':
                    # Determine target based on action[2] (target_position)
                    if team == 'player':
                        target = self.opponent_team.active_pokemon[action[2]]
                    else:
                        target = self.player_team.active_pokemon[action[2]]
                    
                    if not target.is_fainted():
                        self.execute_move(pokemon, target, action[1])

    def is_battle_over(self) -> bool:
        """Check if the battle is over."""
        return self.player_team.is_defeated() or self.opponent_team.is_defeated()

    def get_winner(self) -> Optional[Team]:
        """Get the winner of the battle, or None if the battle isn't over."""
        if not self.is_battle_over():
            return None
        return self.opponent_team if self.player_team.is_defeated() else self.player_team

def main():
    # Choose battle mode
    battle_mode = BattleMode.DOUBLE if input("Choose battle mode (single/double): ").lower() == "double" else BattleMode.SINGLE
    
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
    
    player_team = Team(player_pokemon, battle_mode)
    opponent_team = Team(opponent_pokemon, battle_mode)
    
    # Create adversary for opponent team
    from pokemon_adversary import Adversary
    opponent_ai = Adversary(opponent_team, battle_mode)
    
    # Print team information
    print(f"{battle_mode.value.title()} Battle Start!")
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
        if battle_mode == BattleMode.SINGLE:
            # For demonstration, we'll just use the first move of the active Pokemon
            player_move = battle.player_team.active_pokemon.moves[0]
            player_action = ('move', player_move)
            
            # Get opponent's action from AI
            opponent_action = opponent_ai.choose_action(player_team)
            
            battle.execute_turn(player_action, opponent_action)
            
            # Print current HP of active Pokemon
            print("\nCurrent Status:")
            print(f"Player's {battle.player_team.active_pokemon.name}: {battle.player_team.active_pokemon.current_hp}/{battle.player_team.active_pokemon.hp} HP")
            print(f"Opponent's {battle.opponent_team.active_pokemon.name}: {battle.opponent_team.active_pokemon.current_hp}/{battle.opponent_team.active_pokemon.hp} HP")
        else:  # Double battle
            # For demonstration, we'll just use the first move of each active Pokemon
            player_actions = []
            
            # Generate actions for both player Pokemon
            for i in range(2):
                # Randomly choose target (0 for left opponent, 1 for right opponent)
                target = random.randint(0, 1)
                player_actions.append(('move', battle.player_team.active_pokemon[i].moves[0], target))
            
            # Get opponent's actions from AI
            opponent_actions = opponent_ai.choose_action(player_team)
            
            battle.execute_turn(player_actions, opponent_actions)
            
            # Print current HP of active Pokemon
            print("\nCurrent Status:")
            print("Player's Pokemon:")
            for i, pokemon in enumerate(battle.player_team.active_pokemon):
                print(f"  {pokemon.name}: {pokemon.current_hp}/{pokemon.hp} HP")
            print("Opponent's Pokemon:")
            for i, pokemon in enumerate(battle.opponent_team.active_pokemon):
                print(f"  {pokemon.name}: {pokemon.current_hp}/{pokemon.hp} HP")

    winner = battle.get_winner()
    print(f"\n{'Player' if winner == player_team else 'Opponent'} wins the battle!")

if __name__ == "__main__":
    main() 