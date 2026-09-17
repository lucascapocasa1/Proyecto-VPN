import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { statisticsApi } from "../api";
import type { TopScorer, TopAssist, TopMVP } from "../types";

type TabType = "scorers" | "assists" | "mvp";

export default function Statistics() {
  const [tab, setTab] = useState<TabType>("scorers");
  const [scorers, setScorers] = useState<TopScorer[]>([]);
  const [assists, setAssists] = useState<TopAssist[]>([]);
  const [mvp, setMvp] = useState<TopMVP[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      statisticsApi.topScorers({ limit: 20 }),
      statisticsApi.topAssists({ limit: 20 }),
      statisticsApi.topMvp({ limit: 20 }),
    ]).then(([scorersRes, assistsRes, mvpRes]) => {
      setScorers(scorersRes.data);
      setAssists(assistsRes.data);
      setMvp(mvpRes.data);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Cargando...</div>;

  return (
    <div className="statistics-page">
      <h1>Estadisticas</h1>

      <div className="tabs">
        <button className={`tab ${tab === "scorers" ? "active" : ""}`} onClick={() => setTab("scorers")}>
          Goleadores
        </button>
        <button className={`tab ${tab === "assists" ? "active" : ""}`} onClick={() => setTab("assists")}>
          Asistencias
        </button>
        <button className={`tab ${tab === "mvp" ? "active" : ""}`} onClick={() => setTab("mvp")}>
          MVP
        </button>
      </div>

      <div className="stats-list">
        {tab === "scorers" && scorers.map((s, i) => (
          <Link key={s.player_id} to={`/players/${s.player_id}`} className="stats-item">
            <span className="stats-position">{i + 1}</span>
            <span className="stats-name">{s.nickname}</span>
            <span className="stats-value">{s.goals}</span>
          </Link>
        ))}
        {tab === "assists" && assists.map((a, i) => (
          <Link key={a.player_id} to={`/players/${a.player_id}`} className="stats-item">
            <span className="stats-position">{i + 1}</span>
            <span className="stats-name">{a.nickname}</span>
            <span className="stats-value">{a.assists}</span>
          </Link>
        ))}
        {tab === "mvp" && mvp.map((m, i) => (
          <Link key={m.player_id} to={`/players/${m.player_id}`} className="stats-item">
            <span className="stats-position">{i + 1}</span>
            <span className="stats-name">{m.nickname}</span>
            <span className="stats-value">{m.mvp_count}</span>
          </Link>
        ))}
      </div>
    </div>
  );
}
