import { useState, useEffect, useCallback, useRef } from "react";
import { Link } from "react-router-dom";
import { statisticsApi, seasonsApi, divisionsApi } from "../api";
import type {
  SeasonList, Division, TopScorer, TopAssist, TopMVP,
  PerformanceLeaderboardEntry, PositionPerfRow,
} from "../types";
import Loading from "../components/ui/Loading";
import ErrorMessage from "../components/ui/ErrorMessage";
import LeaderboardChart, { formatMetricValue } from "../components/charts/LeaderboardChart";
import PositionCompareChart from "../components/charts/PositionCompareChart";

type TabKey = "scorers" | "assists" | "mvp" | "perf";

const TABS: { key: TabKey; label: string; valueLabel: string }[] = [
  { key: "scorers", label: "Goleadores", valueLabel: "goles" },
  { key: "assists", label: "Asistencias", valueLabel: "asist." },
  { key: "mvp", label: "MVP", valueLabel: "MVP" },
  { key: "perf", label: "Rendimiento", valueLabel: "" },
];

const PERF_METRIC_OPTIONS = [
  { key: "rating", label: "Rating" },
  { key: "goals", label: "Goles" },
  { key: "assists", label: "Asistencias" },
  { key: "shots", label: "Tiros" },
  { key: "shot_accuracy_pct", label: "Precisión tiros %" },
  { key: "passes", label: "Pases" },
  { key: "pass_accuracy_pct", label: "Precisión pases %" },
  { key: "dribbles", label: "Regates" },
  { key: "dribble_success_pct", label: "Éxito regates %" },
  { key: "tackles", label: "Entradas" },
  { key: "tackle_success_pct", label: "Éxito entradas %" },
  { key: "offsides", label: "Offsides" },
  { key: "fouls", label: "Faltas" },
  { key: "possession_won", label: "Posesión ganada" },
  { key: "possession_lost", label: "Posesión perdida" },
  { key: "minutes_played", label: "Minutos" },
  { key: "distance_km", label: "Distancia km" },
  { key: "sprint_distance_km", label: "Sprint km" },
];

const POSITION_BADGE: Record<string, string> = {
  ARQ: "badge-arq",
  DEF: "badge-def",
  MED: "badge-med",
  DEL: "badge-del",
};

const POSITION_SHORT: Record<string, string> = {
  ARQ: "ARQ",
  DEF: "DEF",
  MED: "MED",
  DEL: "DEL",
};

interface StatEntry {
  id: number;
  name: string;
  value: number;
  position?: string | null;
  country_name?: string | null;
}

export default function Statistics() {
  const [activeTab, setActiveTab] = useState<TabKey>("scorers");
  const [scorers, setScorers] = useState<TopScorer[]>([]);
  const [assists, setAssists] = useState<TopAssist[]>([]);
  const [mvps, setMvps] = useState<TopMVP[]>([]);
  const [seasons, setSeasons] = useState<SeasonList[]>([]);
  const [divisions, setDivisions] = useState<Division[]>([]);
  const [seasonFilter, setSeasonFilter] = useState("");
  const [divisionFilter, setDivisionFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Pestaña Rendimiento (MatchPerformance)
  const [lb, setLb] = useState<PerformanceLeaderboardEntry[]>([]);
  const [posRows, setPosRows] = useState<PositionPerfRow[]>([]);
  const [metric, setMetric] = useState("rating");
  const [agg, setAgg] = useState<"avg" | "sum">("avg");
  const [minMatches, setMinMatches] = useState(3);
  const [perfLoading, setPerfLoading] = useState(false);
  const [perfError, setPerfError] = useState<string | null>(null);
  const [perfVersion, setPerfVersion] = useState(0);
  const perfAbortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    seasonsApi.list().then((res) => setSeasons(res.data.results));
  }, []);

  useEffect(() => {
    if (seasonFilter) {
      divisionsApi.list(Number(seasonFilter)).then((res) => {
        setDivisions(res.data.results || res.data);
      });
    } else {
      setDivisions([]);
      setDivisionFilter("");
    }
  }, [seasonFilter]);

  const fetchData = useCallback(() => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setError(null);
    const params: Record<string, string> = {};
    if (seasonFilter) params.season_id = seasonFilter;
    if (divisionFilter) params.division_id = divisionFilter;

    Promise.all([
      statisticsApi.topScorers({ ...params, limit: 30 }),
      statisticsApi.topAssists({ ...params, limit: 30 }),
      statisticsApi.topMvp({ ...params, limit: 30 }),
    ])
      .then(([scorersRes, assistsRes, mvpsRes]) => {
        if (controller.signal.aborted) return;
        setScorers(scorersRes.data);
        setAssists(assistsRes.data);
        setMvps(mvpsRes.data);
      })
      .catch((err) => {
        if (err?.name !== "CanceledError" && err?.code !== "ERR_CANCELED") {
          setError("Error al cargar estadisticas");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
  }, [seasonFilter, divisionFilter]);

  useEffect(() => {
    fetchData();
    return () => abortRef.current?.abort();
  }, [fetchData]);

  useEffect(() => {
    if (activeTab !== "perf") return;
    perfAbortRef.current?.abort();
    const controller = new AbortController();
    perfAbortRef.current = controller;

    setPerfLoading(true);
    setPerfError(null);
    const params: Record<string, string> = {};
    if (seasonFilter) params.season_id = seasonFilter;
    if (divisionFilter) params.division_id = divisionFilter;

    Promise.all([
      statisticsApi.performanceLeaderboard({
        ...params, metric, agg, min_matches: minMatches, limit: 10,
      }),
      statisticsApi.performanceByPosition({ ...params }),
    ])
      .then(([lbRes, posRes]) => {
        if (controller.signal.aborted) return;
        setLb(lbRes.data);
        setPosRows(posRes.data);
      })
      .catch((err) => {
        if (err?.name !== "CanceledError" && err?.code !== "ERR_CANCELED") {
          setPerfError("Error al cargar rendimiento");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setPerfLoading(false);
      });

    return () => controller.abort();
  }, [activeTab, metric, agg, minMatches, seasonFilter, divisionFilter, perfVersion]);

  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} onRetry={fetchData} />;

  const currentTab = TABS.find((t) => t.key === activeTab)!;

  const data: StatEntry[] = activeTab === "scorers"
    ? scorers.map((s) => ({
        id: s.player_id,
        name: s.nickname,
        value: s.goals,
        position: s.position,
        country_name: s.country_name,
      }))
    : activeTab === "assists"
    ? assists.map((a) => ({
        id: a.player_id,
        name: a.nickname,
        value: a.assists,
        position: a.position,
        country_name: a.country_name,
      }))
    : mvps.map((m) => ({
        id: m.player_id,
        name: m.nickname,
        value: m.mvp_count,
        position: m.position,
        country_name: m.country_name,
      }));

  return (
    <div>
      <div className="page-header">
        <h1 className="heading-page">Estadisticas</h1>
      </div>

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

        {divisions.length > 0 && (
          <select
            className="filter-select"
            value={divisionFilter}
            onChange={(e) => setDivisionFilter(e.target.value)}
          >
            <option value="">Todas las divisiones</option>
            {divisions.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
        )}
      </div>

      <div className="tabs">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            className={`tab ${activeTab === tab.key ? "active" : ""}`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "perf" ? (
        <div>
          <div className="filters" style={{ marginTop: 0 }}>
            <select
              className="filter-select"
              value={metric}
              onChange={(e) => setMetric(e.target.value)}
            >
              {PERF_METRIC_OPTIONS.map((m) => (
                <option key={m.key} value={m.key}>{m.label}</option>
              ))}
            </select>
            <select
              className="filter-select"
              value={agg}
              onChange={(e) => setAgg(e.target.value as "avg" | "sum")}
            >
              <option value="avg">Promedio por partido</option>
              <option value="sum">Total acumulado</option>
            </select>
            <select
              className="filter-select"
              value={String(minMatches)}
              onChange={(e) => setMinMatches(Number(e.target.value))}
            >
              <option value="1">1+ partidos</option>
              <option value="3">3+ partidos</option>
              <option value="5">5+ partidos</option>
              <option value="10">10+ partidos</option>
            </select>
          </div>

          {perfLoading ? (
            <Loading />
          ) : perfError ? (
            <ErrorMessage message={perfError} onRetry={() => setPerfVersion((v) => v + 1)} />
          ) : (
            <>
              <div className="chart-card">
                <h3 className="chart-card-title">
                  Top {PERF_METRIC_OPTIONS.find((m) => m.key === metric)?.label} —{" "}
                  {agg === "avg" ? "promedio" : "total"}
                </h3>
                <LeaderboardChart
                  data={lb}
                  formatValue={(v) => formatMetricValue(v, metric)}
                />
              </div>
              <h2 className="chart-section-title">Promedios por posición</h2>
              <PositionCompareChart rows={posRows} />
            </>
          )}
        </div>
      ) : data.length === 0 ? (
        <p className="empty">No hay datos disponibles</p>
      ) : (
        <div className="top-list">
          {data.map((item, i) => (
            <Link
              key={item.id}
              to={`/players/${item.id}`}
              className="top-item"
            >
              <span className="top-position">{i + 1}</span>
              <div className="top-avatar">{item.name.charAt(0).toUpperCase()}</div>
              <span className="top-info">
                <span className="top-name">{item.name}</span>
                <span className="top-subtitle">
                  {item.position && (
                    <span className={`badge ${POSITION_BADGE[item.position] || "badge-muted"}`} style={{ marginRight: 6 }}>
                      {POSITION_SHORT[item.position] || item.position}
                    </span>
                  )}
                  {item.country_name || ""}
                </span>
              </span>
              <span className="top-value">
                {item.value}
                <span className="top-value-label">{currentTab.valueLabel}</span>
              </span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
