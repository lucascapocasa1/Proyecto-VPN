export interface PerfField {
  key: string;
  label: string;
  step?: string;
  max?: number;
  min?: number;
  required?: boolean;
}

export const PERF_FIELDS: PerfField[] = [
  { key: "rating", label: "Rating", step: "0.1", min: 0, max: 10, required: true },
  { key: "goals", label: "Goles", max: 30 },
  { key: "assists", label: "Asistencias", max: 30 },
  { key: "shots", label: "Tiros", max: 50 },
  { key: "shot_accuracy_pct", label: "Prec. tiros %", max: 100 },
  { key: "passes", label: "Pases", max: 500 },
  { key: "pass_accuracy_pct", label: "Prec. pases %", max: 100 },
  { key: "dribbles", label: "Regates", max: 50 },
  { key: "dribble_success_pct", label: "Éxito regates %", max: 100 },
  { key: "tackles", label: "Entradas", max: 50 },
  { key: "tackle_success_pct", label: "Éxito entradas %", max: 100 },
  { key: "offsides", label: "Offsides", max: 30 },
  { key: "fouls", label: "Faltas", max: 50 },
  { key: "possession_won", label: "Pos. ganada", max: 100 },
  { key: "possession_lost", label: "Pos. perdida", max: 100 },
  { key: "minutes_played", label: "Minutos", max: 130 },
  { key: "distance_km", label: "Dist. km", step: "0.1", max: 999.9 },
  { key: "sprint_distance_km", label: "Sprint km", step: "0.1", max: 999.9 },
];

export const PERF_SUMMARY_KEYS = [
  "rating",
  "goals",
  "assists",
  "passes",
  "minutes_played",
  "distance_km",
];

export function toNum(value: string): number {
  const n = Number(String(value).replace(",", ".").trim());
  return Number.isFinite(n) ? n : 0;
}
