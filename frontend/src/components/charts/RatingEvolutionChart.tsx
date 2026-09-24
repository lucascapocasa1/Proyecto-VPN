import {
  AreaChart, Area, XAxis, YAxis, ResponsiveContainer, Tooltip, ReferenceLine,
} from "recharts";
import type { PlayerMatchSeriesPoint } from "../../types";

interface Props {
  points: PlayerMatchSeriesPoint[];
}

function fmtDate(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(`${iso}T00:00:00`);
  return d.toLocaleDateString("es-AR", { day: "2-digit", month: "2-digit" });
}

function EvoTooltip({ active, payload }: {
  active?: boolean;
  payload?: Array<{ payload: PlayerMatchSeriesPoint & { label: string } }>;
}) {
  if (!active || !payload?.length) return null;
  const p = payload[0].payload;
  const score =
    p.home_goals != null && p.away_goals != null
      ? `(${p.home_goals} - ${p.away_goals})`
      : "";
  return (
    <div className="chart-tooltip">
      <strong>Rating {p.rating?.toFixed(1)}</strong>
      <span>
        {p.label} · {p.is_home ? "vs" : "@"} {p.opponent} {score}
      </span>
      <span>
        {p.goals}G {p.assists}A · {p.minutes_played ?? "—"} min
      </span>
    </div>
  );
}

export default function RatingEvolutionChart({ points }: Props) {
  if (points.length < 2) return null;

  const data = points.map((p, i) => ({
    ...p,
    label: fmtDate(p.date) || `#${i + 1}`,
  }));
  const ratings = data.map((d) => d.rating).filter((r): r is number => r != null);
  const avg = ratings.reduce((a, b) => a + b, 0) / ratings.length;
  const min = Math.min(...ratings);
  const max = Math.max(...ratings);
  const domainMin = Math.max(0, Math.floor((min - 0.5) * 2) / 2);
  const domainMax = Math.min(10, Math.ceil((max + 0.5) * 2) / 2);

  return (
    <div style={{ width: "100%", height: 260 }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 48, bottom: 4, left: -14 }}>
          <defs>
            <linearGradient id="ratingFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.35} />
              <stop offset="100%" stopColor="#7c3aed" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <XAxis
            dataKey="label"
            tick={{ fill: "#6b7891", fontSize: 11 }}
            axisLine={{ stroke: "rgba(255,255,255,0.07)" }}
            tickLine={false}
            interval="preserveStartEnd"
            minTickGap={24}
          />
          <YAxis
            domain={[domainMin, domainMax]}
            tick={{ fill: "#6b7891", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={44}
          />
          <Tooltip content={<EvoTooltip />} cursor={{ stroke: "rgba(255,255,255,0.15)" }} />
          <ReferenceLine
            y={Number(avg.toFixed(1))}
            stroke="#8b97ab"
            strokeDasharray="4 4"
            label={{ value: `Prom ${avg.toFixed(1)}`, fill: "#8b97ab", fontSize: 10, position: "insideTopRight" }}
          />
          <Area
            type="monotone"
            dataKey="rating"
            stroke="#3b82f6"
            strokeWidth={2}
            fill="url(#ratingFill)"
            dot={{ r: 3, fill: "#0b1b35", stroke: "#3b82f6", strokeWidth: 1.5 }}
            activeDot={{ r: 4.5, fill: "#3b82f6" }}
            isAnimationActive={false}
            connectNulls
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
