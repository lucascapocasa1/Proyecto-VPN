import { useState, useEffect } from "react";
import { countriesApi } from "../api";
import type { Country } from "../types";
import Loading from "../components/ui/Loading";
import ErrorMessage from "../components/ui/ErrorMessage";

export default function Countries() {
  const [countries, setCountries] = useState<Country[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = () => {
    setLoading(true);
    setError(null);
    countriesApi.list()
      .then((res) => setCountries(res.data.results))
      .catch(() => setError("Error al cargar paises"))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, []);

  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} onRetry={fetchData} />;

  return (
    <div className="list-page">
      <h1>Paises</h1>
      <div className="card-grid">
        {countries.map((country) => (
          <div key={country.id} className="card">
            <h3>{country.name}</h3>
            <p>{country.code}</p>
          </div>
        ))}
      </div>
      {countries.length === 0 && <p className="empty">No hay paises registrados</p>}
    </div>
  );
}
