import api from "./client";
import type {
  Country, Game, League, Season, SeasonList, Division,
  Club, ClubDetail, ClubSeason, ClubTitle,
  Player, PlayerDetail,
  Match, MatchDetail, MatchPlayer, MatchEvent,
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
  create: (data: { name: string; code: string }) =>
    api.post<Country>("/countries/", data),
  update: (id: number, data: Partial<Country>) =>
    api.patch<Country>(`/countries/${id}/`, data),
  delete: (id: number) => api.delete(`/countries/${id}/`),
};

// Games
export const gamesApi = {
  list: () => api.get<PaginatedResponse<Game>>("/games/"),
  get: (id: number) => api.get<Game>(`/games/${id}/`),
  create: (data: { name: string; year: number }) =>
    api.post<Game>("/games/", data),
};

// Leagues
export const leaguesApi = {
  list: () => api.get<PaginatedResponse<League>>("/leagues/"),
  get: (id: number) => api.get<League>(`/leagues/${id}/`),
  create: (data: { name: string; country: number }) =>
    api.post<League>("/leagues/", data),
  update: (id: number, data: Partial<League>) =>
    api.patch<League>(`/leagues/${id}/`, data),
  delete: (id: number) => api.delete(`/leagues/${id}/`),
};

// Seasons
export const seasonsApi = {
  list: () => api.get<PaginatedResponse<SeasonList>>("/seasons/"),
  get: (id: number) => api.get<Season>(`/seasons/${id}/`),
  create: (data: { name: string; league: number; game: number; format: number; status?: string }) =>
    api.post<Season>("/seasons/", data),
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
  create: (data: { name: string; short_name: string; country: number }) =>
    api.post<Club>("/clubs/", data),
  update: (id: number, data: Partial<Club>) =>
    api.patch<Club>(`/clubs/${id}/`, data),
  delete: (id: number) => api.delete(`/clubs/${id}/`),
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
  create: (data: { nickname: string; platform?: string; country?: number }) =>
    api.post<Player>("/players/", data),
  update: (id: number, data: Partial<Player>) =>
    api.patch<Player>(`/players/${id}/`, data),
  delete: (id: number) => api.delete(`/players/${id}/`),
};

// Matches
export const matchesApi = {
  list: (params?: { season?: number; division?: number; status?: string }) =>
    api.get<PaginatedResponse<Match>>("/matches/", { params }),
  get: (id: number) => api.get<MatchDetail>(`/matches/${id}/`),
  create: (data: {
    season: number; division: number; matchday?: number;
    home_club_season: number; away_club_season: number;
    home_goals?: number; away_goals?: number; status?: string;
  }) => api.post<Match>("/matches/", data),
  update: (id: number, data: Partial<Match>) =>
    api.patch<Match>(`/matches/${id}/`, data),
  delete: (id: number) => api.delete(`/matches/${id}/`),
};

// Match Players
export const matchPlayersApi = {
  create: (data: { match: number; player?: number; club_season: number; display_name: string }) =>
    api.post<MatchPlayer>("/match-players/", data),
  delete: (id: number) => api.delete(`/match-players/${id}/`),
};

// Match Events
export const matchEventsApi = {
  create: (data: { match: number; match_player: number; event_type: string; minute?: number }) =>
    api.post<MatchEvent>("/match-events/", data),
  delete: (id: number) => api.delete(`/match-events/${id}/`),
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
