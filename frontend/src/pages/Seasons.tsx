import { useState, useEffect, useRef } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { seasonsApi, leaguesApi } from "../api";
import type { SeasonList, League } from "../types";
import Loading from "../components/ui/Loading";
import ErrorMessage from "../components/ui/ErrorMessage";
import SearchBar from "../components/ui/SearchBar";
import { useCanEdit } from "../hooks/useCanEdit";

const STATUS_BADGES: Record<string, string> = {
  ACTIVE: "badge-green",
  FINISHED: "badge-muted",
  UPCOMING: "badge-accent",
};

const STATUS_LABELS: Record<string, string> = {
  ACTIVE: "En juego",
  FINISHED: "Finalizada",
  UPCOMING: "Proxima",
};

export default function Seasons() {
  const [searchParams] = useSearchParams();
  const leagueFilter = searchParams.get("league");
  const canEdit = useCanEdit();

  const [seasons, setSeasons] = useState<SeasonList[]>([]);
  const [leagues, setLeagues] = useState<League[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const abortRef = useRef<AbortController | null>(null);

  const updateSeason = async (season: SeasonList, patch: Partial<SeasonList>) => {
    try {
      const res = await seasonsApi.update(season.id, patch);
      setSeasons((prev) =>
        prev.map((s) =>
          s.id === season.id
            ? {
                ...s,
                name: res.data.name,
                status: res.data.status,
              }
            : s
        )
      );
    } catch {
      setError("Error al actualizar temporada");
    }
  };

  const fetchData = () => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setError(null);
    Promise.all([
      seasonsApi.list(),
      leaguesApi.list(),
    ])
      .then(([seasonsRes, leaguesRes]) => {
        if (controller.signal.aborted) return;
        setSeasons(seasonsRes.data.results);
        setLeagues(leaguesRes.data.results || leaguesRes.data);
      })
      .catch((err) => {
        if (err?.name !== "CanceledError" && err?.code !== "ERR_CANCELED") {
          setError("Error al cargar temporadas");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
  };

  useEffect(() => {
    fetchData();
    return () => abortRef.current?.abort();
  }, []);

  let filtered = seasons;
  if (leagueFilter) {
    filtered = filtered.filter((s) => String(s.league) === leagueFilter);
  }
  if (search) {
    filtered = filtered.filter((s) =>
      s.name.toLowerCase().includes(search.toLowerCase()) ||
      s.league_name.toLowerCase().includes(search.toLowerCase())
    );
  }

  const leagueName = leagueFilter
    ? leagues.find((l) => String(l.id) === leagueFilter)?.name
    : null;

  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} onRetry={fetchData} />;

  return (
    <div>
      <div className="page-header">
        <h1 className="heading-page">
          {leagueName ? `Temporadas de ${leagueName}` : "Temporadas"}
        </h1>
      </div>

      <SearchBar value={search} onChange={setSearch} placeholder="Buscar temporada..." />

      <div className="card-grid">
        {filtered.map((season) => (
          <div key={season.id} className="card">
            <h3>
              <Link to={`/standings/${season.id}`} style={{ color: "inherit" }}>
                {season.name}
              </Link>
            </h3>
            <p>{season.league_name}</p>
            <div
              style={{
                display: "flex",
                gap: "var(--space-2)",
                marginTop: "var(--space-2)",
                flexWrap: "wrap",
              }}
            >
              <span className={`badge ${STATUS_BADGES[season.status] || "badge-muted"}`}>
                {STATUS_LABELS[season.status] || season.status}
              </span>
              {season.game_name && (
                <span className="badge badge-muted">{season.game_name}</span>
              )}
            </div>
            {canEdit && (
              <div className="season-edit">
                <select
                  className="filter-select"
                  value={season.status}
                  onChange={(e) =>
                    updateSeason(season, { status: e.target.value as SeasonList["status"] })
                  }
                >
                  <option value="ACTIVE">En juego</option>
                  <option value="FINISHED">Finalizada</option>
                  <option value="UPCOMING">Proxima</option>
                </select>
                <input
                  type="text"
                  className="season-name-input"
                  defaultValue={season.name}
                  aria-label="Nombre de temporada"
                  onKeyDown={(e) => {
                    if (e.key === "Enter") (e.target as HTMLInputElement).blur();
                  }}
                  onBlur={(e) => {
                    const value = e.target.value.trim();
                    if (value && value !== season.name) {
                      updateSeason(season, { name: value });
                    }
                  }}
                />
              </div>
            )}
          </div>
        ))}
      </div>

      {filtered.length === 0 && <p className="empty">No se encontraron temporadas</p>}
    </div>
  );
}
