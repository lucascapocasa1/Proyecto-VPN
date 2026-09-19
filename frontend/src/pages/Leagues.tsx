import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { leaguesApi } from "../api";
import type { League } from "../types";
import Loading from "../components/ui/Loading";
import ErrorMessage from "../components/ui/ErrorMessage";

export default function Leagues() {
  const [leagues, setLeagues] = useState<League[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = () => {
    setLoading(true);
    setError(null);
    leaguesApi.list()
      .then((res) => setLeagues(res.data.results))
      .catch(() => setError("Error al cargar ligas"))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, []);

  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} onRetry={fetchData} />;

  return (
    <div className="list-page">
      <h1>Ligas</h1>
      <div className="card-grid">
        {leagues.map((league) => (
          <Link key={league.id} to={`/seasons?league=${league.id}`} className="card">
            <h3>{league.name}</h3>
            <p>{league.country_name}</p>
          </Link>
        ))}
      </div>
      {leagues.length === 0 && <p className="empty">No hay ligas registradas</p>}
    </div>
  );
}
