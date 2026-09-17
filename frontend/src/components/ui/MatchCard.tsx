import type { Match } from "../../types";

interface MatchCardProps {
  match: Match;
}

const STATUS_LABELS: Record<string, string> = {
  SCHEDULED: "Programado",
  IN_PROGRESS: "En Juego",
  FINISHED: "Finalizado",
  POSTPONED: "Aplazado",
  CANCELLED: "Cancelado",
};

const STATUS_COLORS: Record<string, string> = {
  SCHEDULED: "#94a3b8",
  IN_PROGRESS: "#f59e0b",
  FINISHED: "#22c55e",
  POSTPONED: "#f97316",
  CANCELLED: "#ef4444",
};

export default function MatchCard({ match }: MatchCardProps) {
  const statusColor = STATUS_COLORS[match.status] || "#94a3b8";
  const isFinished = match.status === "FINISHED";

  return (
    <div className="match-card">
      <div className="match-card-header">
        <span className="match-division">{match.division_name}</span>
        <span className="match-date">
          {match.date ? new Date(match.date).toLocaleDateString("es-AR") : ""}
        </span>
      </div>
      <div className="match-card-body">
        <div className="match-team match-home">
          <span className="team-name">{match.home_club_name}</span>
        </div>
        <div className="match-score">
          {isFinished ? (
            <span className="score">
              {match.home_goals} - {match.away_goals}
            </span>
          ) : (
            <span className="vs">vs</span>
          )}
        </div>
        <div className="match-team match-away">
          <span className="team-name">{match.away_club_name}</span>
        </div>
      </div>
      <div className="match-card-footer">
        <span className="match-status" style={{ color: statusColor }}>
          {STATUS_LABELS[match.status]}
        </span>
        {match.matchday_name && (
          <span className="match-matchday">{match.matchday_name}</span>
        )}
      </div>
    </div>
  );
}
