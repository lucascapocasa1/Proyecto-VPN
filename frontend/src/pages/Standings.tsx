import { useState, useEffect, useCallback, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import { standingsApi, seasonsApi } from "../api";
import type { Standing, Season, SeasonList } from "../types";
import StandingsTable from "../components/ui/StandingsTable";
import Loading from "../components/ui/Loading";
import ErrorMessage from "../components/ui/ErrorMessage";
import Breadcrumb from "../components/ui/Breadcrumb";
import { useCanEdit } from "../hooks/useCanEdit";

export default function Standings() {
  const { seasonId, divisionId } = useParams<{ seasonId: string; divisionId: string }>();
  const [standings, setStandings] = useState<Standing[]>([]);
  const [season, setSeason] = useState<Season | null>(null);
  const [allSeasons, setAllSeasons] = useState<SeasonList[]>([]);
  const [selectedDivision, setSelectedDivision] = useState<string | null>(divisionId || null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [recalculating, setRecalculating] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const canRecalculate = useCanEdit();

  const fetchSeasonData = useCallback(() => {
    if (!seasonId) {
      setLoading(true);
      seasonsApi
        .list()
        .then((res) => setAllSeasons(res.data.results))
        .catch(() => setError("Error al cargar temporadas"))
        .finally(() => setLoading(false));
      return;
    }

    setLoading(true);
    setError(null);

    seasonsApi
      .get(Number(seasonId))
      .then((seasonRes) => {
        setSeason(seasonRes.data);
        if (!selectedDivision && seasonRes.data.divisions?.length > 0) {
          setSelectedDivision(String(seasonRes.data.divisions[0].id));
        }
      })
      .catch(() => setError("Error al cargar temporada"))
      .finally(() => setLoading(false));
  }, [seasonId]);

  const fetchStandings = useCallback(() => {
    if (!seasonId || !selectedDivision) return;

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setError(null);

    standingsApi
      .list({ season: Number(seasonId), division: Number(selectedDivision) })
      .then((res) => {
        if (!controller.signal.aborted) setStandings(res.data.results || res.data);
      })
      .catch((err) => {
        if (err?.name !== "CanceledError" && err?.code !== "ERR_CANCELED") {
          setError("Error al cargar posiciones");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
  }, [seasonId, selectedDivision]);

  useEffect(() => {
    fetchSeasonData();
  }, [fetchSeasonData]);

  useEffect(() => {
    fetchStandings();
    return () => abortRef.current?.abort();
  }, [fetchStandings]);

  useEffect(() => {
    if (divisionId) setSelectedDivision(divisionId);
  }, [divisionId]);

  const handleRecalculate = async () => {
    if (!seasonId) return;
    setRecalculating(true);
    try {
      await standingsApi.recalculate(Number(seasonId), selectedDivision ? Number(selectedDivision) : undefined);
      fetchStandings();
    } catch {
      setError("Error al recalcular");
    } finally {
      setRecalculating(false);
    }
  };

  if (!seasonId) {
    if (loading) return <Loading />;
    if (error) return <ErrorMessage message={error} onRetry={fetchSeasonData} />;

    return (
      <div>
        <div className="page-header">
          <h1 className="heading-page">Seleccionar temporada</h1>
        </div>
        <div className="card-grid">
          {allSeasons.map((s) => (
            <Link
              key={s.id}
              to={`/standings/${s.id}`}
              className="card"
              style={{ textDecoration: "none", color: "inherit" }}
            >
              <h3>{s.name}</h3>
              <p>{s.league_name}</p>
              <div style={{ marginTop: "var(--space-2)" }}>
                <span className={`badge ${s.status === "FINISHED" ? "badge-muted" : s.status === "ACTIVE" ? "badge-green" : "badge-accent"}`}>
                  {s.status === "FINISHED" ? "Finalizada" : s.status === "ACTIVE" ? "En juego" : "Proxima"}
                </span>
              </div>
            </Link>
          ))}
        </div>
      </div>
    );
  }

  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} onRetry={fetchStandings} />;

  const currentDivision = season?.divisions?.find(
    (d) => String(d.id) === selectedDivision
  );

  return (
    <div>
      <Breadcrumb
        items={[
          { label: "Competiciones", to: "/seasons" },
          { label: season?.league_name || "", to: `/seasons` },
          { label: season?.name || "" },
        ]}
      />

      <div className="standings-header">
        <div className="standings-competition">
          <h2 className="heading-page">
            {season?.league_name} — {season?.name}
          </h2>
          {currentDivision && (
            <span className="badge badge-accent">{currentDivision.name}</span>
          )}
        </div>
        {canRecalculate && (
          <button
            onClick={handleRecalculate}
            className="btn btn-sm"
            disabled={recalculating}
          >
            {recalculating ? "Recalculando..." : "Recalcular"}
          </button>
        )}
      </div>

      {season?.divisions && season.divisions.length > 1 && (
        <div className="tabs">
          {season.divisions.map((d) => (
            <button
              key={d.id}
              className={`tab ${String(d.id) === selectedDivision ? "active" : ""}`}
              onClick={() => setSelectedDivision(String(d.id))}
            >
              {d.name}
            </button>
          ))}
        </div>
      )}

      {standings.length > 0 ? (
        <StandingsTable standings={standings} />
      ) : (
        <p className="empty">No hay posiciones para esta division</p>
      )}
    </div>
  );
}
