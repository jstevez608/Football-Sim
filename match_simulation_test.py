#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import time
import random

class MatchSimulationBugTest:
    def __init__(self, base_url="https://footysim-pro.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        if details and success:
            print(f"   {details}")

    def run_api_test(self, name, method, endpoint, expected_status=200, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)

            success = response.status_code == expected_status
            if success:
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                error_detail = f"Expected {expected_status}, got {response.status_code}"
                try:
                    error_detail += f" - {response.json()}"
                except:
                    error_detail += f" - {response.text}"
                self.log_test(name, False, error_detail)
                return False, {}

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def setup_minimal_game_for_match_test(self):
        """Set up minimal game scenario to test match simulation"""
        print("\n🔧 Setting up minimal game for match simulation test...")
        
        # 1. Initialize game
        success, response = self.run_api_test("Initialize Game", "POST", "game/init")
        if not success:
            return False
        self.log_test("Game Initialization", True, f"Players available: {response.get('players_available', 0)}")

        # 2. Load players
        success, players = self.run_api_test("Load Players", "GET", "players")
        if not success:
            return False
        self.players = players
        self.log_test("Load Players", True, f"Loaded {len(players)} players")

        # 3. Create exactly 2 teams for testing
        team_data_1 = {
            "name": "Team Alpha",
            "colors": {"primary": "#FF0000", "secondary": "#FFFFFF"},
            "budget": 80000000
        }
        team_data_2 = {
            "name": "Team Beta", 
            "colors": {"primary": "#0000FF", "secondary": "#FFFFFF"},
            "budget": 80000000
        }

        success, response = self.run_api_test("Create Team Alpha", "POST", "teams", data=team_data_1)
        if not success:
            return False
        team_alpha_id = response.get('team_id')

        success, response = self.run_api_test("Create Team Beta", "POST", "teams", data=team_data_2)
        if not success:
            return False
        team_beta_id = response.get('team_id')

        # 4. Create 6 more dummy teams to reach 8 teams requirement
        for i in range(3, 9):
            team_data = {
                "name": f"Team {i}",
                "colors": {"primary": "#00FF00", "secondary": "#FFFFFF"},
                "budget": 80000000
            }
            success, response = self.run_api_test(f"Create Team {i}", "POST", "teams", data=team_data)
            if not success:
                return False

        # 5. Load teams
        success, teams = self.run_api_test("Load Teams", "GET", "teams")
        if not success:
            return False
        self.teams = teams
        self.log_test("Teams Created", True, f"Created {len(teams)} teams")

        # 6. Start draft
        success, response = self.run_api_test("Start Draft", "POST", "draft/start")
        if not success:
            return False
        self.log_test("Draft Started", True)

        # 7. Draft players strategically to ensure Team Alpha and Team Beta have proper lineups
        # Separate players by position
        players_by_position = {
            "PORTERO": [p for p in self.players if p['position'] == 'PORTERO'],
            "DEFENSA": [p for p in self.players if p['position'] == 'DEFENSA'],
            "MEDIO": [p for p in self.players if p['position'] == 'MEDIO'],
            "DELANTERO": [p for p in self.players if p['position'] == 'DELANTERO']
        }

        # Shuffle each position group
        for position_players in players_by_position.values():
            random.shuffle(position_players)

        print(f"   Available players: GK={len(players_by_position['PORTERO'])}, DEF={len(players_by_position['DEFENSA'])}, MID={len(players_by_position['MEDIO'])}, FWD={len(players_by_position['DELANTERO'])}")

        # Draft minimum required players for each team (7 players each)
        required_positions = ["PORTERO", "DEFENSA", "DEFENSA", "MEDIO", "MEDIO", "DELANTERO", "DEFENSA"]  # 7 players

        # Draft 7 rounds
        for round_num in range(7):
            print(f"   Drafting round {round_num + 1}/7...")
            for team_index in range(8):  # 8 teams
                # Get current game state
                success, game_state = self.run_api_test("Get Game State for Draft", "GET", "game/state")
                if not success:
                    return False
                
                current_team_index = game_state.get('current_team_turn', 0)
                draft_order = game_state.get('draft_order', [])
                current_team_id = draft_order[current_team_index]
                
                # Select position for this round
                required_position = required_positions[round_num]
                available_for_position = players_by_position[required_position]
                
                if not available_for_position:
                    # If no players of required position, get any available player
                    player = None
                    for position, position_players in players_by_position.items():
                        if position_players:
                            player = position_players.pop(0)
                            break
                else:
                    player = available_for_position.pop(0)
                
                if not player:
                    self.log_test("Draft", False, f"No more players available")
                    return False
                
                success, response = self.run_api_test(
                    f"Draft {player['name']} ({player['position']}) to Team {team_index + 1}", 
                    "POST", 
                    "draft/pick",
                    data={
                        "team_id": current_team_id,
                        "player_id": player["id"],
                        "clause_amount": 0
                    }
                )
                if not success:
                    return False

        self.log_test("Draft Completed", True, "All teams have 7 players")

        # 8. Start league
        success, response = self.run_api_test("Start League", "POST", "league/start")
        if not success:
            return False
        self.log_test("League Started", True, f"Total matches: {response.get('total_matches', 0)}")

        # 9. Load updated teams and select lineups for all teams
        success, teams = self.run_api_test("Load Updated Teams", "GET", "teams")
        if not success:
            return False
        self.teams = teams

        success, players = self.run_api_test("Load Updated Players", "GET", "players")
        if not success:
            return False
        self.players = players

        # 10. Select lineups for all teams
        formation_requirements = {
            "A": {"PORTERO": 1, "DEFENSA": 2, "MEDIO": 3, "DELANTERO": 1}
        }

        for lineup_turn in range(8):
            print(f"   Selecting lineup {lineup_turn + 1}/8...")
            # Get current game state
            success, game_state = self.run_api_test("Get Game State for Lineup", "GET", "game/state")
            if not success:
                return False
            
            current_team_index = game_state.get('current_team_turn', 0)
            current_team = self.teams[current_team_index] if current_team_index < len(self.teams) else None
            
            if not current_team:
                self.log_test("Lineup Turn", False, f"Could not find current team for lineup selection")
                return False
            
            # Get team players
            team_players = [p for p in self.players if p.get('team_id') == current_team['id']]
            
            if len(team_players) < 7:
                self.log_test(f"Team {current_team['name']} Players", False, f"Team has only {len(team_players)} players, need 7")
                return False
            
            # Select formation A (4-3-1)
            formation = "A"
            requirements = formation_requirements[formation]
            
            # Select players by position
            selected_players = []
            for position, count in requirements.items():
                position_players = [p for p in team_players if p['position'] == position and p['id'] not in selected_players]
                if len(position_players) >= count:
                    selected_players.extend([p['id'] for p in position_players[:count]])
                else:
                    # If not enough players of this position, fill with any available players
                    selected_players.extend([p['id'] for p in position_players])
                    remaining_needed = count - len(position_players)
                    other_players = [p for p in team_players if p['id'] not in selected_players]
                    selected_players.extend([p['id'] for p in other_players[:remaining_needed]])
            
            # Ensure exactly 7 players
            if len(selected_players) < 7:
                other_players = [p for p in team_players if p['id'] not in selected_players]
                selected_players.extend([p['id'] for p in other_players[:7-len(selected_players)]])
            
            selected_players = selected_players[:7]  # Ensure exactly 7
            
            if len(selected_players) == 7:
                success, response = self.run_api_test(
                    f"Select Lineup for {current_team['name']}", 
                    "POST", 
                    "league/lineup/select",
                    data={
                        "team_id": current_team["id"],
                        "formation": formation,
                        "players": selected_players
                    }
                )
                if not success:
                    return False
            else:
                self.log_test(f"Lineup Selection for {current_team['name']}", False, f"Could not select 7 players (found {len(selected_players)})")
                return False

        self.log_test("Complete Game Setup", True, "8 teams with lineups ready for matches")
        return True

    def test_match_simulation_dictionary_access_fix(self):
        """Test the specific dictionary access fix in match simulation"""
        print("\n🐛 Testing Match Simulation Dictionary Access Fix...")
        
        # This test specifically targets the bug that was fixed:
        # Lines 325 and 332 in server.py where getattr(player["stats"], stat.lower()) 
        # was changed to player["stats"][stat.lower()]
        
        # Load current round matches
        success, matches = self.run_api_test("Load Round 1 Matches", "GET", f"league/matches/round/1")
        if not success:
            return False
        
        if not matches:
            self.log_test("Match Loading", False, "No matches found for round 1")
            return False
        
        self.log_test("Match Loading", True, f"Found {len(matches)} matches in round 1")

        # Test simulate next match - this is where the bug would occur
        success, match_result = self.run_api_test("Simulate Match (Dictionary Access Test)", "POST", "league/simulate-next-match")
        if not success:
            return False

        # If we get here without an error, the dictionary access fix is working
        self.log_test("Dictionary Access Fix", True, "Match simulation completed without 'dict' object has no attribute error")

        # Verify match result structure to ensure simulation worked correctly
        required_fields = ['home_team', 'away_team', 'home_score', 'away_score', 'match_log']
        missing_fields = [field for field in required_fields if field not in match_result]
        
        if missing_fields:
            self.log_test("Match Result Structure", False, f"Missing fields: {missing_fields}")
            return False
        
        self.log_test("Match Result Structure", True, "All required fields present")

        # Verify match log has turns with actions
        match_log = match_result.get('match_log', {})
        turns = match_log.get('turns', [])
        
        if len(turns) != 18:
            self.log_test("Turn Count", False, f"Expected 18 turns, got {len(turns)}")
            return False
        
        self.log_test("Turn Count", True, "Exactly 18 turns simulated")

        # Verify that player stats were accessed correctly in actions
        action_count = 0
        stat_access_verified = 0
        
        for turn in turns:
            actions = turn.get('actions', [])
            action_count += len(actions)
            
            for action in actions:
                # Check that attacker and defender have stat_value (this proves dictionary access worked)
                attacker = action.get('attacker', {})
                defender = action.get('defender', {})
                
                if 'stat_value' in attacker and 'stat_value' in defender:
                    stat_access_verified += 1
                    
                    # Verify stat values are in valid range (1-6)
                    attacker_stat = attacker.get('stat_value', 0)
                    defender_stat = defender.get('stat_value', 0)
                    
                    if not (1 <= attacker_stat <= 6):
                        self.log_test("Stat Value Range", False, f"Attacker stat value {attacker_stat} not in range 1-6")
                        return False
                    
                    if not (1 <= defender_stat <= 6):
                        self.log_test("Stat Value Range", False, f"Defender stat value {defender_stat} not in range 1-6")
                        return False

        if stat_access_verified == 0:
            self.log_test("Player Stat Access", False, "No player stats were accessed during simulation")
            return False
        
        self.log_test("Player Stat Access", True, f"Player stats accessed correctly in {stat_access_verified} actions")
        self.log_test("Stat Value Range", True, "All stat values in valid range (1-6)")

        # Test one more match to be sure
        success, match_result_2 = self.run_api_test("Simulate Second Match (Confirmation)", "POST", "league/simulate-next-match")
        if not success:
            return False

        self.log_test("Multiple Match Simulation", True, "Multiple matches simulated successfully without errors")

        return True

    def run_dictionary_access_test(self):
        """Run the specific test for the dictionary access bug fix"""
        print("🚀 Starting Match Simulation Dictionary Access Bug Test")
        print("=" * 70)
        print("Testing fix for: 'dict' object has no attribute 'regate' error")
        print("Fixed lines 325 and 332 in server.py")
        print("=" * 70)
        
        start_time = time.time()
        
        # Setup minimal game scenario
        if not self.setup_minimal_game_for_match_test():
            print(f"\n❌ Setup failed. Cannot proceed with match simulation test.")
            return False
        
        # Test the specific dictionary access fix
        if not self.test_match_simulation_dictionary_access_fix():
            print(f"\n❌ Dictionary access fix test failed.")
            return False
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 70)
        print(f"🏆 DICTIONARY ACCESS BUG TEST COMPLETED")
        print(f"✅ Tests passed: {self.tests_passed}/{self.tests_run}")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED! Dictionary access bug fix is working correctly.")
            print("✅ Match simulation no longer throws 'dict' object has no attribute errors")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed.")
            return False

def main():
    tester = MatchSimulationBugTest()
    success = tester.run_dictionary_access_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())