import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { seasonsApi } from "../api";
import type { SeasonList } from "../types";
import Loading from "../components/ui/Loading";
import ErrorMessage from "../components/ui/ErrorMessage";

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
  const [error, setError] = useState<string | null>(null);

  const fetchData = () => {
    setLoading(true);
    setError(null);
    seasonsApi.list()
      .then((res) => setSeasons(res.data.results))
      .catch(() => setError("Error al cargar temporadas"))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, []);

  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} onRetry={fetchData} />;

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
      {seasons.length === 0 && <p className="empty">No hay temporadas registradas</p>}
    </div>
  );
}
