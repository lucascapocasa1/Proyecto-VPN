export interface Country {
  id: number;
  name: string;
  code: string;
  flag_url: string | null;
}

export interface Game {
  id: number;
  name: string;
  year: number;
}

export interface CompetitionFormat {
  id: number;
  name: string;
  format_type: "ROUND_ROBIN" | "DOUBLE_ROUND_ROBIN" | "CUSTOM";
  has_playoffs: boolean;
  description: string | null;
}

export interface League {
  id: number;
  name: string;
  country: number;
  country_name: string;
}

export interface Division {
  id: number;
  name: string;
  season: number;
  order: number;
  max_clubs: number;
  playoff_zone_start: number | null;
  playoff_zone_end: number | null;
  promotion_zone_start: number | null;
  promotion_zone_end: number | null;
  relegation_zone_start: number | null;
  relegation_zone_end: number | null;
  has_relegation: boolean;
}

export interface Season {
  id: number;
  name: string;
  league: number;
  game: number;
  number: number | null;
  format: number;
  status: "UPCOMING" | "ACTIVE" | "FINISHED";
  created_at: string;
  updated_at: string;
  league_name: string;
  game_name: string;
  format_name: string;
  divisions: Division[];
}

export interface SeasonList {
  id: number;
  name: string;
  league: number;
  game: number;
  number: number | null;
  status: "UPCOMING" | "ACTIVE" | "FINISHED";
  league_name: string;
  game_name: string;
}

export interface Club {
  id: number;
  name: string;
  short_name: string;
  logo: string | null;
  country: number;
  country_name: string;
  founded_date: string | null;
  is_active: boolean;
  created_at: string;
}

export interface ClubDetail extends Club {
  seasons: ClubSeason[];
  titles: ClubTitle[];
}

export interface ClubSeason {
  id: number;
  club: number;
  season: number;
  division: number;
  status: "ACTIVE" | "RELEGATED" | "PROMOTED" | "WITHDRAWN";
  club_name: string;
  season_name: string;
  division_name: string;
  created_at: string;
}

export interface ClubTitle {
  id: number;
  club: number;
  season: number;
  division: number | null;
  title_type: "CHAMPION" | "RUNNER_UP" | "PLAYOFF_WINNER" | "PROMOTION_WINNER";
  name: string;
  awarded_at: string;
  awarded_by: number;
  notes: string | null;
  club_name: string;
  season_name: string;
  division_name: string | null;
  awarded_by_username: string;
  created_at: string;
}

export interface Player {
  id: number;
  nickname: string;
  platform: "PLAYSTATION" | "XBOX" | "PC" | null;
  position: "ARQ" | "DEF" | "MED" | "DEL" | null;
  country: number | null;
  country_name: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PlayerDetail extends Player {
  identity_history: PlayerIdentityHistory[];
  club_history: PlayerClubHistory[];
}

export interface PlayerIdentityHistory {
  id: number;
  nickname: string;
  changed_at: string;
  changed_by: number;
  changed_by_username: string | null;
  reason: string | null;
}

export interface PlayerClubStats {
  matches_played: number;
  goals: number;
  assists: number;
  mvp: number;
  yellow_cards: number;
  red_cards: number;
}

export interface PlayerClubHistory {
  id: number;
  player: number;
  club_season: number;
  joined_at: string;
  left_at: string | null;
  club_name: string;
  club: number;
  player_nickname: string;
  season_name: string;
  division_name: string;
  game_name: string | null;
  is_current: boolean;
  stats: PlayerClubStats;
}

export interface Matchday {
  id: number;
  season: number;
  division: number;
  number: number;
  name: string;
  date: string | null;
  season_name: string;
  division_name: string;
}

export interface Match {
  id: number;
  season: number;
  division: number;
  matchday: number | null;
  home_club_season: number;
  away_club_season: number;
  home_goals: number | null;
  away_goals: number | null;
  date: string | null;
  time: string | null;
  status: "SCHEDULED" | "IN_PROGRESS" | "FINISHED" | "POSTPONED" | "CANCELLED";
  home_club_name: string;
  away_club_name: string;
  season_name: string;
  division_name: string;
  matchday_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface MatchDetail extends Match {
  match_players: MatchPlayer[];
  events: MatchEvent[];
}

export interface MatchPlayer {
  id: number;
  match: number;
  player: number | null;
  club_season: number;
  display_name: string;
  is_starter: boolean;
  player_nickname: string | null;
  club_name: string;
  created_at: string;
}

export interface MatchEvent {
  id: number;
  match: number;
  match_player: number;
  event_type: "GOAL" | "OWN_GOAL" | "ASSIST" | "YELLOW_CARD" | "RED_CARD" | "MVP";
  minute: number | null;
  player_nickname: string | null;
  display_name: string;
  club_name: string;
  created_at: string;
}

export interface Standing {
  id: number;
  season: number;
  division: number;
  club_season: number;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goals_for: number;
  goals_against: number;
  goal_difference: number;
  points: number;
  position: number;
  updated_at: string;
  club_name: string;
  club: number;
  season_name: string;
  division_name: string;
  zone: string | null;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface Transfer {
  id: number;
  player: number;
  from_club_season: number | null;
  to_club_season: number;
  date: string;
  registered_by: number | null;
  created_at: string;
  player_name: string;
  from_club_name: string | null;
  from_division_name: string | null;
  from_season_name: string | null;
  to_club_name: string;
  to_division_name: string;
  to_season_name: string;
  registered_by_username: string | null;
  from_club: number | null;
  to_club: number;
}

export interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface TopScorer {
  player_id: number;
  nickname: string;
  position: string | null;
  country_name: string | null;
  goals: number;
}

export interface TopAssist {
  player_id: number;
  nickname: string;
  position: string | null;
  country_name: string | null;
  assists: number;
}

export interface TopMVP {
  player_id: number;
  nickname: string;
  position: string | null;
  country_name: string | null;
  mvp_count: number;
}
