import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import Layout from "./components/layout/Layout";
import Home from "./pages/Home";
import Countries from "./pages/Countries";
import Leagues from "./pages/Leagues";
import Seasons from "./pages/Seasons";
import Standings from "./pages/Standings";
import Clubs from "./pages/Clubs";
import ClubProfile from "./pages/ClubProfile";
import Players from "./pages/Players";
import PlayerProfile from "./pages/PlayerProfile";
import Matches from "./pages/Matches";
import Statistics from "./pages/Statistics";
import Login from "./pages/Login";
import "./App.css";

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Home />} />
            <Route path="countries" element={<Countries />} />
            <Route path="leagues" element={<Leagues />} />
            <Route path="seasons" element={<Seasons />} />
            <Route path="standings/:seasonId" element={<Standings />} />
            <Route path="standings/:seasonId/:divisionId" element={<Standings />} />
            <Route path="clubs" element={<Clubs />} />
            <Route path="clubs/:id" element={<ClubProfile />} />
            <Route path="players" element={<Players />} />
            <Route path="players/:id" element={<PlayerProfile />} />
            <Route path="matches" element={<Matches />} />
            <Route path="statistics" element={<Statistics />} />
            <Route path="login" element={<Login />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
