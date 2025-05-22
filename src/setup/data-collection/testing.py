import requests
import os
import json
from pathlib import Path

def load_pokemon_data():
    with open('../../collected-data/pokemon_data.json', 'r') as f:
        return json.load(f)

def download_sprite(pokemon_name: str, sprite_url: str, save_dir: str):
    """Download a Pokémon sprite and save it to the specified directory."""
    response = requests.get(sprite_url)
    if response.status_code == 200:
        # Create directory if it doesn't exist
        os.makedirs(save_dir, exist_ok=True)
        
        # Save the sprite
        file_path = os.path.join(save_dir, f"{pokemon_name}.png")
        with open(file_path, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded sprite for {pokemon_name}")
    else:
        print(f"Failed to download sprite for {pokemon_name}")

def download_battle_background():
    """Download a battle background image from Bulbapedia."""
    # Using a battle background from Pokémon Sword/Shield
    background_url = "https://archives.bulbagarden.net/media/upload/thumb/2/2c/Battle_Scene_SwSh.png/800px-Battle_Scene_SwSh.png"
    
    # Create directory if it doesn't exist
    base_dir = "sprites"
    background_dir = os.path.join(base_dir, "background")
    os.makedirs(background_dir, exist_ok=True)
    
    # Set up headers to mimic a browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://bulbapedia.bulbagarden.net/'
    }
    
    # Download the background
    response = requests.get(background_url, headers=headers)
    if response.status_code == 200:
        file_path = os.path.join(background_dir, "battle_background.png")
        with open(file_path, 'wb') as f:
            f.write(response.content)
        print("Downloaded battle background")
    else:
        print(f"Failed to download battle background. Status code: {response.status_code}")
        print("Trying alternative URL...")
        
        # Try alternative URL
        alt_url = "https://archives.bulbagarden.net/media/upload/thumb/2/2c/Battle_Scene_SwSh.png/800px-Battle_Scene_SwSh.png"
        response = requests.get(alt_url, headers=headers)
        if response.status_code == 200:
            file_path = os.path.join(background_dir, "battle_background.png")
            with open(file_path, 'wb') as f:
                f.write(response.content)
            print("Downloaded battle background from alternative URL")
        else:
            print(f"Failed to download battle background from alternative URL. Status code: {response.status_code}")
            print("Please check if the URLs are still valid on Bulbapedia.")

def main():
    # Create directories for sprites
    base_dir = "sprites"
    front_dir = os.path.join(base_dir, "front")
    back_dir = os.path.join(base_dir, "back")
    
    # Download battle background
    download_battle_background()
    
    """
    # Load Pokémon data
    pokemon_data = load_pokemon_data()
    
    # List of Pokémon used in the battle system
    battle_pokemon = [
        "charizard", "blastoise", "venusaur", "pikachu", "snorlax", "gyarados",
        "tyranitar", "metagross", "salamence", "garchomp", "dragonite", "hydreigon"
    ]
    
    # Download sprites for each Pokémon
    for pokemon_name in battle_pokemon:
        # Get Pokémon data from PokeAPI
        response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_name}")
        if response.status_code == 200:
            pokemon_info = response.json()
            
            # Get sprite URLs
            front_sprite = pokemon_info['sprites']['front_default']
            back_sprite = pokemon_info['sprites']['back_default']
            
            # Download sprites
            if front_sprite:
                download_sprite(pokemon_name, front_sprite, front_dir)
            if back_sprite:
                download_sprite(pokemon_name, back_sprite, back_dir)
        else:
            print(f"Failed to get data for {pokemon_name}")
    """

if __name__ == "__main__":
    main() 