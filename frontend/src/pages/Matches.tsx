import { useState, useEffect } from "react";
import { matchesApi } from "../api";
import type { Match } from "../types";
import MatchCard from "../components/ui/MatchCard";
import Loading from "../components/ui/Loading";
import ErrorMessage from "../components/ui/ErrorMessage";
export default function Matches() {
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("");

  const fetchMatches = () => {
    setLoading(true);
    setError(null);
    const params = statusFilter ? { status: statusFilter } : undefined;
    matchesApi.list(params)
      .then((res) => setMatches(res.data.results))
      .catch(() => setError("Error al cargar partidos"))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchMatches(); }, [statusFilter]);

  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} onRetry={fetchMatches} />;

  return (
    <div className="matches-page">
      <div className="page-header">
        <h1>Partidos</h1>
      </div>

      <div className="filters">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="filter-select"
        >
          <option value="">Todos los estados</option>
          <option value="SCHEDULED">Programados</option>
          <option value="IN_PROGRESS">En Juego</option>
          <option value="FINISHED">Finalizados</option>
        </select>
      </div>

      <div className="matches-grid">
        {matches.map((match) => (
          <MatchCard key={match.id} match={match} />
        ))}
      </div>
      {matches.length === 0 && <p className="empty">No hay partidos con este filtro</p>}
    </div>
  );
}
