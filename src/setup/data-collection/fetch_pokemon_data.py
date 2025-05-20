import requests
import json
from tqdm import tqdm
import time

def get_all_pokemon():
    """Get a list of all Pokemon from the API."""

    response = requests.get('https://pokeapi.co/api/v2/pokemon?limit=1')
    total_count = response.json()['count']
    

    response = requests.get(f'https://pokeapi.co/api/v2/pokemon?limit={total_count}')
    return response.json()['results']

def get_pokemon_details(pokemon_url):
    """information about pokemon"""
    response = requests.get(pokemon_url)
    return response.json()

def get_move_details(move_url):
    """info about a move"""
    response = requests.get(move_url)
    return response.json()

def get_move_effect(move_details):
    """extract move effect info."""
    effect_entries = move_details.get('effect_entries', [])
    if effect_entries:
        return {
            'effect': effect_entries[0].get('effect', ''),
            'short_effect': effect_entries[0].get('short_effect', '')
        }
    return {'effect': '', 'short_effect': ''}

def process_pokemon_data():
    """Process all pokemon data and their moves."""
    print("Fetching list of all Pokemon...")
    pokemon_list = get_all_pokemon()
    
    pokemon_data = {}
    moves_data = {}
    processed_moves = set()
    
    print(f"Fetching details for {len(pokemon_list)} Pokemon...")
    for pokemon in tqdm(pokemon_list):

        time.sleep(0.1)
        
        try:
            details = get_pokemon_details(pokemon['url'])
            
            pokemon_info = {
                'id': details['id'],
                'name': details['name'],
                'types': [t['type']['name'] for t in details['types']],
                'abilities': [a['ability']['name'] for a in details['abilities']],
                'base_stats': {
                    'hp': details['stats'][0]['base_stat'],
                    'attack': details['stats'][1]['base_stat'],
                    'defense': details['stats'][2]['base_stat'],
                    'special-attack': details['stats'][3]['base_stat'],
                    'special-defense': details['stats'][4]['base_stat'],
                    'speed': details['stats'][5]['base_stat']
                },
                'moves': [] 
            }
            
            for move in details['moves']:
                move_name = move['move']['name']
                move_url = move['move']['url']
                
                pokemon_info['moves'].append(move_name)
                
                if move_name not in processed_moves:
                    try:
                        move_details = get_move_details(move_url)
                        
                        effect_info = get_move_effect(move_details)
                        
                        move_info = {
                            'name': move_name,
                            'type': move_details['type']['name'],
                            'power': move_details.get('power'),
                            'accuracy': move_details.get('accuracy'),
                            'pp': move_details.get('pp'),
                            'damage_class': move_details['damage_class']['name'],
                            'effect': effect_info['effect'],
                            'short_effect': effect_info['short_effect']
                        }
                        
                        moves_data[move_name] = move_info
                        processed_moves.add(move_name)
                    except Exception as e:
                        print(f"Error processing move {move_name}: {str(e)}")
                        continue
            
            pokemon_data[pokemon['name']] = pokemon_info
            
        except Exception as e:
            print(f"Error processing Pokemon {pokemon['name']}: {str(e)}")
            continue
    
    return pokemon_data, moves_data

def main():
    print("data collection...")
    pokemon_data, moves_data = process_pokemon_data()
    
    print("Saving Pokemon data to pokemon_data.json...")
    with open('pokemon_data.json', 'w') as f:
        json.dump(pokemon_data, f, indent=2)
    
    print("Saving moves data to moves_data.json...")
    with open('moves_data.json', 'w') as f:
        json.dump(moves_data, f, indent=2)
    
    print("Done! Data has been saved to pokemon_data.json and moves_data.json")
    print(f"Processed {len(pokemon_data)} Pokemon and {len(moves_data)} unique moves")

if __name__ == "__main__":
    main() 