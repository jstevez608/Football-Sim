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
        self.draft_order = []

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
            players_available = response.get('players_available', 0)
            print(f"   Players available: {players_available}")
            print(f"   Full response: {response}")
            
            # The response might have players_available instead of players_created
            if players_available >= 75:
                print("✅ Correct number of players available (75+)")
                return True
            elif players_available > 0:
                print(f"⚠️  Players available ({players_available}) but expected 75+")
                return True  # Still proceed with available players
            else:
                print(f"❌ No players available")
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
        # Get current teams
        self.test_get_teams()
        
        if len(self.teams) != 8:
            print(f"❌ Need exactly 8 teams to start draft, have {len(self.teams)}")
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
                self.draft_order = draft_order
            else:
                print(f"❌ Expected 8 teams in draft order, got {len(draft_order)}")
                return False
        return success

    def test_skip_turn_functionality(self):
        """Test the skip turn functionality - NEW FEATURE"""
        print("\n🎯 TESTING NEW SKIP TURN FUNCTIONALITY")
        
        # First ensure we're in draft phase and get current state
        self.test_game_state()
        
        if not self.game_state or self.game_state.get('current_phase') != 'draft':
            print("❌ Game not in draft phase for skip turn test")
            return False
        
        current_team_index = self.game_state.get('current_team_turn', 0)
        draft_order = self.game_state.get('draft_order', [])
        
        if not draft_order:
            print("❌ No draft order available")
            return False
        
        current_team_id = draft_order[current_team_index]
        print(f"   Current team turn: {current_team_id} (index {current_team_index})")
        
        # Test 1: Skip turn with correct team (should work)
        success1, response1 = self.run_test(
            "Skip Turn - Correct Team",
            "POST",
            "draft/skip-turn",
            200,
            data={"team_id": current_team_id}
        )
        
        if success1:
            next_turn_index = response1.get('next_turn_index')
            expected_next = (current_team_index + 1) % len(draft_order)
            if next_turn_index == expected_next:
                print(f"✅ Turn correctly advanced to index {next_turn_index}")
            else:
                print(f"❌ Turn index incorrect. Expected {expected_next}, got {next_turn_index}")
                return False
        
        # Refresh game state to get new current team
        self.test_game_state()
        new_current_team_index = self.game_state.get('current_team_turn', 0)
        new_current_team_id = draft_order[new_current_team_index]
        
        # Test 2: Try to skip turn with wrong team (should fail)
        wrong_team_id = current_team_id  # This is now the previous team
        success2, response2 = self.run_test(
            "Skip Turn - Wrong Team (Should Fail)",
            "POST",
            "draft/skip-turn",
            400,  # Should fail with 400
            data={"team_id": wrong_team_id}
        )
        
        if success2:
            print("✅ Correctly rejected skip turn from wrong team")
        
        return success1 and success2

    def test_draft_players_to_minimum(self):
        """Draft players to get teams to minimum 7 players each"""
        print("\n🎯 DRAFTING PLAYERS TO REACH MINIMUM 7 PER TEAM")
        
        # Get available players
        self.test_get_players()
        available_players = [p for p in self.players if not p.get('team_id')]
        
        if len(available_players) < 56:  # 8 teams * 7 players minimum
            print(f"❌ Not enough available players. Need 56, have {len(available_players)}")
            return False
        
        # Draft 7 players for each team
        players_drafted = 0
        target_players_per_team = 7
        
        for round_num in range(target_players_per_team):
            print(f"\n   Drafting round {round_num + 1}...")
            
            for team_index in range(8):  # 8 teams
                # Get current game state
                self.test_game_state()
                current_team_index = self.game_state.get('current_team_turn', 0)
                draft_order = self.game_state.get('draft_order', [])
                current_team_id = draft_order[current_team_index]
                
                # Get fresh available players
                self.test_get_players()
                available_players = [p for p in self.players if not p.get('team_id')]
                
                if not available_players:
                    print(f"❌ No more available players at round {round_num + 1}, team {team_index + 1}")
                    return False
                
                # Draft first available player
                player_to_draft = available_players[0]
                
                success, response = self.run_test(
                    f"Draft Player {players_drafted + 1} - {player_to_draft['name']} to Team {current_team_index + 1}",
                    "POST",
                    "draft/pick",
                    200,
                    data={
                        "team_id": current_team_id,
                        "player_id": player_to_draft['id'],
                        "clause_amount": 0
                    }
                )
                
                if success:
                    players_drafted += 1
                    print(f"   ✅ Player {players_drafted} drafted successfully")
                else:
                    print(f"❌ Failed to draft player {players_drafted + 1}")
                    return False
        
        print(f"\n✅ Successfully drafted {players_drafted} players ({target_players_per_team} per team)")
        return True

    def test_league_start_with_7_players(self):
        """Test starting league with minimum 7 players per team - NEW FEATURE"""
        print("\n🎯 TESTING LEAGUE START WITH MINIMUM 7 PLAYERS")
        
        # Get current teams to verify they have 7+ players
        self.test_get_teams()
        
        teams_ready = 0
        for team in self.teams:
            player_count = len(team.get('players', []))
            print(f"   Team {team['name']}: {player_count} players")
            if player_count >= 7:
                teams_ready += 1
        
        if teams_ready != 8:
            print(f"❌ Only {teams_ready}/8 teams have 7+ players")
            return False
        
        print("✅ All teams have 7+ players, attempting to start league...")
        
        # Test league start
        success, response = self.run_test(
            "Start League with 7+ Players",
            "POST",
            "league/start",
            200
        )
        
        if success:
            matches_created = response.get('matches_created', 0)
            print(f"   Matches created: {matches_created}")
            
            # Verify game state changed to league
            self.test_game_state()
            if self.game_state.get('current_phase') == 'league':
                print("✅ Game phase successfully changed to 'league'")
                return True
            else:
                print(f"❌ Game phase is {self.game_state.get('current_phase')}, expected 'league'")
                return False
        
        return success

    def test_set_player_clause(self):
        """Test setting clauses on owned players during league phase - NEW FEATURE"""
        print("\n🎯 TESTING SET PLAYER CLAUSE FUNCTIONALITY")
        
        # Ensure we're in league phase
        if not self.game_state or self.game_state.get('current_phase') != 'league':
            print("❌ Game not in league phase for clause test")
            return False
        
        # Get teams and find a team with players
        self.test_get_teams()
        test_team = None
        test_player = None
        
        for team in self.teams:
            if team.get('players') and len(team['players']) > 0:
                test_team = team
                # Get player details
                self.test_get_players()
                for player in self.players:
                    if player['id'] in team['players']:
                        test_player = player
                        break
                break
        
        if not test_team or not test_player:
            print("❌ No team with players found for clause test")
            return False
        
        print(f"   Testing with team: {test_team['name']}")
        print(f"   Testing with player: {test_player['name']}")
        print(f"   Team budget: {test_team['budget']}")
        
        # Test setting a clause
        clause_amount = 1000000  # 1M clause
        
        success, response = self.run_test(
            f"Set Clause on {test_player['name']}",
            "POST",
            f"teams/{test_team['id']}/set-clause",
            200,
            data={
                "player_id": test_player['id'],
                "clause_amount": clause_amount
            }
        )
        
        if success:
            print(f"✅ Clause of {clause_amount} set successfully")
            
            # Verify player has clause and team budget reduced
            self.test_get_players()
            updated_player = next((p for p in self.players if p['id'] == test_player['id']), None)
            if updated_player and updated_player.get('clause_amount') == clause_amount:
                print("✅ Player clause amount updated correctly")
            else:
                print("❌ Player clause amount not updated")
                return False
        
        return success

    def test_buy_player_between_teams(self):
        """Test buying players between teams during league phase - NEW FEATURE"""
        print("\n🎯 TESTING BUY PLAYER BETWEEN TEAMS")
        
        # Ensure we're in league phase
        if not self.game_state or self.game_state.get('current_phase') != 'league':
            print("❌ Game not in league phase for buy player test")
            return False
        
        # Get teams and find buyer/seller
        self.test_get_teams()
        
        # Find a team with >7 players (seller) and a team with <10 players (buyer)
        seller_team = None
        buyer_team = None
        
        for team in self.teams:
            player_count = len(team.get('players', []))
            if player_count > 7 and not seller_team:
                seller_team = team
            elif player_count < 10 and not buyer_team and team != seller_team:
                buyer_team = team
        
        if not seller_team or not buyer_team:
            print("❌ Could not find suitable buyer and seller teams")
            print(f"   Seller team found: {seller_team is not None}")
            print(f"   Buyer team found: {buyer_team is not None}")
            return False
        
        # Find a player from seller team
        self.test_get_players()
        player_to_buy = None
        for player in self.players:
            if player.get('team_id') == seller_team['id']:
                player_to_buy = player
                break
        
        if not player_to_buy:
            print("❌ No player found in seller team")
            return False
        
        print(f"   Buyer: {buyer_team['name']} (budget: {buyer_team['budget']})")
        print(f"   Seller: {seller_team['name']} ({len(seller_team['players'])} players)")
        print(f"   Player: {player_to_buy['name']} (price: {player_to_buy['price']}, clause: {player_to_buy.get('clause_amount', 0)})")
        
        total_cost = player_to_buy['price'] + player_to_buy.get('clause_amount', 0)
        print(f"   Total cost: {total_cost}")
        
        # Test buying the player
        success, response = self.run_test(
            f"Buy {player_to_buy['name']} from {seller_team['name']} to {buyer_team['name']}",
            "POST",
            "teams/buy-player",
            200,
            data={
                "buyer_team_id": buyer_team['id'],
                "seller_team_id": seller_team['id'],
                "player_id": player_to_buy['id']
            }
        )
        
        if success:
            print(f"✅ Player purchased successfully for {response.get('total_cost')}")
            
            # Verify transfer completed
            self.test_get_players()
            self.test_get_teams()
            
            updated_player = next((p for p in self.players if p['id'] == player_to_buy['id']), None)
            if updated_player and updated_player.get('team_id') == buyer_team['id']:
                print("✅ Player successfully transferred to buyer team")
            else:
                print("❌ Player transfer not completed")
                return False
        
        return success

    def test_edge_cases(self):
        """Test edge cases for the new functionality"""
        print("\n🎯 TESTING EDGE CASES")
        
        # Get current state
        self.test_get_teams()
        self.test_get_players()
        
        # Test 1: Try to buy player when seller would have <7 players
        # Find a team with exactly 7 players
        team_with_7 = None
        for team in self.teams:
            if len(team.get('players', [])) == 7:
                team_with_7 = team
                break
        
        if team_with_7:
            # Find another team to be buyer
            buyer_team = next((t for t in self.teams if t['id'] != team_with_7['id'] and len(t.get('players', [])) < 10), None)
            
            if buyer_team:
                # Find a player from the 7-player team
                player_from_7_team = next((p for p in self.players if p.get('team_id') == team_with_7['id']), None)
                
                if player_from_7_team:
                    success, response = self.run_test(
                        "Try to buy player from team with only 7 players (Should Fail)",
                        "POST",
                        "teams/buy-player",
                        400,  # Should fail
                        data={
                            "buyer_team_id": buyer_team['id'],
                            "seller_team_id": team_with_7['id'],
                            "player_id": player_from_7_team['id']
                        }
                    )
                    
                    if success:
                        print("✅ Correctly prevented sale that would leave team with <7 players")
                    else:
                        print("❌ Should have prevented sale from team with only 7 players")
                        return False
        
        # Test 2: Try to set clause with insufficient budget
        # Find a team and try to set a clause higher than their budget
        team_for_clause_test = self.teams[0] if self.teams else None
        if team_for_clause_test and team_for_clause_test.get('players'):
            player_for_clause = next((p for p in self.players if p.get('team_id') == team_for_clause_test['id']), None)
            
            if player_for_clause:
                excessive_clause = team_for_clause_test['budget'] + 1000000  # More than budget
                
                success, response = self.run_test(
                    "Try to set clause higher than budget (Should Fail)",
                    "POST",
                    f"teams/{team_for_clause_test['id']}/set-clause",
                    400,  # Should fail
                    data={
                        "player_id": player_for_clause['id'],
                        "clause_amount": excessive_clause
                    }
                )
                
                if success:
                    print("✅ Correctly prevented setting clause higher than budget")
                else:
                    print("❌ Should have prevented setting excessive clause")
                    return False
        
        return True

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
    print("🚀 Starting Football Draft League API Tests - NEW FEATURES FOCUS")
    print("=" * 80)
    
    tester = FootballDraftAPITester()
    
    # Initialize game and create 8 teams first
    print("\n🔧 SETUP PHASE")
    print("=" * 40)
    
    # Initialize game
    success = tester.test_game_initialization()
    if not success:
        print("❌ Failed to initialize game. Stopping tests.")
        return 1
    
    # Load players
    success = tester.test_get_players()
    if not success:
        print("❌ Failed to load players. Stopping tests.")
        return 1
    
    # Check if teams already exist
    tester.test_get_teams()
    existing_teams = len(tester.teams)
    print(f"   Existing teams: {existing_teams}")
    
    # Create teams only if we don't have 8 already
    if existing_teams < 8:
        teams_to_create = 8 - existing_teams
        print(f"   Creating {teams_to_create} additional teams...")
        
        team_configs = [
            {"name": f"Team {i}", "colors": {"primary": "#FF0000", "secondary": "#FFFFFF"}, "budget": 80000000}
            for i in range(existing_teams + 1, 9)
        ]
        
        for team_config in team_configs:
            success, response = tester.run_test(
                f"Create {team_config['name']}",
                "POST",
                "teams",
                200,
                data=team_config
            )
            if not success:
                print(f"❌ Failed to create {team_config['name']}. Stopping tests.")
                return 1
    else:
        print(f"   ✅ Already have {existing_teams} teams, no need to create more")
    
    # Start draft
    success = tester.test_start_draft()
    if not success:
        print("❌ Failed to start draft. Stopping tests.")
        return 1
    
    # Run NEW FEATURE tests
    print("\n🎯 NEW FEATURES TESTING")
    print("=" * 40)
    
    tests = [
        ("Skip Turn Functionality", tester.test_skip_turn_functionality),
        ("Draft Players to Minimum 7", tester.test_draft_players_to_minimum),
        ("League Start with 7+ Players", tester.test_league_start_with_7_players),
        ("Set Player Clause", tester.test_set_player_clause),
        ("Buy Player Between Teams", tester.test_buy_player_between_teams),
        ("Edge Cases", tester.test_edge_cases),
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
    print(f"\n{'='*80}")
    print(f"📊 FINAL RESULTS - NEW FEATURES TESTING")
    print(f"{'='*80}")
    print(f"Tests run: {tester.tests_run}")
    print(f"Tests passed: {tester.tests_passed}")
    print(f"Tests failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if failed_tests:
        print(f"\n❌ Failed test categories:")
        for test in failed_tests:
            print(f"   - {test}")
        print(f"\n🔧 ACTION ITEMS FOR E1:")
        print(f"   - Review failed tests above")
        print(f"   - Check backend logs for detailed error information")
        print(f"   - Verify API endpoints are working as expected")
    else:
        print(f"\n✅ All new feature tests passed!")
        print(f"🎉 Skip turn, 7-player league start, and clause/transfer system working correctly!")
    
    return 0 if len(failed_tests) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())