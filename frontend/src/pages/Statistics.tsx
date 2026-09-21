import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { statisticsApi, seasonsApi, divisionsApi, playersApi } from "../api";
import type { SeasonList, Division, TopScorer, TopAssist, TopMVP, Player } from "../types";
import Loading from "../components/ui/Loading";
import ErrorMessage from "../components/ui/ErrorMessage";

type TabKey = "scorers" | "assists" | "mvp";

const TABS: { key: TabKey; label: string; valueLabel: string }[] = [
  { key: "scorers", label: "Goleadores", valueLabel: "goles" },
  { key: "assists", label: "Asistencias", valueLabel: "asist." },
  { key: "mvp", label: "MVP", valueLabel: "MVP" },
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

interface EnrichedPlayer {
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
  const [playerCache, setPlayerCache] = useState<Map<number, Player>>(new Map());

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
        setScorers(scorersRes.data);
        setAssists(assistsRes.data);
        setMvps(mvpsRes.data);
      })
      .catch(() => setError("Error al cargar estadisticas"))
      .finally(() => setLoading(false));
  }, [seasonFilter, divisionFilter]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    const allIds = new Set<number>();
    scorers.forEach((s) => allIds.add(s.player_id));
    assists.forEach((a) => allIds.add(a.player_id));
    mvps.forEach((m) => allIds.add(m.player_id));

    const uncached = [...allIds].filter((id) => !playerCache.has(id));
    if (uncached.length === 0) return;

    uncached.slice(0, 15).forEach((id) => {
      playersApi
        .get(id)
        .then((res) => {
          setPlayerCache((prev) => new Map(prev).set(id, res.data));
        })
        .catch(() => {});
    });
  }, [scorers, assists, mvps]);

  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} onRetry={fetchData} />;

  const currentTab = TABS.find((t) => t.key === activeTab)!;

  const data: EnrichedPlayer[] = activeTab === "scorers"
    ? scorers.map((s) => {
        const p = playerCache.get(s.player_id);
        return {
          id: s.player_id,
          name: s.nickname,
          value: s.goals,
          position: p?.position,
          country_name: p?.country_name,
        };
      })
    : activeTab === "assists"
    ? assists.map((a) => {
        const p = playerCache.get(a.player_id);
        return {
          id: a.player_id,
          name: a.nickname,
          value: a.assists,
          position: p?.position,
          country_name: p?.country_name,
        };
      })
    : mvps.map((m) => {
        const p = playerCache.get(m.player_id);
        return {
          id: m.player_id,
          name: m.nickname,
          value: m.mvp_count,
          position: p?.position,
          country_name: p?.country_name,
        };
      });

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

      {data.length === 0 ? (
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
