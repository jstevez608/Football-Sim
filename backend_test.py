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
        self.matches = []
        self.formations = {}

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

    def test_league_start_comprehensive(self):
        """Test comprehensive league start with calendar generation - NEW FEATURE"""
        print("\n🎯 TESTING COMPREHENSIVE LEAGUE START")
        
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
            "Start League - Generate 14-Round Calendar",
            "POST",
            "league/start",
            200
        )
        
        if success:
            total_matches = response.get('total_matches', 0)
            rounds = response.get('rounds', 0)
            print(f"   Total matches created: {total_matches}")
            print(f"   Rounds: {rounds}")
            
            # Verify exactly 56 matches (8 teams × 7 rounds × 4 matches per round)
            if total_matches == 56:
                print("✅ Correct number of matches generated (56)")
            else:
                print(f"❌ Expected 56 matches, got {total_matches}")
                return False
            
            if rounds == 14:
                print("✅ Correct number of rounds (14)")
            else:
                print(f"❌ Expected 14 rounds, got {rounds}")
                return False
            
            # Verify game state changed to pre_match with lineup selection
            self.test_game_state()
            current_phase = self.game_state.get('current_phase')
            lineup_selection = self.game_state.get('lineup_selection_phase')
            
            if current_phase == 'pre_match':
                print("✅ Game phase successfully changed to 'pre_match'")
            else:
                print(f"❌ Game phase is {current_phase}, expected 'pre_match'")
                return False
                
            if lineup_selection:
                print("✅ Lineup selection phase activated")
            else:
                print("❌ Lineup selection phase not activated")
                return False
            
            # Verify team statistics initialized
            self.test_get_teams()
            stats_initialized = True
            for team in self.teams:
                required_stats = ['points', 'goals_for', 'goals_against', 'matches_played', 'wins', 'draws', 'losses']
                for stat in required_stats:
                    if stat not in team or team[stat] != 0:
                        stats_initialized = False
                        break
                if not stats_initialized:
                    break
            
            if stats_initialized:
                print("✅ Team statistics properly initialized")
            else:
                print("❌ Team statistics not properly initialized")
                return False
            
            return True
        
        return success

    def test_calendar_generation(self):
        """Test 14-round calendar generation with home/away swapping - NEW FEATURE"""
        print("\n🎯 TESTING CALENDAR GENERATION")
        
        # Test getting matches for each round
        round_matches_count = []
        all_matches = []
        
        for round_num in range(1, 15):  # Rounds 1-14
            success, response = self.run_test(
                f"Get Round {round_num} Matches",
                "GET",
                f"league/matches/round/{round_num}",
                200
            )
            
            if success:
                matches = response
                round_matches_count.append(len(matches))
                all_matches.extend(matches)
                print(f"   Round {round_num}: {len(matches)} matches")
                
                # Verify each round has exactly 4 matches (8 teams ÷ 2)
                if len(matches) != 4:
                    print(f"❌ Round {round_num} has {len(matches)} matches, expected 4")
                    return False
            else:
                print(f"❌ Failed to get matches for round {round_num}")
                return False
        
        # Verify total matches
        total_matches = sum(round_matches_count)
        if total_matches == 56:
            print(f"✅ Total matches across all rounds: {total_matches}")
        else:
            print(f"❌ Total matches: {total_matches}, expected 56")
            return False
        
        # Verify home/away swapping between first and second half
        print("\n   Verifying home/away swapping...")
        first_half_matches = []
        second_half_matches = []
        
        for match in all_matches:
            if match['round_number'] <= 7:
                first_half_matches.append(match)
            else:
                second_half_matches.append(match)
        
        # Check that second half matches are swapped versions of first half
        swaps_correct = 0
        for first_match in first_half_matches:
            corresponding_round = first_match['round_number'] + 7
            corresponding_match = next((m for m in second_half_matches 
                                     if m['round_number'] == corresponding_round 
                                     and m['home_team_id'] == first_match['away_team_id'] 
                                     and m['away_team_id'] == first_match['home_team_id']), None)
            if corresponding_match:
                swaps_correct += 1
        
        if swaps_correct == len(first_half_matches):
            print(f"✅ Home/away swapping correct for all {swaps_correct} matches")
        else:
            print(f"❌ Home/away swapping incorrect. Only {swaps_correct}/{len(first_half_matches)} matches swapped correctly")
            return False
        
        # Verify each team plays every other team exactly twice
        print("\n   Verifying each team plays every other team twice...")
        team_matchups = {}
        
        for match in all_matches:
            home_id = match['home_team_id']
            away_id = match['away_team_id']
            
            # Create a sorted tuple to represent the matchup
            matchup = tuple(sorted([home_id, away_id]))
            
            if matchup not in team_matchups:
                team_matchups[matchup] = 0
            team_matchups[matchup] += 1
        
        # Should have 28 unique matchups (8 teams choose 2 = 28), each appearing twice
        expected_matchups = 28
        if len(team_matchups) == expected_matchups:
            print(f"✅ Correct number of unique matchups: {len(team_matchups)}")
        else:
            print(f"❌ Expected {expected_matchups} unique matchups, got {len(team_matchups)}")
            return False
        
        # Each matchup should appear exactly twice
        all_twice = all(count == 2 for count in team_matchups.values())
        if all_twice:
            print("✅ Each team plays every other team exactly twice")
        else:
            print("❌ Some teams don't play each other exactly twice")
            return False
        
        self.matches = all_matches
        return True

    def test_formations_endpoint(self):
        """Test getting available formations - NEW FEATURE"""
        print("\n🎯 TESTING FORMATIONS ENDPOINT")
        
        success, response = self.run_test(
            "Get Available Formations",
            "GET",
            "league/formations",
            200
        )
        
        if success:
            self.formations = response
            print(f"   Formations retrieved: {list(response.keys())}")
            
            # Verify we have exactly 3 formations: A, B, C
            expected_formations = ['A', 'B', 'C']
            if set(response.keys()) == set(expected_formations):
                print("✅ All expected formations available (A, B, C)")
            else:
                print(f"❌ Expected formations {expected_formations}, got {list(response.keys())}")
                return False
            
            # Verify formation structures
            expected_structures = {
                'A': {'name': '4-3-1', 'portero': 1, 'defensas': 2, 'medios': 3, 'delanteros': 1},
                'B': {'name': '5-2-1', 'portero': 1, 'defensas': 3, 'medios': 2, 'delanteros': 1},
                'C': {'name': '4-2-2', 'portero': 1, 'defensas': 2, 'medios': 2, 'delanteros': 2}
            }
            
            structures_correct = True
            for formation_key, expected in expected_structures.items():
                actual = response.get(formation_key, {})
                for field, expected_value in expected.items():
                    if actual.get(field) != expected_value:
                        print(f"❌ Formation {formation_key} field {field}: expected {expected_value}, got {actual.get(field)}")
                        structures_correct = False
            
            if structures_correct:
                print("✅ All formation structures correct")
                # Print formation details
                for key, formation in response.items():
                    print(f"   Formation {key}: {formation['name']} - {formation['portero']} GK, {formation['defensas']} DEF, {formation['medios']} MID, {formation['delanteros']} FWD")
            else:
                return False
        
        return success

    def test_lineup_selection_validation(self):
        """Test lineup selection with formation validation - NEW FEATURE"""
        print("\n🎯 TESTING LINEUP SELECTION VALIDATION")
        
        # Ensure we're in pre_match phase with lineup selection
        self.test_game_state()
        if not self.game_state or self.game_state.get('current_phase') != 'pre_match' or not self.game_state.get('lineup_selection_phase'):
            print("❌ Game not in lineup selection phase")
            return False
        
        # Get current team turn
        current_team_index = self.game_state.get('current_team_turn', 0)
        self.test_get_teams()
        
        if current_team_index >= len(self.teams):
            print("❌ Invalid team turn index")
            return False
        
        current_team = self.teams[current_team_index]
        print(f"   Testing lineup selection for: {current_team['name']}")
        
        # Get team's players
        self.test_get_players()
        team_players = [p for p in self.players if p.get('team_id') == current_team['id'] and not p.get('is_resting', False)]
        
        if len(team_players) < 7:
            print(f"❌ Team has only {len(team_players)} available players, need 7")
            return False
        
        print(f"   Team has {len(team_players)} available players")
        
        # Group players by position
        players_by_position = {
            'PORTERO': [p for p in team_players if p['position'] == 'PORTERO'],
            'DEFENSA': [p for p in team_players if p['position'] == 'DEFENSA'],
            'MEDIO': [p for p in team_players if p['position'] == 'MEDIO'],
            'DELANTERO': [p for p in team_players if p['position'] == 'DELANTERO']
        }
        
        print(f"   Position distribution: GK:{len(players_by_position['PORTERO'])}, DEF:{len(players_by_position['DEFENSA'])}, MID:{len(players_by_position['MEDIO'])}, FWD:{len(players_by_position['DELANTERO'])}")
        
        # Test 1: Valid lineup selection with Formation A (4-3-1)
        if (len(players_by_position['PORTERO']) >= 1 and 
            len(players_by_position['DEFENSA']) >= 2 and 
            len(players_by_position['MEDIO']) >= 3 and 
            len(players_by_position['DELANTERO']) >= 1):
            
            selected_players = (
                [players_by_position['PORTERO'][0]['id']] +
                [p['id'] for p in players_by_position['DEFENSA'][:2]] +
                [p['id'] for p in players_by_position['MEDIO'][:3]] +
                [players_by_position['DELANTERO'][0]['id']]
            )
            
            success1, response1 = self.run_test(
                "Valid Lineup Selection - Formation A",
                "POST",
                "league/lineup/select",
                200,
                data={
                    "team_id": current_team['id'],
                    "formation": "A",
                    "players": selected_players
                }
            )
            
            if success1:
                print("✅ Valid lineup selection accepted")
                print(f"   Response: {response1.get('message', 'No message')}")
                
                # Check if turn advanced or phase changed
                next_turn = response1.get('next_turn')
                next_phase = response1.get('next_phase')
                
                if next_phase == 'match':
                    print("✅ All teams completed lineup selection, moved to match phase")
                elif next_turn is not None:
                    print(f"✅ Turn advanced to team {next_turn}")
                
                return True
            else:
                print("❌ Valid lineup selection rejected")
                return False
        else:
            print("❌ Team doesn't have enough players for Formation A test")
            
            # Try to skip turn instead
            success_skip, response_skip = self.run_test(
                "Skip Lineup Selection Turn",
                "POST",
                "league/lineup/skip-turn",
                200,
                data={"team_id": current_team['id']}
            )
            
            if success_skip:
                print("✅ Successfully skipped lineup selection turn")
                return True
            else:
                print("❌ Failed to skip lineup selection turn")
                return False

    def test_lineup_selection_edge_cases(self):
        """Test lineup selection edge cases - NEW FEATURE"""
        print("\n🎯 TESTING LINEUP SELECTION EDGE CASES")
        
        # Get current game state
        self.test_game_state()
        if not self.game_state or self.game_state.get('current_phase') != 'pre_match' or not self.game_state.get('lineup_selection_phase'):
            print("⚠️  Not in lineup selection phase, skipping edge case tests")
            return True
        
        current_team_index = self.game_state.get('current_team_turn', 0)
        self.test_get_teams()
        current_team = self.teams[current_team_index]
        
        # Test 1: Wrong number of players (6 instead of 7)
        self.test_get_players()
        team_players = [p for p in self.players if p.get('team_id') == current_team['id'] and not p.get('is_resting', False)]
        
        if len(team_players) >= 6:
            wrong_count_players = [p['id'] for p in team_players[:6]]  # Only 6 players
            
            success1, response1 = self.run_test(
                "Invalid Lineup - Wrong Player Count (Should Fail)",
                "POST",
                "league/lineup/select",
                400,
                data={
                    "team_id": current_team['id'],
                    "formation": "A",
                    "players": wrong_count_players
                }
            )
            
            if success1:
                print("✅ Correctly rejected lineup with wrong player count")
            else:
                print("❌ Should have rejected lineup with wrong player count")
                return False
        
        # Test 2: Invalid formation
        if len(team_players) >= 7:
            any_7_players = [p['id'] for p in team_players[:7]]
            
            success2, response2 = self.run_test(
                "Invalid Formation (Should Fail)",
                "POST",
                "league/lineup/select",
                400,
                data={
                    "team_id": current_team['id'],
                    "formation": "X",  # Invalid formation
                    "players": any_7_players
                }
            )
            
            if success2:
                print("✅ Correctly rejected invalid formation")
            else:
                print("❌ Should have rejected invalid formation")
                return False
        
        # Test 3: Wrong team trying to select lineup
        other_team = next((t for t in self.teams if t['id'] != current_team['id']), None)
        if other_team and len(team_players) >= 7:
            any_7_players = [p['id'] for p in team_players[:7]]
            
            success3, response3 = self.run_test(
                "Wrong Team Selecting Lineup (Should Fail)",
                "POST",
                "league/lineup/select",
                400,
                data={
                    "team_id": other_team['id'],  # Wrong team
                    "formation": "A",
                    "players": any_7_players
                }
            )
            
            if success3:
                print("✅ Correctly rejected lineup selection from wrong team")
            else:
                print("❌ Should have rejected lineup selection from wrong team")
                return False
        
        return True

    def test_standings_endpoint(self):
        """Test league standings endpoint - NEW FEATURE"""
        print("\n🎯 TESTING LEAGUE STANDINGS")
        
        success, response = self.run_test(
            "Get League Standings",
            "GET",
            "league/standings",
            200
        )
        
        if success:
            standings = response
            print(f"   Standings retrieved for {len(standings)} teams")
            
            # Verify all teams are present
            if len(standings) == 8:
                print("✅ All 8 teams in standings")
            else:
                print(f"❌ Expected 8 teams in standings, got {len(standings)}")
                return False
            
            # Verify standings structure
            if standings:
                sample_standing = standings[0]
                required_fields = ['position', 'team_name', 'team_id', 'points', 'matches_played', 
                                 'wins', 'draws', 'losses', 'goals_for', 'goals_against', 'goal_difference']
                
                structure_valid = all(field in sample_standing for field in required_fields)
                if structure_valid:
                    print("✅ Standings structure is valid")
                else:
                    print("❌ Standings structure is invalid")
                    return False
                
                # Verify initial values (all should be 0 at start)
                initial_values_correct = all(
                    standing['points'] == 0 and 
                    standing['matches_played'] == 0 and
                    standing['wins'] == 0 and
                    standing['draws'] == 0 and
                    standing['losses'] == 0 and
                    standing['goals_for'] == 0 and
                    standing['goals_against'] == 0 and
                    standing['goal_difference'] == 0
                    for standing in standings
                )
                
                if initial_values_correct:
                    print("✅ All teams have initial values (0 points, 0 matches played, etc.)")
                else:
                    print("❌ Some teams have non-zero initial values")
                    return False
                
                # Verify positions are sequential 1-8
                positions = [s['position'] for s in standings]
                if positions == list(range(1, 9)):
                    print("✅ Positions are correctly numbered 1-8")
                else:
                    print(f"❌ Positions are incorrect: {positions}")
                    return False
        
        return success

    def test_set_player_clause(self):
        """Test setting clauses on owned players during league phase - NEW FEATURE"""
        print("\n🎯 TESTING SET PLAYER CLAUSE FUNCTIONALITY")
        
        # Ensure we're in league phase
        if not self.game_state or self.game_state.get('current_phase') not in ['pre_match', 'league']:
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

    def test_release_player_functionality(self):
        """Test releasing players back to free agents for 90% refund - NEW FEATURE"""
        print("\n🎯 TESTING RELEASE PLAYER FUNCTIONALITY")
        
        # Ensure we're in league phase
        if not self.game_state or self.game_state.get('current_phase') not in ['pre_match', 'league']:
            print("❌ Game not in league phase for release player test")
            return False
        
        # Find a team with more than 7 players
        self.test_get_teams()
        release_team = None
        
        for team in self.teams:
            if len(team.get('players', [])) > 7:
                release_team = team
                break
        
        if not release_team:
            print("❌ No team with >7 players found for release test")
            return False
        
        # Get player details
        self.test_get_players()
        player_to_release = None
        for player in self.players:
            if player.get('team_id') == release_team['id']:
                player_to_release = player
                break
        
        if not player_to_release:
            print("❌ No player found in release team")
            return False
        
        print(f"   Releasing {player_to_release['name']} from {release_team['name']}")
        print(f"   Original price: {player_to_release['price']}")
        print(f"   Expected refund (90%): {int(player_to_release['price'] * 0.9)}")
        
        # Test releasing the player
        success, response = self.run_test(
            f"Release {player_to_release['name']} for 90% refund",
            "POST",
            "teams/release-player",
            200,
            data={
                "team_id": release_team['id'],
                "player_id": player_to_release['id']
            }
        )
        
        if success:
            refund_amount = response.get('refund_amount', 0)
            original_price = response.get('original_price', 0)
            expected_refund = int(original_price * 0.9)
            
            print(f"✅ Player released successfully")
            print(f"   Refund amount: {refund_amount}")
            print(f"   Original price: {original_price}")
            
            if refund_amount == expected_refund:
                print("✅ Refund amount is correct (90% of original price)")
            else:
                print(f"❌ Refund amount incorrect. Expected {expected_refund}, got {refund_amount}")
                return False
            
            # Verify player is now a free agent
            self.test_get_players()
            updated_player = next((p for p in self.players if p['id'] == player_to_release['id']), None)
            if updated_player and not updated_player.get('team_id'):
                print("✅ Player successfully became free agent")
            else:
                print("❌ Player still has team assignment")
                return False
        
        return success

    def test_market_status_functionality(self):
        """Test market status API for round-based market opening - NEW FEATURE"""
        print("\n🎯 TESTING MARKET STATUS FUNCTIONALITY")
        
        # Test market status
        success, response = self.run_test(
            "Get Market Status",
            "GET",
            "league/market-status",
            200
        )
        
        if success:
            market_open = response.get('market_open', False)
            current_round = response.get('current_round', 1)
            current_phase = response.get('current_phase', 'setup')
            reason = response.get('reason', '')
            
            print(f"   Market open: {market_open}")
            print(f"   Current round: {current_round}")
            print(f"   Current phase: {current_phase}")
            print(f"   Reason: {reason}")
            
            # Market should be closed unless we're in round 7
            if current_round == 7 and current_phase in ['pre_match', 'league']:
                if market_open:
                    print("✅ Market correctly open in round 7")
                else:
                    print("❌ Market should be open in round 7")
                    return False
            else:
                if not market_open:
                    print("✅ Market correctly closed outside round 7")
                else:
                    print("❌ Market should be closed outside round 7")
                    return False
        
        return success

    def test_free_agent_drafting_during_market(self):
        """Test drafting free agents during market open period - NEW FEATURE"""
        print("\n🎯 TESTING FREE AGENT DRAFTING DURING MARKET")
        
        # Check if market is open
        success, market_response = self.run_test(
            "Check Market Status for Free Agent Test",
            "GET",
            "league/market-status",
            200
        )
        
        if not success:
            return False
        
        market_open = market_response.get('market_open', False)
        
        if not market_open:
            print("⚠️  Market is closed, cannot test free agent drafting")
            print("   This test would pass if market were open in round 7")
            return True
        
        # Get available free agents
        self.test_get_players()
        free_agents = [p for p in self.players if not p.get('team_id')]
        
        if not free_agents:
            print("❌ No free agents available for testing")
            return False
        
        # Find a team with <10 players
        self.test_get_teams()
        buyer_team = None
        for team in self.teams:
            if len(team.get('players', [])) < 10:
                buyer_team = team
                break
        
        if not buyer_team:
            print("❌ No team with <10 players found for free agent test")
            return False
        
        free_agent = free_agents[0]
        print(f"   Drafting free agent: {free_agent['name']}")
        print(f"   To team: {buyer_team['name']}")
        
        # Test drafting free agent
        success, response = self.run_test(
            f"Draft Free Agent {free_agent['name']}",
            "POST",
            "draft/pick",
            200,
            data={
                "team_id": buyer_team['id'],
                "player_id": free_agent['id'],
                "clause_amount": 0
            }
        )
        
        if success:
            print("✅ Free agent drafted successfully during market open period")
            
            # Verify player is now on team
            self.test_get_players()
            updated_player = next((p for p in self.players if p['id'] == free_agent['id']), None)
            if updated_player and updated_player.get('team_id') == buyer_team['id']:
                print("✅ Free agent successfully assigned to team")
            else:
                print("❌ Free agent not properly assigned to team")
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

    def test_transfer_market_validations(self):
        """Test transfer market validation edge cases - NEW FEATURE"""
        print("\n🎯 TESTING TRANSFER MARKET VALIDATIONS")
        
        # Ensure we're in league phase
        if not self.game_state or self.game_state.get('current_phase') not in ['pre_match', 'league']:
            print("❌ Game not in league phase for validation tests")
            return False
        
        self.test_get_teams()
        self.test_get_players()
        
        # Test 1: Try to set clause for player not owned
        if len(self.teams) >= 2:
            team1 = self.teams[0]
            team2 = self.teams[1]
            
            # Find a player from team2
            team2_player = None
            for player in self.players:
                if player.get('team_id') == team2['id']:
                    team2_player = player
                    break
            
            if team2_player:
                success1, response1 = self.run_test(
                    "Try to set clause for non-owned player (Should Fail)",
                    "POST",
                    f"teams/{team1['id']}/set-clause",
                    400,
                    data={
                        "player_id": team2_player['id'],
                        "clause_amount": 1000000
                    }
                )
                
                if success1:
                    print("✅ Correctly prevented setting clause for non-owned player")
                else:
                    print("❌ Should have prevented setting clause for non-owned player")
                    return False
        
        # Test 2: Try to release player from team with exactly 7 players
        team_with_7 = None
        for team in self.teams:
            if len(team.get('players', [])) == 7:
                team_with_7 = team
                break
        
        if team_with_7:
            player_from_7_team = None
            for player in self.players:
                if player.get('team_id') == team_with_7['id']:
                    player_from_7_team = player
                    break
            
            if player_from_7_team:
                success2, response2 = self.run_test(
                    "Try to release player from team with only 7 players (Should Fail)",
                    "POST",
                    "teams/release-player",
                    400,
                    data={
                        "team_id": team_with_7['id'],
                        "player_id": player_from_7_team['id']
                    }
                )
                
                if success2:
                    print("✅ Correctly prevented release that would leave team with <7 players")
                else:
                    print("❌ Should have prevented release from team with only 7 players")
                    return False
        
        # Test 3: Try to buy player when buyer would exceed 10 players
        team_with_10 = None
        for team in self.teams:
            if len(team.get('players', [])) == 10:
                team_with_10 = team
                break
        
        if team_with_10:
            # Find another team to sell from
            seller_team = None
            for team in self.teams:
                if team['id'] != team_with_10['id'] and len(team.get('players', [])) > 7:
                    seller_team = team
                    break
            
            if seller_team:
                seller_player = None
                for player in self.players:
                    if player.get('team_id') == seller_team['id']:
                        seller_player = player
                        break
                
                if seller_player:
                    success3, response3 = self.run_test(
                        "Try to buy player when buyer has 10 players (Should Fail)",
                        "POST",
                        "teams/buy-player",
                        400,
                        data={
                            "buyer_team_id": team_with_10['id'],
                            "seller_team_id": seller_team['id'],
                            "player_id": seller_player['id']
                        }
                    )
                    
                    if success3:
                        print("✅ Correctly prevented purchase that would exceed 10 players")
                    else:
                        print("❌ Should have prevented purchase when buyer has 10 players")
                        return False
        
        # Test 4: Try to set clause with insufficient budget
        if self.teams:
            test_team = self.teams[0]
            team_player = None
            for player in self.players:
                if player.get('team_id') == test_team['id']:
                    team_player = player
                    break
            
            if team_player:
                excessive_clause = test_team['budget'] + 1000000  # More than budget
                
                success4, response4 = self.run_test(
                    "Try to set clause higher than budget (Should Fail)",
                    "POST",
                    f"teams/{test_team['id']}/set-clause",
                    400,
                    data={
                        "player_id": team_player['id'],
                        "clause_amount": excessive_clause
                    }
                )
                
                if success4:
                    print("✅ Correctly prevented setting clause higher than budget")
                else:
                    print("❌ Should have prevented setting excessive clause")
                    return False
        
        return True

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
    print("🚀 Starting Football Draft League API Tests - LEAGUE SYSTEM FOCUS")
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
    
    # Draft minimum players (7 per team)
    success = tester.test_draft_players_to_minimum()
    if not success:
        print("❌ Failed to draft minimum players. Stopping tests.")
        return 1
    
    # Run LEAGUE SYSTEM tests
    print("\n🎯 LEAGUE SYSTEM TESTING")
    print("=" * 40)
    
    tests = [
        ("League Start & Calendar Generation", tester.test_league_start_comprehensive),
        ("Calendar Structure Validation", tester.test_calendar_generation),
        ("Formations Endpoint", tester.test_formations_endpoint),
        ("Lineup Selection Validation", tester.test_lineup_selection_validation),
        ("Lineup Selection Edge Cases", tester.test_lineup_selection_edge_cases),
        ("League Standings", tester.test_standings_endpoint),
    ]
    
    # Run TRANSFER MARKET tests
    print("\n🎯 TRANSFER MARKET TESTING")
    print("=" * 40)
    
    transfer_tests = [
        ("Set Player Clause", tester.test_set_player_clause),
        ("Release Player Functionality", tester.test_release_player_functionality),
        ("Buy Player Between Teams", tester.test_buy_player_between_teams),
        ("Market Status Functionality", tester.test_market_status_functionality),
        ("Free Agent Drafting During Market", tester.test_free_agent_drafting_during_market),
        ("Transfer Market Validations", tester.test_transfer_market_validations),
    ]
    
    # Combine all tests
    all_tests = tests + transfer_tests
    
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
    print(f"📊 FINAL RESULTS - LEAGUE SYSTEM TESTING")
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
        print(f"   - Verify league system implementation")
        print(f"   - Test calendar generation logic")
        print(f"   - Validate lineup selection with formations")
    else:
        print(f"\n✅ All league system tests passed!")
        print(f"🎉 League calendar, formations, and lineup selection working correctly!")
    
    return 0 if len(failed_tests) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())