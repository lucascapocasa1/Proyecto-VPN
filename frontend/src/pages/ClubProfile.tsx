import { useState, useEffect, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import { clubsApi, standingsApi } from "../api";
import type { ClubDetail, Standing } from "../types";
import Loading from "../components/ui/Loading";
import ErrorMessage from "../components/ui/ErrorMessage";
import Breadcrumb from "../components/ui/Breadcrumb";
import CountryFlag from "../components/ui/CountryFlag";

const TITLE_ICONS: Record<string, string> = {
  CHAMPION: "\uD83C\uDFC6",
  RUNNER_UP: "\uD83E\uDD48",
  PLAYOFF_WINNER: "\u2B50",
  PROMOTION_WINNER: "\u2B06\uFE0F",
};

const STATUS_LABELS: Record<string, string> = {
  ACTIVE: "Activa",
  RELEGATED: "Descendido",
  PROMOTED: "Ascendido",
  WITHDRAWN: "Retirado",
};

export default function ClubProfile() {
  const { id } = useParams<{ id: string }>();
  const [club, setClub] = useState<ClubDetail | null>(null);
  const [standings, setStandings] = useState<Standing[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const fetchData = () => {
    if (!id) return;
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setError(null);
    clubsApi
      .get(Number(id))
      .then((res) => {
        if (controller.signal.aborted) return;
        setClub(res.data);
        standingsApi.list().then((standingsRes) => {
          if (controller.signal.aborted) return;
          const allStandings = standingsRes.data.results || standingsRes.data;
          setStandings(
            allStandings.filter((s: Standing) =>
              res.data.seasons?.some((cs: { id: number }) => cs.id === s.club_season)
            )
          );
        });
      })
      .catch((err) => {
        if (err?.name !== "CanceledError" && err?.code !== "ERR_CANCELED") {
          setError("Error al cargar club");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
  };

  useEffect(() => {
    fetchData();
    return () => abortRef.current?.abort();
  }, [id]);

  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} onRetry={fetchData} />;
  if (!club) return <p className="empty">Club no encontrado</p>;

  const currentSeason = club.seasons?.find((s) => s.status === "ACTIVE");
  const currentStanding = standings.find(
    (s) => currentSeason && s.club_season === currentSeason.id
  );

  return (
    <div>
      <Breadcrumb
        items={[
          { label: "Clubes", to: "/clubs" },
          { label: club.name },
        ]}
      />

      <div className="profile-header">
        <div className="profile-avatar" style={{ borderRadius: "var(--radius)" }}>
          {club.logo ? (
            <img
              src={club.logo}
              alt={club.name}
              style={{ width: "100%", height: "100%", objectFit: "cover", borderRadius: "inherit" }}
            />
          ) : (
            <span>{club.short_name}</span>
          )}
        </div>
        <div className="profile-info">
          <h1>{club.name}</h1>
          <div className="profile-meta">
            <span className="badge badge-muted">
              <CountryFlag code={club.country_name} size="sm" /> {club.country_name}
            </span>
            {currentSeason && (
              <span className="badge badge-accent">{currentSeason.division_name}</span>
            )}
            {currentStanding && (
              <span className="badge badge-gold">
                Posición #{currentStanding.position} · {currentStanding.points} pts
              </span>
            )}
          </div>
        </div>
      </div>

      {currentStanding && (
        <div className="profile-section">
          <h2>Estadísticas de temporada actual</h2>
          <div className="stats-grid">
            <div className="stat-card">
              <span className="stat-value">{currentStanding.played}</span>
              <span className="stat-label">PJ</span>
            </div>
            <div className="stat-card">
              <span className="stat-value green">{currentStanding.won}</span>
              <span className="stat-label">Ganados</span>
            </div>
            <div className="stat-card">
              <span className="stat-value gold">{currentStanding.drawn}</span>
              <span className="stat-label">Empates</span>
            </div>
            <div className="stat-card">
              <span className="stat-value red">{currentStanding.lost}</span>
              <span className="stat-label">Perdidos</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">{currentStanding.goals_for}</span>
              <span className="stat-label">GF</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">{currentStanding.goals_against}</span>
              <span className="stat-label">GC</span>
            </div>
            <div className="stat-card">
              <span className="stat-value accent">
                {currentStanding.goal_difference > 0 ? "+" : ""}
                {currentStanding.goal_difference}
              </span>
              <span className="stat-label">DG</span>
            </div>
            <div className="stat-card">
              <span className="stat-value accent">{currentStanding.points}</span>
              <span className="stat-label">PTS</span>
            </div>
          </div>
        </div>
      )}

      {club.titles && club.titles.length > 0 && (
        <div className="profile-section">
          <h2>Títulos</h2>
          <div className="titles-list">
            {club.titles.map((t) => (
              <div key={t.id} className="title-item">
                <span className="title-icon">{TITLE_ICONS[t.title_type] || "\uD83C\uDFC5"}</span>
                <span className="title-name">{t.name}</span>
                <span className="title-season">{t.season_name}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {club.seasons && club.seasons.length > 0 && (
        <div className="profile-section">
          <h2>Participaciones</h2>
          <div className="seasons-list">
            {club.seasons.map((cs) => (
              <Link
                key={cs.id}
                to={`/standings/${cs.season}`}
                className="season-item"
              >
                <span className="season-name">{cs.season_name}</span>
                <div className="season-meta">
                  <span className="season-division">{cs.division_name}</span>
                  <span className={`badge ${
                    cs.status === "ACTIVE" ? "badge-green" :
                    cs.status === "PROMOTED" ? "badge-green" :
                    cs.status === "RELEGATED" ? "badge-red" : "badge-muted"
                  }`}>
                    {STATUS_LABELS[cs.status] || cs.status}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
