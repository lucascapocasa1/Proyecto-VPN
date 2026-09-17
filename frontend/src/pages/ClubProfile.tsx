import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { clubsApi } from "../api";
import type { ClubDetail } from "../types";

const TITLE_BADGES: Record<string, { label: string; color: string }> = {
  CHAMPION: { label: "CAMPEON", color: "#fbbf24" },
  RUNNER_UP: { label: "SUBCAMPEON", color: "#94a3b8" },
  PLAYOFF_WINNER: { label: "REDUCIDO", color: "#60a5fa" },
  PROMOTION_WINNER: { label: "PROMOCION", color: "#34d399" },
};

export default function ClubProfile() {
  const { id } = useParams<{ id: string }>();
  const [club, setClub] = useState<ClubDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    clubsApi.get(Number(id))
      .then((res) => setClub(res.data))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="loading">Cargando...</div>;
  if (!club) return <div className="error">Club no encontrado</div>;

  return (
    <div className="club-profile">
      <div className="profile-header">
        <div className="club-logo large">
          {club.logo ? (
            <img src={club.logo} alt={club.name} />
          ) : (
            <span className="club-initial">{club.short_name.charAt(0)}</span>
          )}
        </div>
        <div className="profile-info">
          <h1>{club.name}</h1>
          <p>{club.country_name}</p>
        </div>
      </div>

      {club.titles.length > 0 && (
        <section className="profile-section">
          <h2>Titulos</h2>
          <div className="titles-list">
            {club.titles.map((title) => {
              const badge = TITLE_BADGES[title.title_type];
              return (
                <div key={title.id} className="title-item">
                  <span className="title-badge" style={{ backgroundColor: badge?.color }}>
                    {badge?.label || title.title_type}
                  </span>
                  <span className="title-name">{title.name}</span>
                  <span className="title-season">{title.season_name}</span>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {club.seasons.length > 0 && (
        <section className="profile-section">
          <h2>Participaciones</h2>
          <div className="seasons-list">
            {club.seasons.map((cs) => (
              <div key={cs.id} className="season-item">
                <span className="season-name">{cs.season_name}</span>
                <span className="season-division">{cs.division_name}</span>
                <span className={`season-status status-${cs.status.toLowerCase()}`}>
                  {cs.status}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
