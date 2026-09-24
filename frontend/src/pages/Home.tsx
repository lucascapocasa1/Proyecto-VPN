import { useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { CalendarDays, History, ListOrdered, Target } from "lucide-react";
import { seasonsApi, standingsApi, statisticsApi, matchesApi } from "../api";
import type { SeasonList, Standing, TopScorer, Match } from "../types";
import Loading from "../components/ui/Loading";
import ErrorMessage from "../components/ui/ErrorMessage";
import SectionHeader from "../components/ui/SectionHeader";

function MatchRow({ match }: { match: Match }) {
  const finished = match.status === "FINISHED";
  const dateLabel = match.date
    ? new Date(match.date + "T00:00:00").toLocaleDateString("es-ES", {
        day: "2-digit",
        month: "short",
      })
    : "Sin fecha";

  return (
    <Link to={`/matches/${match.id}`} className="mini-match">
      <span className="mini-match-date">
        <strong>{dateLabel}</strong>
        <small>{match.time || ""}</small>
      </span>
      <span className="mini-match-teams">
        <span className="mini-match-line">
          <span className="mini-match-team">{match.home_club_name}</span>
          {finished && <span className="mini-match-score">{match.home_goals}</span>}
        </span>
        <span className="mini-match-line">
          <span className="mini-match-team">{match.away_club_name}</span>
          {finished && <span className="mini-match-score">{match.away_goals}</span>}
        </span>
      </span>
      {!finished && <span className="badge badge-accent mini-match-badge">Próximo</span>}
    </Link>
  );
}

export default function Home() {
  const [seasons, setSeasons] = useState<SeasonList[]>([]);
  const [standings, setStandings] = useState<Standing[]>([]);
  const [topScorers, setTopScorers] = useState<TopScorer[]>([]);
  const [recentMatches, setRecentMatches] = useState<Match[]>([]);
  const [nextMatches, setNextMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const fetchData = () => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setError(null);
    Promise.all([seasonsApi.list()])
      .then(([seasonsRes]) => {
        if (controller.signal.aborted) return;
        const allSeasons = seasonsRes.data.results;
        setSeasons(allSeasons);

        const featured =
          allSeasons.find((s) => s.status === "ACTIVE") ||
          allSeasons.find((s) => s.status === "FINISHED") ||
          allSeasons[0];
        if (!featured) return;

        return Promise.all([
          standingsApi.list({ season: featured.id, page_size: 100 }),
          statisticsApi.topScorers({ season_id: featured.id, limit: 5 }),
          matchesApi.list({ season: featured.id, status: "FINISHED", page_size: 50 }),
          matchesApi.list({ season: featured.id, status: "SCHEDULED", page_size: 50 }),
        ]).then(([standingsRes, scorersRes, finishedRes, scheduledRes]) => {
          if (controller.signal.aborted) return;
          setStandings(standingsRes.data.results || standingsRes.data);
          setTopScorers(scorersRes.data);

          const finished = [...finishedRes.data.results].sort((a, b) =>
            (b.date || "").localeCompare(a.date || "")
          );
          const scheduled = [...scheduledRes.data.results].sort((a, b) =>
            (a.date || "9999-12-31").localeCompare(b.date || "9999-12-31")
          );
          setRecentMatches(finished.slice(0, 5));
          setNextMatches(scheduled.slice(0, 4));
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

  const featuredMatch = recentMatches.length
    ? [...recentMatches].sort((a, b) => {
        const goalsA = (a.home_goals ?? 0) + (a.away_goals ?? 0);
        const goalsB = (b.home_goals ?? 0) + (b.away_goals ?? 0);
        return goalsB - goalsA;
      })[0]
    : undefined;

  return (
    <div className="home">
      <section className="hero">
        <h1 className="heading-hero">Virtual Pro Network</h1>
        <p className="hero-subtitle">La liga oficial de Clubes Pro de EA FC 27</p>
      </section>

      <div className="home-grid">
        <div className="home-col">
          <section className="home-panel">
            <SectionHeader
              title="Tabla de Posiciones"
              linkTo={featuredSeason ? `/standings/${featuredSeason.id}` : "/seasons"}
              linkText="Ver completa"
              icon={<ListOrdered size={14} />}
            />
            {standings.length > 0 ? (
              <div className="top-list">
                {standings.slice(0, 8).map((s, i) => (
                  <Link key={s.id} to={`/clubs/${s.club}`} className="top-item">
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
          </section>

          <section className="home-panel">
            <SectionHeader title="Últimos Resultados" linkTo="/matches" linkText="Ver todos" icon={<History size={14} />} />
            {recentMatches.length > 0 ? (
              <div className="mini-match-list">
                {recentMatches.map((m) => (
                  <MatchRow key={m.id} match={m} />
                ))}
              </div>
            ) : (
              <p className="empty">Aún no hay resultados registrados</p>
            )}
          </section>
        </div>

        <div className="home-col">
          <section className="home-panel">
            <SectionHeader title="Próximos Partidos" linkTo="/matches" linkText="Ver calendario" icon={<CalendarDays size={14} />} />
            {nextMatches.length > 0 ? (
              <div className="mini-match-list">
                {nextMatches.map((m) => (
                  <MatchRow key={m.id} match={m} />
                ))}
              </div>
            ) : (
              <p className="empty">No hay partidos programados</p>
            )}
          </section>

          <section className="home-panel">
            <SectionHeader title="Máximos Goleadores" linkTo="/statistics" linkText="Ver ranking" icon={<Target size={14} />} />
            {topScorers.length > 0 ? (
              <div className="top-list">
                {topScorers.map((s, i) => (
                  <Link key={s.player_id} to={`/players/${s.player_id}`} className="top-item">
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
          </section>

          {featuredMatch && (
            <Link to={`/matches/${featuredMatch.id}`} className="featured-match">
              <span className="text-label">Partido destacado</span>
              <div className="featured-match-body">
                <div className="featured-match-side">
                  <span className="featured-match-team">{featuredMatch.home_club_name}</span>
                  <strong className="featured-match-score">{featuredMatch.home_goals}</strong>
                </div>
                <span className="featured-match-vs">vs</span>
                <div className="featured-match-side is-away">
                  <span className="featured-match-team">{featuredMatch.away_club_name}</span>
                  <strong className="featured-match-score">{featuredMatch.away_goals}</strong>
                </div>
              </div>
              <span className="featured-match-meta">
                {featuredMatch.division_name}
                {featuredMatch.matchday_name ? ` · ${featuredMatch.matchday_name}` : ""}
              </span>
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}
