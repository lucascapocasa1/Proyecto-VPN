import {
  BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell, Tooltip,
} from "recharts";
import type { PerformanceLeaderboardEntry } from "../../types";

const GOLD = "#f5c518";
const SILVER = "#c0c0c0";
const BRONZE = "#cd7f32";
const ACCENT = "#3b82f6";

interface Props {
  data: PerformanceLeaderboardEntry[];
  formatValue?: (v: number) => string;
}

function ChartTooltip({ active, payload, formatValue }: {
  active?: boolean;
  payload?: Array<{ payload: PerformanceLeaderboardEntry }>;
  formatValue?: (v: number) => string;
}) {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload;
  return (
    <div className="chart-tooltip">
      <strong>
        {row.nickname} — {formatValue ? formatValue(row.value) : row.value}
      </strong>
      <span>
        {row.position ? `${row.position} · ` : ""}
        {row.matches} {row.matches === 1 ? "partido" : "partidos"}
      </span>
    </div>
  );
}

export default function LeaderboardChart({ data, formatValue }: Props) {
  if (data.length === 0) return <p className="empty">No hay datos disponibles</p>;

  // El backend ya devuelve orden descendente y Recharts renderiza el primer
  // elemento arriba en el eje Y categorico: sin invertir, el #1 queda arriba.
  const rows = data;
  const rowHeight = 30;
  const height = Math.max(160, rows.length * rowHeight + 24);
  const colorOf = (i: number) => {
    if (i === 0) return GOLD;
    if (i === 1) return SILVER;
    if (i === 2) return BRONZE;
    return ACCENT;
  };

  return (
    <div style={{ width: "100%", height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={rows} layout="vertical" margin={{ top: 4, right: 48, bottom: 4, left: 8 }}>
          <XAxis type="number" hide domain={[0, "dataMax"]} />
          <YAxis
            type="category"
            dataKey="nickname"
            width={120}
            tick={{ fill: "#8b97ab", fontSize: 12 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip content={<ChartTooltip formatValue={formatValue} />} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
          <Bar dataKey="value" radius={[0, 3, 3, 0]} barSize={18} isAnimationActive={false}>
            {rows.map((_, i) => (
              <Cell key={i} fill={colorOf(i)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function formatMetricValue(v: number, metric: string): string {
  if (metric === "rating" || metric.endsWith("_km")) return v.toFixed(1);
  if (metric.endsWith("_pct")) return `${Math.round(v)}%`;
  if (Number.isInteger(v)) return String(v);
  return v.toFixed(1);
}
