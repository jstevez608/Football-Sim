import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import { Button } from "./components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "./components/ui/card";
import { Input } from "./components/ui/input";
import { Label } from "./components/ui/label";
import { Badge } from "./components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "./components/ui/alert-dialog";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [gameState, setGameState] = useState(null);
  const [players, setPlayers] = useState([]);
  const [teams, setTeams] = useState([]);
  const [currentView, setCurrentView] = useState('setup');
  const [loading, setLoading] = useState(false);
  const [editingPlayer, setEditingPlayer] = useState(null);

  // Team creation state
  const [newTeam, setNewTeam] = useState({
    name: '',
    colors: { primary: '#FF0000', secondary: '#FFFFFF' },
    budget: 80000000
  });

  const [standings, setStandings] = useState([]);
  const [roundMatches, setRoundMatches] = useState([]);
  const [formations, setFormations] = useState({});
  const [selectedFormation, setSelectedFormation] = useState('A');
  const [selectedPlayers, setSelectedPlayers] = useState([]);
  const [marketStatus, setMarketStatus] = useState({});
  const [showTransferMarket, setShowTransferMarket] = useState(false);

  useEffect(() => {
    loadGameState();
    loadPlayers();
    loadTeams();
    loadStandings();
    loadFormations();
    loadMarketStatus();
  }, []);

  useEffect(() => {
    if (gameState && gameState.current_round) {
      loadRoundMatches(gameState.current_round);
      loadMarketStatus();
    }
  }, [gameState]);

  const loadGameState = async () => {
    try {
      const response = await axios.get(`${API}/game/state`);
      if (!response.data.error) {
        setGameState(response.data);
      }
    } catch (error) {
      console.error('Error loading game state:', error);
    }
  };

  const loadPlayers = async () => {
    try {
      const response = await axios.get(`${API}/players`);
      setPlayers(response.data);
    } catch (error) {
      console.error('Error loading players:', error);
    }
  };

  const loadTeams = async () => {
    try {
      const response = await axios.get(`${API}/teams`);
      setTeams(response.data);
    } catch (error) {
      console.error('Error loading teams:', error);
    }
  };

  const initializeGame = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/game/init`);
      await loadGameState();
      await loadPlayers();
      await loadTeams(); // This should now return empty array after reset
      setCurrentView('setup');
      
      // Show success message
      const playersCount = response.data.players_available || 0;
      console.log(`Game reset successfully. ${playersCount} players available.`);
    } catch (error) {
      console.error('Error resetting game:', error);
    }
    setLoading(false);
  };

  const createTeam = async () => {
    if (!newTeam.name || newTeam.budget < 40000000 || newTeam.budget > 180000000) {
      alert('Por favor completa todos los campos correctamente');
      return;
    }

    try {
      await axios.post(`${API}/teams`, newTeam);
      await loadTeams();
      await loadGameState();
      setNewTeam({
        name: '',
        colors: { primary: '#FF0000', secondary: '#FFFFFF' },
        budget: 80000000
      });
    } catch (error) {
      console.error('Error creating team:', error);
    }
  };

  const updatePlayer = async (playerId, playerData) => {
    try {
      await axios.put(`${API}/players/${playerId}`, playerData);
      await loadPlayers();
      setEditingPlayer(null);
    } catch (error) {
      console.error('Error updating player:', error);
    }
  };

  const startDraft = async () => {
    if (teams.length !== 8) {
      alert('Se necesitan exactamente 8 equipos para comenzar');
      return;
    }
    
    try {
      await axios.post(`${API}/draft/start`);
      await loadGameState();
      setCurrentView('draft');
    } catch (error) {
      console.error('Error starting draft:', error);
    }
  };

  const draftPlayer = async (teamId, playerId) => {
    try {
      const response = await axios.post(`${API}/draft/pick`, {
        team_id: teamId,
        player_id: playerId,
        clause_amount: 0
      });
      await loadGameState();
      await loadPlayers();
      await loadTeams();
      console.log('Player drafted successfully:', response.data);
    } catch (error) {
      console.error('Error drafting player:', error);
      alert('Error al fichar jugador: ' + (error.response?.data?.detail || 'Error desconocido'));
    }
  };

  const skipTurn = async (teamId) => {
    try {
      const response = await axios.post(`${API}/draft/skip-turn`, {
        team_id: teamId
      });
      await loadGameState();
      console.log('Turn skipped successfully:', response.data);
    } catch (error) {
      console.error('Error skipping turn:', error);
      alert('Error al pasar turno: ' + (error.response?.data?.detail || 'Error desconocido'));
    }
  };

  const setPlayerClause = async (teamId, playerId, clauseAmount) => {
    try {
      await axios.post(`${API}/teams/${teamId}/set-clause`, {
        player_id: playerId,
        clause_amount: clauseAmount
      });
      await loadPlayers();
      await loadTeams();
      alert(`Cláusula de ${formatCurrency(clauseAmount)} establecida correctamente`);
    } catch (error) {
      console.error('Error setting clause:', error);
      alert('Error al establecer cláusula: ' + (error.response?.data?.detail || 'Error desconocido'));
    }
  };

  const buyPlayer = async (buyerTeamId, sellerTeamId, playerId) => {
    try {
      const response = await axios.post(`${API}/teams/buy-player`, {
        buyer_team_id: buyerTeamId,
        seller_team_id: sellerTeamId,
        player_id: playerId
      });
      await loadPlayers();
      await loadTeams();
      alert(`${response.data.player_name} fichado por ${formatCurrency(response.data.total_cost)}`);
    } catch (error) {
      console.error('Error buying player:', error);
      alert('Error al comprar jugador: ' + (error.response?.data?.detail || 'Error desconocido'));
    }
  };

  const loadStandings = async () => {
    try {
      const response = await axios.get(`${API}/league/standings`);
      setStandings(response.data);
    } catch (error) {
      console.error('Error loading standings:', error);
    }
  };

  const loadRoundMatches = async (roundNumber) => {
    try {
      const response = await axios.get(`${API}/league/matches/round/${roundNumber}`);
      setRoundMatches(response.data);
    } catch (error) {
      console.error('Error loading round matches:', error);
    }
  };

  const loadFormations = async () => {
    try {
      const response = await axios.get(`${API}/league/formations`);
      setFormations(response.data);
    } catch (error) {
      console.error('Error loading formations:', error);
    }
  };

  const selectLineup = async (teamId, formation, playerIds) => {
    try {
      const response = await axios.post(`${API}/league/lineup/select`, {
        team_id: teamId,
        formation: formation,
        players: playerIds
      });
      await loadGameState();
      await loadTeams();
      setSelectedPlayers([]);
      alert(response.data.message);
    } catch (error) {
      console.error('Error selecting lineup:', error);
      alert('Error al seleccionar alineación: ' + (error.response?.data?.detail || 'Error desconocido'));
    }
  };

  const skipLineupTurn = async (teamId) => {
    try {
      await axios.post(`${API}/league/lineup/skip-turn`, { team_id: teamId });
      await loadGameState();
    } catch (error) {
      console.error('Error skipping turn:', error);
    }
  };

  const loadMarketStatus = async () => {
    try {
      const response = await axios.get(`${API}/league/market-status`);
      setMarketStatus(response.data);
    } catch (error) {
      console.error('Error loading market status:', error);
    }
  };

  const releasePlayer = async (teamId, playerId) => {
    try {
      const response = await axios.post(`${API}/teams/release-player`, {
        team_id: teamId,
        player_id: playerId
      });
      await loadPlayers();
      await loadTeams();
      alert(`${response.data.player_name} liberado por ${formatCurrency(response.data.refund_amount)} (90% del valor original)`);
    } catch (error) {
      console.error('Error releasing player:', error);
      alert('Error al liberar jugador: ' + (error.response?.data?.detail || 'Error desconocido'));
    }
  };

  const draftFreeAgent = async (teamId, playerId) => {
    try {
      const response = await axios.post(`${API}/draft/pick`, {
        team_id: teamId,
        player_id: playerId,
        clause_amount: 0
      });
      await loadPlayers();
      await loadTeams();
      alert('Jugador libre fichado correctamente');
    } catch (error) {
      console.error('Error drafting free agent:', error);
      alert('Error al fichar jugador libre: ' + (error.response?.data?.detail || 'Error desconocido'));
    }
  };

  const startLeague = async () => {
    try {
      await axios.post(`${API}/league/start`);
      await loadGameState();
      setCurrentView('league');
    } catch (error) {
      console.error('Error starting league:', error);
      alert('Error al iniciar liga: ' + (error.response?.data?.detail || 'Error desconocido'));
    }
  };

  const canStartLeague = () => {
    return teams.every(team => (team.players && team.players.length >= 7));
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0
    }).format(amount);
  };

  const getPositionBadgeColor = (position) => {
    const colors = {
      'PORTERO': 'bg-yellow-500',
      'DEFENSA': 'bg-blue-500',
      'MEDIO': 'bg-green-500',
      'DELANTERO': 'bg-red-500'
    };
    return colors[position] || 'bg-gray-500';
  };

  const LineupSelectionInterface = ({ 
    gameState, teams, players, formations, 
    selectedFormation, setSelectedFormation, 
    selectedPlayers, setSelectedPlayers,
    onSelectLineup, onSkipTurn 
  }) => {
    const currentTeamIndex = gameState.current_team_turn || 0;
    const currentTeam = teams[currentTeamIndex];
    
    if (!currentTeam) return null;
    
    const teamPlayers = players.filter(p => p.team_id === currentTeam.id && !p.is_resting);
    const currentFormation = formations[selectedFormation];
    
    const togglePlayerSelection = (playerId) => {
      if (selectedPlayers.includes(playerId)) {
        setSelectedPlayers(selectedPlayers.filter(id => id !== playerId));
      } else if (selectedPlayers.length < 7) {
        setSelectedPlayers([...selectedPlayers, playerId]);
      }
    };
    
    const getPlayersByPosition = (position) => {
      return teamPlayers.filter(p => p.position === position);
    };
    
    const countSelectedByPosition = (position) => {
      return selectedPlayers.filter(playerId => {
        const player = players.find(p => p.id === playerId);
        return player && player.position === position;
      }).length;
    };
    
    const canSelectLineup = () => {
      if (selectedPlayers.length !== 7) return false;
      if (!currentFormation) return false;
      
      const porteros = countSelectedByPosition('PORTERO');
      const defensas = countSelectedByPosition('DEFENSA');
      const medios = countSelectedByPosition('MEDIO');
      const delanteros = countSelectedByPosition('DELANTERO');
      
      return (
        porteros === currentFormation.portero &&
        defensas === currentFormation.defensas &&
        medios === currentFormation.medios &&
        delanteros === currentFormation.delanteros
      );
    };
    
    return (
      <Card>
        <CardHeader>
          <CardTitle>Selección de Alineación - {currentTeam.name}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <div className="mb-4">
                <Label className="text-base font-medium">Formación</Label>
                <div className="grid grid-cols-3 gap-3 mt-2">
                  {Object.entries(formations).map(([key, formation]) => (
                    <Button
                      key={key}
                      variant={selectedFormation === key ? "default" : "outline"}
                      onClick={() => {
                        setSelectedFormation(key);
                        setSelectedPlayers([]); // Reset selection when changing formation
                      }}
                      className="flex flex-col p-3 h-auto"
                    >
                      <span className="font-semibold">{formation.name}</span>
                      <span className="text-xs opacity-75">
                        {formation.defensas}-{formation.medios}-{formation.delanteros}
                      </span>
                    </Button>
                  ))}
                </div>
              </div>
              
              {currentFormation && (
                <div className="space-y-4">
                  <div className="text-sm text-gray-600 mb-4">
                    Selecciona {currentFormation.portero} portero, {currentFormation.defensas} defensas, {currentFormation.medios} medios y {currentFormation.delanteros} delanteros
                  </div>
                  
                  {['PORTERO', 'DEFENSA', 'MEDIO', 'DELANTERO'].map(position => {
                    const positionPlayers = getPlayersByPosition(position);
                    const selectedCount = countSelectedByPosition(position);
                    const requiredCount = position === 'PORTERO' ? currentFormation.portero :
                                        position === 'DEFENSA' ? currentFormation.defensas :
                                        position === 'MEDIO' ? currentFormation.medios :
                                        currentFormation.delanteros;
                    
                    return (
                      <div key={position}>
                        <div className="flex justify-between items-center mb-2">
                          <Label className="font-medium">{position}S</Label>
                          <Badge variant={selectedCount === requiredCount ? "default" : "secondary"}>
                            {selectedCount}/{requiredCount}
                          </Badge>
                        </div>
                        <div className="grid md:grid-cols-2 gap-2">
                          {positionPlayers.map(player => (
                            <div
                              key={player.id}
                              className={`p-3 border rounded cursor-pointer transition-all ${
                                selectedPlayers.includes(player.id) 
                                  ? 'border-blue-500 bg-blue-50' 
                                  : 'border-gray-200 hover:border-gray-300'
                              }`}
                              onClick={() => togglePlayerSelection(player.id)}
                            >
                              <div className="flex justify-between items-center">
                                <div>
                                  <div className="font-medium text-sm">{player.name}</div>
                                  <div className="text-xs text-gray-500">
                                    Resistencia: {player.resistance} | Partidos: {player.games_played || 0}
                                  </div>
                                </div>
                                {selectedPlayers.includes(player.id) && (
                                  <Badge className="text-xs">✓</Badge>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
            
            <div>
              <div className="space-y-4">
                <div>
                  <Label className="text-base font-medium">Jugadores Seleccionados</Label>
                  <div className="text-sm text-gray-600 mt-1">
                    {selectedPlayers.length}/7 jugadores
                  </div>
                </div>
                
                <div className="space-y-2">
                  {selectedPlayers.map(playerId => {
                    const player = players.find(p => p.id === playerId);
                    return player ? (
                      <div key={playerId} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                        <span className="text-sm font-medium">{player.name}</span>
                        <Badge variant="outline" className="text-xs">{player.position}</Badge>
                      </div>
                    ) : null;
                  })}
                </div>
                
                <div className="flex gap-2 pt-4">
                  <Button 
                    onClick={() => onSelectLineup(currentTeam.id, selectedFormation, selectedPlayers)}
                    disabled={!canSelectLineup()}
                    className="flex-1"
                  >
                    Confirmar Alineación
                  </Button>
                  <Button 
                    variant="outline"
                    onClick={() => onSkipTurn(currentTeam.id)}
                  >
                    Pasar Turno
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  const TransferMarket = ({ currentTeam, onSetClause, onBuyPlayer, onReleasePlayer, onDraftFreeAgent }) => (
    <Card>
      <CardHeader>
        <CardTitle>Mercado de Transferencias - {currentTeam.name}</CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="my-team">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="my-team">Mi Equipo</TabsTrigger>
            <TabsTrigger value="other-teams">Otros Equipos</TabsTrigger>
            {marketStatus.market_open && (
              <TabsTrigger value="free-agents">Agentes Libres</TabsTrigger>
            )}
          </TabsList>
          
          <TabsContent value="my-team" className="mt-4">
            <div className="mb-4">
              <h3 className="font-semibold mb-2">Tus Jugadores</h3>
              <p className="text-sm text-gray-600 mb-4">
                Puedes establecer cláusulas de protección o liberar jugadores (recibes 90% del valor original)
              </p>
            </div>
            
            <div className="grid md:grid-cols-2 gap-4">
              {players
                .filter(p => p.team_id === currentTeam.id)
                .map(player => (
                  <Card key={player.id} className="p-4">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <div className="font-medium">{player.name}</div>
                        <Badge className={`${getPositionBadgeColor(player.position)} text-white text-xs`}>
                          {player.position}
                        </Badge>
                      </div>
                      <div className="text-right text-sm">
                        <div className="font-bold text-green-600">{formatCurrency(player.price)}</div>
                        {player.clause_amount > 0 && (
                          <div className="text-orange-600">Cláusula: {formatCurrency(player.clause_amount)}</div>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex gap-2">
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => {
                          const clause = prompt('Introduce el importe de la cláusula (€):', '0');
                          if (clause !== null && !isNaN(clause) && parseInt(clause) >= 0) {
                            onSetClause(currentTeam.id, player.id, parseInt(clause));
                          }
                        }}
                      >
                        {player.clause_amount > 0 ? 'Modificar Cláusula' : 'Establecer Cláusula'}
                      </Button>
                      <Button 
                        size="sm" 
                        variant="destructive"
                        onClick={() => {
                          const refund = Math.floor(player.price * 0.9);
                          if (confirm(`¿Liberar a ${player.name}? Recibirás ${formatCurrency(refund)} (90% del valor original)`)) {
                            onReleasePlayer(currentTeam.id, player.id);
                          }
                        }}
                      >
                        Liberar
                      </Button>
                    </div>
                  </Card>
                ))}
            </div>
          </TabsContent>
          
          <TabsContent value="other-teams" className="mt-4">
            <div className="mb-4">
              <h3 className="font-semibold mb-2">Jugadores de Otros Equipos</h3>
              <p className="text-sm text-gray-600 mb-4">
                Precio total = Precio base + Cláusula. El equipo vendedor debe mantener mínimo 7 jugadores.
              </p>
            </div>
            
            <Tabs defaultValue="PORTERO">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="PORTERO">Porteros</TabsTrigger>
                <TabsTrigger value="DEFENSA">Defensas</TabsTrigger>
                <TabsTrigger value="MEDIO">Medios</TabsTrigger>
                <TabsTrigger value="DELANTERO">Delanteros</TabsTrigger>
              </TabsList>
              
              {['PORTERO', 'DEFENSA', 'MEDIO', 'DELANTERO'].map(position => (
                <TabsContent key={position} value={position} className="mt-4">
                  <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-96 overflow-y-auto">
                    {players
                      .filter(player => player.position === position && player.team_id && player.team_id !== currentTeam.id)
                      .map(player => (
                        <PlayerCard 
                          key={player.id}
                          player={player}
                          onBuyPlayer={onBuyPlayer}
                          currentTeam={currentTeam}
                          gamePhase="league"
                          allTeams={teams}
                        />
                      ))}
                  </div>
                </TabsContent>
              ))}
            </Tabs>
          </TabsContent>
          
          {marketStatus.market_open && (
            <TabsContent value="free-agents" className="mt-4">
              <div className="mb-4">
                <h3 className="font-semibold mb-2">Agentes Libres</h3>
                <p className="text-sm text-gray-600 mb-4">
                  Mercado abierto en Jornada 7. Puedes fichar jugadores libres.
                </p>
              </div>
              
              <Tabs defaultValue="PORTERO">
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="PORTERO">Porteros</TabsTrigger>
                  <TabsTrigger value="DEFENSA">Defensas</TabsTrigger>
                  <TabsTrigger value="MEDIO">Medios</TabsTrigger>
                  <TabsTrigger value="DELANTERO">Delanteros</TabsTrigger>
                </TabsList>
                
                {['PORTERO', 'DEFENSA', 'MEDIO', 'DELANTERO'].map(position => (
                  <TabsContent key={position} value={position} className="mt-4">
                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-96 overflow-y-auto">
                      {players
                        .filter(player => player.position === position && !player.team_id)
                        .map(player => (
                          <Card key={player.id} className="p-4">
                            <div className="flex justify-between items-start mb-3">
                              <div>
                                <div className="font-medium">{player.name}</div>
                                <Badge className={`${getPositionBadgeColor(player.position)} text-white text-xs`}>
                                  {player.position}
                                </Badge>
                              </div>
                              <div className="text-right text-sm">
                                <div className="font-bold text-green-600">{formatCurrency(player.price)}</div>
                              </div>
                            </div>
                            
                            <Button 
                              size="sm" 
                              onClick={() => onDraftFreeAgent(currentTeam.id, player.id)}
                              disabled={currentTeam.players && currentTeam.players.length >= 10}
                              className="w-full"
                            >
                              Fichar
                            </Button>
                          </Card>
                        ))}
                    </div>
                  </TabsContent>
                ))}
              </Tabs>
            </TabsContent>
          )}
        </Tabs>
      </CardContent>
    </Card>
  );
    const [editData, setEditData] = useState({
      name: player.name,
      price: player.price,
      resistance: player.resistance,
      stats: { ...player.stats }
    });

    const handleStatChange = (stat, value) => {
      setEditData(prev => ({
        ...prev,
        stats: {
          ...prev.stats,
          [stat]: parseInt(value)
        }
      }));
    };

    const handleSave = () => {
      onSave(player.id, editData);
    };

    return (
      <AlertDialog open={true} onOpenChange={onClose}>
        <AlertDialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <AlertDialogHeader>
            <AlertDialogTitle>Editar Jugador - {player.position}</AlertDialogTitle>
          </AlertDialogHeader>
          
          <div className="space-y-4">
            <div>
              <Label>Nombre</Label>
              <Input 
                value={editData.name}
                onChange={(e) => setEditData(prev => ({ ...prev, name: e.target.value }))}
              />
            </div>
            
            <div>
              <Label>Precio (€)</Label>
              <Input 
                type="number"
                value={editData.price}
                onChange={(e) => setEditData(prev => ({ ...prev, price: parseInt(e.target.value) }))}
              />
            </div>
            
            <div>
              <Label>Resistencia (4-14)</Label>
              <Input 
                type="number"
                min="4"
                max="14"
                value={editData.resistance}
                onChange={(e) => setEditData(prev => ({ ...prev, resistance: parseInt(e.target.value) }))}
              />
            </div>
            
            <div className="grid grid-cols-3 gap-4">
              {Object.entries(editData.stats).map(([stat, value]) => (
                <div key={stat}>
                  <Label className="text-xs uppercase">{stat}</Label>
                  <Input 
                    type="number"
                    min="1"
                    max="6"
                    value={value}
                    onChange={(e) => handleStatChange(stat, e.target.value)}
                  />
                </div>
              ))}
            </div>
          </div>
          
          <AlertDialogFooter>
            <AlertDialogCancel onClick={onClose}>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={handleSave}>Guardar</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    );
  };

  const PlayerCard = ({ player, canEdit = false, onEdit, onDraft, onSetClause, onBuyPlayer, currentTeam, gamePhase, allTeams = [] }) => (
    <Card className="hover:shadow-lg transition-all">
      <CardHeader className="pb-2">
        <div className="flex justify-between items-start">
          <div>
            <CardTitle className="text-lg">{player.name}</CardTitle>
            <Badge className={`${getPositionBadgeColor(player.position)} text-white`}>
              {player.position}
            </Badge>
          </div>
          <div className="text-right">
            <div className="font-bold text-green-600">{formatCurrency(player.price)}</div>
            <div className="text-sm text-gray-500">Resistencia: {player.resistance}</div>
            {player.clause_amount > 0 && (
              <div className="text-xs text-orange-600 font-medium">
                Cláusula: {formatCurrency(player.clause_amount)}
              </div>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-4 gap-2 text-xs">
          {Object.entries(player.stats).map(([stat, value]) => (
            <div key={stat} className="flex justify-between">
              <span className="uppercase">{stat}:</span>
              <span className="font-bold">{value}</span>
            </div>
          ))}
        </div>
        <div className="flex gap-2 mt-3 flex-wrap">
          {canEdit && (
            <Button size="sm" variant="outline" onClick={() => onEdit(player)}>
              Editar
            </Button>
          )}
          {onDraft && currentTeam && gamePhase === 'draft' && (
            <Button 
              size="sm" 
              onClick={() => onDraft(currentTeam.id, player.id)}
              disabled={player.team_id || (currentTeam.players && currentTeam.players.length >= 10)}
            >
              Fichar
            </Button>
          )}
          {onSetClause && player.team_id === currentTeam?.id && gamePhase === 'league' && (
            <Button 
              size="sm" 
              variant="secondary"
              onClick={() => {
                const clause = prompt('Introduce el importe de la cláusula (€):', '0');
                if (clause !== null && !isNaN(clause) && parseInt(clause) >= 0) {
                  onSetClause(currentTeam.id, player.id, parseInt(clause));
                }
              }}
            >
              Cláusula
            </Button>
          )}
          {onBuyPlayer && player.team_id && player.team_id !== currentTeam?.id && gamePhase === 'league' && (
            <Button 
              size="sm" 
              variant="destructive"
              onClick={() => {
                const sellerTeam = allTeams.find(t => t.id === player.team_id);
                const sellerName = sellerTeam ? sellerTeam.name : 'Equipo desconocido';
                const totalCost = player.price + (player.clause_amount || 0);
                if (confirm(`¿Comprar ${player.name} de ${sellerName} por ${formatCurrency(totalCost)}?`)) {
                  onBuyPlayer(currentTeam.id, player.team_id, player.id);
                }
              }}
              disabled={currentTeam?.players?.length >= 10}
            >
              Comprar
            </Button>
          )}
        </div>
        {player.team_id && (
          <Badge variant="secondary" className="mt-2">
            {gamePhase === 'draft' ? 'Fichado' : allTeams.find(t => t.id === player.team_id)?.name || 'Fichado'}
          </Badge>
        )}
      </CardContent>
    </Card>
  );

  if (!gameState && currentView !== 'setup') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 flex items-center justify-center">
        <Card className="w-96">
          <CardHeader>
            <CardTitle className="text-center">Liga de Fútbol - Fichajes</CardTitle>
          </CardHeader>
          <CardContent>
            <Button onClick={initializeGame} disabled={loading} className="w-full">
              {loading ? 'Inicializando...' : 'Inicializar Juego'}
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-blue-50">
      <header className="bg-white shadow-sm border-b-2 border-green-500">
        <div className="container mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold text-green-800">⚽ Liga de Fútbol</h1>
            <div className="flex gap-2">
              <Button 
                variant={currentView === 'setup' ? 'default' : 'outline'}
                onClick={() => setCurrentView('setup')}
              >
                Configuración
              </Button>
              <Button 
                variant={currentView === 'draft' ? 'default' : 'outline'}
                onClick={() => setCurrentView('draft')}
                disabled={!gameState || gameState.current_phase !== 'draft'}
              >
                Fichajes
              </Button>
              <Button 
                variant={currentView === 'league' ? 'default' : 'outline'}
                onClick={() => setCurrentView('league')}
                disabled={!gameState || gameState.current_phase !== 'league'}
              >
                Liga
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {currentView === 'setup' && (
          <div className="space-y-8">
            <Card>
              <CardHeader>
                <CardTitle>Configuración Inicial</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex gap-4 mb-6">
                  <Button onClick={initializeGame} disabled={loading}>
                    {loading ? 'Reiniciando...' : players.length > 0 ? 'Reiniciar Liga' : 'Inicializar Juego'}
                  </Button>
                  {players.length > 0 && (
                    <Badge variant="secondary">
                      {players.length} jugadores disponibles
                    </Badge>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Crear Equipos ({teams.length}/8)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div>
                      <Label>Nombre del Equipo</Label>
                      <Input 
                        value={newTeam.name}
                        onChange={(e) => setNewTeam(prev => ({ ...prev, name: e.target.value }))}
                        placeholder="Introduce el nombre"
                      />
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>Color Primario</Label>
                        <Input 
                          type="color"
                          value={newTeam.colors.primary}
                          onChange={(e) => setNewTeam(prev => ({ 
                            ...prev, 
                            colors: { ...prev.colors, primary: e.target.value } 
                          }))}
                        />
                      </div>
                      <div>
                        <Label>Color Secundario</Label>
                        <Input 
                          type="color"
                          value={newTeam.colors.secondary}
                          onChange={(e) => setNewTeam(prev => ({ 
                            ...prev, 
                            colors: { ...prev.colors, secondary: e.target.value } 
                          }))}
                        />
                      </div>
                    </div>
                    
                    <div>
                      <Label>Presupuesto (40M - 180M €)</Label>
                      <Input 
                        type="number"
                        min="40000000"
                        max="180000000"
                        step="1000000"
                        value={newTeam.budget}
                        onChange={(e) => setNewTeam(prev => ({ ...prev, budget: parseInt(e.target.value) }))}
                      />
                      <div className="text-sm text-gray-500 mt-1">
                        {formatCurrency(newTeam.budget)}
                      </div>
                    </div>
                    
                    <Button onClick={createTeam} disabled={teams.length >= 8}>
                      Crear Equipo
                    </Button>
                  </div>
                  
                  <div>
                    <h3 className="font-semibold mb-3">Equipos Creados</h3>
                    <div className="space-y-2">
                      {teams.map(team => (
                        <div key={team.id} className="flex items-center gap-3 p-3 border rounded">
                          <div 
                            className="w-4 h-4 rounded"
                            style={{ backgroundColor: team.colors.primary }}
                          />
                          <div 
                            className="w-4 h-4 rounded"
                            style={{ backgroundColor: team.colors.secondary }}
                          />
                          <span className="font-medium">{team.name}</span>
                          <span className="text-sm text-gray-500 ml-auto">
                            {formatCurrency(team.budget)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
                
                {teams.length === 8 && (
                  <div className="mt-6">
                    <Button onClick={startDraft} size="lg" className="w-full">
                      Comenzar Fichajes
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>

            {players.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Jugadores Disponibles</CardTitle>
                </CardHeader>
                <CardContent>
                  <Tabs defaultValue="PORTERO">
                    <TabsList className="grid w-full grid-cols-4">
                      <TabsTrigger value="PORTERO">Porteros</TabsTrigger>
                      <TabsTrigger value="DEFENSA">Defensas</TabsTrigger>
                      <TabsTrigger value="MEDIO">Medios</TabsTrigger>
                      <TabsTrigger value="DELANTERO">Delanteros</TabsTrigger>
                    </TabsList>
                    
                    {['PORTERO', 'DEFENSA', 'MEDIO', 'DELANTERO'].map(position => (
                      <TabsContent key={position} value={position} className="mt-6">
                        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                          {players
                            .filter(player => player.position === position)
                            .map(player => (
                              <PlayerCard 
                                key={player.id}
                                player={player}
                                canEdit={true}
                                onEdit={setEditingPlayer}
                                gamePhase="setup"
                              />
                            ))}
                        </div>
                      </TabsContent>
                    ))}
                  </Tabs>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {currentView === 'draft' && gameState && gameState.current_phase === 'draft' && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Fase de Fichajes</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="mb-4">
                  <p className="text-sm text-gray-600">
                    Turno actual: <strong>{
                      gameState.draft_order && gameState.current_team_turn !== undefined 
                        ? teams.find(t => t.id === gameState.draft_order[gameState.current_team_turn])?.name || 'Equipo desconocido'
                        : 'Cargando...'
                    }</strong>
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    Los equipos pueden fichar hasta 10 jugadores. La liga puede empezar con mínimo 7 jugadores por equipo.
                  </p>
                </div>
                
                <div className="grid lg:grid-cols-3 gap-6">
                  <div className="lg:col-span-2">
                    <h3 className="font-semibold mb-4">Jugadores Disponibles</h3>
                    <Tabs defaultValue="PORTERO">
                      <TabsList className="grid w-full grid-cols-4">
                        <TabsTrigger value="PORTERO">Porteros</TabsTrigger>
                        <TabsTrigger value="DEFENSA">Defensas</TabsTrigger>
                        <TabsTrigger value="MEDIO">Medios</TabsTrigger>
                        <TabsTrigger value="DELANTERO">Delanteros</TabsTrigger>
                      </TabsList>
                      
                      {['PORTERO', 'DEFENSA', 'MEDIO', 'DELANTERO'].map(position => (
                        <TabsContent key={position} value={position} className="mt-4">
                          <div className="grid md:grid-cols-2 gap-4 max-h-96 overflow-y-auto">
                            {players
                              .filter(player => player.position === position && !player.team_id)
                              .map(player => (
                                <PlayerCard 
                                  key={player.id}
                                  player={player}
                                  onDraft={draftPlayer}
                                  currentTeam={
                                    gameState.draft_order && gameState.current_team_turn !== undefined 
                                      ? teams.find(t => t.id === gameState.draft_order[gameState.current_team_turn])
                                      : null
                                  }
                                  gamePhase="draft"
                                />
                              ))}
                          </div>
                        </TabsContent>
                      ))}
                    </Tabs>
                  </div>
                  
                  <div>
                    <div className="flex gap-2 mb-4">
                      <Button 
                        onClick={() => skipTurn(
                          gameState.draft_order && gameState.current_team_turn !== undefined 
                            ? gameState.draft_order[gameState.current_team_turn]
                            : null
                        )}
                        variant="outline"
                        disabled={!gameState.draft_order || gameState.current_team_turn === undefined}
                      >
                        Pasar Turno
                      </Button>
                    </div>
                    
                    <h3 className="font-semibold mb-4">Estado de Equipos</h3>
                    <div className="space-y-3">
                      {teams.map((team, index) => {
                        const isCurrentTurn = gameState.draft_order && 
                          gameState.current_team_turn !== undefined &&
                          gameState.draft_order[gameState.current_team_turn] === team.id;
                        
                        return (
                          <Card key={team.id} className={isCurrentTurn ? 'ring-2 ring-blue-500' : ''}>
                            <CardContent className="p-3">
                              <div className="flex items-center gap-2 mb-2">
                                <div 
                                  className="w-3 h-3 rounded"
                                  style={{ backgroundColor: team.colors.primary }}
                                />
                                <span className="font-medium text-sm">{team.name}</span>
                                {isCurrentTurn && (
                                  <Badge className="text-xs">Su turno</Badge>
                                )}
                              </div>
                              <div className="text-xs text-gray-600">
                                <div>Jugadores: {team.players?.length || 0}/10</div>
                                <div>Presupuesto: {formatCurrency(team.budget)}</div>
                                {(team.players?.length || 0) >= 7 && (
                                  <div className="text-green-600 font-medium">✓ Listo para liga</div>
                                )}
                              </div>
                            </CardContent>
                          </Card>
                        );
                      })}
                    </div>
                    
                    <Button 
                      onClick={startLeague} 
                      className="w-full mt-4"
                      disabled={!canStartLeague()}
                    >
                      {canStartLeague() ? 'Comenzar Liga' : `Equipos necesitan 7+ jugadores`}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {currentView === 'league' && gameState && (gameState.current_phase === 'league' || gameState.current_phase === 'pre_match' || gameState.current_phase === 'match') && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Liga - Jornada {gameState.current_round}</CardTitle>
              </CardHeader>
              <CardContent>
                {gameState.current_phase === 'pre_match' && gameState.lineup_selection_phase && (
                  <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <h3 className="font-semibold text-blue-800 mb-2">Fase de Selección de Alineaciones</h3>
                    <p className="text-sm text-blue-600">
                      Turno actual: <strong>{teams.find(t => t.id === (teams[gameState.current_team_turn] || {}).id)?.name || 'Cargando...'}</strong>
                    </p>
                    <p className="text-xs text-blue-500 mt-1">
                      Cada equipo debe seleccionar formación y 7 jugadores para el próximo partido.
                    </p>
                  </div>
                )}
                
                <div className="grid lg:grid-cols-2 gap-6">
                  <div>
                    <h3 className="font-semibold mb-4">Clasificación</h3>
                    <Card>
                      <CardContent className="p-0">
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead className="bg-gray-50">
                              <tr>
                                <th className="px-3 py-2 text-left">Pos</th>
                                <th className="px-3 py-2 text-left">Equipo</th>
                                <th className="px-3 py-2 text-center">PJ</th>
                                <th className="px-3 py-2 text-center">Pts</th>
                                <th className="px-3 py-2 text-center">GF</th>
                                <th className="px-3 py-2 text-center">GC</th>
                                <th className="px-3 py-2 text-center">DG</th>
                              </tr>
                            </thead>
                            <tbody>
                              {standings.map((team, index) => (
                                <tr key={team.team_id} className={index < 4 ? 'bg-green-50' : index >= standings.length - 2 ? 'bg-red-50' : ''}>
                                  <td className="px-3 py-2 font-medium">{team.position}</td>
                                  <td className="px-3 py-2">{team.team_name}</td>
                                  <td className="px-3 py-2 text-center">{team.matches_played}</td>
                                  <td className="px-3 py-2 text-center font-bold">{team.points}</td>
                                  <td className="px-3 py-2 text-center">{team.goals_for}</td>
                                  <td className="px-3 py-2 text-center">{team.goals_against}</td>
                                  <td className="px-3 py-2 text-center">{team.goal_difference > 0 ? '+' : ''}{team.goal_difference}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                  
                  <div>
                    <h3 className="font-semibold mb-4">Partidos Jornada {gameState.current_round}</h3>
                    <Card>
                      <CardContent className="p-4">
                        <div className="space-y-3">
                          {roundMatches.map((match, index) => {
                            const homeTeam = teams.find(t => t.id === match.home_team_id);
                            const awayTeam = teams.find(t => t.id === match.away_team_id);
                            return (
                              <div key={match.id} className="flex justify-between items-center p-3 border rounded">
                                <div className="flex items-center gap-2">
                                  <span className="font-medium">{homeTeam?.name || 'Equipo'}</span>
                                  {match.played && (
                                    <span className="text-lg font-bold">{match.home_score}</span>
                                  )}
                                </div>
                                <span className="text-gray-500">vs</span>
                                <div className="flex items-center gap-2">
                                  {match.played && (
                                    <span className="text-lg font-bold">{match.away_score}</span>
                                  )}
                                  <span className="font-medium">{awayTeam?.name || 'Equipo'}</span>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </div>

                {gameState.current_phase === 'pre_match' && gameState.lineup_selection_phase && (
                  <div className="mt-6">
                    <LineupSelectionInterface 
                      gameState={gameState}
                      teams={teams}
                      players={players}
                      formations={formations}
                      selectedFormation={selectedFormation}
                      setSelectedFormation={setSelectedFormation}
                      selectedPlayers={selectedPlayers}
                      setSelectedPlayers={setSelectedPlayers}
                      onSelectLineup={selectLineup}
                      onSkipTurn={skipLineupTurn}
                    />
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </main>

      {editingPlayer && (
        <PlayerEditModal 
          player={editingPlayer}
          onSave={updatePlayer}
          onClose={() => setEditingPlayer(null)}
        />
      )}
    </div>
  );
}

export default App;