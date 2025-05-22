from typing import List, Tuple, Optional, Union
import random
from pokemon_battle import Pokemon, Move, Team, BattleMode, TYPES_DATA

class Adversary:
    def __init__(self, team: Team, battle_mode: BattleMode):
        self.team = team
        self.battle_mode = battle_mode

    def choose_action(self, opponent_team: Team) -> Union[tuple, List[tuple]]:
        """Choose an action for the current turn.
        
        Returns:
            For single battle: tuple of (action_type, action_data)
            For double battle: list of two tuples (action_type, action_data, target_position)
        """
        if self.battle_mode == BattleMode.SINGLE:
            return self._choose_single_action(opponent_team)
        else:
            return self._choose_double_actions(opponent_team)

    def _choose_single_action(self, opponent_team: Team) -> tuple:
        """Choose an action for a single battle."""
        # Check if we should switch
        if self._should_switch(opponent_team):
            available_switches = self.team.get_available_switches()
            if available_switches:
                return ('switch', random.choice(available_switches))

        # Choose a move
        current_pokemon = self.team.active_pokemon
        best_move = self._choose_best_move(current_pokemon, opponent_team.active_pokemon)
        return ('move', best_move)

    def _choose_double_actions(self, opponent_team: Team) -> List[tuple]:
        """Choose actions for both Pokémon in a double battle."""
        actions = []
        active_pokemon = self.team.active_pokemon  # This will be a list in double battle mode
        
        for i, pokemon in enumerate(active_pokemon):
            # Check if we should switch
            if self._should_switch(opponent_team):
                available_switches = self.team.get_available_switches()
                if available_switches:
                    actions.append(('switch', random.choice(available_switches), 0))
                    continue

            # Choose a move and target
            best_move = self._choose_best_move(pokemon, opponent_team.active_pokemon[0])
            # Randomly choose target for now, could be improved with better targeting logic
            target = random.randint(0, 1)
            actions.append(('move', best_move, target))

        return actions

    def _should_switch(self, opponent_team: Team) -> bool:
        """Determine if we should switch Pokémon."""
        current_pokemon = self.team.active_pokemon
        opponent_pokemon = opponent_team.active_pokemon

        # Handle single battle case
        if self.battle_mode == BattleMode.SINGLE:
            # Switch if current Pokémon is at low health
            if current_pokemon.current_hp / current_pokemon.hp < 0.3:
                return True

            # Switch if we have a type advantage with another Pokémon
            opponent_types = opponent_pokemon.types
        else:
            # For double battles, check both active Pokémon
            for pokemon in current_pokemon:
                if pokemon.current_hp / pokemon.hp < 0.3:
                    return True

            # Get all opponent types
            opponent_types = []
            for pokemon in opponent_pokemon:
                opponent_types.extend(pokemon.types)

        # Check for type advantages with other team members
        for pokemon in self.team.pokemon:
            if pokemon != current_pokemon and not pokemon.is_fainted():
                # Check if this Pokémon has a type advantage
                if self._has_type_advantage(pokemon, opponent_types):
                    return True

        return False

    def _choose_best_move(self, attacker: Pokemon, defender: Pokemon) -> Move:
        """Choose the best move to use against the defender."""
        # Simple strategy: prefer moves that are super effective
        best_move = None
        best_damage = 0

        for move in attacker.moves:
            # Calculate type effectiveness
            effectiveness = 1.0
            for defender_type in defender.types:
                effectiveness *= self._get_type_effectiveness(move.type, defender_type)

            # Estimate damage
            estimated_damage = move.power * effectiveness if move.power else 0

            if estimated_damage > best_damage:
                best_damage = estimated_damage
                best_move = move

        return best_move or random.choice(attacker.moves)

    def _has_type_advantage(self, pokemon: Pokemon, opponent_types: List[str]) -> bool:
        """Check if a Pokémon has a type advantage against the opponent's types."""
        for move in pokemon.moves:
            for opponent_type in opponent_types:
                if self._get_type_effectiveness(move.type, opponent_type) > 1.0:
                    return True
        return False

    def _get_type_effectiveness(self, attack_type: str, defender_type: str) -> float:
        """Get the type effectiveness multiplier from the types data file."""
        return TYPES_DATA[attack_type][defender_type] 