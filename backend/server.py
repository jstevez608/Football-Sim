from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import random
from fastapi.staticfiles import StaticFiles

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

app.mount("/", StaticFiles(directory="../frontend/dist", html=True), name="static")

# Pydantic Models
class PlayerStats(BaseModel):
    pase: int = Field(..., ge=1, le=6)
    area: int = Field(..., ge=1, le=6)
    tiro: int = Field(..., ge=1, le=6)
    remate: int = Field(..., ge=1, le=6)
    corner: int = Field(..., ge=1, le=6)
    penalti: int = Field(..., ge=1, le=6)
    regate: int = Field(..., ge=1, le=6)
    parada: int = Field(..., ge=1, le=6)
    despeje: int = Field(..., ge=1, le=6)
    robo: int = Field(..., ge=1, le=6)
    bloqueo: int = Field(..., ge=1, le=6)
    atajada: int = Field(..., ge=1, le=6)

class Player(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    position: str  # PORTERO, DEFENSA, MEDIO, DELANTERO
    price: int
    resistance: int = Field(..., ge=4, le=14)
    stats: PlayerStats
    team_id: Optional[str] = None
    jersey_number: Optional[int] = None
    clause_amount: int = 0
    is_resting: bool = False
    games_played: int = 0

class Team(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    colors: Dict[str, str]  # {"primary": "#FF0000", "secondary": "#FFFFFF"}
    budget: int = Field(..., ge=40000000, le=180000000)
    players: List[str] = []  # Player IDs

class GameState(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    teams: List[str] = []  # Team IDs
    current_phase: str = "setup"  # setup, draft, league, finished
    current_round: int = 1
    current_team_turn: int = 0
    market_open: bool = False
    draft_order: List[str] = []

class Match(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    home_team_id: str
    away_team_id: str
    round_number: int
    home_score: int = 0
    away_score: int = 0
    home_lineup: List[str] = []  # Player IDs
    away_lineup: List[str] = []  # Player IDs
    match_log: List[Dict] = []
    played: bool = False

# Initial player data generation
def generate_initial_players():
    positions_data = {
        "PORTERO": {
            "count": 8,
            "base_stats": {"parada": 5, "atajada": 5, "despeje": 3, "pase": 2, "tiro": 1, "area": 1, "remate": 1, "corner": 2, "penalti": 4, "regate": 1, "robo": 2, "bloqueo": 3}
        },
        "DEFENSA": {
            "count": 33,
            "base_stats": {"despeje": 5, "robo": 4, "bloqueo": 4, "pase": 3, "tiro": 2, "area": 2, "remate": 2, "corner": 2, "penalti": 2, "regate": 2, "parada": 1, "atajada": 1}
        },
        "MEDIO": {
            "count": 18,
            "base_stats": {"pase": 5, "corner": 4, "regate": 4, "tiro": 3, "area": 3, "remate": 3, "penalti": 3, "despeje": 3, "robo": 3, "bloqueo": 3, "parada": 1, "atajada": 1}
        },
        "DELANTERO": {
            "count": 16,
            "base_stats": {"remate": 5, "tiro": 5, "penalti": 4, "regate": 4, "area": 4, "pase": 3, "corner": 2, "despeje": 2, "robo": 2, "bloqueo": 2, "parada": 1, "atajada": 1}
        }
    }
    
    player_names = [
        "García", "Rodríguez", "López", "Martínez", "González", "Pérez", "Sánchez", "Ramírez", "Cruz", "Flores",
        "Morales", "Jiménez", "Hernández", "Vargas", "Castro", "Ruiz", "Ortega", "Silva", "Torres", "Mendoza",
        "Gutiérrez", "Vásquez", "Romero", "Álvarez", "Medina", "Guerrero", "Reyes", "Moreno", "Contreras", "Luna",
        "Ríos", "Aguilar", "Domínguez", "Herrera", "Campos", "Vega", "Ramos", "Muñoz", "Delgado", "Rojas",
        "Espinoza", "Castillo", "Salazar", "Navarro", "Paredes", "Sandoval", "Cabrera", "Ibarra", "Figueroa", "Soto",
        "Bravo", "Cortés", "Fuentes", "Peña", "Valdez", "Miranda", "Carrillo", "Maldonado", "Valencia", "Estrada",
        "Villanueva", "Pacheco", "Cáceres", "Quintero", "Molina", "Franco", "Núñez", "Bermúdez", "León", "Bustamante",
        "Ochoa", "Vidal", "Serrano", "Morales", "Pereira"
    ]
    
    players = []
    name_index = 0
    
    for position, data in positions_data.items():
        for _ in range(data["count"]):
            # Generate varied stats based on position
            stats = {}
            for stat, base_value in data["base_stats"].items():
                variation = random.randint(-1, 1)
                stats[stat] = max(1, min(6, base_value + variation))
            
            # Generate price based on overall quality
            avg_stats = sum(stats.values()) / len(stats)
            base_price = int(avg_stats * 1500000)  # Base price calculation
            price_variation = random.randint(-500000, 1000000)
            price = max(500000, base_price + price_variation)
            
            resistance = random.randint(4, 14)
            
            player = Player(
                name=player_names[name_index % len(player_names)],
                position=position,
                price=price,
                resistance=resistance,
                stats=PlayerStats(**stats)
            )
            players.append(player)
            name_index += 1
    
    return players

# Match simulation logic
class MatchSimulator:
    ACTION_PROBABILITIES = {
        "PASE": 0.35,
        "REGATE": 0.20,
        "TIRO": 0.20,
        "CORNER": 0.15,
        "AREA": 0.10
    }
    
    POSITION_ATTACK_PROB = {
        "DELANTERO": 0.40,
        "MEDIO": 0.40,
        "DEFENSA": 0.20,
        "PORTERO": 0.00
    }
    
    POSITION_DEFENSE_PROB = {
        "DELANTERO": 0.20,
        "MEDIO": 0.30,
        "DEFENSA": 0.50,
        "PORTERO": 0.00  # Except for specific actions
    }
    
    DEFENSE_ACTIONS = {
        "PASE": "BLOQUEO",
        "REGATE": "ROBO", 
        "CORNER": "DESPEJE",
        "AREA": "BLOQUEO",
        "TIRO": "PARADA",
        "REMATE": "PARADA",
        "PENALTI": "ATAJADA"
    }
    
    @staticmethod
    def choose_action():
        """Choose random action based on probabilities"""
        rand = random.random()
        cumulative = 0
        for action, prob in MatchSimulator.ACTION_PROBABILITIES.items():
            cumulative += prob
            if rand <= cumulative:
                return action
        return "PASE"
    
    @staticmethod
    def choose_player_by_position(players, attack_mode=True):
        """Choose player based on position probabilities"""
        if attack_mode:
            probabilities = MatchSimulator.POSITION_ATTACK_PROB
        else:
            probabilities = MatchSimulator.POSITION_DEFENSE_PROB
        
        # Filter available players
        available_players = []
        weights = []
        
        for player in players:
            prob = probabilities.get(player["position"], 0)
            if prob > 0:
                available_players.append(player)
                weights.append(prob)
        
        if not available_players:
            return random.choice(players)
        
        # Weighted random selection
        total_weight = sum(weights)
        rand = random.random() * total_weight
        cumulative = 0
        
        for i, weight in enumerate(weights):
            cumulative += weight
            if rand <= cumulative:
                return available_players[i]
        
        return available_players[-1]
    
    @staticmethod
    def choose_defender(players, action):
        """Choose defender based on action type"""
        if action in ["TIRO", "REMATE", "PENALTI"]:
            # Only goalkeeper can defend these
            goalkeepers = [p for p in players if p["position"] == "PORTERO"]
            return goalkeepers[0] if goalkeepers else random.choice(players)
        else:
            # Use defense probabilities for other actions
            return MatchSimulator.choose_player_by_position(players, attack_mode=False)
    
    @staticmethod
    def get_defense_action(attack_action):
        """Get corresponding defense action"""
        return MatchSimulator.DEFENSE_ACTIONS.get(attack_action, "ROBO")
    
    @staticmethod
    def calculate_action_result(attacker, attack_action, defender, defense_action):
        """Calculate if attack succeeds based on player stats + random factor"""
        # Get attacker's stat for the action (using dict access)
        attack_stat = attacker["stats"][attack_action.lower()]
        # Get defender's stat for the defense action (using dict access)
        defense_stat = defender["stats"][defense_action.lower()]
        
        # Add random factor (1-3)
        attacker_total = attack_stat + random.randint(1, 3)
        defender_total = defense_stat + random.randint(1, 3)
        
        return attacker_total > defender_total
    
    @staticmethod
    def get_follow_up_actions(action):
        """Get possible follow-up actions if attack succeeds"""
        follow_ups = {
            "PASE": ["REGATE", "TIRO", "CORNER", "AREA"],
            "REGATE": ["TIRO", "PASE", "AREA"],
            "CORNER": ["REMATE"],
            "AREA": ["PENALTI"]
        }
        return follow_ups.get(action, [])
    
    @staticmethod
    def is_goal_action(action):
        """Check if action results in goal when successful"""
        return action in ["TIRO", "REMATE", "PENALTI"]
    
    @staticmethod
    def simulate_turn(attacking_team, defending_team, attacking_players, defending_players, turn_number):
        """Simulate a single turn of the match"""
        turn_log = {
            "turn": turn_number,
            "attacking_team": attacking_team["name"],
            "defending_team": defending_team["name"],
            "actions": [],
            "goal_scored": False,
            "final_action": None
        }
        
        current_attacker = None
        actions_in_turn = 0
        max_actions = 10  # Prevent infinite loops
        
        while actions_in_turn < max_actions:
            actions_in_turn += 1
            
            # Choose initial action or follow-up action
            if current_attacker is None:
                # First action of turn
                action = MatchSimulator.choose_action()
                current_attacker = MatchSimulator.choose_player_by_position(attacking_players, attack_mode=True)
            else:
                # Follow-up action from previous success
                possible_actions = MatchSimulator.get_follow_up_actions(turn_log["actions"][-1]["action"])
                if not possible_actions:
                    break
                action = random.choice(possible_actions)
                
                # For follow-up actions, same player continues or different player
                if turn_log["actions"][-1]["action"] in ["REGATE", "AREA"]:
                    # Same player continues
                    pass
                else:
                    # Different player for PASE, CORNER
                    current_attacker = MatchSimulator.choose_player_by_position(attacking_players, attack_mode=True)
            
            # Choose defender
            defender = MatchSimulator.choose_defender(defending_players, action)
            defense_action = MatchSimulator.get_defense_action(action)
            
            # Calculate result
            attack_successful = MatchSimulator.calculate_action_result(
                current_attacker, action, defender, defense_action
            )
            
            # Create action log
            action_log = {
                "action": action,
                "attacker": {
                    "name": current_attacker["name"],
                    "position": current_attacker["position"],
                    "stat_value": current_attacker["stats"][action.lower()],
                    "random_bonus": random.randint(1, 3)
                },
                "defender": {
                    "name": defender["name"],
                    "position": defender["position"],
                    "defense_action": defense_action,
                    "stat_value": defender["stats"][defense_action.lower()],
                    "random_bonus": random.randint(1, 3)
                },
                "successful": attack_successful,
                "is_goal": False
            }
            
            # Recalculate for logging (since we used random twice)
            action_log["attacker"]["total"] = action_log["attacker"]["stat_value"] + action_log["attacker"]["random_bonus"]
            action_log["defender"]["total"] = action_log["defender"]["stat_value"] + action_log["defender"]["random_bonus"]
            
            turn_log["actions"].append(action_log)
            
            if attack_successful:
                # Check if it's a goal action
                if MatchSimulator.is_goal_action(action):
                    turn_log["goal_scored"] = True
                    action_log["is_goal"] = True
                    turn_log["final_action"] = action
                    break
                else:
                    # Continue with follow-up action
                    continue
            else:
                # Defense succeeded, turn ends
                turn_log["final_action"] = f"{defense_action}_SUCCESS"
                break
        
        return turn_log
    
    @staticmethod
    def simulate_match(home_team, away_team, home_lineup_ids, away_lineup_ids, players_data):
        """Simulate complete match with 9 turns per team"""
        # Get player objects for lineups
        home_players = [p for p in players_data if p["id"] in home_lineup_ids]
        away_players = [p for p in players_data if p["id"] in away_lineup_ids]
        
        if len(home_players) != 7 or len(away_players) != 7:
            raise ValueError("Each team must have exactly 7 players in lineup")
        
        match_log = {
            "home_team": home_team["name"],
            "away_team": away_team["name"],
            "home_score": 0,
            "away_score": 0,
            "turns": [],
            "total_turns": 18
        }
        
        # Simulate 18 turns (9 per team, alternating)
        for turn_num in range(1, 19):
            if turn_num % 2 == 1:  # Odd turns: home team attacks
                attacking_team = home_team
                defending_team = away_team
                attacking_players = home_players
                defending_players = away_players
            else:  # Even turns: away team attacks
                attacking_team = away_team
                defending_team = home_team
                attacking_players = away_players
                defending_players = home_players
            
            turn_result = MatchSimulator.simulate_turn(
                attacking_team, defending_team, 
                attacking_players, defending_players, 
                turn_num
            )
            
            # Update score if goal was scored
            if turn_result["goal_scored"]:
                if turn_num % 2 == 1:  # Home team scored
                    match_log["home_score"] += 1
                else:  # Away team scored
                    match_log["away_score"] += 1
            
            match_log["turns"].append(turn_result)
        
        return match_log

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Football Draft League API"}

@api_router.post("/game/init")
async def initialize_game():
    """Initialize a new game, reset teams but keep customized players"""
    # Clear existing game state and teams (but keep players with user modifications)
    await db.game_state.delete_many({})
    await db.teams.delete_many({})
    await db.matches.delete_many({})
    
    # For this update, we need to regenerate players to include ATAJADA stat
    # Check if players have the new ATAJADA field
    sample_player = await db.players.find_one()
    needs_regeneration = False
    
    if sample_player and 'stats' in sample_player:
        if 'atajada' not in sample_player['stats']:
            needs_regeneration = True
    
    players_created = 0
    
    if not sample_player or needs_regeneration:
        # Regenerate players if none exist or they don't have ATAJADA stat
        await db.players.delete_many({})
        players = generate_initial_players()
        
        # Insert players into database
        for player in players:
            await db.players.insert_one(player.dict())
        players_created = len(players)
    else:
        # Reset player team assignments but keep their custom stats/names/prices
        await db.players.update_many(
            {},
            {"$unset": {"team_id": "", "jersey_number": ""}, 
             "$set": {"clause_amount": 0, "is_resting": False, "games_played": 0}}
        )
        players_created = await db.players.count_documents({})
    
    # Create initial game state
    game_state = GameState(
        current_phase="setup"
    )
    await db.game_state.insert_one(game_state.dict())
    
    return {"message": "Game reset successfully", "players_available": players_created}

@api_router.get("/players", response_model=List[Player])
async def get_players():
    """Get all players"""
    players = await db.players.find().to_list(length=None)
    return [Player(**player) for player in players]

@api_router.put("/players/{player_id}")
async def update_player(player_id: str, player_data: dict):
    """Update player information"""
    await db.players.update_one(
        {"id": player_id}, 
        {"$set": player_data}
    )
    return {"message": "Player updated"}

@api_router.post("/teams")
async def create_team(team_data: dict):
    """Create a new team"""
    try:
        team = Team(**team_data)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    
    await db.teams.insert_one(team.dict())
    
    # Update game state with new team
    game_state = await db.game_state.find_one()
    if game_state:
        teams_list = game_state.get("teams", [])
        teams_list.append(team.id)
        await db.game_state.update_one(
            {"id": game_state["id"]},
            {"$set": {"teams": teams_list}}
        )
    
    return {"team_id": team.id}

@api_router.get("/teams", response_model=List[Team])
async def get_teams():
    """Get all teams"""
    teams = await db.teams.find().to_list(length=None)
    return [Team(**team) for team in teams]

@api_router.get("/game/state")
async def get_game_state():
    """Get current game state"""
    game_state = await db.game_state.find_one()
    if not game_state:
        return {"error": "No game initialized"}
    # Convert ObjectId to string for JSON serialization
    if "_id" in game_state:
        game_state["_id"] = str(game_state["_id"])
    
    # Add debug information
    print(f"DEBUG: Game state - Phase: {game_state.get('current_phase')}")
    print(f"DEBUG: Current team turn: {game_state.get('current_team_turn')}")
    print(f"DEBUG: Draft order: {game_state.get('draft_order', [])}")
    
    return game_state

@api_router.post("/draft/start")
async def start_draft():
    """Start the draft phase"""
    game_state = await db.game_state.find_one()
    if not game_state:
        raise HTTPException(status_code=404, detail="No game found")
    
    # Use cyclic order (sequential) instead of random
    teams = game_state.get("teams", [])
    # Keep teams in their original creation order for cyclic turns
    
    await db.game_state.update_one(
        {"id": game_state["id"]},
        {"$set": {
            "current_phase": "draft",
            "draft_order": teams,  # Sequential order, not shuffled
            "current_team_turn": 0
        }}
    )
    
    return {"message": "Draft started", "draft_order": teams}

class DraftPickRequest(BaseModel):
    team_id: str
    player_id: str
    clause_amount: int = 0

class Formation(BaseModel):
    name: str
    portero: int = 1
    defensas: int
    medios: int 
    delanteros: int

class LineupSelection(BaseModel):
    team_id: str
    formation: str  # "A", "B", or "C"
    players: List[str]  # 7 player IDs

class DraftSkipRequest(BaseModel):
    team_id: str

class SetClauseRequest(BaseModel):
    player_id: str
    clause_amount: int = Field(..., ge=0)

class BuyPlayerRequest(BaseModel):
    buyer_team_id: str
    seller_team_id: str
    player_id: str

class MatchResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    home_team_id: str
    away_team_id: str
    round_number: int
    home_score: int = 0
    away_score: int = 0
    home_lineup: List[str] = []  # Player IDs
    away_lineup: List[str] = []  # Player IDs
    played: bool = False

@api_router.post("/draft/pick")
async def draft_player(request: DraftPickRequest):
    """Draft a player for a team"""
    team_id = request.team_id
    player_id = request.player_id
    clause_amount = request.clause_amount
    
    # Check if it's the team's turn
    game_state = await db.game_state.find_one()
    if not game_state or game_state["current_phase"] != "draft":
        raise HTTPException(status_code=400, detail="Not in draft phase")
    
    # Debug information
    current_team_index = game_state.get("current_team_turn", 0)
    draft_order = game_state.get("draft_order", [])
    
    if current_team_index >= len(draft_order):
        raise HTTPException(status_code=400, detail="Invalid turn index")
    
    current_team = draft_order[current_team_index]
    
    # Debug: log the comparison
    print(f"DEBUG: Current team ID: {current_team}, Requested team ID: {team_id}")
    print(f"DEBUG: Turn index: {current_team_index}, Draft order: {draft_order}")
    
    if current_team != team_id:
        raise HTTPException(status_code=400, detail=f"Not your turn. Current turn: team index {current_team_index}")
    
    # Check team budget and player availability
    team = await db.teams.find_one({"id": team_id})
    player = await db.players.find_one({"id": player_id})
    
    if not team or not player:
        raise HTTPException(status_code=404, detail="Team or player not found")
    
    if player.get("team_id"):
        raise HTTPException(status_code=400, detail="Player already drafted")
    
    current_player_count = len(team.get("players", []))
    print(f"DEBUG: Team {team.get('name')} has {current_player_count} players")
    
    if current_player_count >= 10:
        raise HTTPException(status_code=400, detail=f"Team is full (has {current_player_count}/10 players)")
    
    total_cost = player["price"] + clause_amount
    if team["budget"] < total_cost:
        raise HTTPException(status_code=400, detail="Insufficient budget")
    
    # Update player and team
    await db.players.update_one(
        {"id": player_id},
        {"$set": {"team_id": team_id, "clause_amount": clause_amount}}
    )
    
    team_players = team.get("players", [])
    team_players.append(player_id)
    
    await db.teams.update_one(
        {"id": team_id},
        {"$set": {
            "players": team_players,
            "budget": team["budget"] - total_cost
        }}
    )
    
    # Move to next team's turn
    next_turn = (current_team_index + 1) % len(draft_order)
    await db.game_state.update_one(
        {"id": game_state["id"]},
        {"$set": {"current_team_turn": next_turn}}
    )
    
    return {"message": "Player drafted successfully", "next_turn_index": next_turn}

@api_router.post("/draft/skip-turn")
async def skip_draft_turn(request: DraftSkipRequest):
    """Skip current team's draft turn"""
    team_id = request.team_id
    
    # Check if it's the team's turn
    game_state = await db.game_state.find_one()
    if not game_state or game_state["current_phase"] != "draft":
        raise HTTPException(status_code=400, detail="Not in draft phase")
    
    current_team_index = game_state.get("current_team_turn", 0)
    draft_order = game_state.get("draft_order", [])
    
    if current_team_index >= len(draft_order):
        raise HTTPException(status_code=400, detail="Invalid turn index")
    
    current_team = draft_order[current_team_index]
    
    if current_team != team_id:
        raise HTTPException(status_code=400, detail="Not your turn")
    
    # Move to next team's turn
    next_turn = (current_team_index + 1) % len(draft_order)
    await db.game_state.update_one(
        {"id": game_state["id"]},
        {"$set": {"current_team_turn": next_turn}}
    )
    
    return {"message": "Turn skipped successfully", "next_turn_index": next_turn}

def generate_league_calendar(team_ids):
    """Generate full league calendar with all teams playing each other twice"""
    if len(team_ids) != 8:
        raise ValueError("Need exactly 8 teams for league calendar")
    
    matches = []
    match_id_counter = 1
    
    # First round (rounds 1-7): each team plays every other team once
    for round_num in range(1, 8):
        round_matches = []
        teams_in_round = team_ids.copy()
        
        # Generate 4 matches per round (8 teams = 4 matches)
        while len(teams_in_round) >= 2:
            home_team = teams_in_round.pop(0)
            away_team = teams_in_round.pop()
            
            match = {
                "id": str(uuid.uuid4()),
                "home_team_id": home_team,
                "away_team_id": away_team,
                "round_number": round_num,
                "home_score": 0,
                "away_score": 0,
                "home_lineup": [],
                "away_lineup": [],
                "played": False
            }
            round_matches.append(match)
        
        matches.extend(round_matches)
        # Rotate teams for next round
        team_ids = [team_ids[0]] + [team_ids[-1]] + team_ids[1:-1]
    
    # Second round (rounds 8-14): repeat with home/away swapped
    first_round_matches = matches.copy()
    for match in first_round_matches:
        second_match = {
            "id": str(uuid.uuid4()),
            "home_team_id": match["away_team_id"],  # Swap home/away
            "away_team_id": match["home_team_id"],
            "round_number": match["round_number"] + 7,  # Add 7 rounds
            "home_score": 0,
            "away_score": 0,
            "home_lineup": [],
            "away_lineup": [],
            "played": False
        }
        matches.append(second_match)
    
    return matches

@api_router.post("/league/start")
async def start_league():
    """Start the league phase - requires minimum 7 players per team"""
    # Check if all teams have at least 7 players
    teams = await db.teams.find().to_list(length=None)
    if len(teams) != 8:
        raise HTTPException(status_code=400, detail="Need exactly 8 teams to start league")
    
    for team in teams:
        player_count = len(team.get("players", []))
        if player_count < 7:
            raise HTTPException(
                status_code=400, 
                detail=f"Team '{team['name']}' needs at least 7 players (has {player_count})"
            )
    
    # Update game state
    await db.game_state.update_one(
        {},
        {"$set": {
            "current_phase": "pre_match", 
            "current_round": 1,
            "current_team_turn": 0,
            "lineup_selection_phase": True
        }}
    )
    
    # Generate full league calendar (14 rounds)
    team_ids = [team["id"] for team in teams]
    matches = generate_league_calendar(team_ids)
    
    # Clear existing matches and insert new calendar
    await db.matches.delete_many({})
    await db.matches.insert_many(matches)
    
    # Initialize team statistics
    for team in teams:
        await db.teams.update_one(
            {"id": team["id"]},
            {"$set": {
                "points": 0,
                "goals_for": 0,
                "goals_against": 0,
                "matches_played": 0,
                "wins": 0,
                "draws": 0,
                "losses": 0,
                "current_lineup": [],
                "current_formation": ""
            }}
        )
    
    # Reset player match counts
    await db.players.update_many(
        {},
        {"$set": {"games_played": 0, "is_resting": False}}
    )
    
    return {"message": "League started", "total_matches": len(matches), "rounds": 14}

@api_router.get("/league/formations")
async def get_available_formations():
    """Get available team formations"""
    formations = {
        "A": {"name": "4-3-1", "portero": 1, "defensas": 2, "medios": 3, "delanteros": 1},
        "B": {"name": "5-2-1", "portero": 1, "defensas": 3, "medios": 2, "delanteros": 1},
        "C": {"name": "4-2-2", "portero": 1, "defensas": 2, "medios": 2, "delanteros": 2}
    }
    return formations

@api_router.get("/league/matches/round/{round_number}")
async def get_round_matches(round_number: int):
    """Get matches for a specific round"""
    matches = await db.matches.find({"round_number": round_number}).to_list(length=None)
    # Convert ObjectId to string for JSON serialization
    for match in matches:
        if "_id" in match:
            match["_id"] = str(match["_id"])
    return matches

@api_router.get("/league/standings")
async def get_league_standings():
    """Get current league standings sorted by points, goal difference, goals scored"""
    teams = await db.teams.find().to_list(length=None)
    
    # Sort by: 1. Points (desc), 2. Goal difference (desc), 3. Goals scored (desc)
    def sorting_key(team):
        points = team.get("points", 0)
        goals_for = team.get("goals_for", 0)
        goals_against = team.get("goals_against", 0)
        goal_difference = goals_for - goals_against
        return (-points, -goal_difference, -goals_for)
    
    teams.sort(key=sorting_key)
    
    standings = []
    for i, team in enumerate(teams):
        standing = {
            "position": i + 1,
            "team_name": team["name"],
            "team_id": team["id"],
            "points": team.get("points", 0),
            "matches_played": team.get("matches_played", 0),
            "wins": team.get("wins", 0),
            "draws": team.get("draws", 0),
            "losses": team.get("losses", 0),
            "goals_for": team.get("goals_for", 0),
            "goals_against": team.get("goals_against", 0),
            "goal_difference": team.get("goals_for", 0) - team.get("goals_against", 0)
        }
        standings.append(standing)
    
    return standings

@api_router.post("/league/lineup/select")
async def select_team_lineup(lineup: LineupSelection):
    """Select team lineup and formation for current round"""
    game_state = await db.game_state.find_one()
    if not game_state or game_state.get("current_phase") != "pre_match":
        raise HTTPException(status_code=400, detail="Not in pre-match phase")
    
    if not game_state.get("lineup_selection_phase"):
        raise HTTPException(status_code=400, detail="Not in lineup selection phase")
    
    # Check if it's this team's turn
    teams = await db.teams.find().to_list(length=None)
    current_team_index = game_state.get("current_team_turn", 0)
    
    if current_team_index >= len(teams):
        raise HTTPException(status_code=400, detail="Invalid team turn")
    
    current_team = teams[current_team_index]
    if current_team["id"] != lineup.team_id:
        raise HTTPException(status_code=400, detail="Not your turn to select lineup")
    
    # Validate formation
    formations = {
        "A": {"portero": 1, "defensas": 2, "medios": 3, "delanteros": 1},
        "B": {"portero": 1, "defensas": 3, "medios": 2, "delanteros": 1},
        "C": {"portero": 1, "defensas": 2, "medios": 2, "delanteros": 2}
    }
    
    if lineup.formation not in formations:
        raise HTTPException(status_code=400, detail="Invalid formation")
    
    formation = formations[lineup.formation]
    
    # Validate lineup length
    if len(lineup.players) != 7:
        raise HTTPException(status_code=400, detail="Must select exactly 7 players")
    
    # Get selected players and validate they belong to the team
    selected_players = await db.players.find({"id": {"$in": lineup.players}}).to_list(length=None)
    
    if len(selected_players) != 7:
        raise HTTPException(status_code=400, detail="Some selected players not found")
    
    # Check all players belong to the team
    for player in selected_players:
        if player.get("team_id") != lineup.team_id:
            raise HTTPException(status_code=400, detail=f"Player {player['name']} doesn't belong to your team")
    
    # Check players are available (not resting due to resistance)
    for player in selected_players:
        if player.get("is_resting", False):
            raise HTTPException(status_code=400, detail=f"Player {player['name']} is resting and cannot play")
    
    # Validate formation requirements
    position_counts = {"PORTERO": 0, "DEFENSA": 0, "MEDIO": 0, "DELANTERO": 0}
    for player in selected_players:
        position_counts[player["position"]] += 1
    
    if (position_counts["PORTERO"] != formation["portero"] or
        position_counts["DEFENSA"] != formation["defensas"] or
        position_counts["MEDIO"] != formation["medios"] or
        position_counts["DELANTERO"] != formation["delanteros"]):
        raise HTTPException(
            status_code=400, 
            detail=f"Formation {lineup.formation} requires {formation['portero']} GK, {formation['defensas']} DEF, {formation['medios']} MID, {formation['delanteros']} FWD"
        )
    
    # Update team with selected lineup
    await db.teams.update_one(
        {"id": lineup.team_id},
        {"$set": {
            "current_lineup": lineup.players,
            "current_formation": lineup.formation
        }}
    )
    
    # Move to next team's turn
    next_turn = (current_team_index + 1) % len(teams)
    
    # If all teams have selected their lineups, move to match phase
    if next_turn == 0:
        # Check if all teams have selected lineups
        teams_with_lineups = await db.teams.count_documents({"current_lineup": {"$ne": []}})
        if teams_with_lineups == len(teams):
            await db.game_state.update_one(
                {"id": game_state["id"]},
                {"$set": {
                    "lineup_selection_phase": False,
                    "current_phase": "match",
                    "current_team_turn": 0
                }}
            )
            return {"message": "Lineup selected. All teams ready - proceeding to matches!", "next_phase": "match"}
    
    await db.game_state.update_one(
        {"id": game_state["id"]},
        {"$set": {"current_team_turn": next_turn}}
    )
    
    return {"message": "Lineup selected successfully", "next_turn": next_turn}

@api_router.post("/league/lineup/skip-turn")
async def skip_lineup_turn(team_data: dict):
    """Skip lineup selection turn"""
    team_id = team_data.get("team_id")
    
    game_state = await db.game_state.find_one()
    if not game_state or not game_state.get("lineup_selection_phase"):
        raise HTTPException(status_code=400, detail="Not in lineup selection phase")
    
    teams = await db.teams.find().to_list(length=None)
    current_team_index = game_state.get("current_team_turn", 0)
    
    if current_team_index >= len(teams):
        raise HTTPException(status_code=400, detail="Invalid team turn")
    
    current_team = teams[current_team_index]
    if current_team["id"] != team_id:
        raise HTTPException(status_code=400, detail="Not your turn")
    
    # Move to next team's turn
    next_turn = (current_team_index + 1) % len(teams)
    
    await db.game_state.update_one(
        {"id": game_state["id"]},
        {"$set": {"current_team_turn": next_turn}}
    )
    
    return {"message": "Turn skipped", "next_turn": next_turn}
class ReleasePlayerRequest(BaseModel):
    team_id: str
    player_id: str

@api_router.post("/teams/{team_id}/set-clause")
async def set_player_clause(team_id: str, request: SetClauseRequest):
    """Set protection clause for team's own player"""
    game_state = await db.game_state.find_one()
    if not game_state or game_state.get("current_phase") not in ["pre_match", "league"]:
        raise HTTPException(status_code=400, detail="Can only set clauses during league phase")
    
    # Verify team owns the player
    player = await db.players.find_one({"id": request.player_id})
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    if player.get("team_id") != team_id:
        raise HTTPException(status_code=400, detail="You can only set clauses for your own players")
    
    # Verify team has enough budget for the clause
    team = await db.teams.find_one({"id": team_id})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    if team["budget"] < request.clause_amount:
        raise HTTPException(status_code=400, detail="Insufficient budget to set clause")
    
    # Update player clause and deduct cost from team budget
    await db.players.update_one(
        {"id": request.player_id},
        {"$set": {"clause_amount": request.clause_amount}}
    )
    
    await db.teams.update_one(
        {"id": team_id},
        {"$inc": {"budget": -request.clause_amount}}
    )
    
    return {"message": "Clause set successfully", "clause_amount": request.clause_amount}

@api_router.post("/teams/release-player")
async def release_player_to_market(request: ReleasePlayerRequest):
    """Release player back to free agents market for 90% of original value"""
    game_state = await db.game_state.find_one()
    if not game_state or game_state.get("current_phase") not in ["pre_match", "league"]:
        raise HTTPException(status_code=400, detail="Can only release players during league phase")
    
    # Get player and team
    player = await db.players.find_one({"id": request.player_id})
    team = await db.teams.find_one({"id": request.team_id})
    
    if not player or not team:
        raise HTTPException(status_code=404, detail="Player or team not found")
    
    # Verify player belongs to team
    if player.get("team_id") != request.team_id:
        raise HTTPException(status_code=400, detail="Player doesn't belong to your team")
    
    # Verify team won't go below 7 players
    current_player_count = len(team.get("players", []))
    if current_player_count <= 7:
        raise HTTPException(
            status_code=400, 
            detail="Cannot release player - team must maintain at least 7 players"
        )
    
    # Calculate 90% of original value
    original_price = player["price"]
    refund_amount = int(original_price * 0.9)
    
    # Release player (remove from team, clear clause)
    await db.players.update_one(
        {"id": request.player_id},
        {"$unset": {"team_id": "", "jersey_number": ""}, 
         "$set": {"clause_amount": 0, "is_resting": False, "games_played": 0}}
    )
    
    # Update team (remove player from list, add refund)
    team_players = team.get("players", [])
    if request.player_id in team_players:
        team_players.remove(request.player_id)
    
    await db.teams.update_one(
        {"id": request.team_id},
        {"$set": {"players": team_players}, "$inc": {"budget": refund_amount}}
    )
    
    return {
        "message": "Player released successfully",
        "player_name": player["name"],
        "refund_amount": refund_amount,
        "original_price": original_price
    }

@api_router.get("/league/market-status")
async def get_market_status():
    """Get current market status (open/closed based on round)"""
    game_state = await db.game_state.find_one()
    if not game_state:
        return {"market_open": False, "reason": "No active game"}
    
    current_round = game_state.get("current_round", 1)
    current_phase = game_state.get("current_phase", "setup")
    
    # Market opens after round 7 and closes after round 8
    market_open = current_round == 7 and current_phase in ["pre_match", "league"]
    
    return {
        "market_open": market_open,
        "current_round": current_round,
        "current_phase": current_phase,
        "reason": "Market opens after round 7 and closes after round 8" if not market_open else "Market is open for free agent signings"
    }

@api_router.post("/teams/buy-player")
async def buy_player_from_team(request: BuyPlayerRequest):
    """Buy player from another team during league phase"""
    game_state = await db.game_state.find_one()
    if not game_state or game_state.get("current_phase") not in ["pre_match", "league"]:
        raise HTTPException(status_code=400, detail="Can only buy players during league phase")
    
    # Get player, buyer and seller teams
    player = await db.players.find_one({"id": request.player_id})
    buyer_team = await db.teams.find_one({"id": request.buyer_team_id})
    seller_team = await db.teams.find_one({"id": request.seller_team_id})
    
    if not player or not buyer_team or not seller_team:
        raise HTTPException(status_code=404, detail="Player or team not found")
    
    # Verify player belongs to seller team
    if player.get("team_id") != request.seller_team_id:
        raise HTTPException(status_code=400, detail="Player doesn't belong to seller team")
    
    # Verify seller team won't go below 7 players
    seller_player_count = len(seller_team.get("players", []))
    if seller_player_count <= 7:
        raise HTTPException(
            status_code=400, 
            detail="Cannot buy player - seller team must maintain at least 7 players"
        )
    
    # Verify buyer team won't exceed 10 players
    buyer_player_count = len(buyer_team.get("players", []))
    if buyer_player_count >= 10:
        raise HTTPException(status_code=400, detail="Buyer team already has maximum players (10)")
    
    # Calculate total cost (base price + clause)
    base_price = player["price"]
    clause_amount = player.get("clause_amount", 0)
    total_cost = base_price + clause_amount
    
    # Verify buyer has enough budget
    if buyer_team["budget"] < total_cost:
        raise HTTPException(
            status_code=400, 
            detail=f"Insufficient budget. Need {total_cost}, have {buyer_team['budget']}"
        )
    
    # Check if player was in seller team's current lineup
    seller_current_lineup = seller_team.get("current_lineup", [])
    player_was_in_lineup = request.player_id in seller_current_lineup
    
    # Transfer player
    await db.players.update_one(
        {"id": request.player_id},
        {"$set": {"team_id": request.buyer_team_id, "clause_amount": 0}}
    )
    
    # Update buyer team (add player, deduct money)
    buyer_players = buyer_team.get("players", [])
    buyer_players.append(request.player_id)
    await db.teams.update_one(
        {"id": request.buyer_team_id},
        {"$set": {"players": buyer_players}, "$inc": {"budget": -total_cost}}
    )
    
    # Update seller team (remove player, add money)
    seller_players = seller_team.get("players", [])
    if request.player_id in seller_players:
        seller_players.remove(request.player_id)
    
    # If player was in lineup, remove from lineup and clear formation
    lineup_affected = False
    if player_was_in_lineup:
        new_lineup = [pid for pid in seller_current_lineup if pid != request.player_id]
        await db.teams.update_one(
            {"id": request.seller_team_id},
            {"$set": {
                "players": seller_players, 
                "current_lineup": new_lineup,
                "current_formation": "",  # Clear formation since lineup is now invalid
                "needs_replacement_turn": True  # Flag that this team needs an extra turn
            }, "$inc": {"budget": total_cost}}
        )
        lineup_affected = True
        
        # Give seller team an additional turn if we're in lineup selection phase
        if game_state.get("lineup_selection_phase") and game_state.get("current_phase") == "pre_match":
            # Mark that seller team needs to re-select lineup
            await handle_lineup_disruption(seller_team["id"], player["name"])
    else:
        await db.teams.update_one(
            {"id": request.seller_team_id},
            {"$set": {"players": seller_players}, "$inc": {"budget": total_cost}}
        )
    
    response_data = {
        "message": "Player purchased successfully",
        "player_name": player["name"],
        "total_cost": total_cost,
        "base_price": base_price,
        "clause_amount": clause_amount,
        "lineup_affected": lineup_affected
    }
    
    if lineup_affected:
        response_data["additional_message"] = f"{seller_team['name']} must select a replacement player as {player['name']} was in their lineup"
    
    return response_data

async def handle_lineup_disruption(affected_team_id, transferred_player_name):
    """Handle when a team loses a player from their current lineup"""
    game_state = await db.game_state.find_one()
    if not game_state:
        return
    
    # If we're in lineup selection phase, we need to handle this carefully
    if game_state.get("lineup_selection_phase") and game_state.get("current_phase") == "pre_match":
        # Get current turn info
        current_team_turn = game_state.get("current_team_turn", 0)
        teams = await db.teams.find().to_list(length=None)
        
        # Check how many teams still need to complete their lineups
        teams_without_lineup = []
        affected_team_needs_turn = False
        
        for i, team in enumerate(teams):
            current_lineup = team.get("current_lineup", [])
            needs_replacement = team.get("needs_replacement_turn", False)
            
            # Team needs a turn if they don't have a valid lineup or need replacement
            if len(current_lineup) != 7 or needs_replacement:
                teams_without_lineup.append(team["id"])
                if team["id"] == affected_team_id:
                    affected_team_needs_turn = True
        
        # If affected team needs a turn but it's not their current turn, 
        # we need to adjust the turn order
        if affected_team_needs_turn and len(teams_without_lineup) > 0:
            # Create a custom turn order that prioritizes the affected team
            current_team_id = teams[current_team_turn]["id"] if current_team_turn < len(teams) else None
            
            # If it's not the affected team's turn, make it their turn next
            if current_team_id != affected_team_id:
                # Insert the affected team as next in turn order by creating a special flag
                await db.teams.update_one(
                    {"id": affected_team_id},
                    {"$set": {"priority_turn": True}}
                )
    
    # Log the disruption for debugging
    print(f"Lineup disruption handled: Team {affected_team_id} lost {transferred_player_name} from lineup")

@api_router.post("/league/lineup/select")
async def select_team_lineup(lineup: LineupSelection):
    """Select team lineup and formation for current round"""
    game_state = await db.game_state.find_one()
    if not game_state or game_state.get("current_phase") != "pre_match":
        raise HTTPException(status_code=400, detail="Not in pre-match phase")
    
    if not game_state.get("lineup_selection_phase"):
        raise HTTPException(status_code=400, detail="Not in lineup selection phase")
    
    # Get all teams
    teams = await db.teams.find().to_list(length=None)
    current_team_index = game_state.get("current_team_turn", 0)
    
    # Check if this team has priority turn due to lineup disruption
    requesting_team = await db.teams.find_one({"id": lineup.team_id})
    if requesting_team and requesting_team.get("priority_turn"):
        # This team has priority, allow them to select
        current_team = requesting_team
    else:
        # Normal turn order
        if current_team_index >= len(teams):
            raise HTTPException(status_code=400, detail="Invalid team turn")
        
        current_team = teams[current_team_index]
        if current_team["id"] != lineup.team_id:
            raise HTTPException(status_code=400, detail="Not your turn to select lineup")
    
    # Validate formation
    formations = {
        "A": {"portero": 1, "defensas": 2, "medios": 3, "delanteros": 1},
        "B": {"portero": 1, "defensas": 3, "medios": 2, "delanteros": 1},
        "C": {"portero": 1, "defensas": 2, "medios": 2, "delanteros": 2}
    }
    
    if lineup.formation not in formations:
        raise HTTPException(status_code=400, detail="Invalid formation")
    
    formation = formations[lineup.formation]
    
    # Validate lineup length
    if len(lineup.players) != 7:
        raise HTTPException(status_code=400, detail="Must select exactly 7 players")
    
    # Get selected players and validate they belong to the team
    selected_players = await db.players.find({"id": {"$in": lineup.players}}).to_list(length=None)
    
    if len(selected_players) != 7:
        raise HTTPException(status_code=400, detail="Some selected players not found")
    
    # Check all players belong to the team
    for player in selected_players:
        if player.get("team_id") != lineup.team_id:
            raise HTTPException(status_code=400, detail=f"Player {player['name']} doesn't belong to your team")
    
    # Check players are available (not resting due to resistance)
    for player in selected_players:
        if player.get("is_resting", False):
            raise HTTPException(status_code=400, detail=f"Player {player['name']} is resting and cannot play")
    
    # Validate formation requirements
    position_counts = {"PORTERO": 0, "DEFENSA": 0, "MEDIO": 0, "DELANTERO": 0}
    for player in selected_players:
        position_counts[player["position"]] += 1
    
    if (position_counts["PORTERO"] != formation["portero"] or
        position_counts["DEFENSA"] != formation["defensas"] or
        position_counts["MEDIO"] != formation["medios"] or
        position_counts["DELANTERO"] != formation["delanteros"]):
        raise HTTPException(
            status_code=400, 
            detail=f"Formation {lineup.formation} requires {formation['portero']} GK, {formation['defensas']} DEF, {formation['medios']} MID, {formation['delanteros']} FWD"
        )
    
    # Update team with selected lineup and clear any special flags
    await db.teams.update_one(
        {"id": lineup.team_id},
        {"$set": {
            "current_lineup": lineup.players,
            "current_formation": lineup.formation
        }, "$unset": {
            "needs_replacement_turn": "",
            "priority_turn": ""
        }}
    )
    
    # Determine next turn
    # First, check if there are any teams with priority turns
    priority_team = await db.teams.find_one({"priority_turn": True})
    if priority_team:
        # Let the priority team go next by not changing the turn
        return {"message": "Lineup selected successfully. Priority team will go next.", "priority_turn": True}
    
    # Normal turn progression
    next_turn = (current_team_index + 1) % len(teams)
    
    # Check if all teams have selected lineups
    teams_with_lineups = await db.teams.count_documents({
        "current_lineup": {"$exists": True, "$ne": []},
        "$expr": {"$eq": [{"$size": "$current_lineup"}, 7]}
    })
    
    if teams_with_lineups == len(teams):
        # All teams have valid lineups, move to match phase
        await db.game_state.update_one(
            {"id": game_state["id"]},
            {"$set": {
                "lineup_selection_phase": False,
                "current_phase": "match",
                "current_team_turn": 0
            }}
        )
        return {"message": "Lineup selected. All teams ready - proceeding to matches!", "next_phase": "match"}
    
    await db.game_state.update_one(
        {"id": game_state["id"]},
        {"$set": {"current_team_turn": next_turn}}
    )
    
    return {"message": "Lineup selected successfully", "next_turn": next_turn}

@api_router.get("/matches/round/{round_number}")
async def get_round_matches_legacy(round_number: int):
    """Get matches for a specific round (legacy endpoint)"""
    matches = await db.matches.find({"round_number": round_number}).to_list(length=None)
    # Convert ObjectId to string for JSON serialization
    for match in matches:
        if "_id" in match:
            match["_id"] = str(match["_id"])
    return matches

@api_router.post("/matches/{match_id}/simulate")
async def simulate_match(match_id: str):
    """Simulate a match with full mechanics"""
    match = await db.matches.find_one({"id": match_id})
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    if match.get("played"):
        raise HTTPException(status_code=400, detail="Match already played")
    
    # Get teams and their lineups
    home_team = await db.teams.find_one({"id": match["home_team_id"]})
    away_team = await db.teams.find_one({"id": match["away_team_id"]})
    
    if not home_team or not away_team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Check if both teams have selected lineups
    home_lineup = home_team.get("current_lineup", [])
    away_lineup = away_team.get("current_lineup", [])
    
    if len(home_lineup) != 7 or len(away_lineup) != 7:
        raise HTTPException(status_code=400, detail="Both teams must have 7 players selected")
    
    # Get all players data
    all_players = await db.players.find().to_list(length=None)
    players_dict = {p["id"]: p for p in all_players}
    
    # Convert to format expected by simulator
    home_players = [players_dict[pid] for pid in home_lineup if pid in players_dict]
    away_players = [players_dict[pid] for pid in away_lineup if pid in players_dict]
    
    # Run simulation
    match_result = MatchSimulator.simulate_match(
        home_team, away_team, home_lineup, away_lineup, all_players
    )
    
    home_score = match_result["home_score"]
    away_score = match_result["away_score"]
    
    # Update match result
    await db.matches.update_one(
        {"id": match_id},
        {"$set": {
            "home_score": home_score,
            "away_score": away_score,
            "home_lineup": home_lineup,
            "away_lineup": away_lineup,
            "match_log": match_result,
            "played": True
        }}
    )
    
    # Update team statistics and budgets
    await update_team_stats_after_match(home_team, away_team, home_score, away_score, match["round_number"])
    
    # Update player resistance (games played)
    await update_player_resistance(home_lineup + away_lineup)
    
    return {
        "message": "Match simulated successfully",
        "home_team": home_team["name"],
        "away_team": away_team["name"],
        "home_score": home_score,
        "away_score": away_score,
        "match_log": match_result
    }

async def update_team_stats_after_match(home_team, away_team, home_score, away_score, round_number):
    """Update team statistics after match"""
    # Calculate points
    if home_score > away_score:
        home_points = 3
        away_points = 0
        home_wins = 1
        away_wins = 0
        home_losses = 0
        away_losses = 1
        home_draws = 0
        away_draws = 0
    elif home_score < away_score:
        home_points = 0
        away_points = 3
        home_wins = 0
        away_wins = 1
        home_losses = 1
        away_losses = 0
        home_draws = 0
        away_draws = 0
    else:
        home_points = 1
        away_points = 1
        home_wins = 0
        away_wins = 0
        home_losses = 0
        away_losses = 0
        home_draws = 1
        away_draws = 1
    
    # Calculate prize money
    home_prize = 500000 + (home_points * 1000000)  # Local bonus + points bonus
    away_prize = away_points * 1000000  # Only points bonus for away team
    
    # Update home team
    await db.teams.update_one(
        {"id": home_team["id"]},
        {"$inc": {
            "points": home_points,
            "goals_for": home_score,
            "goals_against": away_score,
            "matches_played": 1,
            "wins": home_wins,
            "draws": home_draws,
            "losses": home_losses,
            "budget": home_prize
        }}
    )
    
    # Update away team
    await db.teams.update_one(
        {"id": away_team["id"]},
        {"$inc": {
            "points": away_points,
            "goals_for": away_score,
            "goals_against": home_score,
            "matches_played": 1,
            "wins": away_wins,
            "draws": away_draws,
            "losses": away_losses,
            "budget": away_prize
        }}
    )

async def update_player_resistance(player_ids):
    """Update player resistance after match"""
    for player_id in player_ids:
        player = await db.players.find_one({"id": player_id})
        if player:
            games_played = player.get("games_played", 0) + 1
            resistance = player.get("resistance", 10)
            
            # Check if player needs to rest
            needs_rest = games_played >= resistance
            
            await db.players.update_one(
                {"id": player_id},
                {"$set": {
                    "games_played": 0 if needs_rest else games_played,
                    "is_resting": needs_rest
                }}
            )

@api_router.get("/matches/round/{round_number}")
async def get_round_matches(round_number: int):
    """Get matches for a specific round"""
    matches = await db.matches.find({"round_number": round_number}).to_list(length=None)
    return matches

@api_router.get("/matches/round/{round_number}/current")
async def get_current_round_status(round_number: int):
    """Get status of current round matches"""
    matches = await db.matches.find({"round_number": round_number}).to_list(length=None)
    
    total_matches = len(matches)
    played_matches = len([m for m in matches if m.get("played", False)])
    
    # Find next match to play
    next_match = None
    for match in matches:
        if not match.get("played", False):
            next_match = match
            break
    
    return {
        "round_number": round_number,
        "total_matches": total_matches,
        "played_matches": played_matches,
        "completed": played_matches == total_matches,
        "next_match": next_match
    }

@api_router.post("/league/simulate-next-match")
async def simulate_next_match():
    """Simulate the next available match in current round"""
    game_state = await db.game_state.find_one()
    if not game_state:
        raise HTTPException(status_code=404, detail="No game found")
    
    current_round = game_state.get("current_round", 1)
    
    # Find next unplayed match
    next_match = await db.matches.find_one({
        "round_number": current_round,
        "played": {"$ne": True}
    })
    
    if not next_match:
        raise HTTPException(status_code=404, detail="No more matches in current round")
    
    # Simulate the match
    try:
        result = await simulate_match(next_match["id"])
        
        # Check if round is complete
        round_status = await get_current_round_status(current_round)
        if round_status["completed"]:
            # Reset lineups for next round and move to lineup selection phase
            await db.teams.update_many(
                {},
                {"$set": {"current_lineup": [], "current_formation": ""}}
            )
            
            # Check if league is complete (14 rounds)
            if current_round >= 14:
                await db.game_state.update_one(
                    {"id": game_state["id"]},
                    {"$set": {"current_phase": "finished"}}
                )
                return {**result, "league_completed": True, "message": "League completed!"}
            else:
                # Move to next round
                await db.game_state.update_one(
                    {"id": game_state["id"]},
                    {"$set": {
                        "current_round": current_round + 1,
                        "current_phase": "pre_match",
                        "lineup_selection_phase": True,
                        "current_team_turn": 0
                    }}
                )
                return {**result, "round_completed": True, "next_round": current_round + 1}
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
