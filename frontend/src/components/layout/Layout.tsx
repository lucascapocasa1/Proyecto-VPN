import { useEffect, useState } from "react";
import { Link, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import GlobalSearch from "../ui/GlobalSearch";
import {
  ArrowLeftRight,
  BarChart3,
  Bell,
  CalendarDays,
  Crown,
  Home as HomeIcon,
  ListOrdered,
  LogOut,
  Menu,
  Shield,
  Trophy,
  Users,
  X,
} from "lucide-react";

const NAV_ITEMS = [
  { path: "/", label: "Inicio", icon: HomeIcon },
  { path: "/seasons", label: "Competiciones", icon: Trophy },
  { path: "/standings", label: "Tabla de Posiciones", icon: ListOrdered },
  { path: "/clubs", label: "Clubes", icon: Shield },
  { path: "/players", label: "Jugadores", icon: Users },
  { path: "/matches", label: "Partidos", icon: CalendarDays },
  { path: "/transfers", label: "Mercado", icon: ArrowLeftRight },
  { path: "/statistics", label: "Estadísticas", icon: BarChart3 },
];

export default function Layout() {
  const { user, isAuthenticated, logout } = useAuth();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    setMenuOpen(false);
  }, [location.pathname]);

  const isActive = (path: string) =>
    path === "/"
      ? location.pathname === "/"
      : location.pathname === path || location.pathname.startsWith(path + "/");

  return (
    <div className="app">
      <aside className={`sidebar ${menuOpen ? "sidebar-open" : ""}`}>
        <Link to="/" className="sidebar-brand">
          <span className="brand-mark">
            <Shield size={22} strokeWidth={2.2} />
          </span>
          <span className="brand-text">
            <strong>FC 27</strong>
            <small>PRO CLUBS</small>
          </span>
        </Link>

        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`sidebar-link ${isActive(item.path) ? "active" : ""}`}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          <Crown size={22} className="sidebar-crown" />
          <div className="sidebar-vpn">VPN</div>
          <div className="sidebar-vpn-sub">VIRTUAL PRO NETWORK</div>
          <div className="sidebar-tagline">
            MÁS QUE UN JUEGO,
            <br />
            UNA LIGA.
          </div>
        </div>
      </aside>

      {menuOpen && <div className="sidebar-overlay" onClick={() => setMenuOpen(false)} />}

      <div className="app-body">
        <header className="topbar">
          <button
            className="icon-btn topbar-menu-btn"
            onClick={() => setMenuOpen((v) => !v)}
            aria-label="Abrir menú"
            type="button"
          >
            {menuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>

          <GlobalSearch />

          <div className="topbar-right">
            <button
              className="icon-btn notification-btn"
              title="Notificaciones (próximamente)"
              aria-label="Notificaciones"
              type="button"
            >
              <Bell size={18} />
              <span className="notification-dot" />
            </button>

            {isAuthenticated ? (
              <div className="user-menu">
                <span className="user-avatar">{user?.username?.charAt(0).toUpperCase()}</span>
                <span className="user-meta">
                  <span className="username">{user?.username}</span>
                  <span className="role-badge">{user?.role}</span>
                </span>
                <button
                  onClick={logout}
                  className="btn btn-ghost btn-sm"
                  aria-label="Cerrar sesión"
                  title="Cerrar sesión"
                  type="button"
                >
                  <LogOut size={14} />
                </button>
              </div>
            ) : (
              <Link to="/login" className="btn btn-primary btn-sm">
                Ingresar
              </Link>
            )}
          </div>
        </header>

        <main className="main">
          <Outlet />
        </main>

        <footer className="footer">
          <p>VPN — Virtual Pro Network · La liga oficial de Clubes Pro de EA FC 27</p>
        </footer>
      </div>
    </div>
  );
}
