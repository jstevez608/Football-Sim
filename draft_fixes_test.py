import requests
import sys
import json
from datetime import datetime

class DraftFixesAPITester:
    def __init__(self, base_url="https://soccer-draft-league.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.game_state = None
        self.teams = []
        self.draft_order = []

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)

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

    def test_draft_order_sequential(self):
        """Test that draft order is sequential (not random) - FIX #1"""
        print("\n🎯 TESTING DRAFT ORDER IS SEQUENTIAL (FIX #1)")
        
        # Initialize game and create 8 teams
        success, _ = self.run_test("Initialize Game", "POST", "game/init", 200)
        if not success:
            return False
        
        # Create 8 teams
        team_ids = []
        for i in range(1, 9):
            team_data = {
                "name": f"Team {i}",
                "colors": {"primary": "#FF0000", "secondary": "#FFFFFF"},
                "budget": 80000000
            }
            success, response = self.run_test(f"Create Team {i}", "POST", "teams", 200, data=team_data)
            if success:
                team_ids.append(response.get('team_id'))
            else:
                return False
        
        print(f"   Created teams with IDs: {team_ids}")
        
        # Start draft
        success, response = self.run_test("Start Draft", "POST", "draft/start", 200)
        if not success:
            return False
        
        draft_order = response.get('draft_order', [])
        print(f"   Draft order returned: {draft_order}")
        
        # Verify draft order is sequential (same as team creation order)
        if draft_order == team_ids:
            print("✅ Draft order is sequential (matches team creation order)")
            self.draft_order = draft_order
            return True
        else:
            print(f"❌ Draft order is NOT sequential")
            print(f"   Expected: {team_ids}")
            print(f"   Got:      {draft_order}")
            return False

    def test_team_player_limit_10(self):
        """Test that teams can draft up to 10 players (not 8) - FIX #2"""
        print("\n🎯 TESTING TEAM PLAYER LIMIT IS 10 (FIX #2)")
        
        if not self.draft_order:
            print("❌ No draft order available - run draft order test first")
            return False
        
        # Get players
        success, players = self.run_test("Get Players", "GET", "players", 200)
        if not success:
            return False
        
        available_players = [p for p in players if not p.get('team_id')]
        if len(available_players) < 10:
            print(f"❌ Not enough available players. Need 10, have {len(available_players)}")
            return False
        
        # Test with first team - draft 10 players
        test_team_id = self.draft_order[0]
        print(f"   Testing with team: {test_team_id}")
        
        # Draft 10 players for the first team
        for i in range(10):
            # Get current game state to ensure it's this team's turn
            success, game_state = self.run_test("Get Game State", "GET", "game/state", 200)
            if not success:
                return False
            
            current_team_index = game_state.get('current_team_turn', 0)
            current_team_id = self.draft_order[current_team_index]
            
            # If it's not our test team's turn, skip turns until it is
            while current_team_id != test_team_id:
                success, _ = self.run_test(f"Skip Turn to reach test team", "POST", "draft/skip-turn", 200, 
                                        data={"team_id": current_team_id})
                if not success:
                    return False
                
                # Get updated game state
                success, game_state = self.run_test("Get Game State", "GET", "game/state", 200)
                if not success:
                    return False
                current_team_index = game_state.get('current_team_turn', 0)
                current_team_id = self.draft_order[current_team_index]
            
            # Get fresh available players
            success, players = self.run_test("Get Players", "GET", "players", 200)
            if not success:
                return False
            available_players = [p for p in players if not p.get('team_id')]
            
            if not available_players:
                print(f"❌ No more available players at player {i + 1}")
                return False
            
            player_to_draft = available_players[0]
            
            # Draft the player
            success, response = self.run_test(
                f"Draft Player {i + 1}/10 - {player_to_draft['name']}",
                "POST",
                "draft/pick",
                200,
                data={
                    "team_id": test_team_id,
                    "player_id": player_to_draft['id'],
                    "clause_amount": 0
                }
            )
            
            if not success:
                if i < 8:
                    print(f"❌ Failed to draft player {i + 1} - should be allowed up to 10")
                    return False
                else:
                    print(f"   Player {i + 1} draft failed - checking if it's the expected limit")
                    # Check if error message mentions team is full
                    return False
        
        print("✅ Successfully drafted 10 players - team limit is correctly set to 10")
        
        # Now try to draft an 11th player (should fail)
        # Skip turns to get back to our test team
        success, game_state = self.run_test("Get Game State", "GET", "game/state", 200)
        if not success:
            return False
        
        current_team_index = game_state.get('current_team_turn', 0)
        current_team_id = self.draft_order[current_team_index]
        
        # Skip turns until we reach our test team again
        while current_team_id != test_team_id:
            success, _ = self.run_test(f"Skip Turn to reach test team for 11th player", "POST", "draft/skip-turn", 200, 
                                    data={"team_id": current_team_id})
            if not success:
                break
            
            success, game_state = self.run_test("Get Game State", "GET", "game/state", 200)
            if not success:
                break
            current_team_index = game_state.get('current_team_turn', 0)
            current_team_id = self.draft_order[current_team_index]
        
        # Try to draft 11th player (should fail)
        success, players = self.run_test("Get Players", "GET", "players", 200)
        if success and players:
            available_players = [p for p in players if not p.get('team_id')]
            if available_players:
                player_to_draft = available_players[0]
                
                success, response = self.run_test(
                    f"Draft 11th Player (Should Fail) - {player_to_draft['name']}",
                    "POST",
                    "draft/pick",
                    400,  # Should fail with 400
                    data={
                        "team_id": test_team_id,
                        "player_id": player_to_draft['id'],
                        "clause_amount": 0
                    }
                )
                
                if success:
                    print("✅ Correctly rejected 11th player - team limit working")
                    return True
                else:
                    print("❌ Should have rejected 11th player")
                    return False
        
        return True

    def test_cyclic_turn_order(self):
        """Test that turns advance in cyclic order - VERIFICATION"""
        print("\n🎯 TESTING CYCLIC TURN ORDER")
        
        if not self.draft_order:
            print("❌ No draft order available")
            return False
        
        # Get initial game state
        success, game_state = self.run_test("Get Game State", "GET", "game/state", 200)
        if not success:
            return False
        
        initial_turn = game_state.get('current_team_turn', 0)
        print(f"   Initial turn index: {initial_turn}")
        
        # Test cycling through all teams
        for i in range(len(self.draft_order)):
            success, game_state = self.run_test("Get Game State", "GET", "game/state", 200)
            if not success:
                return False
            
            current_turn = game_state.get('current_team_turn', 0)
            expected_turn = (initial_turn + i) % len(self.draft_order)
            current_team_id = self.draft_order[current_turn]
            
            print(f"   Turn {i}: Expected index {expected_turn}, Got index {current_turn}, Team: {current_team_id}")
            
            if current_turn != expected_turn:
                print(f"❌ Turn order incorrect at step {i}")
                return False
            
            # Skip this team's turn to advance to next
            if i < len(self.draft_order) - 1:  # Don't skip on last iteration
                success, _ = self.run_test(f"Skip Turn {i}", "POST", "draft/skip-turn", 200, 
                                        data={"team_id": current_team_id})
                if not success:
                    return False
        
        print("✅ Cyclic turn order working correctly")
        return True

def main():
    print("🚀 Testing Specific Draft Fixes")
    print("=" * 60)
    print("FIX #1: Draft order should be sequential (not random)")
    print("FIX #2: Team player limit should be 10 (not 8)")
    print("=" * 60)
    
    tester = DraftFixesAPITester()
    
    tests = [
        ("Draft Order Sequential", tester.test_draft_order_sequential),
        ("Team Player Limit 10", tester.test_team_player_limit_10),
        ("Cyclic Turn Order", tester.test_cyclic_turn_order),
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
    print(f"📊 DRAFT FIXES TEST RESULTS")
    print(f"{'='*60}")
    print(f"Tests run: {tester.tests_run}")
    print(f"Tests passed: {tester.tests_passed}")
    print(f"Tests failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if failed_tests:
        print(f"\n❌ Failed tests:")
        for test in failed_tests:
            print(f"   - {test}")
        print(f"\n🔧 ISSUES FOUND:")
        print(f"   - Review failed tests above")
        print(f"   - Check if fixes were properly implemented")
    else:
        print(f"\n✅ All draft fixes working correctly!")
        print(f"🎉 Sequential draft order and 10-player limit confirmed!")
    
    return 0 if len(failed_tests) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())