import { useState, useEffect, useCallback } from "react";
import { playersApi } from "../api";
import type { Player } from "../types";
import PlayerCard from "../components/ui/PlayerCard";
import Loading from "../components/ui/Loading";
import ErrorMessage from "../components/ui/ErrorMessage";
import Pagination from "../components/ui/Pagination";
import SearchBar from "../components/ui/SearchBar";
import { useAuth } from "../context/AuthContext";

export default function Players() {
  const [players, setPlayers] = useState<Player[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ nickname: "", platform: "", country: 1 });
  const [submitting, setSubmitting] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState("");
  const { user } = useAuth();

  const canManage = user?.role === "SUPERADMIN";

  const fetchPlayers = useCallback(() => {
    setLoading(true);
    setError(null);
    playersApi.list()
      .then((res) => {
        let filtered = res.data.results;
        if (search) {
          filtered = filtered.filter(p =>
            p.nickname.toLowerCase().includes(search.toLowerCase())
          );
        }
        setPlayers(filtered);
        setTotalPages(Math.max(1, Math.ceil(res.data.count / 25)));
      })
      .catch(() => setError("Error al cargar jugadores"))
      .finally(() => setLoading(false));
  }, [search]);

  useEffect(() => { fetchPlayers(); }, [fetchPlayers]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await playersApi.create({
        nickname: form.nickname,
        platform: form.platform || undefined,
        country: form.country || undefined,
      });
      setShowForm(false);
      setForm({ nickname: "", platform: "", country: 1 });
      fetchPlayers();
    } catch {
      setError("Error al crear jugador");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} onRetry={fetchPlayers} />;

  return (
    <div className="list-page">
      <div className="page-header">
        <h1>Jugadores</h1>
        {canManage && (
          <button onClick={() => setShowForm(!showForm)} className="btn btn-primary">
            {showForm ? "Cancelar" : "+ Nuevo Jugador"}
          </button>
        )}
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="form-inline">
          <input
            type="text"
            placeholder="Nickname"
            value={form.nickname}
            onChange={(e) => setForm({ ...form, nickname: e.target.value })}
            required
          />
          <select
            value={form.platform}
            onChange={(e) => setForm({ ...form, platform: e.target.value })}
          >
            <option value="">Plataforma</option>
            <option value="PLAYSTATION">PlayStation</option>
            <option value="XBOX">Xbox</option>
            <option value="PC">PC</option>
          </select>
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? "Creando..." : "Crear"}
          </button>
        </form>
      )}

      <SearchBar value={search} onChange={setSearch} placeholder="Buscar jugador..." />

      <div className="card-grid">
        {players.map((player) => (
          <PlayerCard key={player.id} player={player} />
        ))}
      </div>

      <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />

      {players.length === 0 && <p className="empty">No se encontraron jugadores</p>}
    </div>
  );
}
