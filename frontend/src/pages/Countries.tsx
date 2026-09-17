import { useState, useEffect } from "react";
import { countriesApi } from "../api";
import type { Country } from "../types";

export default function Countries() {
  const [countries, setCountries] = useState<Country[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    countriesApi.list()
      .then((res) => setCountries(res.data.results))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Cargando...</div>;

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
    </div>
  );
}
