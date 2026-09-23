import { useState, useEffect, useRef } from "react";
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
  own_goals?: number;
}

const INITIAL_STATS: PlayerStats = {
  goals: 0,
  assists: 0,
  mvp_count: 0,
  yellow_cards: 0,
  red_cards: 0,
  matches_played: 0,
  own_goals: 0,
};

export default function PlayerProfile() {
  const { id } = useParams<{ id: string }>();
  const [player, setPlayer] = useState<PlayerDetail | null>(null);
  const [stats, setStats] = useState<PlayerStats>(INITIAL_STATS);
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

    Promise.all([
      playersApi.get(Number(id)),
      statisticsApi.player(Number(id)).catch(() => ({ data: {} })),
      statisticsApi.playerHistory(Number(id)).catch(() => ({ data: { history: [] } })),
    ])
      .then(([playerRes, statsRes, historyRes]) => {
        if (controller.signal.aborted) return;
        setPlayer(playerRes.data);
        const raw = statsRes.data?.stats || statsRes.data || {};
        const historySeasons = historyRes.data?.history || [];
        const matchesPlayed = historySeasons.length || raw.matches_played || 0;
        setStats({
          goals: raw.goals || 0,
          assists: raw.assists || 0,
          mvp_count: raw.mvp || raw.mvp_count || 0,
          yellow_cards: raw.yellow_cards || 0,
          red_cards: raw.red_cards || 0,
          matches_played: matchesPlayed,
          own_goals: raw.own_goals || 0,
        });
      })
      .catch((err) => {
        if (err?.name !== "CanceledError" && err?.code !== "ERR_CANCELED") {
          setError("Error al cargar jugador");
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
  if (!player) return <p className="empty">Jugador no encontrado</p>;

  const currentClub = player.club_history?.find((ch) => ch.is_current);
  const historyStints = [...(player.club_history || [])].sort((a, b) => {
    const ta = new Date(a.joined_at).getTime();
    const tb = new Date(b.joined_at).getTime();
    return ta - tb;
  });

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
            <span className="stat-label">Temporadas</span>
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

      {historyStints.length > 0 && (
        <div className="profile-section">
          <h2>Historial de clubes</h2>
          <div className="history-list">
            {historyStints.map((ch) => (
              <div key={ch.id} className={`history-item ${ch.is_current ? "history-item-current" : ""}`}>
                <div className="history-main">
                  <span className="history-club">
                    {ch.club_name}
                    {ch.is_current && <span className="history-current-tag">Actual</span>}
                  </span>
                  <span className="history-context">
                    {ch.game_name ? `${ch.game_name} · ` : ""}
                    {ch.season_name} · {ch.division_name}
                  </span>
                </div>
                <div className="history-chips">
                  <span className="stat-chip">
                    <span className="stat-chip-label">PJ</span>
                    <span className="stat-chip-value">{ch.stats?.matches_played ?? 0}</span>
                  </span>
                  <span className="stat-chip stat-chip-green">
                    <span className="stat-chip-label">G</span>
                    <span className="stat-chip-value">{ch.stats?.goals ?? 0}</span>
                  </span>
                  <span className="stat-chip stat-chip-green">
                    <span className="stat-chip-label">A</span>
                    <span className="stat-chip-value">{ch.stats?.assists ?? 0}</span>
                  </span>
                  <span className="stat-chip stat-chip-gold">
                    <span className="stat-chip-label">MVP</span>
                    <span className="stat-chip-value">{ch.stats?.mvp ?? 0}</span>
                  </span>
                  <span className="stat-chip stat-chip-amber">
                    <span className="stat-chip-label">TA</span>
                    <span className="stat-chip-value">{ch.stats?.yellow_cards ?? 0}</span>
                  </span>
                  <span className="stat-chip stat-chip-red">
                    <span className="stat-chip-label">TR</span>
                    <span className="stat-chip-value">{ch.stats?.red_cards ?? 0}</span>
                  </span>
                </div>
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
