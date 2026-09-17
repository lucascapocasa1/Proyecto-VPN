import api from "./client";
import type {
  Country, Game, League, Season, SeasonList, Division,
  Club, ClubDetail, ClubSeason, ClubTitle,
  Player, PlayerDetail,
  Match, MatchDetail,
  Standing, PaginatedResponse,
  TopScorer, TopAssist, TopMVP, User,
} from "../types";

// Auth
export const authApi = {
  login: (username: string, password: string) =>
    api.post<{ access: string; refresh: string; user: User }>("/auth/login/", { username, password }),
  register: (data: { username: string; email: string; password: string; role: string }) =>
    api.post<{ access: string; refresh: string; user: User }>("/auth/register/", data),
  profile: () => api.get<User>("/auth/profile/"),
};

// Countries
export const countriesApi = {
  list: () => api.get<PaginatedResponse<Country>>("/countries/"),
  get: (id: number) => api.get<Country>(`/countries/${id}/`),
};

// Games
export const gamesApi = {
  list: () => api.get<PaginatedResponse<Game>>("/games/"),
  get: (id: number) => api.get<Game>(`/games/${id}/`),
};

// Leagues
export const leaguesApi = {
  list: () => api.get<PaginatedResponse<League>>("/leagues/"),
  get: (id: number) => api.get<League>(`/leagues/${id}/`),
};

// Seasons
export const seasonsApi = {
  list: () => api.get<PaginatedResponse<SeasonList>>("/seasons/"),
  get: (id: number) => api.get<Season>(`/seasons/${id}/`),
};

// Divisions
export const divisionsApi = {
  list: (seasonId?: number) => {
    const params = seasonId ? { season: seasonId } : {};
    return api.get<PaginatedResponse<Division>>("/divisions/", { params });
  },
  get: (id: number) => api.get<Division>(`/divisions/${id}/`),
};

// Clubs
export const clubsApi = {
  list: () => api.get<PaginatedResponse<Club>>("/clubs/"),
  get: (id: number) => api.get<ClubDetail>(`/clubs/${id}/`),
};

// Club Seasons
export const clubSeasonsApi = {
  list: (params?: { season?: number; division?: number }) =>
    api.get<PaginatedResponse<ClubSeason>>("/club-seasons/", { params }),
};

// Club Titles
export const clubTitlesApi = {
  list: (params?: { club?: number; season?: number }) =>
    api.get<PaginatedResponse<ClubTitle>>("/club-titles/", { params }),
};

// Players
export const playersApi = {
  list: () => api.get<PaginatedResponse<Player>>("/players/"),
  get: (id: number) => api.get<PlayerDetail>(`/players/${id}/`),
};

// Matches
export const matchesApi = {
  list: (params?: { season?: number; division?: number; status?: string }) =>
    api.get<PaginatedResponse<Match>>("/matches/", { params }),
  get: (id: number) => api.get<MatchDetail>(`/matches/${id}/`),
};

// Standings
export const standingsApi = {
  list: (params?: { season?: number; division?: number }) =>
    api.get<PaginatedResponse<Standing>>("/standings/", { params }),
  recalculate: (seasonId: number, divisionId?: number) =>
    api.post("/standings/recalculate/", { season_id: seasonId, division_id: divisionId }),
};

// Statistics
export const statisticsApi = {
  player: (playerId: number, params?: { season_id?: number; division_id?: number }) =>
    api.get("/statistics/player/", { params: { player_id: playerId, ...params } }),
  playerHistory: (playerId: number) =>
    api.get("/statistics/player_history/", { params: { player_id: playerId } }),
  topScorers: (params?: { season_id?: number; division_id?: number; limit?: number }) =>
    api.get<TopScorer[]>("/statistics/top_scorers/", { params }),
  topAssists: (params?: { season_id?: number; division_id?: number; limit?: number }) =>
    api.get<TopAssist[]>("/statistics/top_assists/", { params }),
  topMvp: (params?: { season_id?: number; division_id?: number; limit?: number }) =>
    api.get<TopMVP[]>("/statistics/top_mvp/", { params }),
};
