import { useState, useEffect, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import { playersApi, statisticsApi, countriesApi, matchPerformancesApi } from "../api";
import type {
  PlayerDetail, Player, Country, MatchPerformance, PlayerMatchSeriesPoint,
} from "../types";
import { PERF_FIELDS } from "../lib/performance";
import Loading from "../components/ui/Loading";
import ErrorMessage from "../components/ui/ErrorMessage";
import Breadcrumb from "../components/ui/Breadcrumb";
import CountryFlag from "../components/ui/CountryFlag";
import Sparkline from "../components/charts/Sparkline";
import RatingEvolutionChart from "../components/charts/RatingEvolutionChart";
import { useCanEdit } from "../hooks/useCanEdit";

function apiErrorMessage(err: unknown): string {
  const data = (err as { response?: { data?: unknown } })?.response?.data;
  if (!data) return "Error de conexión";
  if (typeof data === "string") return data;
  const obj = data as Record<string, unknown>;
  if (typeof obj.error === "string") return obj.error;
  const first = Object.values(obj)[0];
  if (Array.isArray(first) && first.length > 0) return String(first[0]);
  if (typeof first === "string") return first;
  return "Error inesperado";
}

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
  const canEdit = useCanEdit();
  const [player, setPlayer] = useState<PlayerDetail | null>(null);
  const [stats, setStats] = useState<PlayerStats>(INITIAL_STATS);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [countries, setCountries] = useState<Country[]>([]);
  const [saving, setSaving] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [performances, setPerformances] = useState<MatchPerformance[]>([]);
  const [perfExpanded, setPerfExpanded] = useState<number | null>(null);
  const [series, setSeries] = useState<PlayerMatchSeriesPoint[]>([]);
  const [draft, setDraft] = useState({
    nickname: "",
    position: "" as Player["position"] | "",
    platform: "" as Player["platform"] | "",
    country: "",
    is_active: true,
  });
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
      matchPerformancesApi.forPlayer(Number(id), { page_size: 100 }).catch(() => ({ data: { results: [] } })),
      statisticsApi.playerMatchSeries(Number(id)).catch(() => ({ data: [] })),
    ])
      .then(([playerRes, statsRes, historyRes, perfRes, seriesRes]) => {
        if (controller.signal.aborted) return;
        setPlayer(playerRes.data);
        setPerformances(perfRes.data?.results || []);
        setSeries(
          (seriesRes.data as PlayerMatchSeriesPoint[] | undefined) || []
        );
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

  const openEdit = () => {
    if (!player) return;
    setDraft({
      nickname: player.nickname,
      position: player.position || "",
      platform: player.platform || "",
      country: player.country != null ? String(player.country) : "",
      is_active: player.is_active,
    });
    setEditError(null);
    setNotice(null);
    setEditing(true);
    if (countries.length === 0) {
      countriesApi
        .list()
        .then((res) => setCountries(res.data.results || []))
        .catch(() => {});
    }
  };

  const savePlayer = async () => {
    if (!player || !draft.nickname.trim()) return;
    setSaving(true);
    setEditError(null);
    try {
      const updated = await playersApi.update(player.id, {
        nickname: draft.nickname.trim(),
        position: draft.position || null,
        platform: draft.platform || null,
        country: draft.country ? Number(draft.country) : null,
        is_active: draft.is_active,
      });
      setPlayer((prev) => (prev ? { ...prev, ...updated.data } : prev));
      setEditing(false);
      setNotice("Jugador actualizado");
    } catch (err) {
      setEditError(apiErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} onRetry={fetchData} />;
  if (!player) return <p className="empty">Jugador no encontrado</p>;

  const currentClub = player.club_history?.find((ch) => ch.is_current);
  const historyStints = [...(player.club_history || [])].sort((a, b) => {
    const ta = new Date(a.joined_at).getTime();
    const tb = new Date(b.joined_at).getTime();
    return ta - tb;
  });
  const evoPoints = series.filter((s) => s.rating != null);
  const seriesGoals = series.map((s) => s.goals);
  const seriesAssists = series.map((s) => s.assists);
  const seriesMvp = series.map((s) => s.mvp);
  const seriesYellow = series.map((s) => s.yellow);
  const seriesRed = series.map((s) => s.red);
  const hasSpark = series.length >= 2;

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
            {!player.is_active && <span className="badge badge-red">Inactivo</span>}
          </div>
          {currentClub && (
            <div style={{ marginTop: "var(--space-3)" }}>
              <Link
                to={`/clubs/${currentClub.club}`}
                className="badge badge-accent"
                style={{ textDecoration: "none" }}
              >
                {currentClub.club_name}
              </Link>
            </div>
          )}
        </div>
        {canEdit && !editing && (
          <button
            className="btn btn-sm"
            onClick={openEdit}
            style={{ marginLeft: "auto", alignSelf: "flex-start" }}
          >
            Editar
          </button>
        )}
      </div>

      {editing && (
        <div className="profile-section">
          <h2>Editar jugador</h2>
          <div
            className="transfer-form"
            style={{ gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))" }}
          >
            <div className="form-group">
              <label>Nickname</label>
              <input
                type="text"
                value={draft.nickname}
                onChange={(e) => setDraft({ ...draft, nickname: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Posición</label>
              <select
                value={draft.position || ""}
                onChange={(e) =>
                  setDraft({ ...draft, position: e.target.value as Player["position"] | "" })
                }
              >
                <option value="">Sin posición</option>
                <option value="ARQ">Arquero</option>
                <option value="DEF">Defensor</option>
                <option value="MED">Mediocampista</option>
                <option value="DEL">Delantero</option>
              </select>
            </div>
            <div className="form-group">
              <label>Plataforma</label>
              <select
                value={draft.platform || ""}
                onChange={(e) =>
                  setDraft({ ...draft, platform: e.target.value as Player["platform"] | "" })
                }
              >
                <option value="">Sin plataforma</option>
                <option value="PLAYSTATION">PlayStation</option>
                <option value="XBOX">Xbox</option>
                <option value="PC">PC</option>
              </select>
            </div>
            <div className="form-group">
              <label>País</label>
              <select
                value={draft.country}
                onChange={(e) => setDraft({ ...draft, country: e.target.value })}
              >
                <option value="">Sin país</option>
                {countries.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Activo</label>
              <input
                type="checkbox"
                checked={draft.is_active}
                onChange={(e) => setDraft({ ...draft, is_active: e.target.checked })}
              />
            </div>
            <div className="form-group">
              <label>&nbsp;</label>
              <div style={{ display: "flex", gap: "var(--space-2)" }}>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={savePlayer}
                  disabled={saving}
                >
                  {saving ? "Guardando..." : "Guardar"}
                </button>
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={() => setEditing(false)}
                >
                  Cancelar
                </button>
              </div>
            </div>
          </div>
          {editError && (
            <p className="error-msg" style={{ textAlign: "left" }}>
              {editError}
            </p>
          )}
        </div>
      )}

      {notice && <p className="success-msg">{notice}</p>}

      <div className="profile-section">
        <h2>Estadísticas</h2>
        <div className="stats-grid">
          <div className="stat-card">
            <span className="stat-value accent">{stats.goals || 0}</span>
            <span className="stat-label">Goles</span>
            {hasSpark && <Sparkline values={seriesGoals} color="var(--accent)" />}
          </div>
          <div className="stat-card">
            <span className="stat-value green">{stats.assists || 0}</span>
            <span className="stat-label">Asistencias</span>
            {hasSpark && <Sparkline values={seriesAssists} color="var(--green)" />}
          </div>
          <div className="stat-card">
            <span className="stat-value gold">{stats.mvp_count || 0}</span>
            <span className="stat-label">MVP</span>
            {hasSpark && <Sparkline values={seriesMvp} color="var(--gold)" />}
          </div>
          <div className="stat-card">
            <span className="stat-value">{stats.matches_played || 0}</span>
            <span className="stat-label">Temporadas</span>
          </div>
          <div className="stat-card">
            <span className="stat-value gold">{stats.yellow_cards || 0}</span>
            <span className="stat-label">Amarillas</span>
            {hasSpark && <Sparkline values={seriesYellow} color="var(--amber)" />}
          </div>
          <div className="stat-card">
            <span className="stat-value red">{stats.red_cards || 0}</span>
            <span className="stat-label">Rojas</span>
            {hasSpark && <Sparkline values={seriesRed} color="var(--red)" />}
          </div>
        </div>
      </div>

      {evoPoints.length >= 2 && (
        <div className="profile-section">
          <h2>Evolución de rendimiento</h2>
          <div className="chart-card" style={{ marginBottom: 0 }}>
            <RatingEvolutionChart points={evoPoints} />
          </div>
        </div>
      )}

      {performances.length > 0 && (
        <div className="profile-section">
          <h2>Partidos y rendimiento</h2>
          <div className="history-list">
            {performances.map((pf) => (
              <div key={pf.id} className="history-item" style={{ flexDirection: "column", alignItems: "stretch" }}>
                <div
                  style={{
                    display: "flex",
                    flexWrap: "wrap",
                    gap: "var(--space-3)",
                    alignItems: "center",
                    justifyContent: "space-between",
                    cursor: "pointer",
                  }}
                  onClick={() => setPerfExpanded(perfExpanded === pf.id ? null : pf.id)}
                >
                  <span className="history-club">
                    <Link
                      to={`/matches/${pf.match}`}
                      style={{ color: "inherit" }}
                      onClick={(e) => e.stopPropagation()}
                    >
                      {pf.home_club_name} {pf.home_goals ?? "-"} - {pf.away_goals ?? "-"} {pf.away_club_name}
                    </Link>
                  </span>
                  <span className="history-context">
                    {pf.match_date
                      ? new Date(`${pf.match_date}T00:00:00`).toLocaleDateString("es-AR")
                      : ""}
                    {" · "}
                    {pf.club_name}
                  </span>
                  <div className="history-chips">
                    <span className="stat-chip">
                      <span className="stat-chip-label">Rating</span>
                      <span className="stat-chip-value">{pf.rating}</span>
                    </span>
                    <span className="stat-chip stat-chip-green">
                      <span className="stat-chip-label">G</span>
                      <span className="stat-chip-value">{pf.goals}</span>
                    </span>
                    <span className="stat-chip stat-chip-green">
                      <span className="stat-chip-label">A</span>
                      <span className="stat-chip-value">{pf.assists}</span>
                    </span>
                    <span className="stat-chip">
                      <span className="stat-chip-label">Min</span>
                      <span className="stat-chip-value">{pf.minutes_played}</span>
                    </span>
                    <span className="stat-chip">
                      <span className="stat-chip-label">Km</span>
                      <span className="stat-chip-value">{pf.distance_km}</span>
                    </span>
                  </div>
                </div>
                {perfExpanded === pf.id && (
                  <div className="history-chips" style={{ marginTop: "var(--space-3)" }}>
                    {PERF_FIELDS.map((field) => (
                      <span key={field.key} className="stat-chip">
                        <span className="stat-chip-label">{field.label}</span>
                        <span className="stat-chip-value">
                          {(pf as unknown as Record<string, number>)[field.key] ?? 0}
                        </span>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {historyStints.length > 0 && (
        <div className="profile-section">
          <h2>Historial de clubes</h2>
          <div className="history-list">
            {historyStints.map((ch) => (
              <div key={ch.id} className={`history-item ${ch.is_current ? "history-item-current" : ""}`}>
                <div className="history-main">
                  <span className="history-club">
                    <Link to={`/clubs/${ch.club}`} style={{ color: "inherit" }}>
                      {ch.club_name}
                    </Link>
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
