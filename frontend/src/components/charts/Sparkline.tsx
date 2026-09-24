interface SparklineProps {
  values: (number | null | undefined)[];
  color?: string;
  height?: number;
}

export default function Sparkline({ values, color = "var(--accent)", height = 26 }: SparklineProps) {
  const pts = values.filter((v): v is number => typeof v === "number" && Number.isFinite(v));
  if (pts.length < 2) return null;

  const min = Math.min(...pts);
  const max = Math.max(...pts);
  const range = max - min || 1;
  const W = 100;
  const H = 24;
  const pad = 3;

  const points = values
    .map((v, i) => {
      if (typeof v !== "number" || !Number.isFinite(v)) return null;
      const x = (i / (values.length - 1)) * W;
      const y = H - pad - ((v - min) / range) * (H - pad * 2);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .filter(Boolean)
    .join(" ");

  const lastIdx = values.length - 1;
  const lastVal = values[lastIdx];
  const lastX = W;
  const lastY =
    typeof lastVal === "number" && Number.isFinite(lastVal)
      ? H - pad - ((lastVal - min) / range) * (H - pad * 2)
      : null;

  return (
    <svg
      className="sparkline"
      viewBox={`0 0 ${W} ${H}`}
      preserveAspectRatio="none"
      style={{ width: "100%", height, color }}
      aria-hidden="true"
    >
      <polyline
        points={points}
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
        vectorEffect="non-scaling-stroke"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      {lastY !== null && (
        <circle cx={lastX} cy={lastY} r="2" fill="currentColor" />
      )}
    </svg>
  );
}
