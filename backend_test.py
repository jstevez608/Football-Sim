import requests
import sys
import json
from datetime import datetime

class FootballDraftAPITester:
    def __init__(self, base_url="https://soccer-draft-league.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.game_state = None
        self.players = []
        self.teams = []

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error details: {error_detail}")
                except:
                    print(f"   Response text: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        success, response = self.run_test(
            "Root API Endpoint",
            "GET",
            "",
            200
        )
        return success

    def test_game_initialization(self):
        """Test game initialization with 75 players"""
        success, response = self.run_test(
            "Game Initialization",
            "POST",
            "game/init",
            200
        )
        if success:
            players_created = response.get('players_created', 0)
            print(f"   Players created: {players_created}")
            if players_created == 75:
                print("✅ Correct number of players generated (75)")
            else:
                print(f"❌ Expected 75 players, got {players_created}")
                return False
        return success

    def test_get_players(self):
        """Test getting all players and validate structure"""
        success, response = self.run_test(
            "Get All Players",
            "GET",
            "players",
            200
        )
        if success:
            self.players = response
            print(f"   Total players retrieved: {len(self.players)}")
            
            # Validate player distribution by position
            positions = {'PORTERO': 0, 'DEFENSA': 0, 'MEDIO': 0, 'DELANTERO': 0}
            for player in self.players:
                positions[player['position']] += 1
            
            print(f"   Position distribution:")
            print(f"     PORTERO: {positions['PORTERO']} (expected: 8)")
            print(f"     DEFENSA: {positions['DEFENSA']} (expected: 33)")
            print(f"     MEDIO: {positions['MEDIO']} (expected: 18)")
            print(f"     DELANTERO: {positions['DELANTERO']} (expected: 16)")
            
            # Validate expected distribution
            expected = {'PORTERO': 8, 'DEFENSA': 33, 'MEDIO': 18, 'DELANTERO': 16}
            distribution_correct = all(positions[pos] == expected[pos] for pos in expected)
            
            if distribution_correct:
                print("✅ Player position distribution is correct")
            else:
                print("❌ Player position distribution is incorrect")
            
            # Validate player structure
            if self.players:
                sample_player = self.players[0]
                required_fields = ['id', 'name', 'position', 'price', 'resistance', 'stats']
                stats_fields = ['pase', 'area', 'tiro', 'remate', 'corner', 'penalti', 'regate', 'parada', 'despeje', 'robo', 'bloqueo']
                
                structure_valid = all(field in sample_player for field in required_fields)
                stats_valid = all(stat in sample_player['stats'] for stat in stats_fields)
                
                if structure_valid and stats_valid:
                    print("✅ Player structure is valid")
                else:
                    print("❌ Player structure is invalid")
                    return False
                
                # Validate stats are in range 1-6
                stats_in_range = all(
                    1 <= sample_player['stats'][stat] <= 6 
                    for stat in stats_fields
                )
                
                if stats_in_range:
                    print("✅ Player stats are in valid range (1-6)")
                else:
                    print("❌ Player stats are out of range")
                    return False
            
            return distribution_correct and structure_valid and stats_valid
        return success

    def test_create_teams(self):
        """Test creating teams with different budgets"""
        team_configs = [
            {
                "name": "Real Madrid Test",
                "colors": {"primary": "#FFFFFF", "secondary": "#000000"},
                "budget": 180000000  # Max budget
            },
            {
                "name": "Barcelona Test", 
                "colors": {"primary": "#FF0000", "secondary": "#0000FF"},
                "budget": 120000000  # Mid budget
            },
            {
                "name": "Atletico Test",
                "colors": {"primary": "#FF0000", "secondary": "#FFFFFF"},
                "budget": 40000000   # Min budget
            }
        ]
        
        created_teams = []
        for i, team_config in enumerate(team_configs):
            success, response = self.run_test(
                f"Create Team {i+1} - {team_config['name']}",
                "POST",
                "teams",
                200,
                data=team_config
            )
            if success:
                team_id = response.get('team_id')
                if team_id:
                    created_teams.append(team_id)
                    print(f"   Team created with ID: {team_id}")
                else:
                    print("❌ No team_id returned")
                    return False
            else:
                return False
        
        return len(created_teams) == 3

    def test_get_teams(self):
        """Test getting all teams"""
        success, response = self.run_test(
            "Get All Teams",
            "GET",
            "teams",
            200
        )
        if success:
            self.teams = response
            print(f"   Total teams retrieved: {len(self.teams)}")
            
            # Validate team structure
            if self.teams:
                sample_team = self.teams[0]
                required_fields = ['id', 'name', 'colors', 'budget', 'players']
                structure_valid = all(field in sample_team for field in required_fields)
                
                if structure_valid:
                    print("✅ Team structure is valid")
                else:
                    print("❌ Team structure is invalid")
                    return False
        return success

    def test_game_state(self):
        """Test getting game state"""
        success, response = self.run_test(
            "Get Game State",
            "GET",
            "game/state",
            200
        )
        if success:
            self.game_state = response
            print(f"   Current phase: {response.get('current_phase')}")
            print(f"   Teams in game: {len(response.get('teams', []))}")
            
            # Validate game state structure
            required_fields = ['id', 'teams', 'current_phase', 'current_round', 'current_team_turn']
            structure_valid = all(field in response for field in required_fields)
            
            if structure_valid:
                print("✅ Game state structure is valid")
            else:
                print("❌ Game state structure is invalid")
                return False
        return success

    def test_player_update(self):
        """Test updating a player"""
        if not self.players:
            print("❌ No players available for update test")
            return False
        
        # Get first player
        player = self.players[0]
        player_id = player['id']
        
        # Update player data
        update_data = {
            "name": "Updated Player Name",
            "price": 5000000,
            "resistance": 10
        }
        
        success, response = self.run_test(
            f"Update Player - {player['name']}",
            "PUT",
            f"players/{player_id}",
            200,
            data=update_data
        )
        return success

    def test_start_draft(self):
        """Test starting the draft phase"""
        # First, create enough teams (need 8 total)
        additional_teams = [
            {"name": f"Team {i}", "colors": {"primary": "#FF0000", "secondary": "#FFFFFF"}, "budget": 80000000}
            for i in range(4, 9)  # Create teams 4-8
        ]
        
        for team_config in additional_teams:
            success, response = self.run_test(
                f"Create Additional Team - {team_config['name']}",
                "POST",
                "teams",
                200,
                data=team_config
            )
            if not success:
                print("❌ Failed to create additional teams for draft test")
                return False
        
        # Now start draft
        success, response = self.run_test(
            "Start Draft Phase",
            "POST",
            "draft/start",
            200
        )
        if success:
            draft_order = response.get('draft_order', [])
            print(f"   Draft order set with {len(draft_order)} teams")
            if len(draft_order) == 8:
                print("✅ Draft order contains all 8 teams")
            else:
                print(f"❌ Expected 8 teams in draft order, got {len(draft_order)}")
                return False
        return success

    def test_draft_player(self):
        """Test drafting a player"""
        # Refresh game state and teams after starting draft
        self.test_game_state()
        self.test_get_teams()
        
        if not self.game_state or not self.teams or not self.players:
            print("❌ Missing required data for draft test")
            return False
        
        # Get current team turn
        current_team_index = self.game_state.get('current_team_turn', 0)
        draft_order = self.game_state.get('draft_order', [])
        
        if not draft_order:
            print("❌ No draft order available")
            return False
        
        current_team_id = draft_order[current_team_index]
        
        # Find an available player
        available_players = [p for p in self.players if not p.get('team_id')]
        if not available_players:
            print("❌ No available players for drafting")
            return False
        
        player_to_draft = available_players[0]
        
        # Draft the player using query parameters
        success, response = self.run_test(
            f"Draft Player - {player_to_draft['name']}",
            "POST",
            f"draft/pick?team_id={current_team_id}&player_id={player_to_draft['id']}",
            200
        )
        return success

    def test_budget_validation(self):
        """Test budget validation during drafting"""
        # Try to create a team with invalid budget (too low)
        invalid_team = {
            "name": "Invalid Budget Team",
            "colors": {"primary": "#FF0000", "secondary": "#FFFFFF"},
            "budget": 30000000  # Below minimum of 40M
        }
        
        success, response = self.run_test(
            "Create Team with Invalid Budget (Too Low)",
            "POST",
            "teams",
            422,  # Validation error expected
            data=invalid_team
        )
        
        # Success here means we got the expected validation error
        if success:
            print("✅ Budget validation working correctly (rejected low budget)")
        
        # Try with budget too high
        invalid_team_high = {
            "name": "Invalid Budget Team High",
            "colors": {"primary": "#FF0000", "secondary": "#FFFFFF"},
            "budget": 200000000  # Above maximum of 180M
        }
        
        success2, response2 = self.run_test(
            "Create Team with Invalid Budget (Too High)",
            "POST",
            "teams",
            422,  # Validation error expected
            data=invalid_team_high
        )
        
        if success2:
            print("✅ Budget validation working correctly (rejected high budget)")
        
        return success and success2

def main():
    print("🚀 Starting Football Draft League API Tests")
    print("=" * 60)
    
    tester = FootballDraftAPITester()
    
    # Run all tests in sequence
    tests = [
        ("Root Endpoint", tester.test_root_endpoint),
        ("Game Initialization", tester.test_game_initialization),
        ("Get Players", tester.test_get_players),
        ("Create Teams", tester.test_create_teams),
        ("Get Teams", tester.test_get_teams),
        ("Game State", tester.test_game_state),
        ("Player Update", tester.test_player_update),
        ("Budget Validation", tester.test_budget_validation),
        ("Start Draft", tester.test_start_draft),
        ("Draft Player", tester.test_draft_player),
    ]
    
    failed_tests = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            if not result:
                failed_tests.append(test_name)
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {str(e)}")
            failed_tests.append(test_name)
    
    # Print final results
    print(f"\n{'='*60}")
    print(f"📊 FINAL RESULTS")
    print(f"{'='*60}")
    print(f"Tests run: {tester.tests_run}")
    print(f"Tests passed: {tester.tests_passed}")
    print(f"Tests failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if failed_tests:
        print(f"\n❌ Failed test categories:")
        for test in failed_tests:
            print(f"   - {test}")
    else:
        print(f"\n✅ All test categories passed!")
    
    return 0 if len(failed_tests) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())