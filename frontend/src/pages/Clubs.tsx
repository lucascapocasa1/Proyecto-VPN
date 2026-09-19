import { useState, useEffect, useCallback } from "react";
import { clubsApi } from "../api";
import type { Club } from "../types";
import ClubCard from "../components/ui/ClubCard";
import Loading from "../components/ui/Loading";
import ErrorMessage from "../components/ui/ErrorMessage";
import Pagination from "../components/ui/Pagination";
import SearchBar from "../components/ui/SearchBar";
import { useAuth } from "../context/AuthContext";

export default function Clubs() {
  const [clubs, setClubs] = useState<Club[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", short_name: "", country: 1 });
  const [submitting, setSubmitting] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState("");
  const { user } = useAuth();

  const canManage = user?.role === "SUPERADMIN";

  const fetchClubs = useCallback(() => {
    setLoading(true);
    setError(null);
    clubsApi.list()
      .then((res) => {
        let filtered = res.data.results;
        if (search) {
          filtered = filtered.filter(c =>
            c.name.toLowerCase().includes(search.toLowerCase()) ||
            c.short_name.toLowerCase().includes(search.toLowerCase())
          );
        }
        setClubs(filtered);
        setTotalPages(Math.max(1, Math.ceil(res.data.count / 25)));
      })
      .catch(() => setError("Error al cargar clubes"))
      .finally(() => setLoading(false));
  }, [search]);

  useEffect(() => { fetchClubs(); }, [fetchClubs]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await clubsApi.create(form);
      setShowForm(false);
      setForm({ name: "", short_name: "", country: 1 });
      fetchClubs();
    } catch {
      setError("Error al crear club");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} onRetry={fetchClubs} />;

  return (
    <div className="list-page">
      <div className="page-header">
        <h1>Clubes</h1>
        {canManage && (
          <button onClick={() => setShowForm(!showForm)} className="btn btn-primary">
            {showForm ? "Cancelar" : "+ Nuevo Club"}
          </button>
        )}
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="form-inline">
          <input
            type="text"
            placeholder="Nombre del club"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
          />
          <input
            type="text"
            placeholder="Sigla"
            value={form.short_name}
            onChange={(e) => setForm({ ...form, short_name: e.target.value })}
            maxLength={20}
            required
          />
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? "Creando..." : "Crear"}
          </button>
        </form>
      )}

      <SearchBar value={search} onChange={setSearch} placeholder="Buscar club..." />

      <div className="card-grid">
        {clubs.map((club) => (
          <ClubCard key={club.id} club={club} />
        ))}
      </div>

      <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />

      {clubs.length === 0 && <p className="empty">No se encontraron clubes</p>}
    </div>
  );
}
