import requests
import json
from tqdm import tqdm
import time

def get_all_abilities():
    """Get a list of all abilities from the API."""
    # First, get the total count of abilities
    response = requests.get('https://pokeapi.co/api/v2/ability?limit=1')
    total_count = response.json()['count']
    
    # Then get all abilities
    response = requests.get(f'https://pokeapi.co/api/v2/ability?limit={total_count}')
    return response.json()['results']

def get_ability_details(ability_url):
    """Get detailed information about a specific ability."""
    response = requests.get(ability_url)
    return response.json()

def process_abilities():
    """Process all abilities and their effects."""
    print("Fetching list of all abilities...")
    abilities_list = get_all_abilities()
    
    abilities_data = {}
    
    print(f"Fetching details for {len(abilities_list)} abilities...")
    for ability in tqdm(abilities_list):
        # Add a small delay to be nice to the API
        time.sleep(0.1)
        
        try:
            ability_details = get_ability_details(ability['url'])
            
            # Extract relevant ability information
            ability_info = {
                'id': ability_details['id'],
                'name': ability_details['name'],
                'generation': ability_details['generation']['name'],
                'is_main_series': ability_details['is_main_series'],
                'effect_entries': [],
                'pokemon': []
            }
            
            # Get effect entries in different languages
            for entry in ability_details['effect_entries']:
                if entry['language']['name'] == 'en':
                    ability_info['effect_entries'].append({
                        'effect': entry['effect'],
                        'short_effect': entry['short_effect']
                    })
            
            # Get Pokemon that can have this ability
            for pokemon in ability_details['pokemon']:
                ability_info['pokemon'].append({
                    'name': pokemon['pokemon']['name'],
                    'is_hidden': pokemon['is_hidden']
                })
            
            abilities_data[ability['name']] = ability_info
            
        except Exception as e:
            print(f"Error processing ability {ability['name']}: {str(e)}")
            continue
    
    return abilities_data

def main():
    print("Starting ability data collection...")
    abilities_data = process_abilities()
    
    # Save abilities data to JSON file
    print("Saving abilities data to abilities_data.json...")
    with open('abilities_data.json', 'w') as f:
        json.dump(abilities_data, f, indent=2)
    
    print("Done! Data has been saved to abilities_data.json")
    print(f"Processed {len(abilities_data)} abilities")

if __name__ == "__main__":
    main() 