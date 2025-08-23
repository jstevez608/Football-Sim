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

  useEffect(() => {
    loadGameState();
    loadPlayers();
    loadTeams();
  }, []);

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
      await axios.post(`${API}/game/init`);
      await loadGameState();
      await loadPlayers();
      setCurrentView('setup');
    } catch (error) {
      console.error('Error initializing game:', error);
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
      await axios.post(`${API}/draft/pick`, {
        team_id: teamId,
        player_id: playerId
      });
      await loadGameState();
      await loadPlayers();
      await loadTeams();
    } catch (error) {
      console.error('Error drafting player:', error);
      alert('Error al fichar jugador: ' + (error.response?.data?.detail || 'Error desconocido'));
    }
  };

  const startLeague = async () => {
    try {
      await axios.post(`${API}/league/start`);
      await loadGameState();
      setCurrentView('league');
    } catch (error) {
      console.error('Error starting league:', error);
    }
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

  const PlayerEditModal = ({ player, onSave, onClose }) => {
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

  const PlayerCard = ({ player, canEdit = false, onEdit, onDraft, currentTeam }) => (
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
        <div className="flex gap-2 mt-3">
          {canEdit && (
            <Button size="sm" variant="outline" onClick={() => onEdit(player)}>
              Editar
            </Button>
          )}
          {onDraft && currentTeam && (
            <Button 
              size="sm" 
              onClick={() => onDraft(currentTeam.id, player.id)}
              disabled={player.team_id || (currentTeam.players && currentTeam.players.length >= 10)}
            >
              Fichar
            </Button>
          )}
        </div>
        {player.team_id && (
          <Badge variant="secondary" className="mt-2">
            Fichado
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
                    {loading ? 'Inicializando...' : 'Reiniciar Juego'}
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
                    Turno actual: <strong>{teams[gameState.current_team_turn]?.name}</strong>
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
                                  currentTeam={teams[gameState.current_team_turn]}
                                />
                              ))}
                          </div>
                        </TabsContent>
                      ))}
                    </Tabs>
                  </div>
                  
                  <div>
                    <h3 className="font-semibold mb-4">Estado de Equipos</h3>
                    <div className="space-y-3">
                      {teams.map((team, index) => (
                        <Card key={team.id} className={index === gameState.current_team_turn ? 'ring-2 ring-blue-500' : ''}>
                          <CardContent className="p-3">
                            <div className="flex items-center gap-2 mb-2">
                              <div 
                                className="w-3 h-3 rounded"
                                style={{ backgroundColor: team.colors.primary }}
                              />
                              <span className="font-medium text-sm">{team.name}</span>
                            </div>
                            <div className="text-xs text-gray-600">
                              <div>Jugadores: {team.players?.length || 0}/10</div>
                              <div>Presupuesto: {formatCurrency(team.budget)}</div>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                    
                    <Button 
                      onClick={startLeague} 
                      className="w-full mt-4"
                      disabled={teams.some(team => !team.players || team.players.length === 0)}
                    >
                      Comenzar Liga
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {currentView === 'league' && gameState && gameState.current_phase === 'league' && (
          <Card>
            <CardHeader>
              <CardTitle>Liga - Jornada {gameState.current_round}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-center text-gray-600">
                Sistema de liga en desarrollo...
              </p>
            </CardContent>
          </Card>
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