import type { Match } from "../../types";

interface MatchCardProps {
  match: Match;
  showDivision?: boolean;
}

const STATUS_CONFIG: Record<string, { label: string; className: string }> = {
  SCHEDULED: { label: "Programado", className: "badge-muted" },
  IN_PROGRESS: { label: "En Juego", className: "badge-amber" },
  FINISHED: { label: "Finalizado", className: "badge-green" },
  POSTPONED: { label: "Aplazado", className: "badge-amber" },
  CANCELLED: { label: "Cancelado", className: "badge-red" },
};

export default function MatchCard({ match, showDivision = true }: MatchCardProps) {
  const status = STATUS_CONFIG[match.status] || STATUS_CONFIG.SCHEDULED;
  const isFinished = match.status === "FINISHED";

  return (
    <div className="match-card">
      <div className="match-card-header">
        <span>{showDivision ? match.division_name : ""}</span>
        <span>
          {match.date
            ? new Date(`${match.date}T00:00:00`).toLocaleDateString("es-AR")
            : ""}
        </span>
      </div>
      <div className="match-card-body">
        <div className="match-team match-home">
          <span className="match-team-name">{match.home_club_name}</span>
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
          <span className="match-team-name">{match.away_club_name}</span>
        </div>
      </div>
      <div className="match-card-footer">
        <span className={`match-status badge ${status.className}`}>
          {status.label}
        </span>
        {match.matchday_name && <span>{match.matchday_name}</span>}
      </div>
    </div>
  );
}
