import { Link, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

const NAV_ITEMS = [
  { path: "/seasons", label: "Competiciones" },
  { path: "/clubs", label: "Clubes" },
  { path: "/players", label: "Jugadores" },
  { path: "/matches", label: "Partidos" },
  { path: "/statistics", label: "Estadisticas" },
];

export default function Layout() {
  const { user, isAuthenticated, logout } = useAuth();
  const location = useLocation();

  const isActive = (path: string) =>
    location.pathname === path || location.pathname.startsWith(path + "/");

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <Link to="/" className="logo">
            <span className="logo-icon">&#9917;</span>
            EA FC Clubes Pro
          </Link>
          <nav className="nav">
            {NAV_ITEMS.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={isActive(item.path) ? "active" : ""}
              >
                {item.label}
              </Link>
            ))}
          </nav>
          <div className="header-right">
            {isAuthenticated ? (
              <div className="user-menu">
                <span className="username">{user?.username}</span>
                <span className="role-badge">{user?.role}</span>
                <button onClick={logout} className="btn btn-sm btn-ghost">
                  Salir
                </button>
              </div>
            ) : (
              <Link to="/login" className="btn btn-primary btn-sm">
                Ingresar
              </Link>
            )}
          </div>
        </div>
      </header>
      <main className="main">
        <Outlet />
      </main>
      <footer className="footer">
        <p>EA FC Clubes Pro — Plataforma de Gestion de Ligas</p>
      </footer>
    </div>
  );
}
