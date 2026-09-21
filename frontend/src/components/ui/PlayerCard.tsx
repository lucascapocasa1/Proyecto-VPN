import { Link } from "react-router-dom";
import type { Player } from "../../types";

interface PlayerCardProps {
  player: Player;
}

const PLATFORM_ICONS: Record<string, string> = {
  PLAYSTATION: "PS",
  XBOX: "XB",
  PC: "PC",
};

const POSITION_LABELS: Record<string, string> = {
  ARQ: "ARQ",
  DEF: "DEF",
  MED: "MED",
  DEL: "DEL",
};

export default function PlayerCard({ player }: PlayerCardProps) {
  return (
    <Link to={`/players/${player.id}`} className="player-card">
      <div className="player-avatar">
        {player.nickname.charAt(0).toUpperCase()}
      </div>
      <div className="player-info">
        <span className="player-nickname">{player.nickname}</span>
        <div className="player-meta">
          {player.position && (
            <span className="platform-badge">{POSITION_LABELS[player.position]}</span>
          )}
          {player.platform && (
            <span className="platform-badge">{PLATFORM_ICONS[player.platform]}</span>
          )}
          {player.country_name && (
            <span className="country-name">{player.country_name}</span>
          )}
        </div>
      </div>
    </Link>
  );
}
