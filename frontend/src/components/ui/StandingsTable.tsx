import { Link } from "react-router-dom";
import type { Standing } from "../../types";

const ZONE_CLASSES: Record<string, string> = {
  "CAMPEÓN": "zone-campeon",
  "REDUCIDO": "zone-reducido",
  "PROMOCIÓN": "zone-promocion",
  "DESCENSO": "zone-descenso",
};

const ZONE_DIVIDER_CLASSES: Record<string, string> = {
  "CAMPEÓN": "zone-divider-campeon",
  "REDUCIDO": "zone-divider-reducido",
  "PROMOCIÓN": "zone-divider-promocion",
  "DESCENSO": "zone-divider-descenso",
};

const ZONE_LABELS: Record<string, string> = {
  "CAMPEÓN": "Zona Campeón",
  "REDUCIDO": "Zona Reducido",
  "PROMOCIÓN": "Zona Promoción",
  "DESCENSO": "Zona Descenso",
};

interface StandingsTableProps {
  standings: Standing[];
  showZone?: boolean;
}

export default function StandingsTable({ standings, showZone = true }: StandingsTableProps) {
  const grouped: { zone: string | null; items: Standing[] }[] = [];

  if (showZone) {
    let currentZone: string | null = null;
    let currentGroup: Standing[] = [];

    for (const s of standings) {
      if (s.zone !== currentZone) {
        if (currentGroup.length > 0) {
          grouped.push({ zone: currentZone, items: currentGroup });
        }
        currentZone = s.zone || null;
        currentGroup = [s];
      } else {
        currentGroup.push(s);
      }
    }
    if (currentGroup.length > 0) {
      grouped.push({ zone: currentZone, items: currentGroup });
    }
  } else {
    grouped.push({ zone: null, items: standings });
  }

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
            {showZone && <th className="col-zone">Zona</th>}
          </tr>
        </thead>
        <tbody>
          {grouped.map((group, gi) => (
            <Fragment key={gi}>
              {group.zone && (
                <tr>
                  <td colSpan={showZone ? 11 : 10}>
                    <div className={`zone-divider ${ZONE_DIVIDER_CLASSES[group.zone] || ""}`}>
                      {ZONE_LABELS[group.zone] || group.zone}
                    </div>
                  </td>
                </tr>
              )}
              {group.items.map((s) => {
                const zoneClass = s.zone ? ZONE_CLASSES[s.zone] || "" : "";
                return (
                  <tr key={s.id} className={showZone ? `zone-row ${zoneClass}` : ""}>
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
                    {showZone && (
                      <td className="col-zone">
                        {s.zone && (
                          <span className={`zone-badge badge ${ZONE_CLASSES[s.zone] ? `badge-${s.zone === "CAMPEÓN" ? "gold" : s.zone === "REDUCIDO" ? "accent" : s.zone === "PROMOCIÓN" ? "green" : "red"}` : "badge-muted"}`}>
                            {s.zone}
                          </span>
                        )}
                      </td>
                    )}
                  </tr>
                );
              })}
            </Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}

import { Fragment } from "react";
