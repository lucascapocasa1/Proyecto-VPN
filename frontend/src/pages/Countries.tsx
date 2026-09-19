import { useState, useEffect, useCallback } from "react";
import { countriesApi } from "../api";
import type { Country } from "../types";
import Loading from "../components/ui/Loading";
import ErrorMessage from "../components/ui/ErrorMessage";
import SearchBar from "../components/ui/SearchBar";

export default function Countries() {
  const [countries, setCountries] = useState<Country[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const fetchData = useCallback(() => {
    setLoading(true);
    setError(null);
    countriesApi.list()
      .then((res) => {
        let filtered = res.data.results;
        if (search) {
          filtered = filtered.filter(c =>
            c.name.toLowerCase().includes(search.toLowerCase()) ||
            c.code.toLowerCase().includes(search.toLowerCase())
          );
        }
        setCountries(filtered);
      })
      .catch(() => setError("Error al cargar paises"))
      .finally(() => setLoading(false));
  }, [search]);

  useEffect(() => { fetchData(); }, [fetchData]);

  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} onRetry={fetchData} />;

  return (
    <div className="list-page">
      <h1>Paises</h1>
      <SearchBar value={search} onChange={setSearch} placeholder="Buscar pais..." />
      <div className="card-grid">
        {countries.map((country) => (
          <div key={country.id} className="card">
            <h3>{country.name}</h3>
            <p>{country.code}</p>
          </div>
        ))}
      </div>
      {countries.length === 0 && <p className="empty">No se encontraron paises</p>}
    </div>
  );
}
