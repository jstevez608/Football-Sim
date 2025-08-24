#!/usr/bin/env python3

import requests
import json

def debug_team_composition():
    base_url = "https://footysim-pro.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # Get teams
    response = requests.get(f"{api_url}/teams")
    teams = response.json()
    
    # Get players
    response = requests.get(f"{api_url}/players")
    players = response.json()
    
    print("Team Composition Analysis:")
    print("=" * 50)
    
    for team in teams:
        team_players = [p for p in players if p.get('team_id') == team['id']]
        print(f"\n{team['name']} ({len(team_players)} players):")
        
        # Count by position
        position_counts = {"PORTERO": 0, "DEFENSA": 0, "MEDIO": 0, "DELANTERO": 0}
        for player in team_players:
            position = player.get('position', 'UNKNOWN')
            if position in position_counts:
                position_counts[position] += 1
            print(f"  - {player['name']} ({position})")
        
        print(f"  Position counts: {position_counts}")
        
        # Check if team can form a valid lineup
        formation_a = {"PORTERO": 1, "DEFENSA": 2, "MEDIO": 3, "DELANTERO": 1}
        can_form_lineup = all(position_counts[pos] >= count for pos, count in formation_a.items())
        print(f"  Can form Formation A (4-3-1): {can_form_lineup}")

if __name__ == "__main__":
    debug_team_composition()