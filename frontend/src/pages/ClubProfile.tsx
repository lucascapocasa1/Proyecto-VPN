import { useState, useEffect, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import { clubsApi, standingsApi, seasonsApi, clubTitlesApi } from "../api";
import type { ClubDetail, Standing, SeasonList, ClubTitle } from "../types";
import Loading from "../components/ui/Loading";
import ErrorMessage from "../components/ui/ErrorMessage";
import Breadcrumb from "../components/ui/Breadcrumb";
import CountryFlag from "../components/ui/CountryFlag";
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
  const canEdit = useCanEdit();
  const [club, setClub] = useState<ClubDetail | null>(null);
  const [standings, setStandings] = useState<Standing[]>([]);
  const [seasons, setSeasons] = useState<SeasonList[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingClub, setEditingClub] = useState(false);
  const [clubDraft, setClubDraft] = useState({
    name: "",
    short_name: "",
    is_active: true,
  });
  const [titleDraft, setTitleDraft] = useState({
    season: "",
    title_type: "CHAMPION" as ClubTitle["title_type"],
    name: "",
  });
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
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

  useEffect(() => {
    if (!canEdit) return;
    seasonsApi
      .list()
      .then((res) => setSeasons(res.data.results))
      .catch(() => {});
  }, [canEdit]);

  const openClubEdit = () => {
    if (!club) return;
    setClubDraft({
      name: club.name,
      short_name: club.short_name,
      is_active: club.is_active,
    });
    setFormError(null);
    setEditingClub(true);
  };

  const saveClub = async () => {
    if (!club || !clubDraft.name.trim() || !clubDraft.short_name.trim()) return;
    setSaving(true);
    setFormError(null);
    try {
      await clubsApi.update(club.id, {
        name: clubDraft.name.trim(),
        short_name: clubDraft.short_name.trim(),
        is_active: clubDraft.is_active,
      });
      setEditingClub(false);
      setNotice("Club actualizado");
      fetchData();
    } catch (err) {
      setFormError(apiErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const addTitle = async () => {
    if (!club || !titleDraft.season || !titleDraft.name.trim()) return;
    setSaving(true);
    setFormError(null);
    setNotice(null);
    try {
      await clubTitlesApi.create({
        club: club.id,
        season: Number(titleDraft.season),
        title_type: titleDraft.title_type,
        name: titleDraft.name.trim(),
      });
      setTitleDraft({ season: "", title_type: "CHAMPION", name: "" });
      setNotice("Título agregado");
      fetchData();
    } catch (err) {
      setFormError(apiErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const deleteTitle = async (t: ClubTitle) => {
    if (!window.confirm(`¿Eliminar el título "${t.name}"?`)) return;
    setFormError(null);
    setNotice(null);
    try {
      await clubTitlesApi.delete(t.id);
      setNotice("Título eliminado");
      fetchData();
    } catch (err) {
      setFormError(apiErrorMessage(err));
    }
  };

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
            {!club.is_active && <span className="badge badge-red">Inactivo</span>}
          </div>
        </div>
        {canEdit && !editingClub && (
          <button
            className="btn btn-sm"
            onClick={openClubEdit}
            style={{ marginLeft: "auto", alignSelf: "flex-start" }}
          >
            Editar club
          </button>
        )}
      </div>

      {editingClub && (
        <div className="profile-section">
          <h2>Editar club</h2>
          <div
            className="transfer-form"
            style={{ gridTemplateColumns: "2fr 1fr auto auto auto" }}
          >
            <div className="form-group">
              <label>Nombre</label>
              <input
                type="text"
                value={clubDraft.name}
                onChange={(e) => setClubDraft({ ...clubDraft, name: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Sigla</label>
              <input
                type="text"
                value={clubDraft.short_name}
                maxLength={20}
                onChange={(e) => setClubDraft({ ...clubDraft, short_name: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Activo</label>
              <input
                type="checkbox"
                checked={clubDraft.is_active}
                onChange={(e) => setClubDraft({ ...clubDraft, is_active: e.target.checked })}
              />
            </div>
            <div className="form-group">
              <label>&nbsp;</label>
              <button
                type="button"
                className="btn btn-primary"
                onClick={saveClub}
                disabled={saving}
              >
                {saving ? "Guardando..." : "Guardar"}
              </button>
            </div>
            <div className="form-group">
              <label>&nbsp;</label>
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => setEditingClub(false)}
              >
                Cancelar
              </button>
            </div>
          </div>
          {formError && (
            <p className="error-msg" style={{ textAlign: "left" }}>
              {formError}
            </p>
          )}
        </div>
      )}

      {notice && <p className="success-msg">{notice}</p>}

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

      {(canEdit || (club.titles && club.titles.length > 0)) && (
        <div className="profile-section">
          <h2>Títulos</h2>
          {club.titles && club.titles.length > 0 && (
            <div className="titles-list">
              {club.titles.map((t) => (
                <div key={t.id} className="title-item">
                  <span className="title-icon">{TITLE_ICONS[t.title_type] || "\uD83C\uDFC5"}</span>
                  <span className="title-name">{t.name}</span>
                  <span className="title-season">{t.season_name}</span>
                  {canEdit && (
                    <button
                      className="btn btn-sm btn-ghost"
                      onClick={() => deleteTitle(t)}
                      style={{ marginLeft: "auto" }}
                    >
                      Eliminar
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
          {canEdit && (
            <div
              className="transfer-form"
              style={{
                gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
                marginTop: "var(--space-4)",
              }}
            >
              <div className="form-group">
                <label>Temporada</label>
                <select
                  value={titleDraft.season}
                  onChange={(e) => setTitleDraft({ ...titleDraft, season: e.target.value })}
                >
                  <option value="">Elegir...</option>
                  {seasons.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.league_name} — {s.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Tipo</label>
                <select
                  value={titleDraft.title_type}
                  onChange={(e) =>
                    setTitleDraft({
                      ...titleDraft,
                      title_type: e.target.value as ClubTitle["title_type"],
                    })
                  }
                >
                  <option value="CHAMPION">Campeón</option>
                  <option value="RUNNER_UP">Subcampeón</option>
                  <option value="PLAYOFF_WINNER">Ganador playoff</option>
                  <option value="PROMOTION_WINNER">Ganador ascenso</option>
                </select>
              </div>
              <div className="form-group">
                <label>Nombre</label>
                <input
                  type="text"
                  value={titleDraft.name}
                  placeholder="Campeón Liga..."
                  onChange={(e) => setTitleDraft({ ...titleDraft, name: e.target.value })}
                />
              </div>
              <button
                type="button"
                className="btn btn-primary"
                onClick={addTitle}
                disabled={saving || !titleDraft.season || !titleDraft.name.trim()}
              >
                {saving ? "Agregando..." : "Agregar"}
              </button>
            </div>
          )}
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
