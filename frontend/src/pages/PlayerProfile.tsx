import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { playersApi, statisticsApi } from "../api";
import type { PlayerDetail } from "../types";

export default function PlayerProfile() {
  const { id } = useParams<{ id: string }>();
  const [player, setPlayer] = useState<PlayerDetail | null>(null);
  const [stats, setStats] = useState<Record<string, number> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    Promise.all([
      playersApi.get(Number(id)),
      statisticsApi.player(Number(id)),
    ]).then(([playerRes, statsRes]) => {
      setPlayer(playerRes.data);
      setStats(statsRes.data.stats);
    }).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="loading">Cargando...</div>;
  if (!player) return <div className="error">Jugador no encontrado</div>;

  const currentClub = player.club_history.find((h) => h.is_current);
  const pastClubs = player.club_history.filter((h) => !h.is_current);

  return (
    <div className="player-profile">
      <div className="profile-header">
        <div className="player-avatar large">
          {player.nickname.charAt(0).toUpperCase()}
        </div>
        <div className="profile-info">
          <h1>{player.nickname}</h1>
          <div className="profile-meta">
            {player.platform && <span className="badge">{player.platform}</span>}
            {player.country_name && <span className="badge">{player.country_name}</span>}
          </div>
        </div>
      </div>

      {currentClub && (
        <section className="profile-section">
          <h2>Club Actual</h2>
          <Link to={`/clubs/0`} className="current-club">
            {currentClub.club_name} — {currentClub.division_name}
          </Link>
        </section>
      )}

      {stats && (
        <section className="profile-section">
          <h2>Estadisticas</h2>
          <div className="stats-grid">
            <div className="stat-item">
              <span className="stat-value">{stats.goals}</span>
              <span className="stat-label">Goles</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">{stats.assists}</span>
              <span className="stat-label">Asistencias</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">{stats.mvp}</span>
              <span className="stat-label">MVP</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">{stats.yellow_cards}</span>
              <span className="stat-label">Amarillas</span>
            </div>
            <div className="stat-item">
              <span className="stat-value">{stats.red_cards}</span>
              <span className="stat-label">Rojas</span>
            </div>
          </div>
        </section>
      )}

      {pastClubs.length > 0 && (
        <section className="profile-section">
          <h2>Historial de Clubes</h2>
          <div className="history-list">
            {pastClubs.map((h) => (
              <div key={h.id} className="history-item">
                <span className="history-club">{h.club_name}</span>
                <span className="history-season">{h.season_name}</span>
                <span className="history-division">{h.division_name}</span>
                <span className="history-dates">
                  {new Date(h.joined_at).toLocaleDateString("es-AR")}
                  {h.left_at && ` — ${new Date(h.left_at).toLocaleDateString("es-AR")}`}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}

      {player.identity_history.length > 0 && (
        <section className="profile-section">
          <h2>Historial de Nicknames</h2>
          <div className="history-list">
            {player.identity_history.map((h) => (
              <div key={h.id} className="history-item">
                <span className="history-nickname">{h.nickname}</span>
                <span className="history-date">
                  {new Date(h.changed_at).toLocaleDateString("es-AR")}
                </span>
                {h.reason && <span className="history-reason">{h.reason}</span>}
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
