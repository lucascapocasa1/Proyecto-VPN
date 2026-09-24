import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell, Tooltip } from "recharts";
import type { PositionPerfRow } from "../../types";

const POSITION_COLORS: Record<string, string> = {
  ARQ: "#3b82f6",
  DEF: "#60a5fa",
  MED: "#7c3aed",
  DEL: "#a78bfa",
};

const METRICS: {
  key: keyof Omit<PositionPerfRow, "position" | "matches">;
  label: string;
  decimals: number;
}[] = [
  { key: "rating", label: "Rating", decimals: 1 },
  { key: "pass_accuracy_pct", label: "Prec. pases %", decimals: 0 },
  { key: "dribbles", label: "Regates / partido", decimals: 1 },
  { key: "tackles", label: "Entradas / partido", decimals: 1 },
  { key: "distance_km", label: "Distancia km", decimals: 1 },
  { key: "possession_won", label: "Posesión ganada", decimals: 1 },
];

interface Props {
  rows: PositionPerfRow[];
}

function PosTooltip({ active, payload, decimals }: {
  active?: boolean;
  payload?: Array<{ payload: { position: string; value: number | null; matches: number } }>;
  decimals: number;
}) {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload;
  return (
    <div className="chart-tooltip">
      <strong>{row.position}</strong>
      <span>
        {row.value === null ? "sin datos" : row.value.toFixed(decimals)} · {row.matches} partidos
      </span>
    </div>
  );
}

export default function PositionCompareChart({ rows }: Props) {
  if (rows.length === 0) return <p className="empty">No hay datos disponibles</p>;

  return (
    <div className="chart-position-grid">
      {METRICS.map((metric) => {
        const data = rows.map((r) => ({
          position: r.position,
          value: r[metric.key],
          matches: r.matches,
        }));
        return (
          <div key={metric.key} className="chart-card">
            <h3 className="chart-card-title">{metric.label}</h3>
            <div style={{ width: "100%", height: 170 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data} margin={{ top: 8, right: 8, bottom: 4, left: -20 }}>
                  <XAxis
                    dataKey="position"
                    tick={{ fill: "#8b97ab", fontSize: 11 }}
                    axisLine={{ stroke: "rgba(255,255,255,0.07)" }}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fill: "#6b7891", fontSize: 10 }}
                    axisLine={false}
                    tickLine={false}
                    width={44}
                    domain={[0, "auto"]}
                  />
                  <Tooltip content={<PosTooltip decimals={metric.decimals} />} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
                  <Bar dataKey="value" radius={[3, 3, 0, 0]} barSize={26} isAnimationActive={false}>
                    {data.map((d) => (
                      <Cell key={d.position} fill={POSITION_COLORS[d.position] || "#3b82f6"} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            <p className="chart-card-sub">
              {rows.map((r) => `${r.position} ${r[metric.key] === null ? "—" : r[metric.key]!.toFixed(metric.decimals)}`).join(" · ")}
            </p>
          </div>
        );
      })}
    </div>
  );
}
