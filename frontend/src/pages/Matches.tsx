import { useState, useEffect } from "react";
import { matchesApi } from "../api";
import type { Match } from "../types";
import MatchCard from "../components/ui/MatchCard";

export default function Matches() {
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    matchesApi.list()
      .then((res) => setMatches(res.data.results))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Cargando...</div>;

  return (
    <div className="matches-page">
      <h1>Partidos</h1>
      <div className="matches-grid">
        {matches.map((match) => (
          <MatchCard key={match.id} match={match} />
        ))}
      </div>
      {matches.length === 0 && <p className="empty">No hay partidos</p>}
    </div>
  );
}
