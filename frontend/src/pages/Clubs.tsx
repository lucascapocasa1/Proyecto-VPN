import { useState, useEffect } from "react";
import { clubsApi } from "../api";
import type { Club } from "../types";
import ClubCard from "../components/ui/ClubCard";

export default function Clubs() {
  const [clubs, setClubs] = useState<Club[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    clubsApi.list()
      .then((res) => setClubs(res.data.results))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Cargando...</div>;

  return (
    <div className="list-page">
      <h1>Clubes</h1>
      <div className="card-grid">
        {clubs.map((club) => (
          <ClubCard key={club.id} club={club} />
        ))}
      </div>
    </div>
  );
}
