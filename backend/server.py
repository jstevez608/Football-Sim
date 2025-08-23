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
    
    @staticmethod
    def choose_action():
        rand = random.random()
        cumulative = 0
        for action, prob in MatchSimulator.ACTION_PROBABILITIES.items():
            cumulative += prob
            if rand <= cumulative:
                return action
        return "PASE"
    
    @staticmethod
    def choose_player(players, probabilities, attacking=True):
        available_players = [p for p in players if p.position != "PORTERO" or not attacking]
        if not available_players:
            return random.choice(players)
        
        weights = []
        for player in available_players:
            if attacking:
                weights.append(MatchSimulator.POSITION_ATTACK_PROB.get(player.position, 0))
            else:
                weights.append(MatchSimulator.POSITION_DEFENSE_PROB.get(player.position, 0))
        
        if sum(weights) == 0:
            return random.choice(available_players)
        
        rand = random.random() * sum(weights)
        cumulative = 0
        for i, weight in enumerate(weights):
            cumulative += weight
            if rand <= cumulative:
                return available_players[i]
        
        return available_players[-1]
    
    @staticmethod
    def choose_defender(players, action):
        if action in ["TIRO", "REMATE", "PENALTI"]:
            # Only goalkeeper can defend these
            goalkeepers = [p for p in players if p.position == "PORTERO"]
            return goalkeepers[0] if goalkeepers else random.choice(players)
        else:
            return MatchSimulator.choose_player(players, MatchSimulator.POSITION_DEFENSE_PROB, attacking=False)
    
    @staticmethod
    def get_defense_action(attack_action):
        defense_map = {
            "PASE": "BLOQUEO",
            "REGATE": "ROBO", 
            "CORNER": "DESPEJE",
            "AREA": "BLOQUEO",
            "TIRO": "PARADA",
            "REMATE": "PARADA",
            "PENALTI": "ATAJADA"
        }
        return defense_map.get(attack_action, "ROBO")
    
    @staticmethod
    def calculate_action_result(attacker, attack_action, defender, defense_action):
        # Get attacker's stat for the action
        attacker_stat = getattr(attacker.stats, attack_action.lower())
        # Get defender's stat for the defense action
        defender_stat = getattr(defender.stats, defense_action.lower())
        
        # Add random factor (1-3)
        attacker_total = attacker_stat + random.randint(1, 3)
        defender_total = defender_stat + random.randint(1, 3)
        
        return attacker_total > defender_total
    
    @staticmethod
    def get_follow_up_actions(action):
        follow_ups = {
            "PASE": ["REGATE", "TIRO", "CORNER", "AREA"],
            "REGATE": ["TIRO", "PASE", "AREA"],
            "CORNER": ["REMATE"],
            "AREA": ["PENALTI"]
        }
        return follow_ups.get(action, [])
    
    @staticmethod
    def simulate_match(home_team, away_team, home_lineup, away_lineup):
        home_score = 0
        away_score = 0
        match_log = []
        
        # Convert lineup IDs to player objects (this would need actual player lookup)
        # For now, simulating with basic structure
        
        for turn in range(18):  # 9 turns per team
            attacking_team = home_team if turn % 2 == 0 else away_team
            defending_team = away_team if turn % 2 == 0 else home_team
            attacking_lineup = home_lineup if turn % 2 == 0 else away_lineup
            defending_lineup = away_lineup if turn % 2 == 0 else home_lineup
            
            # For simulation purposes - in real implementation, need to fetch actual player objects
            turn_log = {
                "turn": turn + 1,
                "attacking_team": attacking_team.name,
                "actions": []
            }
            
            # Simulate turn actions (simplified for now)
            action = MatchSimulator.choose_action()
            
            turn_log["actions"].append({
                "action": action,
                "result": "simulated"  # Would contain actual simulation results
            })
            
            # Simplified scoring - in real implementation would use full logic
            if random.random() < 0.1:  # 10% chance of goal per turn
                if turn % 2 == 0:
                    home_score += 1
                else:
                    away_score += 1
                turn_log["goal"] = True
            
            match_log.append(turn_log)
        
        return home_score, away_score, match_log

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
async def set_player_clause(team_id: str, request: SetClauseRequest):
    """Set protection clause for team's own player"""
    game_state = await db.game_state.find_one()
    if not game_state or game_state["current_phase"] != "league":
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

@api_router.post("/teams/buy-player")
async def buy_player_from_team(request: BuyPlayerRequest):
    """Buy player from another team during league phase"""
    game_state = await db.game_state.find_one()
    if not game_state or game_state["current_phase"] != "league":
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
    seller_players.remove(request.player_id)
    await db.teams.update_one(
        {"id": request.seller_team_id},
        {"$set": {"players": seller_players}, "$inc": {"budget": total_cost}}
    )
    
    return {
        "message": "Player purchased successfully",
        "player_name": player["name"],
        "total_cost": total_cost,
        "base_price": base_price,
        "clause_amount": clause_amount
    }

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
async def simulate_match(match_id: str, home_lineup: List[str], away_lineup: List[str]):
    """Simulate a match"""
    match = await db.matches.find_one({"id": match_id})
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    # Get teams
    home_team = await db.teams.find_one({"id": match["home_team_id"]})
    away_team = await db.teams.find_one({"id": match["away_team_id"]})
    
    # For now, simple simulation
    home_score = random.randint(0, 4)
    away_score = random.randint(0, 4)
    
    # Update match result
    await db.matches.update_one(
        {"id": match_id},
        {"$set": {
            "home_score": home_score,
            "away_score": away_score,
            "home_lineup": home_lineup,
            "away_lineup": away_lineup,
            "played": True,
            "match_log": []  # Would contain detailed simulation log
        }}
    )
    
    # Update team budgets (prize money)
    home_prize = 500000  # Local team bonus
    away_prize = 0
    
    # Points calculation
    if home_score > away_score:
        home_prize += 1000000 * 3  # 3 points * 1M
    elif home_score < away_score:
        away_prize += 1000000 * 3  # 3 points * 1M
    else:
        home_prize += 1000000 * 1  # 1 point * 1M
        away_prize += 1000000 * 1  # 1 point * 1M
    
    # Update budgets
    await db.teams.update_one(
        {"id": match["home_team_id"]},
        {"$inc": {"budget": home_prize}}
    )
    await db.teams.update_one(
        {"id": match["away_team_id"]},
        {"$inc": {"budget": away_prize}}
    )
    
    return {
        "home_score": home_score,
        "away_score": away_score,
        "home_prize": home_prize,
        "away_prize": away_prize
    }

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