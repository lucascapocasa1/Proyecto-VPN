import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { leaguesApi } from "../api";
import type { League } from "../types";

export default function Leagues() {
  const [leagues, setLeagues] = useState<League[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    leaguesApi.list()
      .then((res) => setLeagues(res.data.results))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Cargando...</div>;

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
    </div>
  );
}
