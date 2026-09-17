import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { seasonsApi } from "../api";
import type { SeasonList } from "../types";

const STATUS_LABELS: Record<string, string> = {
  UPCOMING: "Proxima",
  ACTIVE: "Activa",
  FINISHED: "Finalizada",
};

const STATUS_COLORS: Record<string, string> = {
  UPCOMING: "#94a3b8",
  ACTIVE: "#22c55e",
  FINISHED: "#6b7280",
};

export default function Seasons() {
  const [seasons, setSeasons] = useState<SeasonList[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    seasonsApi.list()
      .then((res) => setSeasons(res.data.results))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Cargando...</div>;

  return (
    <div className="list-page">
      <h1>Temporadas</h1>
      <div className="card-grid">
        {seasons.map((season) => (
          <Link key={season.id} to={`/standings/${season.id}`} className="card">
            <h3>{season.name}</h3>
            <p>{season.league_name}</p>
            <span className="badge" style={{ backgroundColor: STATUS_COLORS[season.status] }}>
              {STATUS_LABELS[season.status]}
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
}
