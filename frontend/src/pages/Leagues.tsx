import { useState, useEffect, useRef } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { leaguesApi, countriesApi } from "../api";
import type { League, Country } from "../types";
import Loading from "../components/ui/Loading";
import ErrorMessage from "../components/ui/ErrorMessage";
import SearchBar from "../components/ui/SearchBar";

export default function Leagues() {
  const [searchParams] = useSearchParams();
  const countryFilter = searchParams.get("country");

  const [leagues, setLeagues] = useState<League[]>([]);
  const [countries, setCountries] = useState<Country[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const abortRef = useRef<AbortController | null>(null);

  const fetchData = () => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setError(null);
    Promise.all([
      leaguesApi.list(),
      countriesApi.list(),
    ])
      .then(([leaguesRes, countriesRes]) => {
        if (controller.signal.aborted) return;
        setLeagues(leaguesRes.data.results || leaguesRes.data);
        setCountries(countriesRes.data.results || countriesRes.data);
      })
      .catch((err) => {
        if (err?.name !== "CanceledError" && err?.code !== "ERR_CANCELED") {
          setError("Error al cargar ligas");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
  };

  useEffect(() => {
    fetchData();
    return () => abortRef.current?.abort();
  }, []);

  let filtered = leagues;
  if (countryFilter) {
    filtered = filtered.filter((l) => String(l.country) === countryFilter);
  }
  if (search) {
    filtered = filtered.filter((l) =>
      l.name.toLowerCase().includes(search.toLowerCase())
    );
  }

  const countryName = countryFilter
    ? countries.find((c) => String(c.id) === countryFilter)?.name
    : null;

  if (loading) return <Loading />;
  if (error) return <ErrorMessage message={error} onRetry={fetchData} />;

  return (
    <div>
      <div className="page-header">
        <h1 className="heading-page">
          {countryName ? `Ligas de ${countryName}` : "Ligas"}
        </h1>
      </div>

      <SearchBar value={search} onChange={setSearch} placeholder="Buscar liga..." />

      <div className="card-grid">
        {filtered.map((league) => {
          const country = countries.find((c) => c.id === league.country);
          return (
            <Link
              key={league.id}
              to={`/seasons?league=${league.id}`}
              className="card"
              style={{ textDecoration: "none", color: "inherit" }}
            >
              <h3>{league.name}</h3>
              <p>{country?.name || "—"}</p>
            </Link>
          );
        })}
      </div>

      {filtered.length === 0 && <p className="empty">No se encontraron ligas</p>}
    </div>
  );
}
