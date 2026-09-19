import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { clubsApi } from "../api";
import type { ClubDetail } from "../types";
import Loading from "../components/ui/Loading";
import ErrorMessage from "../components/ui/ErrorMessage";

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
  const [error, setError] = useState<string | null>(null);

  const fetchClub = () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    clubsApi.get(Number(id))
      .then((res) => setClub(res.data))
      .catch(() => setError("Club no encontrado"))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchClub(); }, [id]);

  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} onRetry={fetchClub} />;
  if (!club) return <ErrorMessage message="Club no encontrado" />;

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

      {club.seasons.length === 0 && club.titles.length === 0 && (
        <p className="empty">Este club no tiene participaciones ni titulos registrados</p>
      )}
    </div>
  );
}
