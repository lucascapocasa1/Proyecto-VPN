import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { useParams } from "react-router-dom";
import {
  matchesApi,
  matchEventsApi,
  matchPlayersApi,
  playerClubHistoryApi,
  matchPerformancesApi,
} from "../api";
import type {
  Match, MatchDetail, MatchEvent, MatchPerformance, MatchAnalyzeResult,
  PlayerClubHistory,
} from "../types";
import { PERF_FIELDS, PERF_SUMMARY_KEYS, toNum } from "../lib/performance";
import Loading from "../components/ui/Loading";
import ErrorMessage from "../components/ui/ErrorMessage";
import Breadcrumb from "../components/ui/Breadcrumb";
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

const STATUS_CONFIG: Record<string, { label: string; className: string }> = {
  SCHEDULED: { label: "Programado", className: "badge-muted" },
  IN_PROGRESS: { label: "En Juego", className: "badge-amber" },
  FINISHED: { label: "Finalizado", className: "badge-green" },
  POSTPONED: { label: "Aplazado", className: "badge-amber" },
  CANCELLED: { label: "Cancelado", className: "badge-red" },
};

const EVENT_LABELS: Record<string, string> = {
  GOAL: "Gol",
  OWN_GOAL: "Autogol",
  ASSIST: "Asistencia",
  YELLOW_CARD: "Amarilla",
  RED_CARD: "Roja",
  MVP: "MVP",
};

const EVENT_BADGES: Record<string, string> = {
  GOAL: "badge-green",
  OWN_GOAL: "badge-red",
  ASSIST: "badge-accent",
  YELLOW_CARD: "badge-amber",
  RED_CARD: "badge-red",
  MVP: "badge-gold",
};

interface EditState {
  home_goals: string;
  away_goals: string;
  status: Match["status"];
  date: string;
  time: string;
}

interface PerfRow {
  player: number;
  nickname: string;
  clubName: string;
  isHome: boolean;
  performance: MatchPerformance | null;
}

const PERF_FIELD_LABELS: Record<string, string> = Object.fromEntries(
  PERF_FIELDS.map((f) => [f.key, f.label])
);

function initialPerfDraft(pf: MatchPerformance | null): Record<string, string> {
  const draft: Record<string, string> = {};
  for (const field of PERF_FIELDS) {
    const raw = pf ? (pf as unknown as Record<string, number>)[field.key] : undefined;
    if (raw !== undefined && raw !== null) {
      draft[field.key] = String(raw);
    } else {
      draft[field.key] = field.required ? "" : "0";
    }
  }
  return draft;
}

export default function MatchDetailPage() {
  const { id } = useParams<{ id: string }>();
  const canEdit = useCanEdit();
  const [match, setMatch] = useState<MatchDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [roster, setRoster] = useState<PlayerClubHistory[]>([]);
  const [edit, setEdit] = useState<EditState>({
    home_goals: "",
    away_goals: "",
    status: "SCHEDULED",
    date: "",
    time: "",
  });
  const [evForm, setEvForm] = useState({
    match_player: "",
    event_type: "GOAL" as MatchEvent["event_type"],
    minute: "",
  });
  const [editingEventId, setEditingEventId] = useState<number | null>(null);
  const [eventDraft, setEventDraft] = useState({
    event_type: "GOAL" as MatchEvent["event_type"],
    minute: "",
  });
  const [lineupForm, setLineupForm] = useState({ pch: "", starter: false });
  const [performances, setPerformances] = useState<MatchPerformance[]>([]);
  const [perfExpanded, setPerfExpanded] = useState<number | null>(null);
  const [perfDraft, setPerfDraft] = useState<Record<string, string>>({});
  const [perfSaving, setPerfSaving] = useState(false);
  const [perfError, setPerfError] = useState<string | null>(null);
  const [ocrFiles, setOcrFiles] = useState<File[]>([]);
  const [ocrLoading, setOcrLoading] = useState(false);
  const [ocrError, setOcrError] = useState<string | null>(null);
  const [ocrResults, setOcrResults] = useState<MatchAnalyzeResult[]>([]);
  const [ocrAssign, setOcrAssign] = useState<Record<number, number | "">>({});
  const abortRef = useRef<AbortController | null>(null);

  const fetchMatch = useCallback(() => {
    if (!id) return;
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setError(null);
    matchesApi
      .get(Number(id))
      .then((res) => {
        if (controller.signal.aborted) return;
        setMatch(res.data);
        setEdit({
          home_goals: res.data.home_goals != null ? String(res.data.home_goals) : "",
          away_goals: res.data.away_goals != null ? String(res.data.away_goals) : "",
          status: res.data.status,
          date: res.data.date || "",
          time: res.data.time ? res.data.time.slice(0, 5) : "",
        });
      })
      .catch((err) => {
        if (err?.name !== "CanceledError" && err?.code !== "ERR_CANCELED") {
          setError("Error al cargar el partido");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
  }, [id]);

  useEffect(() => {
    fetchMatch();
    return () => abortRef.current?.abort();
  }, [fetchMatch]);

  const fetchPerformances = useCallback(() => {
    if (!id) return;
    matchPerformancesApi
      .list({ match: Number(id), page_size: 100 })
      .then((res) => setPerformances(res.data.results || []))
      .catch(() => setPerformances([]));
  }, [id]);

  useEffect(() => {
    fetchPerformances();
  }, [fetchPerformances]);

  useEffect(() => {
    if (!canEdit || !match) {
      setRoster([]);
      return;
    }
    Promise.all([
      playerClubHistoryApi.list({ club_season: match.home_club_season, page_size: 100 }),
      playerClubHistoryApi.list({ club_season: match.away_club_season, page_size: 100 }),
    ])
      .then(([homeRes, awayRes]) => {
        const all = [...(homeRes.data.results || []), ...(awayRes.data.results || [])];
        const seen = new Set<number>();
        const unique = all.filter((p) => {
          if (seen.has(p.player)) return false;
          seen.add(p.player);
          return true;
        });
        unique.sort((a, b) =>
          (a.player_nickname || "").localeCompare(b.player_nickname || "")
        );
        setRoster(unique);
      })
      .catch(() => setRoster([]));
  }, [canEdit, match?.id, match?.home_club_season, match?.away_club_season]);

  const saveMatch = async () => {
    if (!match) return;
    setSaving(true);
    setFormError(null);
    setNotice(null);
    try {
      await matchesApi.update(match.id, {
        home_goals: edit.home_goals === "" ? null : Number(edit.home_goals),
        away_goals: edit.away_goals === "" ? null : Number(edit.away_goals),
        status: edit.status,
        date: edit.date || null,
        time: edit.time || null,
      });
      setNotice("Partido actualizado — posiciones recalculadas");
      fetchMatch();
    } catch (err) {
      setFormError(apiErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const addEvent = async () => {
    if (!match || !evForm.match_player) return;
    setFormError(null);
    setNotice(null);
    try {
      await matchEventsApi.create({
        match: match.id,
        match_player: Number(evForm.match_player),
        event_type: evForm.event_type,
        minute: evForm.minute === "" ? undefined : Number(evForm.minute),
      });
      setEvForm({ ...evForm, minute: "" });
      setNotice("Evento agregado");
      fetchMatch();
    } catch (err) {
      setFormError(apiErrorMessage(err));
    }
  };

  const saveEvent = async () => {
    if (editingEventId == null) return;
    setFormError(null);
    try {
      await matchEventsApi.update(editingEventId, {
        event_type: eventDraft.event_type,
        minute: eventDraft.minute === "" ? null : Number(eventDraft.minute),
      });
      setEditingEventId(null);
      setNotice("Evento actualizado");
      fetchMatch();
    } catch (err) {
      setFormError(apiErrorMessage(err));
    }
  };

  const deleteEvent = async (ev: MatchEvent) => {
    if (!window.confirm(`¿Eliminar el evento de ${ev.display_name}?`)) return;
    setFormError(null);
    try {
      await matchEventsApi.delete(ev.id);
      setNotice("Evento eliminado");
      fetchMatch();
    } catch (err) {
      setFormError(apiErrorMessage(err));
    }
  };

  const addLineup = async () => {
    if (!match || !lineupForm.pch) return;
    const pch = roster.find((r) => r.id === Number(lineupForm.pch));
    if (!pch) return;
    setFormError(null);
    setNotice(null);
    try {
      await matchPlayersApi.create({
        match: match.id,
        player: pch.player,
        club_season: pch.club_season,
        display_name: pch.player_nickname,
        is_starter: lineupForm.starter,
      });
      setLineupForm({ pch: "", starter: false });
      setNotice("Jugador agregado a la alineación");
      fetchMatch();
    } catch (err) {
      setFormError(apiErrorMessage(err));
    }
  };

  const removeLineup = async (mpId: number) => {
    if (!window.confirm("¿Quitar de la alineación?")) return;
    setFormError(null);
    try {
      await matchPlayersApi.delete(mpId);
      setNotice("Jugador quitado de la alineación");
      fetchMatch();
    } catch (err) {
      setFormError(apiErrorMessage(err));
    }
  };

  const perfRows = useMemo<PerfRow[]>(() => {
    if (!match) return [];
    const byPlayer = new Map<number, PerfRow>();
    for (const mp of match.match_players) {
      if (mp.player == null) continue;
      byPlayer.set(mp.player, {
        player: mp.player,
        nickname: mp.player_nickname || mp.display_name,
        clubName: mp.club_name,
        isHome: mp.club_season === match.home_club_season,
        performance: null,
      });
    }
    for (const pch of roster) {
      if (byPlayer.has(pch.player)) continue;
      byPlayer.set(pch.player, {
        player: pch.player,
        nickname: pch.player_nickname,
        clubName: pch.club_name,
        isHome: pch.club_season === match.home_club_season,
        performance: null,
      });
    }
    for (const pf of performances) {
      if (pf.player == null) continue;
      const existing = byPlayer.get(pf.player);
      if (existing) {
        existing.performance = pf;
      } else {
        byPlayer.set(pf.player, {
          player: pf.player,
          nickname: pf.player_nickname || pf.display_name,
          clubName: pf.club_name,
          isHome: pf.club_name === match.home_club_name,
          performance: pf,
        });
      }
    }
    return Array.from(byPlayer.values());
  }, [match, roster, performances]);

  const openPerfEdit = (row: PerfRow) => {
    setPerfDraft(initialPerfDraft(row.performance));
    setPerfExpanded(row.player);
    setPerfError(null);
  };

  const savePerfRow = async (row: PerfRow) => {
    if (!match) return;
    if (perfDraft.rating == null || perfDraft.rating.trim() === "") {
      setPerfError("El rating es obligatorio");
      return;
    }
    setPerfSaving(true);
    setPerfError(null);
    try {
      const item: Record<string, number | string> = { player: row.player };
      for (const field of PERF_FIELDS) {
        item[field.key] = toNum(perfDraft[field.key] ?? "0");
      }
      await matchPerformancesApi.saveBatch(match.id, [
        item as unknown as Parameters<typeof matchPerformancesApi.saveBatch>[1][number],
      ]);
      setNotice(`Rendimiento de ${row.nickname} guardado`);
      setPerfExpanded(null);
      fetchPerformances();
      fetchMatch();
    } catch (err) {
      setPerfError(apiErrorMessage(err));
    } finally {
      setPerfSaving(false);
    }
  };

  const runOcr = async () => {
    if (!match || ocrFiles.length === 0) return;
    setOcrLoading(true);
    setOcrError(null);
    setOcrResults([]);
    setOcrAssign({});
    try {
      const res = await matchPerformancesApi.analyze(match.id, ocrFiles);
      setOcrResults(res.data.results);
      if (res.data.fallidos > 0) {
        setOcrError(`${res.data.fallidos} imagen(es) con error`);
      }
    } catch (err) {
      setOcrError(apiErrorMessage(err));
    } finally {
      setOcrLoading(false);
    }
  };

  const ocrResultPlayer = (result: MatchAnalyzeResult, index: number): number | null => {
    if (result.player != null) return result.player;
    const assigned = ocrAssign[index];
    return assigned != null && assigned !== "" ? Number(assigned) : null;
  };

  const applyOcrResult = (index: number) => {
    const result = ocrResults[index];
    const playerId = ocrResultPlayer(result, index);
    if (playerId == null) {
      setOcrError("Asigná un jugador antes de editar");
      return;
    }
    if (!perfRows.some((r) => r.player === playerId)) {
      setOcrError("El jugador detectado no está en este partido");
      return;
    }
    const stats = (result.stats || {}) as Record<string, number | null>;
    const draft: Record<string, string> = {};
    for (const field of PERF_FIELDS) {
      const v = stats[field.key];
      draft[field.key] = v != null ? String(v) : field.required ? "" : "0";
    }
    setPerfDraft(draft);
    setPerfExpanded(playerId);
    setPerfError(null);
    setOcrError(null);
  };

  const saveOcrResult = async (index: number) => {
    if (!match) return;
    const result = ocrResults[index];
    const playerId = ocrResultPlayer(result, index);
    if (playerId == null) {
      setOcrError("Asigná un jugador antes de guardar");
      return;
    }
    if (!result.stats || result.stats.rating == null) {
      setOcrError("Sin rating detectado: usá Editar para completarlo");
      return;
    }
    setPerfSaving(true);
    setOcrError(null);
    try {
      const stats = result.stats as unknown as Record<string, number | null>;
      const item: Record<string, number | string> = { player: playerId };
      for (const field of PERF_FIELDS) {
        const v = stats[field.key];
        item[field.key] = v != null ? v : 0;
      }
      await matchPerformancesApi.saveBatch(match.id, [
        item as unknown as Parameters<typeof matchPerformancesApi.saveBatch>[1][number],
      ]);
      const row = perfRows.find((r) => r.player === playerId);
      setNotice(`Rendimiento de ${row?.nickname || result.filename} guardado`);
      setOcrResults((prev) => prev.filter((_, i) => i !== index));
      fetchPerformances();
      fetchMatch();
    } catch (err) {
      setOcrError(apiErrorMessage(err));
    } finally {
      setPerfSaving(false);
    }
  };

  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} onRetry={fetchMatch} />;
  if (!match) return <p className="empty">Partido no encontrado</p>;

  const status = STATUS_CONFIG[match.status] || STATUS_CONFIG.SCHEDULED;
  const homeRoster = match.match_players.filter(
    (mp) => mp.club_season === match.home_club_season
  );
  const awayRoster = match.match_players.filter(
    (mp) => mp.club_season === match.away_club_season
  );
  const sortedEvents = [...match.events].sort(
    (a, b) => (a.minute ?? 999) - (b.minute ?? 999)
  );

  return (
    <div>
      <Breadcrumb
        items={[
          { label: "Partidos", to: "/matches" },
          { label: `${match.home_club_name} vs ${match.away_club_name}` },
        ]}
      />

      <div className="match-detail-hero">
        <div className="match-detail-meta">
          <span className={`badge ${status.className}`}>{status.label}</span>
          <span className="badge badge-accent">{match.division_name}</span>
          {match.matchday_name && (
            <span className="badge badge-muted">{match.matchday_name}</span>
          )}
          <span className="badge badge-muted">{match.season_name}</span>
        </div>
        <div className="match-detail-scoreboard">
          <div className="match-team match-home">
            <span className="match-team-name">{match.home_club_name}</span>
          </div>
          <div className="match-score">
            {match.home_goals != null || match.away_goals != null ? (
              <span className="score">
                {match.home_goals ?? 0} - {match.away_goals ?? 0}
              </span>
            ) : (
              <span className="vs">vs</span>
            )}
          </div>
          <div className="match-team match-away">
            <span className="match-team-name">{match.away_club_name}</span>
          </div>
        </div>
        <div className="match-detail-info">
          {match.date &&
            new Date(`${match.date}T00:00:00`).toLocaleDateString("es-AR")}
          {match.time ? ` · ${match.time.slice(0, 5)}` : ""}
        </div>
      </div>

      {formError && (
        <p className="error-msg" style={{ textAlign: "left" }}>
          {formError}
        </p>
      )}
      {notice && <p className="success-msg">{notice}</p>}

      {canEdit && (
        <div className="profile-section">
          <h2>Editar resultado</h2>
          <div
            className="transfer-form"
            style={{ gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))" }}
          >
            <div className="form-group">
              <label>Goles local</label>
              <input
                type="number"
                min={0}
                value={edit.home_goals}
                onChange={(e) => setEdit({ ...edit, home_goals: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Goles visitante</label>
              <input
                type="number"
                min={0}
                value={edit.away_goals}
                onChange={(e) => setEdit({ ...edit, away_goals: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Estado</label>
              <select
                value={edit.status}
                onChange={(e) =>
                  setEdit({ ...edit, status: e.target.value as Match["status"] })
                }
              >
                {Object.entries(STATUS_CONFIG).map(([value, cfg]) => (
                  <option key={value} value={value}>
                    {cfg.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Fecha</label>
              <input
                type="date"
                value={edit.date}
                onChange={(e) => setEdit({ ...edit, date: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Hora</label>
              <input
                type="time"
                value={edit.time}
                onChange={(e) => setEdit({ ...edit, time: e.target.value })}
              />
            </div>
            <button
              type="button"
              className="btn btn-primary"
              onClick={saveMatch}
              disabled={saving}
            >
              {saving ? "Guardando..." : "Guardar"}
            </button>
          </div>
        </div>
      )}

      <div className="match-detail-columns">
        <div className="profile-section">
          <h2>Alineaciones</h2>

          {canEdit && (
            <div className="transfer-form" style={{ gridTemplateColumns: "1fr auto auto" }}>
              <div className="form-group">
                <label>Agregar jugador</label>
                <select
                  value={lineupForm.pch}
                  onChange={(e) => setLineupForm({ ...lineupForm, pch: e.target.value })}
                >
                  <option value="">Elegir jugador...</option>
                  {roster.map((pch) => (
                    <option key={pch.id} value={pch.id}>
                      {pch.player_nickname} ({pch.club_name})
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Titular</label>
                <input
                  type="checkbox"
                  checked={lineupForm.starter}
                  onChange={(e) =>
                    setLineupForm({ ...lineupForm, starter: e.target.checked })
                  }
                />
              </div>
              <button
                type="button"
                className="btn btn-primary"
                onClick={addLineup}
                disabled={!lineupForm.pch}
              >
                Agregar
              </button>
            </div>
          )}

          {homeRoster.length + awayRoster.length === 0 ? (
            <p className="empty">Sin alineaciones cargadas</p>
          ) : (
            <>
              {homeRoster.length > 0 && (
                <>
                  <h3 className="lineup-club">{match.home_club_name}</h3>
                  <div className="history-list" style={{ marginBottom: "var(--space-4)" }}>
                    {homeRoster.map((mp) => (
                      <div key={mp.id} className="history-item">
                        <span className="event-player">
                          {mp.display_name}
                          {mp.is_starter && (
                            <span className="badge badge-accent" style={{ marginLeft: "var(--space-2)" }}>
                              Titular
                            </span>
                          )}
                        </span>
                        {canEdit && (
                          <div className="lineup-item-actions">
                            <button
                              className="btn btn-sm btn-ghost"
                              onClick={() => removeLineup(mp.id)}
                            >
                              Quitar
                            </button>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </>
              )}
              {awayRoster.length > 0 && (
                <>
                  <h3 className="lineup-club">{match.away_club_name}</h3>
                  <div className="history-list">
                    {awayRoster.map((mp) => (
                      <div key={mp.id} className="history-item">
                        <span className="event-player">
                          {mp.display_name}
                          {mp.is_starter && (
                            <span className="badge badge-accent" style={{ marginLeft: "var(--space-2)" }}>
                              Titular
                            </span>
                          )}
                        </span>
                        {canEdit && (
                          <div className="lineup-item-actions">
                            <button
                              className="btn btn-sm btn-ghost"
                              onClick={() => removeLineup(mp.id)}
                            >
                              Quitar
                            </button>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </>
              )}
            </>
          )}
        </div>

        <div className="profile-section">
          <h2>Eventos</h2>

          {canEdit && match.match_players.length > 0 && (
            <div
              className="transfer-form"
              style={{ gridTemplateColumns: "1.5fr 1fr auto auto" }}
            >
              <div className="form-group">
                <label>Jugador</label>
                <select
                  value={evForm.match_player}
                  onChange={(e) =>
                    setEvForm({ ...evForm, match_player: e.target.value })
                  }
                >
                  <option value="">Elegir...</option>
                  {match.match_players.map((mp) => (
                    <option key={mp.id} value={mp.id}>
                      {mp.display_name} ({mp.club_name})
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Tipo</label>
                <select
                  value={evForm.event_type}
                  onChange={(e) =>
                    setEvForm({
                      ...evForm,
                      event_type: e.target.value as MatchEvent["event_type"],
                    })
                  }
                >
                  {Object.entries(EVENT_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Minuto</label>
                <input
                  type="number"
                  min={0}
                  value={evForm.minute}
                  onChange={(e) => setEvForm({ ...evForm, minute: e.target.value })}
                />
              </div>
              <button
                type="button"
                className="btn btn-primary"
                onClick={addEvent}
                disabled={!evForm.match_player}
              >
                Agregar
              </button>
            </div>
          )}

          {sortedEvents.length === 0 ? (
            <p className="empty">Sin eventos registrados</p>
          ) : (
            <div className="history-list">
              {sortedEvents.map((ev) =>
                editingEventId === ev.id ? (
                  <div key={ev.id} className="history-item event-edit-row">
                    <select
                      value={eventDraft.event_type}
                      onChange={(e) =>
                        setEventDraft({
                          ...eventDraft,
                          event_type: e.target.value as MatchEvent["event_type"],
                        })
                      }
                    >
                      {Object.entries(EVENT_LABELS).map(([value, label]) => (
                        <option key={value} value={value}>
                          {label}
                        </option>
                      ))}
                    </select>
                    <input
                      type="number"
                      min={0}
                      value={eventDraft.minute}
                      onChange={(e) =>
                        setEventDraft({ ...eventDraft, minute: e.target.value })
                      }
                      style={{ width: 70 }}
                    />
                    <button className="btn btn-sm btn-primary" onClick={saveEvent}>
                      Guardar
                    </button>
                    <button
                      className="btn btn-sm btn-ghost"
                      onClick={() => setEditingEventId(null)}
                    >
                      Cancelar
                    </button>
                  </div>
                ) : (
                  <div key={ev.id} className="history-item">
                    <span className="event-minute">
                      {ev.minute != null ? `${ev.minute}'` : "—"}
                    </span>
                    <span className={`badge ${EVENT_BADGES[ev.event_type] || "badge-muted"}`}>
                      {EVENT_LABELS[ev.event_type] || ev.event_type}
                    </span>
                    <span className="event-player">{ev.display_name}</span>
                    <span className="event-club">{ev.club_name}</span>
                    {canEdit && (
                      <div className="event-actions">
                        <button
                          className="btn btn-sm btn-ghost"
                          onClick={() => {
                            setEditingEventId(ev.id);
                            setEventDraft({
                              event_type: ev.event_type,
                              minute: ev.minute != null ? String(ev.minute) : "",
                            });
                          }}
                        >
                          Editar
                        </button>
                        <button
                          className="btn btn-sm btn-ghost"
                          onClick={() => deleteEvent(ev)}
                        >
                          Eliminar
                        </button>
                      </div>
                    )}
                  </div>
                )
              )}
            </div>
          )}
        </div>
      </div>

      <div className="profile-section">
        <h2>Rendimiento detallado</h2>

        {!canEdit ? (
          performances.length === 0 ? (
            <p className="empty">Sin datos de rendimiento</p>
          ) : (
            <div className="history-list">
              {performances.map((pf) => (
                <div key={pf.id} className="history-item" style={{ flexWrap: "wrap", gap: "var(--space-3)" }}>
                  <span className="event-player">
                    {pf.player_nickname || pf.display_name}
                    <span className="event-club" style={{ marginLeft: "var(--space-2)" }}>
                      {pf.club_name}
                    </span>
                  </span>
                  <div className="history-chips">
                    {PERF_SUMMARY_KEYS.map((key) => (
                      <span key={key} className="stat-chip">
                        <span className="stat-chip-label">{PERF_FIELD_LABELS[key]}</span>
                        <span className="stat-chip-value">
                          {(pf as unknown as Record<string, number>)[key] ?? 0}
                        </span>
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )
        ) : perfRows.length === 0 ? (
          <p className="empty">Sin jugadores para cargar rendimiento</p>
        ) : (
          <>
            <p className="empty" style={{ marginBottom: "var(--space-3)", textAlign: "left" }}>
              Cargá las stats de cada jugador. El rating es obligatorio; el resto admite 0.
            </p>

            <div
              className="transfer-form"
              style={{
                gridTemplateColumns: "1fr auto auto",
                alignItems: "end",
                marginBottom: "var(--space-4)",
              }}
            >
              <div className="form-group">
                <label>Capturas de FIFA (máx. 30)</label>
                <input
                  type="file"
                  accept="image/*"
                  multiple
                  onChange={(e) => setOcrFiles(Array.from(e.target.files || []))}
                />
              </div>
              <div className="form-group">
                <label>&nbsp;</label>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={runOcr}
                  disabled={ocrLoading || ocrFiles.length === 0 || perfSaving}
                >
                  {ocrLoading ? "Analizando..." : `Analizar con OCR (${ocrFiles.length})`}
                </button>
              </div>
              <div className="form-group">
                <label>&nbsp;</label>
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={() => {
                    setOcrResults([]);
                    setOcrError(null);
                    setOcrFiles([]);
                  }}
                  disabled={ocrLoading || (ocrResults.length === 0 && ocrFiles.length === 0)}
                >
                  Limpiar
                </button>
              </div>
            </div>

            {ocrError && (
              <p className="error-msg" style={{ textAlign: "left" }}>
                {ocrError}
              </p>
            )}

            {ocrResults.length > 0 && (
              <div className="history-list" style={{ marginBottom: "var(--space-4)" }}>
                {ocrResults.map((result, index) => {
                  const playerId = ocrResultPlayer(result, index);
                  const row = playerId != null ? perfRows.find((r) => r.player === playerId) : undefined;
                  const stats = (result.stats || {}) as Record<string, number | null>;
                  return (
                    <div
                      key={`${result.filename}-${index}`}
                      className="history-item"
                      style={{ flexDirection: "column", alignItems: "stretch" }}
                    >
                      <div
                        style={{
                          display: "flex",
                          flexWrap: "wrap",
                          gap: "var(--space-3)",
                          alignItems: "center",
                          justifyContent: "space-between",
                        }}
                      >
                        <span className="event-player">
                          {row ? row.nickname : result.player_nickname || result.detected_name || "Sin jugador"}
                          <span className="event-club" style={{ marginLeft: "var(--space-2)" }}>
                            {result.filename}
                          </span>
                        </span>

                        {result.player == null && (
                          <select
                            value={ocrAssign[index] ?? ""}
                            onChange={(e) =>
                              setOcrAssign({
                                ...ocrAssign,
                                [index]: e.target.value === "" ? "" : Number(e.target.value),
                              })
                            }
                          >
                            <option value="">Asignar jugador...</option>
                            {perfRows.map((r) => (
                              <option key={r.player} value={r.player}>
                                {r.nickname} ({r.clubName})
                              </option>
                            ))}
                          </select>
                        )}

                        <div className="history-chips">
                          {PERF_SUMMARY_KEYS.map((key) => (
                            <span key={key} className="stat-chip">
                              <span className="stat-chip-label">{PERF_FIELD_LABELS[key]}</span>
                              <span className="stat-chip-value">
                                {stats[key] != null ? stats[key] : "—"}
                              </span>
                            </span>
                          ))}
                        </div>

                        <div style={{ display: "flex", gap: "var(--space-2)" }}>
                          <button
                            type="button"
                            className="btn btn-sm btn-ghost"
                            onClick={() => applyOcrResult(index)}
                            disabled={perfSaving}
                          >
                            Editar
                          </button>
                          <button
                            type="button"
                            className="btn btn-sm btn-primary"
                            onClick={() => saveOcrResult(index)}
                            disabled={perfSaving}
                          >
                            {perfSaving ? "Guardando..." : "Guardar"}
                          </button>
                        </div>
                      </div>

                      {(result.warnings.length > 0 || result.errors.length > 0) && (
                        <ul style={{ textAlign: "left", margin: "var(--space-2) 0 0", paddingLeft: "1.2em" }}>
                          {result.errors.map((msg, i) => (
                            <li key={`e${i}`} className="error-msg">
                              {msg}
                            </li>
                          ))}
                          {result.warnings.map((msg, i) => (
                            <li key={`w${i}`} style={{ color: "var(--text-muted, #aaa)", fontSize: "0.85em" }}>
                              {msg}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            {[
              { label: match.home_club_name, rows: perfRows.filter((r) => r.isHome) },
              { label: match.away_club_name, rows: perfRows.filter((r) => !r.isHome) },
            ].map((group) =>
              group.rows.length > 0 ? (
                <div key={group.label}>
                  <h3 className="lineup-club">{group.label}</h3>
                  <div className="history-list" style={{ marginBottom: "var(--space-4)" }}>
                    {group.rows.map((row) =>
                      perfExpanded === row.player ? (
                        <div
                          key={row.player}
                          className="history-item"
                          style={{ flexDirection: "column", alignItems: "stretch" }}
                        >
                          <div
                            className="transfer-form"
                            style={{ gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))" }}
                          >
                            {PERF_FIELDS.map((field) => (
                              <div key={field.key} className="form-group">
                                <label>
                                  {field.label}
                                  {field.required ? " *" : ""}
                                </label>
                                <input
                                  type="number"
                                  min={field.min ?? 0}
                                  max={field.max}
                                  step={field.step}
                                  value={perfDraft[field.key] ?? ""}
                                  onChange={(e) =>
                                    setPerfDraft({ ...perfDraft, [field.key]: e.target.value })
                                  }
                                />
                              </div>
                            ))}
                            <div className="form-group">
                              <label>&nbsp;</label>
                              <div style={{ display: "flex", gap: "var(--space-2)" }}>
                                <button
                                  type="button"
                                  className="btn btn-primary"
                                  onClick={() => savePerfRow(row)}
                                  disabled={perfSaving}
                                >
                                  {perfSaving ? "Guardando..." : "Guardar"}
                                </button>
                                <button
                                  type="button"
                                  className="btn btn-ghost"
                                  onClick={() => setPerfExpanded(null)}
                                  disabled={perfSaving}
                                >
                                  Cancelar
                                </button>
                              </div>
                            </div>
                          </div>
                          {perfError && (
                            <p className="error-msg" style={{ textAlign: "left" }}>
                              {perfError}
                            </p>
                          )}
                        </div>
                      ) : (
                        <div key={row.player} className="history-item" style={{ flexWrap: "wrap", gap: "var(--space-3)" }}>
                          <span className="event-player">{row.nickname}</span>
                          {row.performance ? (
                            <div className="history-chips">
                              {PERF_SUMMARY_KEYS.map((key) => (
                                <span key={key} className="stat-chip">
                                  <span className="stat-chip-label">{PERF_FIELD_LABELS[key]}</span>
                                  <span className="stat-chip-value">
                                    {(row.performance as unknown as Record<string, number>)[key] ?? 0}
                                  </span>
                                </span>
                              ))}
                            </div>
                          ) : (
                            <span className="badge badge-muted">Sin datos</span>
                          )}
                          <button
                            type="button"
                            className="btn btn-sm btn-ghost"
                            onClick={() => openPerfEdit(row)}
                          >
                            {row.performance ? "Editar" : "Cargar"}
                          </button>
                        </div>
                      )
                    )}
                  </div>
                </div>
              ) : null
            )}
          </>
        )}
      </div>
    </div>
  );
}
