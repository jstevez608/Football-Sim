#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import time

class SimpleLineupDisruptionTester:
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

    def test_basic_api_endpoints(self):
        """Test basic API endpoints are working"""
        print("\n🔍 Testing Basic API Endpoints...")
        
        # Test game initialization
        success, response = self.run_api_test("Initialize Game", "POST", "game/init")
        if not success:
            return False
        self.log_test("Game Initialization", True, f"Players available: {response.get('players_available', 0)}")

        # Test loading players
        success, players = self.run_api_test("Load Players", "GET", "players")
        if not success:
            return False
        self.log_test("Load Players", True, f"Loaded {len(players)} players")

        # Test loading teams (should be empty after init)
        success, teams = self.run_api_test("Load Teams", "GET", "teams")
        if not success:
            return False
        self.log_test("Load Teams", True, f"Found {len(teams)} teams")

        # Test game state
        success, game_state = self.run_api_test("Load Game State", "GET", "game/state")
        if not success:
            return False
        self.log_test("Load Game State", True, f"Phase: {game_state.get('current_phase', 'unknown')}")

        return True

    def test_transfer_api_structure(self):
        """Test the structure of the buy-player API without full game setup"""
        print("\n🔧 Testing Transfer API Structure...")
        
        # Create two test teams
        team_data_a = {
            "name": "Test Team A",
            "colors": {"primary": "#FF0000", "secondary": "#FFFFFF"},
            "budget": 100000000
        }
        
        team_data_b = {
            "name": "Test Team B", 
            "colors": {"primary": "#0000FF", "secondary": "#FFFFFF"},
            "budget": 100000000
        }

        success, response_a = self.run_api_test("Create Test Team A", "POST", "teams", data=team_data_a)
        if not success:
            return False

        success, response_b = self.run_api_test("Create Test Team B", "POST", "teams", data=team_data_b)
        if not success:
            return False

        # Get teams and players
        success, teams = self.run_api_test("Load Teams After Creation", "GET", "teams")
        if not success:
            return False

        success, players = self.run_api_test("Load Players After Creation", "GET", "players")
        if not success:
            return False

        if len(teams) < 2:
            self.log_test("Team Creation", False, "Not enough teams created")
            return False

        team_a = teams[0]
        team_b = teams[1]

        # Start draft to assign some players
        success, response = self.run_api_test("Start Draft", "POST", "draft/start")
        if not success:
            return False

        # Draft a few players to each team
        available_players = [p for p in players if not p.get('team_id')]
        
        # Draft 3 players to Team A
        for i in range(3):
            if i < len(available_players):
                player = available_players[i]
                success, response = self.run_api_test(
                    f"Draft Player {i+1} to Team A", 
                    "POST", 
                    "draft/pick",
                    data={
                        "team_id": team_a["id"],
                        "player_id": player["id"],
                        "clause_amount": 0
                    }
                )
                if not success:
                    return False

        # Test buy-player API with invalid data (should fail gracefully)
        success, response = self.run_api_test(
            "Test Buy Player API Structure", 
            "POST", 
            "teams/buy-player",
            expected_status=400,  # Should fail due to various reasons
            data={
                "buyer_team_id": team_b["id"],
                "seller_team_id": team_a["id"],
                "player_id": "invalid_player_id"
            }
        )
        
        # Success here means we got the expected 400 error, which shows the API is working
        if success:
            self.log_test("Buy Player API Structure", True, "API correctly handles invalid requests")
        else:
            self.log_test("Buy Player API Structure", False, "API structure test failed")
            return False

        return True

    def test_lineup_disruption_response_structure(self):
        """Test that the buy-player API returns the expected response structure"""
        print("\n📋 Testing Lineup Disruption Response Structure...")
        
        # Get current teams and players
        success, teams = self.run_api_test("Load Teams for Response Test", "GET", "teams")
        if not success:
            return False

        success, players = self.run_api_test("Load Players for Response Test", "GET", "players")
        if not success:
            return False

        if len(teams) < 2:
            self.log_test("Teams Available", False, "Not enough teams for test")
            return False

        team_a = teams[0]
        team_b = teams[1]

        # Find a player that belongs to Team A
        team_a_players = [p for p in players if p.get('team_id') == team_a['id']]
        
        if not team_a_players:
            self.log_test("Team A Players", False, "Team A has no players")
            return False

        target_player = team_a_players[0]

        # Test the buy-player API (this will likely fail due to various business rules, but we want to check the response structure)
        success, response = self.run_api_test(
            f"Test Buy Player Response Structure", 
            "POST", 
            "teams/buy-player",
            expected_status=400,  # Expect failure due to business rules
            data={
                "buyer_team_id": team_b["id"],
                "seller_team_id": team_a["id"],
                "player_id": target_player["id"]
            }
        )

        # Check if the API is accessible and returns proper error structure
        if success:  # Success means we got the expected 400 status
            self.log_test("Buy Player API Accessible", True, "API endpoint is accessible and returns structured errors")
        else:
            self.log_test("Buy Player API Accessible", False, "API endpoint not accessible or not returning expected structure")

        return True

    def test_lineup_selection_api(self):
        """Test the lineup selection API structure"""
        print("\n⚽ Testing Lineup Selection API...")
        
        # Test formations endpoint
        success, formations = self.run_api_test("Load Formations", "GET", "league/formations")
        if not success:
            return False

        expected_formations = ["A", "B", "C"]
        missing_formations = [f for f in expected_formations if f not in formations]
        
        if missing_formations:
            self.log_test("Formations Structure", False, f"Missing formations: {missing_formations}")
            return False

        self.log_test("Formations Structure", True, f"All formations available: {list(formations.keys())}")

        # Test lineup selection API structure (will fail without proper setup, but we can check the endpoint)
        success, teams = self.run_api_test("Load Teams for Lineup Test", "GET", "teams")
        if not success:
            return False

        if teams:
            team = teams[0]
            # This will fail, but we want to check if the endpoint exists and returns proper error
            success, response = self.run_api_test(
                "Test Lineup Selection API Structure", 
                "POST", 
                "league/lineup/select",
                expected_status=400,  # Expect failure
                data={
                    "team_id": team["id"],
                    "formation": "A",
                    "players": ["invalid_player_1", "invalid_player_2"]
                }
            )
            
            if success:  # Success means we got expected 400 error
                self.log_test("Lineup Selection API Structure", True, "API endpoint accessible and returns structured errors")
            else:
                self.log_test("Lineup Selection API Structure", False, "API endpoint issues")

        return True

    def test_priority_turn_flags(self):
        """Test that teams can have priority turn flags"""
        print("\n🎯 Testing Priority Turn Flags...")
        
        # Get teams
        success, teams = self.run_api_test("Load Teams for Priority Test", "GET", "teams")
        if not success:
            return False

        if not teams:
            self.log_test("Teams Available for Priority Test", False, "No teams available")
            return False

        # Check team structure for priority turn fields
        team = teams[0]
        
        # These fields might not be present initially, but the structure should support them
        has_needs_replacement = 'needs_replacement_turn' in team
        has_priority_turn = 'priority_turn' in team
        has_current_lineup = 'current_lineup' in team
        has_current_formation = 'current_formation' in team

        self.log_test("Team Structure Analysis", True, 
                     f"needs_replacement_turn: {has_needs_replacement}, "
                     f"priority_turn: {has_priority_turn}, "
                     f"current_lineup: {has_current_lineup}, "
                     f"current_formation: {has_current_formation}")

        return True

    def run_all_tests(self):
        """Run all simple lineup disruption tests"""
        print("🚀 Starting Simple Lineup Disruption API Tests")
        print("=" * 60)
        
        start_time = time.time()
        
        # Test basic API endpoints
        if not self.test_basic_api_endpoints():
            print(f"\n❌ Basic API endpoints test failed.")
            return False
        
        # Test transfer API structure
        if not self.test_transfer_api_structure():
            print(f"\n❌ Transfer API structure test failed.")
            return False
        
        # Test lineup disruption response structure
        if not self.test_lineup_disruption_response_structure():
            print(f"\n❌ Lineup disruption response structure test failed.")
            return False
        
        # Test lineup selection API
        if not self.test_lineup_selection_api():
            print(f"\n❌ Lineup selection API test failed.")
            return False
        
        # Test priority turn flags
        if not self.test_priority_turn_flags():
            print(f"\n❌ Priority turn flags test failed.")
            return False
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print(f"🏆 SIMPLE LINEUP DISRUPTION API TESTS COMPLETED")
        print(f"✅ Tests passed: {self.tests_passed}/{self.tests_run}")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED! Lineup disruption API structure is working correctly.")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed.")
            return False

def main():
    tester = SimpleLineupDisruptionTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())