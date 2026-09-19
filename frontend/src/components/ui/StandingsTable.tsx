import type { Standing } from "../../types";

const ZONE_COLORS: Record<string, { bg: string; text: string; label: string }> = {
  "CAMPEÓN": { bg: "#fbbf24", text: "#78350f", label: "CAMPEÓN" },
  "REDUCIDO": { bg: "#60a5fa", text: "#1e3a5f", label: "REDUCIDO" },
  "PROMOCIÓN": { bg: "#34d399", text: "#064e3b", label: "PROMOCIÓN" },
  "DESCENSO": { bg: "#f87171", text: "#7f1d1d", label: "DESCENSO" },
};

interface StandingsTableProps {
  standings: Standing[];
  showZone?: boolean;
}

export default function StandingsTable({ standings, showZone = true }: StandingsTableProps) {
  return (
    <div className="table-container">
      <table className="table standings-table">
        <thead>
          <tr>
            <th className="col-pos">#</th>
            <th className="col-club">Club</th>
            <th className="col-num">PJ</th>
            <th className="col-num">PG</th>
            <th className="col-num">PE</th>
            <th className="col-num">PP</th>
            <th className="col-num">GF</th>
            <th className="col-num">GC</th>
            <th className="col-num">DG</th>
            <th className="col-num">PTS</th>
            {showZone && <th className="col-zone">Zona</th>}
          </tr>
        </thead>
        <tbody>
          {standings.map((s) => {
            const zone = s.zone ? ZONE_COLORS[s.zone] : null;
            return (
              <tr key={s.id}>
                <td className="col-pos">{s.position}</td>
                <td className="col-club">{s.club_name}</td>
                <td className="col-num">{s.played}</td>
                <td className="col-num">{s.won}</td>
                <td className="col-num">{s.drawn}</td>
                <td className="col-num">{s.lost}</td>
                <td className="col-num">{s.goals_for}</td>
                <td className="col-num">{s.goals_against}</td>
                <td className="col-num">{s.goal_difference > 0 ? `+${s.goal_difference}` : s.goal_difference}</td>
                <td className="col-num pts">{s.points}</td>
                {showZone && (
                  <td className="col-zone">
                    {zone && (
                      <span className="zone-badge" style={{ backgroundColor: zone.bg, color: zone.text }}>
                        {zone.label}
                      </span>
                    )}
                  </td>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
