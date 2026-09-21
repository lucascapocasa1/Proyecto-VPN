import { useState, useEffect, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { standingsApi, seasonsApi } from "../api";
import type { Standing, Season, SeasonList } from "../types";
import StandingsTable from "../components/ui/StandingsTable";
import Loading from "../components/ui/Loading";
import ErrorMessage from "../components/ui/ErrorMessage";
import { useAuth } from "../context/AuthContext";

export default function Standings() {
  const { seasonId, divisionId } = useParams<{ seasonId: string; divisionId: string }>();
  const [standings, setStandings] = useState<Standing[]>([]);
  const [season, setSeason] = useState<Season | null>(null);
  const [allSeasons, setAllSeasons] = useState<SeasonList[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [recalculating, setRecalculating] = useState(false);
  const { user } = useAuth();

  const canRecalculate = user?.role === "SUPERADMIN" || user?.role === "ADMIN_LIGA";

  const fetchData = useCallback(() => {
    if (!seasonId) {
      seasonsApi.list().then((res) => {
        setAllSeasons(res.data.results);
        setLoading(false);
      }).catch(() => setError("Error al cargar temporadas")).finally(() => setLoading(false));
      return;
    }
    setLoading(true);
    setError(null);
    Promise.all([
      seasonsApi.get(Number(seasonId)),
      standingsApi.list({ season: Number(seasonId), division: divisionId ? Number(divisionId) : undefined }),
    ]).then(([seasonRes, standingsRes]) => {
      setSeason(seasonRes.data);
      setStandings(standingsRes.data.results);
    }).catch(() => setError("Error al cargar datos")).finally(() => setLoading(false));
  }, [seasonId, divisionId]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleRecalculate = async () => {
    if (!seasonId) return;
    setRecalculating(true);
    try {
      await standingsApi.recalculate(Number(seasonId), divisionId ? Number(divisionId) : undefined);
      fetchData();
    } catch {
      setError("Error al recalcular posiciones");
    } finally {
      setRecalculating(false);
    }
  };

  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} onRetry={fetchData} />;

  if (!seasonId) {
    return (
      <div className="standings-page">
        <h1>Tabla de Posiciones</h1>
        <p className="empty">Selecciona una temporada para ver la tabla de posiciones</p>
        <div className="card-grid">
          {allSeasons.map((s) => (
            <Link key={s.id} to={`/standings/${s.id}`} className="card">
              <h3>{s.name}</h3>
              <p>{s.league_name}</p>
              <span className="badge">{s.status}</span>
            </Link>
          ))}
        </div>
        {allSeasons.length === 0 && <p className="empty">No hay temporadas disponibles</p>}
      </div>
    );
  }

  if (!season) return <ErrorMessage message="Temporada no encontrada" />;

  return (
    <div className="standings-page">
      <div className="page-header">
        <h1>Tabla de Posiciones</h1>
        <div className="breadcrumbs">
          <Link to="/seasons">{season.league_name}</Link>
          <span>/</span>
          <span>{season.name}</span>
        </div>
      </div>

      {season.divisions.length > 0 && (
        <div className="division-tabs">
          {season.divisions.map((div) => (
            <Link
              key={div.id}
              to={`/standings/${seasonId}/${div.id}`}
              className={`tab ${(!divisionId && div.order === 1) || Number(divisionId) === div.id ? "active" : ""}`}
            >
              {div.name}
            </Link>
          ))}
        </div>
      )}

      {canRecalculate && (
        <div className="page-actions">
          <button
            onClick={handleRecalculate}
            className="btn btn-primary"
            disabled={recalculating}
          >
            {recalculating ? "Recalculando..." : "Recalcular Tabla"}
          </button>
        </div>
      )}

      {standings.length > 0 ? (
        <StandingsTable standings={standings} />
      ) : (
        <p className="empty">No hay posiciones calculadas para esta division</p>
      )}
    </div>
  );
}
