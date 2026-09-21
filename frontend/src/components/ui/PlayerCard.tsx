import { Link } from "react-router-dom";
import type { Player } from "../../types";
import CountryFlag from "./CountryFlag";

interface PlayerCardProps {
  player: Player;
}

const PLATFORM_ICONS: Record<string, string> = {
  PLAYSTATION: "PS",
  XBOX: "XB",
  PC: "PC",
};

const POSITION_BADGE: Record<string, string> = {
  ARQ: "badge-arq",
  DEF: "badge-def",
  MED: "badge-med",
  DEL: "badge-del",
};

const POSITION_AVATAR: Record<string, string> = {
  ARQ: "pos-arq",
  DEF: "pos-def",
  MED: "pos-med",
  DEL: "pos-del",
};

export default function PlayerCard({ player }: PlayerCardProps) {
  return (
    <Link to={`/players/${player.id}`} className="player-card">
      <div className={`player-avatar ${player.position ? POSITION_AVATAR[player.position] : ""}`}>
        {player.nickname.charAt(0).toUpperCase()}
      </div>
      <div className="player-info">
        <span className="player-nickname">{player.nickname}</span>
        <div className="player-meta">
          {player.position && (
            <span className={`badge ${POSITION_BADGE[player.position]}`}>
              {player.position}
            </span>
          )}
          {player.platform && (
            <span className="badge badge-muted">{PLATFORM_ICONS[player.platform]}</span>
          )}
          {player.country_name && (
            <span className="badge badge-muted">
              <CountryFlag code={player.country_name} size="sm" /> {player.country_name}
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}
