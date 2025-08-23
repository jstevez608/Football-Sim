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
    return game_state

@api_router.post("/draft/start")
async def start_draft():
    """Start the draft phase"""
    game_state = await db.game_state.find_one()
    if not game_state:
        raise HTTPException(status_code=404, detail="No game found")
    
    # Randomize draft order
    teams = game_state.get("teams", [])
    random.shuffle(teams)
    
    await db.game_state.update_one(
        {"id": game_state["id"]},
        {"$set": {
            "current_phase": "draft",
            "draft_order": teams,
            "current_team_turn": 0
        }}
    )
    
    return {"message": "Draft started", "draft_order": teams}

class DraftPickRequest(BaseModel):
    team_id: str
    player_id: str
    clause_amount: int = 0

class DraftSkipRequest(BaseModel):
    team_id: str

class SetClauseRequest(BaseModel):
    player_id: str
    clause_amount: int = Field(..., ge=0)

class BuyPlayerRequest(BaseModel):
    buyer_team_id: str
    seller_team_id: str
    player_id: str

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
    
    if len(team.get("players", [])) >= 10:
        raise HTTPException(status_code=400, detail="Team is full")
    
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

@api_router.post("/league/start")
async def start_league():
    """Start the league phase"""
    await db.game_state.update_one(
        {},
        {"$set": {"current_phase": "league", "current_round": 1}}
    )
    
    # Generate match fixtures
    teams = await db.teams.find().to_list(length=None)
    team_ids = [team["id"] for team in teams]
    
    # Generate all possible matches (round-robin)
    matches = []
    for i, home_team in enumerate(team_ids):
        for j, away_team in enumerate(team_ids):
            if i != j:
                match = Match(
                    home_team_id=home_team,
                    away_team_id=away_team,
                    round_number=1  # Will be distributed across rounds
                )
                matches.append(match.dict())
    
    # Insert matches
    await db.matches.delete_many({})  # Clear existing matches
    await db.matches.insert_many(matches)
    
    return {"message": "League started", "matches_created": len(matches)}

@api_router.get("/matches/round/{round_number}")
async def get_round_matches(round_number: int):
    """Get matches for a specific round"""
    matches = await db.matches.find({"round_number": round_number}).to_list(length=None)
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