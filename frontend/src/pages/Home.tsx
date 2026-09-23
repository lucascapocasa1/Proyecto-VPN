import { useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { seasonsApi, clubsApi, standingsApi, statisticsApi } from "../api";
import type { SeasonList, Club, Standing, TopScorer } from "../types";
import Loading from "../components/ui/Loading";
import ErrorMessage from "../components/ui/ErrorMessage";
import SectionHeader from "../components/ui/SectionHeader";

export default function Home() {
  const [seasons, setSeasons] = useState<SeasonList[]>([]);
  const [clubs, setClubs] = useState<Club[]>([]);
  const [standings, setStandings] = useState<Standing[]>([]);
  const [topScorers, setTopScorers] = useState<TopScorer[]>([]);
  const [topAssists, setTopAssists] = useState<{ player_id: number; nickname: string; assists: number }[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const fetchData = () => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setError(null);
    Promise.all([seasonsApi.list(), clubsApi.list()])
      .then(([seasonsRes, clubsRes]) => {
        if (controller.signal.aborted) return;
        const allSeasons = seasonsRes.data.results;
        setSeasons(allSeasons);
        setClubs(clubsRes.data.results.slice(0, 6));

        const featured =
          allSeasons.find((s) => s.status === "ACTIVE") ||
          allSeasons.find((s) => s.status === "FINISHED") ||
          allSeasons[0];
        if (!featured) return;

        return Promise.all([
          standingsApi.list({ season: featured.id, page_size: 100 }),
          statisticsApi.topScorers({ season_id: featured.id, limit: 5 }),
          statisticsApi.topAssists({ season_id: featured.id, limit: 5 }),
        ]).then(([standingsRes, scorersRes, assistsRes]) => {
          if (controller.signal.aborted) return;
          setStandings(standingsRes.data.results || standingsRes.data);
          setTopScorers(scorersRes.data);
          setTopAssists(assistsRes.data);
        });
      })
      .catch(() => {
        if (!controller.signal.aborted) setError("Error al cargar datos");
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
  };

  useEffect(() => {
    fetchData();
    return () => abortRef.current?.abort();
  }, []);

  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} onRetry={fetchData} />;

  const featuredSeason =
    seasons.find((s) => s.status === "ACTIVE") ||
    seasons.find((s) => s.status === "FINISHED") ||
    seasons[0];
  const upcomingSeason = seasons.find((s) => s.status === "UPCOMING");

  const heroLabel = !featuredSeason
    ? "Competicion destacada"
    : featuredSeason.status === "ACTIVE"
    ? "Competicion en juego"
    : featuredSeason.status === "FINISHED"
    ? `${featuredSeason.name} finalizada`
    : "Proxima competicion";

  const heroBadge = !featuredSeason
    ? ""
    : featuredSeason.status === "ACTIVE"
    ? "En juego"
    : featuredSeason.status === "FINISHED"
    ? "Finalizada"
    : "Proxima";

  return (
    <div className="home">
      <section className="hero">
        <h1 className="heading-hero">EA FC Clubes Pro</h1>
        <p className="hero-subtitle">
          Plataforma de gestion de ligas competitivas de Clubes Pro
        </p>
      </section>

      {featuredSeason && (
        <Link
          to={`/standings/${featuredSeason.id}`}
          className="home-hero-banner card-accent"
          style={{ textDecoration: "none", color: "inherit", display: "flex" }}
        >
          <div className="home-hero-info">
            <span className="text-label">{heroLabel}</span>
            <h2>
              {featuredSeason.league_name} — {featuredSeason.name}
            </h2>
            <div className="home-hero-meta">
              <span className={`badge ${featuredSeason.status === "FINISHED" ? "badge-muted" : "badge-green"}`}>
                {heroBadge}
              </span>
              {featuredSeason.game_name && (
                <span className="badge badge-muted">{featuredSeason.game_name}</span>
              )}
            </div>
          </div>
          <div className="home-hero-stats">
            <div className="home-hero-stat">
              <div className="home-hero-stat-value">{standings.length}</div>
              <div className="home-hero-stat-label">Clubes</div>
            </div>
            <div className="home-hero-stat">
              <div className="home-hero-stat-value">
                {Math.round(standings.reduce((acc, s) => acc + s.played, 0) / 2)}
              </div>
              <div className="home-hero-stat-label">Partidos</div>
            </div>
          </div>
        </Link>
      )}

      <div className="home-columns">
        <div>
          <SectionHeader title="Tabla de posiciones" linkTo={featuredSeason ? `/standings/${featuredSeason.id}` : "/seasons"} linkText="Ver completa" />
          {standings.length > 0 ? (
            <div className="top-list">
              {standings.slice(0, 8).map((s, i) => (
                <Link
                  key={s.id}
                  to={`/clubs/${s.club_season}`}
                  className="top-item"
                >
                  <span className="top-position">{i + 1}</span>
                  <span className="top-info">
                    <span className="top-name">{s.club_name}</span>
                  </span>
                  <span className="top-value">
                    {s.points}
                    <span className="top-value-label">pts</span>
                  </span>
                </Link>
              ))}
            </div>
          ) : (
            <p className="empty">No hay posiciones disponibles</p>
          )}
        </div>

        <div>
          <SectionHeader title="Goleadores" linkTo="/statistics" linkText="Ver ranking" />
          {topScorers.length > 0 ? (
            <div className="top-list">
              {topScorers.map((s, i) => (
                <Link
                  key={s.player_id}
                  to={`/players/${s.player_id}`}
                  className="top-item"
                >
                  <span className="top-position">{i + 1}</span>
                  <div className="top-avatar">{s.nickname.charAt(0).toUpperCase()}</div>
                  <span className="top-info">
                    <span className="top-name">{s.nickname}</span>
                  </span>
                  <span className="top-value">
                    {s.goals}
                    <span className="top-value-label">goles</span>
                  </span>
                </Link>
              ))}
            </div>
          ) : (
            <p className="empty">No hay goleadores registrados</p>
          )}
        </div>
      </div>

      <div className="home-columns">
        <div>
          <SectionHeader title="Asistencias" linkTo="/statistics" linkText="Ver ranking" />
          {topAssists.length > 0 ? (
            <div className="top-list">
              {topAssists.map((s, i) => (
                <Link
                  key={s.player_id}
                  to={`/players/${s.player_id}`}
                  className="top-item"
                >
                  <span className="top-position">{i + 1}</span>
                  <div className="top-avatar">{s.nickname.charAt(0).toUpperCase()}</div>
                  <span className="top-info">
                    <span className="top-name">{s.nickname}</span>
                  </span>
                  <span className="top-value">
                    {s.assists}
                    <span className="top-value-label">asist.</span>
                  </span>
                </Link>
              ))}
            </div>
          ) : (
            <p className="empty">No hay asistencias registradas</p>
          )}
        </div>

        <div>
          <SectionHeader title="Clubes" linkTo="/clubs" linkText="Ver todos" />
          <div className="card-grid" style={{ gridTemplateColumns: "1fr 1fr" }}>
            {clubs.map((club) => (
              <Link
                key={club.id}
                to={`/clubs/${club.id}`}
                className="club-card"
              >
                <div className="club-logo">
                  {club.logo ? (
                    <img src={club.logo} alt={club.name} />
                  ) : (
                    <span>{club.short_name.charAt(0)}</span>
                  )}
                </div>
                <div className="club-info">
                  <span className="club-name">{club.name}</span>
                  <span className="club-country">{club.country_name}</span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>

      {upcomingSeason && (
        <SectionHeader
          title="Proxima temporada"
          linkTo={`/standings/${upcomingSeason.id}`}
          linkText="Ver"
        />
      )}
      {upcomingSeason && (
        <Link
          to={`/standings/${upcomingSeason.id}`}
          className="card card-accent"
          style={{ textDecoration: "none", color: "inherit", display: "block" }}
        >
          <h3>{upcomingSeason.name}</h3>
          <p>{upcomingSeason.league_name}</p>
          <div style={{ marginTop: "var(--space-2)" }}>
            <span className="badge badge-accent">Proxima</span>
          </div>
        </Link>
      )}
    </div>
  );
}
