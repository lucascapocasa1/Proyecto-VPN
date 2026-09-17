import { useState, useEffect } from "react";
import { playersApi } from "../api";
import type { Player } from "../types";
import PlayerCard from "../components/ui/PlayerCard";

export default function Players() {
  const [players, setPlayers] = useState<Player[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    playersApi.list()
      .then((res) => setPlayers(res.data.results))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Cargando...</div>;

  return (
    <div className="list-page">
      <h1>Jugadores</h1>
      <div className="card-grid">
        {players.map((player) => (
          <PlayerCard key={player.id} player={player} />
        ))}
      </div>
    </div>
  );
}
