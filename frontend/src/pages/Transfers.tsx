import { useState, useEffect, useCallback, useRef } from "react";
import { Link } from "react-router-dom";
import { transfersApi, playersApi, clubSeasonsApi, seasonsApi } from "../api";
import type { Transfer, Player, ClubSeason, SeasonList } from "../types";
import Loading from "../components/ui/Loading";
import ErrorMessage from "../components/ui/ErrorMessage";
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

function todayISO(): string {
  const d = new Date();
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
}

export default function Transfers() {
  const canEdit = useCanEdit();
  const [transfers, setTransfers] = useState<Transfer[]>([]);
  const [seasons, setSeasons] = useState<SeasonList[]>([]);
  const [seasonFilter, setSeasonFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const [playerQuery, setPlayerQuery] = useState("");
  const [playerResults, setPlayerResults] = useState<Player[]>([]);
  const [selectedPlayer, setSelectedPlayer] = useState<Player | null>(null);
  const [currentClubName, setCurrentClubName] = useState<string | null>(null);
  const [destinations, setDestinations] = useState<ClubSeason[]>([]);
  const [dest, setDest] = useState("");
  const [date, setDate] = useState(todayISO());
  const [submitting, setSubmitting] = useState(false);

  const fetchTransfers = useCallback(() => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setError(null);
    const params: Record<string, string | number> = { page_size: 100 };
    if (seasonFilter) params.season = seasonFilter;

    transfersApi
      .list(params)
      .then((res) => {
        if (!controller.signal.aborted) setTransfers(res.data.results || res.data);
      })
      .catch((err) => {
        if (err?.name !== "CanceledError" && err?.code !== "ERR_CANCELED") {
          setError("Error al cargar transferencias");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
  }, [seasonFilter]);

  useEffect(() => {
    seasonsApi.list().then((res) => setSeasons(res.data.results)).catch(() => {});
    return () => abortRef.current?.abort();
  }, []);

  useEffect(() => {
    fetchTransfers();
    return () => abortRef.current?.abort();
  }, [fetchTransfers]);

  useEffect(() => {
    if (!canEdit) return;
    if (selectedPlayer && playerQuery === selectedPlayer.nickname) return;

    if (selectedPlayer) {
      setSelectedPlayer(null);
      setCurrentClubName(null);
      setDestinations([]);
      setDest("");
    }
    if (playerQuery.trim().length < 2) {
      setPlayerResults([]);
      return;
    }
    const timer = setTimeout(() => {
      playersApi
        .list({ search: playerQuery.trim(), page_size: 100 })
        .then((res) => setPlayerResults(res.data.results || []))
        .catch(() => setPlayerResults([]));
    }, 300);
    return () => clearTimeout(timer);
  }, [playerQuery, selectedPlayer, canEdit]);

  const selectPlayer = (p: Player) => {
    setSelectedPlayer(p);
    setPlayerQuery(p.nickname);
    setPlayerResults([]);
    setFormError(null);
    setCurrentClubName("Cargando...");
    setDestinations([]);
    setDest("");

    playersApi
      .get(p.id)
      .then((res) => {
        const current = res.data.club_history?.find((ch) => ch.is_current);
        if (!current) {
          setCurrentClubName("Sin club actual");
          return null;
        }
        setCurrentClubName(current.club_name);
        return clubSeasonsApi.get(current.club_season).then((csRes) =>
          clubSeasonsApi
            .list({ season: csRes.data.season, page_size: 100 })
            .then((listRes) => {
              const all = listRes.data.results || [];
              setDestinations(all.filter((cs) => cs.id !== current.club_season));
            })
        );
      })
      .catch(() => setCurrentClubName("Error al cargar jugador"));
  };

  const submit = async () => {
    if (!selectedPlayer || !dest) return;
    setSubmitting(true);
    setFormError(null);
    setNotice(null);
    try {
      await transfersApi.create({
        player: selectedPlayer.id,
        to_club_season: Number(dest),
        date,
      });
      setNotice(`Transferencia de ${selectedPlayer.nickname} registrada`);
      setSelectedPlayer(null);
      setPlayerQuery("");
      setDestinations([]);
      setDest("");
      fetchTransfers();
    } catch (err) {
      setFormError(apiErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (t: Transfer) => {
    if (
      !window.confirm(
        `¿Eliminar la transferencia de ${t.player_name}? Se revertirá al club anterior.`
      )
    ) {
      return;
    }
    setFormError(null);
    setNotice(null);
    try {
      await transfersApi.delete(t.id);
      setNotice("Transferencia eliminada");
      fetchTransfers();
    } catch (err) {
      setFormError(apiErrorMessage(err));
    }
  };

  if (loading && transfers.length === 0 && !seasonFilter && !error) return <Loading />;
  if (error && transfers.length === 0) return <ErrorMessage message={error} onRetry={fetchTransfers} />;

  return (
    <div>
      <div className="page-header">
        <h1 className="heading-page">Mercado de pases</h1>
      </div>

      {canEdit && (
        <div className="transfer-form">
          <div className="form-group" style={{ position: "relative" }}>
            <label>Jugador</label>
            <input
              type="text"
              value={playerQuery}
              onChange={(e) => setPlayerQuery(e.target.value)}
              placeholder="Buscar jugador..."
              autoComplete="off"
            />
            {playerResults.length > 0 && (
              <ul className="search-dropdown">
                {playerResults.map((p) => (
                  <li key={p.id}>
                    <button type="button" onClick={() => selectPlayer(p)}>
                      {p.nickname}
                      {p.position ? ` · ${p.position}` : ""}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="form-group">
            <label>Club actual</label>
            <div className="form-readonly">{currentClubName || "—"}</div>
          </div>

          <div className="form-group">
            <label>Destino</label>
            <select
              value={dest}
              onChange={(e) => setDest(e.target.value)}
              disabled={!destinations.length}
            >
              <option value="">
                {selectedPlayer ? "Elegir club" : "Primero elegí un jugador"}
              </option>
              {destinations.map((cs) => (
                <option key={cs.id} value={cs.id}>
                  {cs.club_name} ({cs.division_name})
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Fecha</label>
            <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
          </div>

          <button
            type="button"
            className="btn btn-primary"
            onClick={submit}
            disabled={submitting || !selectedPlayer || !dest}
          >
            {submitting ? "Registrando..." : "Registrar"}
          </button>
        </div>
      )}

      {formError && <p className="error-msg" style={{ textAlign: "left" }}>{formError}</p>}
      {notice && <p className="success-msg">{notice}</p>}

      <div className="filters">
        <select
          className="filter-select"
          value={seasonFilter}
          onChange={(e) => setSeasonFilter(e.target.value)}
        >
          <option value="">Todas las temporadas</option>
          {seasons.map((s) => (
            <option key={s.id} value={s.id}>
              {s.league_name} — {s.name}
            </option>
          ))}
        </select>
      </div>

      {loading && transfers.length > 0 ? (
        <Loading />
      ) : transfers.length === 0 ? (
        <p className="empty">No hay transferencias registradas</p>
      ) : (
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Jugador</th>
                <th>Desde</th>
                <th>Hacia</th>
                {canEdit && <th style={{ textAlign: "right" }}>Acción</th>}
              </tr>
            </thead>
            <tbody>
              {transfers.map((t) => (
                <tr key={t.id}>
                  <td>
                    {new Date(`${t.date}T00:00:00`).toLocaleDateString("es-AR")}
                  </td>
                  <td className="col-club">
                    <Link to={`/players/${t.player}`} style={{ color: "inherit" }}>
                      {t.player_name}
                    </Link>
                  </td>
                  <td>
                    {t.from_club ? (
                      <Link to={`/clubs/${t.from_club}`}>{t.from_club_name}</Link>
                    ) : (
                      "—"
                    )}{" "}
                    {t.from_division_name && (
                      <span className="badge badge-muted">{t.from_division_name}</span>
                    )}
                  </td>
                  <td>
                    <Link to={`/clubs/${t.to_club}`}>{t.to_club_name}</Link>{" "}
                    <span className="badge badge-accent">{t.to_division_name}</span>
                  </td>
                  {canEdit && (
                    <td style={{ textAlign: "right" }}>
                      <button
                        className="btn btn-sm btn-ghost"
                        onClick={() => handleDelete(t)}
                      >
                        Eliminar
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
