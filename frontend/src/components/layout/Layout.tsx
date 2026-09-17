import { Link, Outlet } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

export default function Layout() {
  const { user, isAuthenticated, logout } = useAuth();

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <Link to="/" className="logo">
            <span className="logo-icon">&#9917;</span>
            EA FC Clubes Pro
          </Link>
          <nav className="nav">
            <Link to="/countries">Paises</Link>
            <Link to="/leagues">Ligas</Link>
            <Link to="/seasons">Temporadas</Link>
            <Link to="/clubs">Clubes</Link>
            <Link to="/players">Jugadores</Link>
            <Link to="/matches">Partidos</Link>
            <Link to="/statistics">Estadisticas</Link>
          </nav>
          <div className="header-right">
            {isAuthenticated ? (
              <div className="user-menu">
                <span className="username">{user?.username}</span>
                <button onClick={logout} className="btn btn-sm">Salir</button>
              </div>
            ) : (
              <Link to="/login" className="btn btn-primary btn-sm">Ingresar</Link>
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
