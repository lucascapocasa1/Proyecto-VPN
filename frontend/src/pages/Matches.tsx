import { useState, useEffect, useCallback } from "react";
import { matchesApi } from "../api";
import type { Match } from "../types";
import MatchCard from "../components/ui/MatchCard";
import Loading from "../components/ui/Loading";
import ErrorMessage from "../components/ui/ErrorMessage";
import Pagination from "../components/ui/Pagination";
import SearchBar from "../components/ui/SearchBar";

export default function Matches() {
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState("");

  const fetchMatches = useCallback(() => {
    setLoading(true);
    setError(null);
    const params = statusFilter ? { status: statusFilter } : undefined;
    matchesApi.list(params)
      .then((res) => {
        let filtered = res.data.results;
        if (search) {
          filtered = filtered.filter(m =>
            m.home_club_name.toLowerCase().includes(search.toLowerCase()) ||
            m.away_club_name.toLowerCase().includes(search.toLowerCase())
          );
        }
        setMatches(filtered);
        setTotalPages(Math.max(1, Math.ceil(res.data.count / 25)));
      })
      .catch(() => setError("Error al cargar partidos"))
      .finally(() => setLoading(false));
  }, [statusFilter, search]);

  useEffect(() => { fetchMatches(); }, [fetchMatches]);

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
        <SearchBar value={search} onChange={setSearch} placeholder="Buscar por club..." />
      </div>

      <div className="matches-grid">
        {matches.map((match) => (
          <MatchCard key={match.id} match={match} />
        ))}
      </div>

      <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />

      {matches.length === 0 && <p className="empty">No hay partidos con este filtro</p>}
    </div>
  );
}
