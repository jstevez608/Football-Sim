import requests
import sys
import json
from datetime import datetime

class DraftTurnTester:
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
        if data:
            print(f"   Data: {json.dumps(data, indent=2)}")
        
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
                    print(f"   Error details: {json.dumps(error_detail, indent=2)}")
                except:
                    print(f"   Response text: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def setup_complete_draft_scenario(self):
        """Set up a complete draft scenario with 8 teams"""
        print("\n🏗️  Setting up complete draft scenario...")
        
        # 1. Initialize game
        success, response = self.run_test(
            "Initialize Game",
            "POST",
            "game/init",
            200
        )
        if not success:
            return False
        
        # 2. Get players
        success, response = self.run_test(
            "Get Players",
            "GET",
            "players",
            200
        )
        if not success:
            return False
        self.players = response
        print(f"   Loaded {len(self.players)} players")
        
        # 3. Create exactly 8 teams
        team_configs = [
            {"name": f"Team {i+1}", "colors": {"primary": "#FF0000", "secondary": "#FFFFFF"}, "budget": 80000000}
            for i in range(8)
        ]
        
        created_teams = []
        for i, team_config in enumerate(team_configs):
            success, response = self.run_test(
                f"Create Team {i+1}",
                "POST",
                "teams",
                200,
                data=team_config
            )
            if not success:
                return False
            created_teams.append(response.get('team_id'))
        
        # 4. Get teams to verify
        success, response = self.run_test(
            "Get All Teams",
            "GET",
            "teams",
            200
        )
        if not success:
            return False
        self.teams = response
        print(f"   Created {len(self.teams)} teams")
        
        # 5. Get initial game state
        success, response = self.run_test(
            "Get Initial Game State",
            "GET",
            "game/state",
            200
        )
        if not success:
            return False
        self.game_state = response
        print(f"   Game phase: {self.game_state.get('current_phase')}")
        
        return len(self.teams) == 8

    def test_draft_start(self):
        """Test starting the draft phase"""
        success, response = self.run_test(
            "Start Draft Phase",
            "POST",
            "draft/start",
            200
        )
        if success:
            draft_order = response.get('draft_order', [])
            print(f"   Draft order: {draft_order}")
            print(f"   Draft order length: {len(draft_order)}")
            
            # Verify draft order contains all team IDs
            team_ids = [team['id'] for team in self.teams]
            all_teams_in_order = all(team_id in draft_order for team_id in team_ids)
            
            if all_teams_in_order and len(draft_order) == 8:
                print("✅ Draft order contains all 8 teams")
                return True
            else:
                print("❌ Draft order is incomplete or incorrect")
                return False
        return False

    def test_game_state_after_draft_start(self):
        """Test game state after draft starts"""
        success, response = self.run_test(
            "Get Game State After Draft Start",
            "GET",
            "game/state",
            200
        )
        if success:
            self.game_state = response
            print(f"   Current phase: {response.get('current_phase')}")
            print(f"   Current team turn: {response.get('current_team_turn')}")
            print(f"   Draft order: {response.get('draft_order')}")
            
            # Verify draft state
            if (response.get('current_phase') == 'draft' and 
                response.get('current_team_turn') == 0 and
                len(response.get('draft_order', [])) == 8):
                print("✅ Draft state is correct")
                return True
            else:
                print("❌ Draft state is incorrect")
                return False
        return False

    def test_first_team_can_draft(self):
        """Test that the first team in draft order can draft successfully"""
        if not self.game_state or not self.game_state.get('draft_order'):
            print("❌ No draft order available")
            return False
        
        # Get the first team in draft order
        draft_order = self.game_state['draft_order']
        first_team_id = draft_order[0]
        
        # Find an available player
        available_players = [p for p in self.players if not p.get('team_id')]
        if not available_players:
            print("❌ No available players")
            return False
        
        player_to_draft = available_players[0]
        
        # Test the NEW POST body approach (this is the fix being tested)
        draft_request = {
            "team_id": first_team_id,
            "player_id": player_to_draft['id'],
            "clause_amount": 0
        }
        
        success, response = self.run_test(
            f"First Team Draft Player (NEW POST body approach)",
            "POST",
            "draft/pick",
            200,
            data=draft_request
        )
        
        if success:
            print(f"✅ First team successfully drafted player {player_to_draft['name']}")
            next_turn = response.get('next_turn_index')
            print(f"   Next turn index: {next_turn}")
            return True
        else:
            print(f"❌ First team failed to draft player - this indicates the 'Not your turn' bug is still present")
            return False

    def test_turn_progression(self):
        """Test that turns progress correctly"""
        # Get updated game state
        success, response = self.run_test(
            "Get Game State After First Draft",
            "GET",
            "game/state",
            200
        )
        if not success:
            return False
        
        self.game_state = response
        current_turn = self.game_state.get('current_team_turn')
        draft_order = self.game_state.get('draft_order', [])
        
        print(f"   Current turn after first draft: {current_turn}")
        
        if current_turn == 1:
            print("✅ Turn progressed correctly to next team")
            
            # Test that the second team can now draft
            if len(draft_order) > 1:
                second_team_id = draft_order[1]
                
                # Find another available player
                available_players = [p for p in self.players if not p.get('team_id')]
                if available_players:
                    player_to_draft = available_players[0]
                    
                    draft_request = {
                        "team_id": second_team_id,
                        "player_id": player_to_draft['id'],
                        "clause_amount": 0
                    }
                    
                    success, response = self.run_test(
                        f"Second Team Draft Player",
                        "POST",
                        "draft/pick",
                        200,
                        data=draft_request
                    )
                    
                    if success:
                        print("✅ Second team can also draft successfully")
                        return True
                    else:
                        print("❌ Second team failed to draft")
                        return False
            return True
        else:
            print(f"❌ Turn did not progress correctly (expected 1, got {current_turn})")
            return False

    def test_wrong_team_draft_error(self):
        """Test that wrong team gets 'Not your turn' error"""
        if not self.game_state or not self.game_state.get('draft_order'):
            print("❌ No draft order available")
            return False
        
        # Get current game state
        success, response = self.run_test(
            "Get Current Game State",
            "GET",
            "game/state",
            200
        )
        if not success:
            return False
        
        self.game_state = response
        current_turn = self.game_state.get('current_team_turn', 0)
        draft_order = self.game_state.get('draft_order', [])
        
        if len(draft_order) < 3:
            print("❌ Not enough teams in draft order")
            return False
        
        # Try to draft with a team that's NOT the current turn
        wrong_team_index = (current_turn + 2) % len(draft_order)  # Skip ahead
        wrong_team_id = draft_order[wrong_team_index]
        
        # Find an available player
        available_players = [p for p in self.players if not p.get('team_id')]
        if not available_players:
            print("❌ No available players")
            return False
        
        player_to_draft = available_players[0]
        
        draft_request = {
            "team_id": wrong_team_id,
            "player_id": player_to_draft['id'],
            "clause_amount": 0
        }
        
        # This should fail with 400 status
        success, response = self.run_test(
            f"Wrong Team Tries to Draft (Should Fail)",
            "POST",
            "draft/pick",
            400,  # Expecting error
            data=draft_request
        )
        
        if success:
            print("✅ Wrong team correctly received 'Not your turn' error")
            return True
        else:
            print("❌ Wrong team was allowed to draft (turn validation not working)")
            return False

    def test_player_already_drafted_error(self):
        """Test error when trying to draft already drafted player"""
        if not self.game_state or not self.game_state.get('draft_order'):
            return False
        
        # Get current game state
        success, response = self.run_test(
            "Get Current Game State for Already Drafted Test",
            "GET",
            "game/state",
            200
        )
        if not success:
            return False
        
        self.game_state = response
        current_turn = self.game_state.get('current_team_turn', 0)
        draft_order = self.game_state.get('draft_order', [])
        current_team_id = draft_order[current_turn]
        
        # Get updated players list
        success, response = self.run_test(
            "Get Updated Players List",
            "GET",
            "players",
            200
        )
        if not success:
            return False
        self.players = response
        
        # Find a player that's already drafted
        drafted_players = [p for p in self.players if p.get('team_id')]
        if not drafted_players:
            print("❌ No drafted players found")
            return False
        
        already_drafted_player = drafted_players[0]
        
        draft_request = {
            "team_id": current_team_id,
            "player_id": already_drafted_player['id'],
            "clause_amount": 0
        }
        
        # This should fail with 400 status
        success, response = self.run_test(
            f"Try to Draft Already Drafted Player (Should Fail)",
            "POST",
            "draft/pick",
            400,  # Expecting error
            data=draft_request
        )
        
        if success:
            print("✅ Correctly prevented drafting already drafted player")
            return True
        else:
            print("❌ Allowed drafting already drafted player")
            return False

def main():
    print("🚀 Starting Draft Turn Fix Verification Tests")
    print("=" * 70)
    print("Testing the fix for 'Not your turn' error in draft phase")
    print("=" * 70)
    
    tester = DraftTurnTester()
    
    # Run tests in sequence
    tests = [
        ("Setup Complete Draft Scenario", tester.setup_complete_draft_scenario),
        ("Start Draft Phase", tester.test_draft_start),
        ("Game State After Draft Start", tester.test_game_state_after_draft_start),
        ("First Team Can Draft (KEY TEST)", tester.test_first_team_can_draft),
        ("Turn Progression Works", tester.test_turn_progression),
        ("Wrong Team Gets Error", tester.test_wrong_team_draft_error),
        ("Already Drafted Player Error", tester.test_player_already_drafted_error),
    ]
    
    failed_tests = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*25} {test_name} {'='*25}")
        try:
            result = test_func()
            if not result:
                failed_tests.append(test_name)
                # If setup fails, stop testing
                if test_name == "Setup Complete Draft Scenario":
                    print("❌ Setup failed, stopping tests")
                    break
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {str(e)}")
            failed_tests.append(test_name)
    
    # Print final results
    print(f"\n{'='*70}")
    print(f"📊 DRAFT FIX VERIFICATION RESULTS")
    print(f"{'='*70}")
    print(f"Tests run: {tester.tests_run}")
    print(f"Tests passed: {tester.tests_passed}")
    print(f"Tests failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if failed_tests:
        print(f"\n❌ Failed tests:")
        for test in failed_tests:
            print(f"   - {test}")
        
        # Check if the key test passed
        if "First Team Can Draft (KEY TEST)" in failed_tests:
            print(f"\n🚨 CRITICAL: The main 'Not your turn' fix verification FAILED!")
            print(f"   The first team in draft order still cannot draft players.")
            print(f"   This indicates the backend fix may not be working correctly.")
        else:
            print(f"\n✅ GOOD: The main 'Not your turn' fix verification PASSED!")
            print(f"   The first team can now draft players successfully.")
    else:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"✅ The 'Not your turn' fix is working correctly!")
        print(f"✅ Draft turn progression is working!")
        print(f"✅ Error handling is working properly!")
    
    return 0 if len(failed_tests) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())