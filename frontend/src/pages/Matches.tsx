import { useState, useEffect, useCallback } from "react";
import { matchesApi, seasonsApi, divisionsApi } from "../api";
import type { Match, SeasonList, Division } from "../types";
import MatchCard from "../components/ui/MatchCard";
import Loading from "../components/ui/Loading";
import ErrorMessage from "../components/ui/ErrorMessage";

export default function Matches() {
  const [matches, setMatches] = useState<Match[]>([]);
  const [seasons, setSeasons] = useState<SeasonList[]>([]);
  const [divisions, setDivisions] = useState<Division[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState("");
  const [seasonFilter, setSeasonFilter] = useState("");
  const [divisionFilter, setDivisionFilter] = useState("");

  const fetchMatches = useCallback(() => {
    setLoading(true);
    setError(null);
    const params: Record<string, string> = {};
    if (statusFilter) params.status = statusFilter;
    if (seasonFilter) params.season = seasonFilter;
    if (divisionFilter) params.division = divisionFilter;

    matchesApi
      .list(params)
      .then((res) => setMatches(res.data.results || res.data))
      .catch(() => setError("Error al cargar partidos"))
      .finally(() => setLoading(false));
  }, [statusFilter, seasonFilter, divisionFilter]);

  useEffect(() => {
    seasonsApi.list().then((res) => setSeasons(res.data.results));
  }, []);

  useEffect(() => {
    if (seasonFilter) {
      divisionsApi.list(Number(seasonFilter)).then((res) => {
        const data = res.data.results || res.data;
        setDivisions(data);
      });
    } else {
      setDivisions([]);
      setDivisionFilter("");
    }
  }, [seasonFilter]);

  useEffect(() => {
    fetchMatches();
  }, [fetchMatches]);

  const grouped = matches.reduce<Record<string, Match[]>>((acc, m) => {
    const key = m.matchday_name || "Sin jornada";
    if (!acc[key]) acc[key] = [];
    acc[key].push(m);
    return acc;
  }, {});

  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} onRetry={fetchMatches} />;

  return (
    <div>
      <div className="page-header">
        <h1 className="heading-page">Partidos</h1>
      </div>

      <div className="filters">
        <select
          className="filter-select"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="">Todos los estados</option>
          <option value="SCHEDULED">Programados</option>
          <option value="IN_PROGRESS">En Juego</option>
          <option value="FINISHED">Finalizados</option>
          <option value="POSTPONED">Aplazados</option>
          <option value="CANCELLED">Cancelados</option>
        </select>

        <select
          className="filter-select"
          value={seasonFilter}
          onChange={(e) => setSeasonFilter(e.target.value)}
        >
          <option value="">Todas las temporadas</option>
          {seasons.map((s) => (
            <option key={s.id} value={s.id}>
              {s.league_name} — {s.name}
            </option>
          ))}
        </select>

        {divisions.length > 0 && (
          <select
            className="filter-select"
            value={divisionFilter}
            onChange={(e) => setDivisionFilter(e.target.value)}
          >
            <option value="">Todas las divisiones</option>
            {divisions.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
        )}
      </div>

      {Object.keys(grouped).length === 0 ? (
        <p className="empty">No se encontraron partidos</p>
      ) : (
        Object.entries(grouped).map(([matchday, matchdayMatches]) => (
          <div key={matchday} className="matchday-group">
            <div className="matchday-header">
              <h3>{matchday}</h3>
              <span>{matchdayMatches[0]?.division_name}</span>
            </div>
            <div className="matches-grid">
              {matchdayMatches.map((match) => (
                <MatchCard key={match.id} match={match} showDivision={false} />
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
