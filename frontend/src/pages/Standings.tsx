import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { standingsApi, seasonsApi } from "../api";
import type { Standing, Season } from "../types";
import StandingsTable from "../components/ui/StandingsTable";

export default function Standings() {
  const { seasonId, divisionId } = useParams<{ seasonId: string; divisionId: string }>();
  const [standings, setStandings] = useState<Standing[]>([]);
  const [season, setSeason] = useState<Season | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!seasonId) return;
    setLoading(true);
    Promise.all([
      seasonsApi.get(Number(seasonId)),
      standingsApi.list({ season: Number(seasonId), division: divisionId ? Number(divisionId) : undefined }),
    ]).then(([seasonRes, standingsRes]) => {
      setSeason(seasonRes.data);
      setStandings(standingsRes.data.results);
    }).finally(() => setLoading(false));
  }, [seasonId, divisionId]);

  if (loading) return <div className="loading">Cargando...</div>;
  if (!season) return <div className="error">Temporada no encontrada</div>;

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

      {standings.length > 0 ? (
        <StandingsTable standings={standings} />
      ) : (
        <p className="empty">No hay posiciones calculadas para esta division</p>
      )}
    </div>
  );
}
