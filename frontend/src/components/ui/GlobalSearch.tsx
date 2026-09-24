import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, Users, Shield } from "lucide-react";
import { playersApi, clubsApi } from "../../api";
import type { Club } from "../../types";

interface SearchResult {
  id: number;
  type: "Jugador" | "Club";
  label: string;
  sub: string;
  to: string;
}

let clubsCache: Promise<{ data: { count: number; next: null; previous: null; results: Club[] } }> | null = null;

const getClubs = () => {
  if (!clubsCache) clubsCache = clubsApi.list();
  return clubsCache;
};

export default function GlobalSearch() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const q = query.trim().toLowerCase();
    if (q.length < 2) {
      setResults([]);
      return;
    }
    let cancelled = false;
    const timer = setTimeout(() => {
      Promise.allSettled([playersApi.list({ search: q, page_size: 5 }), getClubs()]).then(
        ([playersRes, clubsRes]) => {
          if (cancelled) return;
          const next: SearchResult[] = [];
          if (playersRes.status === "fulfilled") {
            playersRes.value.data.results.forEach((p) =>
              next.push({
                id: p.id,
                type: "Jugador",
                label: p.nickname,
                sub: p.position || "Jugador",
                to: `/players/${p.id}`,
              })
            );
          }
          if (clubsRes.status === "fulfilled") {
            clubsRes.value.data.results
              .filter(
                (c) => c.name.toLowerCase().includes(q) || c.short_name.toLowerCase().includes(q)
              )
              .slice(0, 5)
              .forEach((c) =>
                next.push({
                  id: c.id,
                  type: "Club",
                  label: c.name,
                  sub: c.country_name,
                  to: `/clubs/${c.id}`,
                })
              );
          }
          setResults(next.slice(0, 8));
        }
      );
    }, 250);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [query]);

  useEffect(() => {
    const onMouseDown = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onMouseDown);
    return () => document.removeEventListener("mousedown", onMouseDown);
  }, []);

  const goTo = (to: string) => {
    setOpen(false);
    setQuery("");
    navigate(to);
  };

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (results.length > 0) goTo(results[0].to);
  };

  return (
    <div className="global-search" ref={containerRef}>
      <form onSubmit={onSubmit} role="search">
        <Search className="global-search-icon" size={16} />
        <input
          type="text"
          className="global-search-input"
          placeholder="Buscar equipos o jugadores..."
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          aria-label="Buscar"
        />
      </form>
      {open && query.trim().length >= 2 && (
        <div className="global-results">
          {results.length === 0 ? (
            <p className="global-results-empty">Sin resultados para "{query.trim()}"</p>
          ) : (
            results.map((r) => (
              <button
                key={`${r.type}-${r.id}`}
                className="global-result"
                onClick={() => goTo(r.to)}
                type="button"
              >
                <span className={`global-result-icon ${r.type === "Club" ? "is-club" : ""}`}>
                  {r.type === "Club" ? <Shield size={14} /> : <Users size={14} />}
                </span>
                <span className="global-result-info">
                  <span className="global-result-label">{r.label}</span>
                  <span className="global-result-sub">{r.sub}</span>
                </span>
                <span className="global-result-type">{r.type}</span>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}
