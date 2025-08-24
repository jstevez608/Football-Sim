#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import time
import random

class MatchSimulationTester:
    def __init__(self, base_url="https://soccer-draft-league.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.game_state = None
        self.teams = []
        self.players = []
        self.matches = []

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

    def setup_complete_game_scenario(self):
        """Set up a complete game scenario with 8 teams and lineups"""
        print("\n🔧 Setting up complete game scenario...")
        
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

        # 3. Create 8 teams
        team_names = ["Real Madrid", "Barcelona", "Atletico", "Valencia", "Sevilla", "Betis", "Athletic", "Villarreal"]
        colors = [
            {"primary": "#FFFFFF", "secondary": "#000000"},
            {"primary": "#FF0000", "secondary": "#0000FF"},
            {"primary": "#FF0000", "secondary": "#FFFFFF"},
            {"primary": "#FF8C00", "secondary": "#000000"},
            {"primary": "#FF0000", "secondary": "#FFFFFF"},
            {"primary": "#00FF00", "secondary": "#FFFFFF"},
            {"primary": "#FF0000", "secondary": "#FFFFFF"},
            {"primary": "#FFFF00", "secondary": "#000000"}
        ]

        for i, name in enumerate(team_names):
            team_data = {
                "name": name,
                "colors": colors[i],
                "budget": 80000000
            }
            success, response = self.run_api_test(f"Create Team {name}", "POST", "teams", data=team_data)
            if not success:
                return False

        # 4. Load teams
        success, teams = self.run_api_test("Load Teams", "GET", "teams")
        if not success:
            return False
        self.teams = teams
        self.log_test("Teams Created", True, f"Created {len(teams)} teams")

        # 5. Start draft
        success, response = self.run_api_test("Start Draft", "POST", "draft/start")
        if not success:
            return False
        self.log_test("Draft Started", True)

        # 6. Draft players for each team (7 players minimum)
        available_players = [p for p in self.players if not p.get('team_id')]
        random.shuffle(available_players)
        
        player_index = 0
        # Draft 7 rounds of players (each team gets 7 players)
        for round_num in range(7):
            for team_index in range(8):  # 8 teams
                if player_index >= len(available_players):
                    break
                
                # Get current game state to find whose turn it is
                success, game_state = self.run_api_test("Get Game State for Draft", "GET", "game/state")
                if not success:
                    return False
                
                current_team_index = game_state.get('current_team_turn', 0)
                draft_order = game_state.get('draft_order', [])
                current_team_id = draft_order[current_team_index]
                current_team = next((t for t in self.teams if t['id'] == current_team_id), None)
                
                if not current_team:
                    self.log_test("Draft Turn", False, f"Could not find current team")
                    return False
                
                player = available_players[player_index]
                success, response = self.run_api_test(
                    f"Draft {player['name']} to {current_team['name']}", 
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
                player_index += 1

        # 7. Start league
        success, response = self.run_api_test("Start League", "POST", "league/start")
        if not success:
            return False
        self.log_test("League Started", True, f"Total matches: {response.get('total_matches', 0)}")

        # 8. Load updated teams and game state
        success, teams = self.run_api_test("Load Updated Teams", "GET", "teams")
        if not success:
            return False
        self.teams = teams

        success, players = self.run_api_test("Load Updated Players", "GET", "players")
        if not success:
            return False
        self.players = players

        success, game_state = self.run_api_test("Load Game State", "GET", "game/state")
        if not success:
            return False
        self.game_state = game_state

        # 9. Select lineups for all teams
        formations = {"A": "4-3-1", "B": "5-2-1", "C": "4-2-2"}
        formation_requirements = {
            "A": {"PORTERO": 1, "DEFENSA": 2, "MEDIO": 3, "DELANTERO": 1},
            "B": {"PORTERO": 1, "DEFENSA": 3, "MEDIO": 2, "DELANTERO": 1},
            "C": {"PORTERO": 1, "DEFENSA": 2, "MEDIO": 2, "DELANTERO": 2}
        }

        for team in self.teams:
            # Get team players
            team_players = [p for p in self.players if p.get('team_id') == team['id']]
            
            if len(team_players) < 7:
                self.log_test(f"Team {team['name']} Players", False, f"Team has only {len(team_players)} players, need 7")
                return False
            
            # Select formation A (4-3-1) for simplicity
            formation = "A"
            requirements = formation_requirements[formation]
            
            # Select players by position
            selected_players = []
            for position, count in requirements.items():
                position_players = [p for p in team_players if p['position'] == position and p['id'] not in selected_players]
                selected_players.extend([p['id'] for p in position_players[:count]])
            
            if len(selected_players) == 7:
                success, response = self.run_api_test(
                    f"Select Lineup for {team['name']}", 
                    "POST", 
                    "league/lineup/select",
                    data={
                        "team_id": team["id"],
                        "formation": formation,
                        "players": selected_players
                    }
                )
                if not success:
                    return False
            else:
                self.log_test(f"Lineup Selection for {team['name']}", False, f"Could not select 7 players (found {len(selected_players)})")
                return False

        self.log_test("Complete Game Setup", True, "8 teams with lineups ready for matches")
        return True

    def test_match_simulator_mechanics(self):
        """Test the core match simulation mechanics"""
        print("\n⚽ Testing Match Simulation Mechanics...")
        
        # Load current round matches
        success, matches = self.run_api_test("Load Round 1 Matches", "GET", f"league/matches/round/1")
        if not success:
            return False
        
        if not matches:
            self.log_test("Match Loading", False, "No matches found for round 1")
            return False
        
        self.matches = matches
        self.log_test("Match Loading", True, f"Found {len(matches)} matches in round 1")

        # Test simulate next match
        success, match_result = self.run_api_test("Simulate Next Match", "POST", "league/simulate-next-match")
        if not success:
            return False

        # Verify match result structure
        required_fields = ['home_team', 'away_team', 'home_score', 'away_score', 'match_log']
        missing_fields = [field for field in required_fields if field not in match_result]
        
        if missing_fields:
            self.log_test("Match Result Structure", False, f"Missing fields: {missing_fields}")
            return False
        
        self.log_test("Match Result Structure", True, "All required fields present")

        # Verify match log structure
        match_log = match_result.get('match_log', {})
        if not isinstance(match_log, dict):
            self.log_test("Match Log Structure", False, "Match log is not a dictionary")
            return False

        log_fields = ['home_team', 'away_team', 'home_score', 'away_score', 'turns', 'total_turns']
        missing_log_fields = [field for field in log_fields if field not in match_log]
        
        if missing_log_fields:
            self.log_test("Match Log Fields", False, f"Missing log fields: {missing_log_fields}")
            return False
        
        self.log_test("Match Log Fields", True, "All match log fields present")

        # Verify 18 turns total
        turns = match_log.get('turns', [])
        if len(turns) != 18:
            self.log_test("Turn Count", False, f"Expected 18 turns, got {len(turns)}")
            return False
        
        self.log_test("Turn Count", True, "Exactly 18 turns simulated")

        # Verify alternating teams
        home_team_name = match_log['home_team']
        away_team_name = match_log['away_team']
        
        for i, turn in enumerate(turns):
            expected_attacking_team = home_team_name if (i + 1) % 2 == 1 else away_team_name
            if turn.get('attacking_team') != expected_attacking_team:
                self.log_test("Alternating Teams", False, f"Turn {i+1}: Expected {expected_attacking_team}, got {turn.get('attacking_team')}")
                return False
        
        self.log_test("Alternating Teams", True, "Teams alternate correctly (odd=home, even=away)")

        # Verify action structure
        action_count = 0
        goal_count = 0
        
        for turn in turns:
            actions = turn.get('actions', [])
            action_count += len(actions)
            
            for action in actions:
                # Check action structure
                required_action_fields = ['action', 'attacker', 'defender', 'successful']
                missing_action_fields = [field for field in required_action_fields if field not in action]
                
                if missing_action_fields:
                    self.log_test("Action Structure", False, f"Missing action fields: {missing_action_fields}")
                    return False
                
                # Check attacker structure
                attacker = action.get('attacker', {})
                required_attacker_fields = ['name', 'position', 'stat_value', 'random_bonus', 'total']
                missing_attacker_fields = [field for field in required_attacker_fields if field not in attacker]
                
                if missing_attacker_fields:
                    self.log_test("Attacker Structure", False, f"Missing attacker fields: {missing_attacker_fields}")
                    return False
                
                # Check defender structure
                defender = action.get('defender', {})
                required_defender_fields = ['name', 'position', 'defense_action', 'stat_value', 'random_bonus', 'total']
                missing_defender_fields = [field for field in required_defender_fields if field not in defender]
                
                if missing_defender_fields:
                    self.log_test("Defender Structure", False, f"Missing defender fields: {missing_defender_fields}")
                    return False
                
                # Verify random bonus is 1-3
                if not (1 <= attacker.get('random_bonus', 0) <= 3):
                    self.log_test("Random Bonus Range", False, f"Attacker random bonus {attacker.get('random_bonus')} not in range 1-3")
                    return False
                
                if not (1 <= defender.get('random_bonus', 0) <= 3):
                    self.log_test("Random Bonus Range", False, f"Defender random bonus {defender.get('random_bonus')} not in range 1-3")
                    return False
                
                # Verify total calculation
                expected_attacker_total = attacker.get('stat_value', 0) + attacker.get('random_bonus', 0)
                if attacker.get('total') != expected_attacker_total:
                    self.log_test("Total Calculation", False, f"Attacker total mismatch: expected {expected_attacker_total}, got {attacker.get('total')}")
                    return False
                
                expected_defender_total = defender.get('stat_value', 0) + defender.get('random_bonus', 0)
                if defender.get('total') != expected_defender_total:
                    self.log_test("Total Calculation", False, f"Defender total mismatch: expected {expected_defender_total}, got {defender.get('total')}")
                    return False
                
                # Count goals
                if action.get('is_goal', False):
                    goal_count += 1
            
            if turn.get('goal_scored', False):
                # Verify goal was marked in actions
                turn_goals = sum(1 for action in actions if action.get('is_goal', False))
                if turn_goals == 0:
                    self.log_test("Goal Consistency", False, f"Turn marked as goal but no goal action found")
                    return False

        self.log_test("Action Structure", True, f"All actions properly structured ({action_count} total actions)")
        self.log_test("Statistical Calculations", True, "All stat + random calculations correct")
        self.log_test("Goal Detection", True, f"Goals properly detected ({goal_count} total goals)")

        # Verify final score matches goal count
        final_home_score = match_log.get('home_score', 0)
        final_away_score = match_log.get('away_score', 0)
        total_goals_in_log = final_home_score + final_away_score
        
        if total_goals_in_log != goal_count:
            self.log_test("Score Consistency", False, f"Final score total ({total_goals_in_log}) doesn't match goal actions ({goal_count})")
            return False
        
        self.log_test("Score Consistency", True, f"Final score matches goal actions: {final_home_score}-{final_away_score}")

        return True

    def test_team_statistics_update(self):
        """Test team statistics and prize money updates"""
        print("\n📊 Testing Team Statistics Updates...")
        
        # Get teams before and after match
        success, teams_before = self.run_api_test("Load Teams Before Match", "GET", "teams")
        if not success:
            return False

        # Simulate another match
        success, match_result = self.run_api_test("Simulate Second Match", "POST", "league/simulate-next-match")
        if not success:
            return False

        success, teams_after = self.run_api_test("Load Teams After Match", "GET", "teams")
        if not success:
            return False

        # Find the teams that played
        home_team_name = match_result.get('home_team')
        away_team_name = match_result.get('away_team')
        home_score = match_result.get('home_score', 0)
        away_score = match_result.get('away_score', 0)

        home_team_before = next((t for t in teams_before if t['name'] == home_team_name), None)
        away_team_before = next((t for t in teams_before if t['name'] == away_team_name), None)
        home_team_after = next((t for t in teams_after if t['name'] == home_team_name), None)
        away_team_after = next((t for t in teams_after if t['name'] == away_team_name), None)

        if not all([home_team_before, away_team_before, home_team_after, away_team_after]):
            self.log_test("Team Statistics Update", False, "Could not find teams before/after match")
            return False

        # Verify matches played increased
        if home_team_after.get('matches_played', 0) != home_team_before.get('matches_played', 0) + 1:
            self.log_test("Matches Played Update", False, f"Home team matches played not incremented")
            return False

        if away_team_after.get('matches_played', 0) != away_team_before.get('matches_played', 0) + 1:
            self.log_test("Matches Played Update", False, f"Away team matches played not incremented")
            return False

        self.log_test("Matches Played Update", True, "Both teams' matches played incremented")

        # Verify goals for/against
        expected_home_goals_for = home_team_before.get('goals_for', 0) + home_score
        expected_home_goals_against = home_team_before.get('goals_against', 0) + away_score
        expected_away_goals_for = away_team_before.get('goals_for', 0) + away_score
        expected_away_goals_against = away_team_before.get('goals_against', 0) + home_score

        if home_team_after.get('goals_for', 0) != expected_home_goals_for:
            self.log_test("Goals For Update", False, f"Home team goals for: expected {expected_home_goals_for}, got {home_team_after.get('goals_for', 0)}")
            return False

        if home_team_after.get('goals_against', 0) != expected_home_goals_against:
            self.log_test("Goals Against Update", False, f"Home team goals against: expected {expected_home_goals_against}, got {home_team_after.get('goals_against', 0)}")
            return False

        self.log_test("Goals Statistics Update", True, "Goals for/against updated correctly")

        # Verify points and win/draw/loss
        if home_score > away_score:
            # Home win
            expected_home_points = home_team_before.get('points', 0) + 3
            expected_away_points = away_team_before.get('points', 0)
            expected_home_wins = home_team_before.get('wins', 0) + 1
            expected_away_losses = away_team_before.get('losses', 0) + 1
        elif home_score < away_score:
            # Away win
            expected_home_points = home_team_before.get('points', 0)
            expected_away_points = away_team_before.get('points', 0) + 3
            expected_home_losses = home_team_before.get('losses', 0) + 1
            expected_away_wins = away_team_before.get('wins', 0) + 1
        else:
            # Draw
            expected_home_points = home_team_before.get('points', 0) + 1
            expected_away_points = away_team_before.get('points', 0) + 1
            expected_home_draws = home_team_before.get('draws', 0) + 1
            expected_away_draws = away_team_before.get('draws', 0) + 1

        if home_team_after.get('points', 0) != expected_home_points:
            self.log_test("Points Update", False, f"Home team points: expected {expected_home_points}, got {home_team_after.get('points', 0)}")
            return False

        if away_team_after.get('points', 0) != expected_away_points:
            self.log_test("Points Update", False, f"Away team points: expected {expected_away_points}, got {away_team_after.get('points', 0)}")
            return False

        self.log_test("Points Update", True, "Points updated correctly based on result")

        # Verify prize money (500k home bonus + 1M per point)
        if home_score > away_score:
            expected_home_prize = 500000 + (3 * 1000000)  # Home bonus + 3 points
            expected_away_prize = 0  # No points
        elif home_score < away_score:
            expected_home_prize = 500000  # Only home bonus
            expected_away_prize = 3 * 1000000  # 3 points
        else:
            expected_home_prize = 500000 + (1 * 1000000)  # Home bonus + 1 point
            expected_away_prize = 1 * 1000000  # 1 point

        home_budget_increase = home_team_after.get('budget', 0) - home_team_before.get('budget', 0)
        away_budget_increase = away_team_after.get('budget', 0) - away_team_before.get('budget', 0)

        if home_budget_increase != expected_home_prize:
            self.log_test("Prize Money", False, f"Home team prize: expected {expected_home_prize}, got {home_budget_increase}")
            return False

        if away_budget_increase != expected_away_prize:
            self.log_test("Prize Money", False, f"Away team prize: expected {expected_away_prize}, got {away_budget_increase}")
            return False

        self.log_test("Prize Money", True, f"Prize money distributed correctly (Home: €{expected_home_prize:,}, Away: €{expected_away_prize:,})")

        return True

    def test_player_resistance_system(self):
        """Test player resistance/fatigue system"""
        print("\n💪 Testing Player Resistance System...")
        
        # Get players before match
        success, players_before = self.run_api_test("Load Players Before Match", "GET", "players")
        if not success:
            return False

        # Simulate a match
        success, match_result = self.run_api_test("Simulate Match for Resistance Test", "POST", "league/simulate-next-match")
        if not success:
            return False

        # Get players after match
        success, players_after = self.run_api_test("Load Players After Match", "GET", "players")
        if not success:
            return False

        # Find players who played in the match
        match_log = match_result.get('match_log', {})
        played_player_names = set()
        
        for turn in match_log.get('turns', []):
            for action in turn.get('actions', []):
                played_player_names.add(action.get('attacker', {}).get('name'))
                played_player_names.add(action.get('defender', {}).get('name'))

        # Check if games_played was updated for players who played
        resistance_updates = 0
        resting_players = 0
        
        for player_after in players_after:
            if player_after['name'] in played_player_names:
                player_before = next((p for p in players_before if p['id'] == player_after['id']), None)
                if player_before:
                    games_before = player_before.get('games_played', 0)
                    games_after = player_after.get('games_played', 0)
                    resistance = player_after.get('resistance', 10)
                    is_resting = player_after.get('is_resting', False)
                    
                    # Check if player needs to rest (games_played >= resistance)
                    if games_before + 1 >= resistance:
                        # Player should be resting and games_played reset to 0
                        if is_resting and games_after == 0:
                            resting_players += 1
                        else:
                            self.log_test("Player Resistance", False, f"Player {player_after['name']} should be resting but isn't")
                            return False
                    else:
                        # Player should have games_played incremented
                        if games_after == games_before + 1 and not is_resting:
                            resistance_updates += 1
                        else:
                            self.log_test("Player Resistance", False, f"Player {player_after['name']} games_played not updated correctly")
                            return False

        self.log_test("Player Resistance System", True, f"Resistance updated for {resistance_updates} players, {resting_players} players resting")
        return True

    def test_round_progression(self):
        """Test round completion and progression"""
        print("\n🔄 Testing Round Progression...")
        
        # Get current game state
        success, game_state = self.run_api_test("Load Game State", "GET", "game/state")
        if not success:
            return False

        current_round = game_state.get('current_round', 1)
        
        # Simulate remaining matches in current round
        matches_simulated = 0
        while True:
            success, match_result = self.run_api_test(f"Simulate Match {matches_simulated + 1}", "POST", "league/simulate-next-match")
            if not success:
                # Check if it's because no more matches in round
                if "No more matches in current round" in str(match_result):
                    break
                else:
                    return False
            
            matches_simulated += 1
            
            # Check if round completed
            if match_result.get('round_completed', False):
                next_round = match_result.get('next_round')
                self.log_test("Round Completion", True, f"Round {current_round} completed, moving to round {next_round}")
                
                # Verify game state updated
                success, new_game_state = self.run_api_test("Load Updated Game State", "GET", "game/state")
                if not success:
                    return False
                
                if new_game_state.get('current_round') != next_round:
                    self.log_test("Round Progression", False, f"Game state not updated to round {next_round}")
                    return False
                
                self.log_test("Round Progression", True, f"Successfully progressed to round {next_round}")
                return True
            
            # Safety check to avoid infinite loop
            if matches_simulated > 10:
                self.log_test("Round Progression", False, "Too many matches simulated without round completion")
                return False

        self.log_test("Round Progression", True, f"Simulated {matches_simulated} matches in round {current_round}")
        return True

    def run_all_tests(self):
        """Run all match simulation tests"""
        print("🚀 Starting Match Simulation System Tests")
        print("=" * 60)
        
        start_time = time.time()
        
        # Setup complete game scenario
        if not self.setup_complete_game_scenario():
            print(f"\n❌ Setup failed. Cannot proceed with match simulation tests.")
            return False
        
        # Test match simulation mechanics
        if not self.test_match_simulator_mechanics():
            print(f"\n❌ Match simulation mechanics test failed.")
            return False
        
        # Test team statistics updates
        if not self.test_team_statistics_update():
            print(f"\n❌ Team statistics update test failed.")
            return False
        
        # Test player resistance system
        if not self.test_player_resistance_system():
            print(f"\n❌ Player resistance system test failed.")
            return False
        
        # Test round progression
        if not self.test_round_progression():
            print(f"\n❌ Round progression test failed.")
            return False
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print(f"🏆 MATCH SIMULATION TESTS COMPLETED")
        print(f"✅ Tests passed: {self.tests_passed}/{self.tests_run}")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED! Match simulation system working correctly.")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed.")
            return False

def main():
    tester = MatchSimulationTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())