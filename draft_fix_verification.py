import requests
import sys
import json

class DraftFixVerification:
    def __init__(self, base_url="https://soccer-draft-league.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 {name}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ PASS - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                print(f"❌ FAIL - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail.get('detail', 'Unknown error')}")
                except:
                    print(f"   Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ FAIL - Exception: {str(e)}")
            return False, {}

def main():
    print("🎯 DRAFT FIX VERIFICATION - Testing 'Not your turn' Bug Fix")
    print("=" * 65)
    
    tester = DraftFixVerification()
    
    # Step 1: Initialize game
    print("\n📋 STEP 1: Initialize Game")
    success, _ = tester.run_test("Initialize Game", "POST", "game/init", 200)
    if not success:
        print("❌ Cannot proceed without game initialization")
        return 1
    
    # Step 2: Create 8 teams
    print("\n📋 STEP 2: Create 8 Teams")
    team_ids = []
    for i in range(8):
        team_data = {
            "name": f"Team {i+1}",
            "colors": {"primary": "#FF0000", "secondary": "#FFFFFF"},
            "budget": 80000000
        }
        success, response = tester.run_test(f"Create Team {i+1}", "POST", "teams", 200, team_data)
        if success:
            team_ids.append(response.get('team_id'))
        else:
            print(f"❌ Failed to create team {i+1}")
            return 1
    
    print(f"✅ Created {len(team_ids)} teams successfully")
    
    # Step 3: Get players
    print("\n📋 STEP 3: Get Available Players")
    success, players = tester.run_test("Get Players", "GET", "players", 200)
    if not success or not players:
        print("❌ Cannot get players")
        return 1
    print(f"✅ Retrieved {len(players)} players")
    
    # Step 4: Start draft
    print("\n📋 STEP 4: Start Draft Phase")
    success, draft_response = tester.run_test("Start Draft", "POST", "draft/start", 200)
    if not success:
        print("❌ Cannot start draft")
        return 1
    
    draft_order = draft_response.get('draft_order', [])
    print(f"✅ Draft started with order: {draft_order[:2]}... (showing first 2)")
    
    # Step 5: Get game state to verify draft setup
    print("\n📋 STEP 5: Verify Draft State")
    success, game_state = tester.run_test("Get Game State", "GET", "game/state", 200)
    if not success:
        print("❌ Cannot get game state")
        return 1
    
    current_turn = game_state.get('current_team_turn', -1)
    phase = game_state.get('current_phase', '')
    draft_order = game_state.get('draft_order', [])
    
    print(f"   Phase: {phase}")
    print(f"   Current turn: {current_turn}")
    print(f"   Draft order length: {len(draft_order)}")
    
    if phase != 'draft' or current_turn != 0 or len(draft_order) != 8:
        print("❌ Draft state is not correct")
        return 1
    
    # Step 6: THE KEY TEST - First team drafts player (this was failing before)
    print("\n📋 STEP 6: 🎯 KEY TEST - First Team Drafts Player")
    print("This is testing the fix for the 'Not your turn' error")
    
    first_team_id = draft_order[0]
    available_players = [p for p in players if not p.get('team_id')]
    if not available_players:
        print("❌ No available players")
        return 1
    
    player_to_draft = available_players[0]
    
    draft_request = {
        "team_id": first_team_id,
        "player_id": player_to_draft['id'],
        "clause_amount": 0
    }
    
    print(f"   Attempting to draft: {player_to_draft['name']} ({player_to_draft['position']})")
    print(f"   Team ID: {first_team_id}")
    print(f"   Using NEW POST body format (not query params)")
    
    success, draft_result = tester.run_test(
        "🎯 CRITICAL: First Team Draft", 
        "POST", 
        "draft/pick", 
        200, 
        draft_request
    )
    
    if success:
        print(f"🎉 SUCCESS! The 'Not your turn' bug has been FIXED!")
        print(f"   Player {player_to_draft['name']} was successfully drafted")
        print(f"   Next turn: {draft_result.get('next_turn_index', 'unknown')}")
    else:
        print(f"🚨 FAILURE! The 'Not your turn' bug is still present!")
        return 1
    
    # Step 7: Verify turn progression
    print("\n📋 STEP 7: Verify Turn Progression")
    success, updated_state = tester.run_test("Get Updated Game State", "GET", "game/state", 200)
    if success:
        new_turn = updated_state.get('current_team_turn', -1)
        print(f"   Turn progressed from 0 to {new_turn}")
        if new_turn == 1:
            print("✅ Turn progression working correctly")
        else:
            print(f"❌ Turn progression issue (expected 1, got {new_turn})")
    
    # Step 8: Test wrong team gets error
    print("\n📋 STEP 8: Verify Wrong Team Gets Error")
    if len(draft_order) >= 3:
        wrong_team_id = draft_order[2]  # Team that's not current turn
        available_players = [p for p in players if not p.get('team_id')]
        if available_players:
            wrong_draft_request = {
                "team_id": wrong_team_id,
                "player_id": available_players[0]['id'],
                "clause_amount": 0
            }
            
            success, _ = tester.run_test(
                "Wrong Team Draft (Should Fail)", 
                "POST", 
                "draft/pick", 
                400,  # Expecting error
                wrong_draft_request
            )
            
            if success:
                print("✅ Turn validation working - wrong team correctly rejected")
            else:
                print("❌ Turn validation not working - wrong team was allowed to draft")
    
    # Final Results
    print(f"\n{'='*65}")
    print(f"🏆 FINAL RESULTS")
    print(f"{'='*65}")
    print(f"Tests run: {tester.tests_run}")
    print(f"Tests passed: {tester.tests_passed}")
    print(f"Success rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"✅ The 'Not your turn' draft bug has been successfully FIXED!")
        print(f"✅ Draft functionality is working correctly!")
        return 0
    else:
        print(f"\n❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())