import { useState, useEffect, useRef } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { seasonsApi, leaguesApi } from "../api";
import type { SeasonList, League } from "../types";
import Loading from "../components/ui/Loading";
import ErrorMessage from "../components/ui/ErrorMessage";
import SearchBar from "../components/ui/SearchBar";

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

  const [seasons, setSeasons] = useState<SeasonList[]>([]);
  const [leagues, setLeagues] = useState<League[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const abortRef = useRef<AbortController | null>(null);

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
          <Link
            key={season.id}
            to={`/standings/${season.id}`}
            className="card"
            style={{ textDecoration: "none", color: "inherit" }}
          >
            <h3>{season.name}</h3>
            <p>{season.league_name}</p>
            <div style={{ display: "flex", gap: "var(--space-2)", marginTop: "var(--space-2)", flexWrap: "wrap" }}>
              <span className={`badge ${STATUS_BADGES[season.status] || "badge-muted"}`}>
                {STATUS_LABELS[season.status] || season.status}
              </span>
              {season.game_name && (
                <span className="badge badge-muted">{season.game_name}</span>
              )}
            </div>
          </Link>
        ))}
      </div>

      {filtered.length === 0 && <p className="empty">No se encontraron temporadas</p>}
    </div>
  );
}
