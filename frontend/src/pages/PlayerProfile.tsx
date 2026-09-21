import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { playersApi, statisticsApi } from "../api";
import type { PlayerDetail } from "../types";
import Loading from "../components/ui/Loading";
import ErrorMessage from "../components/ui/ErrorMessage";
import Breadcrumb from "../components/ui/Breadcrumb";
import CountryFlag from "../components/ui/CountryFlag";

const POSITION_BADGE: Record<string, string> = {
  ARQ: "badge-arq",
  DEF: "badge-def",
  MED: "badge-med",
  DEL: "badge-del",
};

const POSITION_AVATAR: Record<string, string> = {
  ARQ: "pos-arq",
  DEF: "pos-def",
  MED: "pos-med",
  DEL: "pos-del",
};

const POSITION_LABELS: Record<string, string> = {
  ARQ: "Arquero",
  DEF: "Defensor",
  MED: "Mediocampista",
  DEL: "Delantero",
};

interface PlayerStats {
  goals?: number;
  assists?: number;
  mvp_count?: number;
  yellow_cards?: number;
  red_cards?: number;
  matches_played?: number;
}

export default function PlayerProfile() {
  const { id } = useParams<{ id: string }>();
  const [player, setPlayer] = useState<PlayerDetail | null>(null);
  const [stats, setStats] = useState<PlayerStats>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = () => {
    if (!id) return;
    setLoading(true);
    setError(null);

    Promise.all([
      playersApi.get(Number(id)),
      statisticsApi.player(Number(id)).catch(() => ({ data: {} })),
    ])
      .then(([playerRes, statsRes]) => {
        setPlayer(playerRes.data);
        setStats(statsRes.data);
      })
      .catch(() => setError("Error al cargar jugador"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchData();
  }, [id]);

  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} onRetry={fetchData} />;
  if (!player) return <p className="empty">Jugador no encontrado</p>;

  const currentClub = player.club_history?.find((ch) => ch.is_current);
  const pastClubs = player.club_history?.filter((ch) => !ch.is_current) || [];

  return (
    <div>
      <Breadcrumb
        items={[
          { label: "Jugadores", to: "/players" },
          { label: player.nickname },
        ]}
      />

      <div className="profile-header">
        <div className={`profile-avatar ${player.position ? POSITION_AVATAR[player.position] : ""}`}>
          {player.nickname.charAt(0).toUpperCase()}
        </div>
        <div className="profile-info">
          <h1>{player.nickname}</h1>
          <div className="profile-meta">
            {player.position && (
              <span className={`badge ${POSITION_BADGE[player.position]}`}>
                {POSITION_LABELS[player.position] || player.position}
              </span>
            )}
            {player.platform && (
              <span className="badge badge-muted">{player.platform}</span>
            )}
            {player.country_name && (
              <span className="badge badge-muted">
                <CountryFlag code={player.country_name} size="sm" /> {player.country_name}
              </span>
            )}
          </div>
          {currentClub && (
            <div style={{ marginTop: "var(--space-3)" }}>
              <Link
                to={`/clubs/${currentClub.club_season}`}
                className="badge badge-accent"
                style={{ textDecoration: "none" }}
              >
                {currentClub.club_name}
              </Link>
            </div>
          )}
        </div>
      </div>

      <div className="profile-section">
        <h2>Estadísticas</h2>
        <div className="stats-grid">
          <div className="stat-card">
            <span className="stat-value accent">{stats.goals || 0}</span>
            <span className="stat-label">Goles</span>
          </div>
          <div className="stat-card">
            <span className="stat-value green">{stats.assists || 0}</span>
            <span className="stat-label">Asistencias</span>
          </div>
          <div className="stat-card">
            <span className="stat-value gold">{stats.mvp_count || 0}</span>
            <span className="stat-label">MVP</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{stats.matches_played || 0}</span>
            <span className="stat-label">Partidos</span>
          </div>
          <div className="stat-card">
            <span className="stat-value gold">{stats.yellow_cards || 0}</span>
            <span className="stat-label">Amarillas</span>
          </div>
          <div className="stat-card">
            <span className="stat-value red">{stats.red_cards || 0}</span>
            <span className="stat-label">Rojas</span>
          </div>
        </div>
      </div>

      {pastClubs.length > 0 && (
        <div className="profile-section">
          <h2>Historial de clubes</h2>
          <div className="history-list">
            {pastClubs.map((ch) => (
              <div key={ch.id} className="history-item">
                <span className="history-club">{ch.club_name}</span>
                <span className="history-season">{ch.season_name}</span>
                <span className="history-division">{ch.division_name}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {player.identity_history && player.identity_history.length > 0 && (
        <div className="profile-section">
          <h2>Historial de nicknames</h2>
          <div className="history-list">
            {player.identity_history.map((ih) => (
              <div key={ih.id} className="history-item">
                <span className="history-nickname">{ih.nickname}</span>
                <span className="history-date">
                  {new Date(ih.changed_at).toLocaleDateString("es-AR")}
                </span>
                {ih.reason && (
                  <span className="history-reason">{ih.reason}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
