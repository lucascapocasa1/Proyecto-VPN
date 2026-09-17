import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { seasonsApi, clubsApi, statisticsApi } from "../api";
import type { SeasonList, Club, TopScorer } from "../types";

export default function Home() {
  const [seasons, setSeasons] = useState<SeasonList[]>([]);
  const [clubs, setClubs] = useState<Club[]>([]);
  const [topScorers, setTopScorers] = useState<TopScorer[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      seasonsApi.list(),
      clubsApi.list(),
      statisticsApi.topScorers({ limit: 5 }),
    ]).then(([seasonsRes, clubsRes, scorersRes]) => {
      setSeasons(seasonsRes.data.results);
      setClubs(clubsRes.data.results.slice(0, 8));
      setTopScorers(scorersRes.data);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Cargando...</div>;

  return (
    <div className="home">
      <section className="hero">
        <h1>EA FC Clubes Pro</h1>
        <p>Plataforma de gestion de ligas de Clubes Pro</p>
      </section>

      <section className="home-section">
        <h2>Temporadas Activas</h2>
        <div className="card-grid">
          {seasons.filter(s => s.status === "ACTIVE").map((season) => (
            <Link key={season.id} to={`/seasons/${season.id}`} className="card">
              <h3>{season.name}</h3>
              <p>{season.league_name}</p>
              <span className="badge badge-active">Activa</span>
            </Link>
          ))}
          {seasons.filter(s => s.status === "ACTIVE").length === 0 && (
            <p className="empty">No hay temporadas activas</p>
          )}
        </div>
      </section>

      <section className="home-section">
        <h2>Clubes</h2>
        <div className="card-grid">
          {clubs.map((club) => (
            <Link key={club.id} to={`/clubs/${club.id}`} className="card">
              <h3>{club.name}</h3>
              <p>{club.country_name}</p>
            </Link>
          ))}
        </div>
        <Link to="/clubs" className="see-all">Ver todos los clubes</Link>
      </section>

      <section className="home-section">
        <h2>Goleadores</h2>
        <div className="top-list">
          {topScorers.map((s, i) => (
            <Link key={s.player_id} to={`/players/${s.player_id}`} className="top-item">
              <span className="top-position">{i + 1}</span>
              <span className="top-name">{s.nickname}</span>
              <span className="top-value">{s.goals} goles</span>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
