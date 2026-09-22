import { Link } from "react-router-dom";
import type { Standing } from "../../types";

interface StandingsTableProps {
  standings: Standing[];
}

export default function StandingsTable({ standings }: StandingsTableProps) {
  return (
    <div className="table-container">
      <table className="table">
        <thead>
          <tr>
            <th className="col-pos">#</th>
            <th className="col-club">Club</th>
            <th className="col-num">PJ</th>
            <th className="col-num">G</th>
            <th className="col-num">E</th>
            <th className="col-num">P</th>
            <th className="col-num">GF</th>
            <th className="col-num">GC</th>
            <th className="col-num">DG</th>
            <th className="col-num">PTS</th>
          </tr>
        </thead>
        <tbody>
          {standings.map((s) => (
            <tr key={s.id}>
              <td className="col-pos">{s.position}</td>
              <td className="col-club">
                <Link to={`/clubs/${s.club_season}`} style={{ color: "inherit" }}>
                  {s.club_name}
                </Link>
              </td>
              <td className="col-num">{s.played}</td>
              <td className="col-num">{s.won}</td>
              <td className="col-num">{s.drawn}</td>
              <td className="col-num">{s.lost}</td>
              <td className="col-num">{s.goals_for}</td>
              <td className="col-num">{s.goals_against}</td>
              <td className="col-num">
                {s.goal_difference > 0 ? `+${s.goal_difference}` : s.goal_difference}
              </td>
              <td className="col-num pts">{s.points}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
