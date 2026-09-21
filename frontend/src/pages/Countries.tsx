import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { countriesApi } from "../api";
import type { Country } from "../types";
import Loading from "../components/ui/Loading";
import ErrorMessage from "../components/ui/ErrorMessage";
import SearchBar from "../components/ui/SearchBar";

const FLAG_BY_CODE: Record<string, string> = {
  AR: "\u{1F1E6}\u{1F1F7}",
  UY: "\u{1F1FA}\u{1F1FE}",
  BR: "\u{1F1E7}\u{1F1F7}",
};

export default function Countries() {
  const [countries, setCountries] = useState<Country[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const fetchCountries = () => {
    setLoading(true);
    setError(null);
    countriesApi
      .list()
      .then((res) => setCountries(res.data.results || res.data))
      .catch(() => setError("Error al cargar paises"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchCountries();
  }, []);

  const filtered = countries.filter((c) =>
    c.name.toLowerCase().includes(search.toLowerCase()) ||
    c.code.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} onRetry={fetchCountries} />;

  return (
    <div>
      <div className="page-header">
        <h1 className="heading-page">Paises</h1>
      </div>

      <SearchBar value={search} onChange={setSearch} placeholder="Buscar pais..." />

      <div className="card-grid">
        {filtered.map((country) => (
          <Link
            key={country.id}
            to={`/leagues?country=${country.id}`}
            className="card"
            style={{ textDecoration: "none", color: "inherit" }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)" }}>
              <span style={{ fontSize: "2rem" }}>
                {FLAG_BY_CODE[country.code.toUpperCase()] || "\uD83C\uDF0D"}
              </span>
              <div>
                <h3>{country.name}</h3>
                <p>{country.code}</p>
              </div>
            </div>
          </Link>
        ))}
      </div>

      {filtered.length === 0 && <p className="empty">No se encontraron paises</p>}
    </div>
  );
}
