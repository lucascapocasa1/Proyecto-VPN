import { Link } from "react-router-dom";
import type { Club } from "../../types";
import CountryFlag from "./CountryFlag";

interface ClubCardProps {
  club: Club;
}

export default function ClubCard({ club }: ClubCardProps) {
  return (
    <Link to={`/clubs/${club.id}`} className="club-card">
      <div className="club-logo">
        {club.logo ? (
          <img src={club.logo} alt={club.name} />
        ) : (
          <span>{club.short_name.charAt(0)}</span>
        )}
      </div>
      <div className="club-info">
        <span className="club-name">{club.name}</span>
        <span className="club-country">
          <CountryFlag code={club.country_name} size="sm" /> {club.country_name}
        </span>
      </div>
    </Link>
  );
}
