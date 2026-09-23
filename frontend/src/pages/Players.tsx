import { useState, useEffect, useCallback, useRef } from "react";
import { playersApi } from "../api";
import type { Player } from "../types";
import PlayerCard from "../components/ui/PlayerCard";
import Loading from "../components/ui/Loading";
import ErrorMessage from "../components/ui/ErrorMessage";
import SearchBar from "../components/ui/SearchBar";
import Pagination from "../components/ui/Pagination";
import { useCanEdit } from "../hooks/useCanEdit";

const PAGE_SIZE = 20;

export default function Players() {
  const [players, setPlayers] = useState<Player[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ nickname: "", platform: "", country: 1 });
  const [submitting, setSubmitting] = useState(false);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const abortRef = useRef<AbortController | null>(null);

  const canManage = useCanEdit();

  const fetchPlayers = useCallback(() => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setError(null);
    playersApi
      .list()
      .then((res) => {
        if (!controller.signal.aborted) setPlayers(res.data.results || res.data);
      })
      .catch((err) => {
        if (err?.name !== "CanceledError" && err?.code !== "ERR_CANCELED") {
          setError("Error al cargar jugadores");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
  }, []);

  useEffect(() => {
    fetchPlayers();
    return () => abortRef.current?.abort();
  }, [fetchPlayers]);

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

  const filtered = players.filter((p) =>
    search
      ? p.nickname.toLowerCase().includes(search.toLowerCase())
      : true
  );

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} onRetry={fetchPlayers} />;

  return (
    <div>
      <div className="page-header">
        <h1 className="heading-page">Jugadores</h1>
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

      <SearchBar value={search} onChange={(v) => { setSearch(v); setPage(1); }} placeholder="Buscar jugador..." />

      <div className="card-grid">
        {paginated.map((player) => (
          <PlayerCard key={player.id} player={player} />
        ))}
      </div>

      {filtered.length === 0 && <p className="empty">No se encontraron jugadores</p>}

      <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
    </div>
  );
}
