import random
from datetime import timedelta

from django.utils import timezone
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import F

from apps.accounts.models import User
from apps.competitions.models import Country
from apps.clubs.models import ClubSeason, ClubTitle
from apps.matches.models import Match
from apps.players.models import PlayerClubHistory, Transfer
from apps.standings.models import Standing
from apps.standings.services import recalculate_standings
from apps.standings.management.commands._seed_helpers import (
    S1_J1_OFFSET,
    S1_MATCHDAYS,
    S2_PLAYED_MATCHDAYS,
    S2_TOTAL_MATCHDAYS,
    s2_matchday_date,
    create_matchdays,
)


class Command(BaseCommand):
    help = (
        "One-off data fix: zone configs (PROMOCION/DESCENSO labels), correct S1 "
        "champion titles, apply direct S1->S2 club transitions (pos 20 down, "
        "2da champion up) and regenerate S2 fixtures with the new composition."
    )

    def handle(self, *args, **options):
        random.seed(42)
        countries = Country.objects.filter(code__in=["AR", "UY"])
        if not countries.exists():
            self.stdout.write(self.style.ERROR("No seeded countries found. Run seed_data first."))
            return

        for country in countries:
            league = country.leagues.first()
            if not league:
                self.stdout.write(f"{country.name}: no league found, skipping.")
                continue

            season1 = league.seasons.filter(number=1).first()
            season2 = league.seasons.filter(number=2).first()
            if not season1 or not season2:
                self.stdout.write(f"{country.name}: seasons 1/2 not found, skipping.")
                continue

            self.stdout.write(f"\n=== {country.name} ===")
            self._configure_zones(league)
            self._fix_titles(league, season1)
            moved = self._apply_transitions(season1, season2)
            if moved or self._is_stale(season2) or not Match.objects.filter(season=season2).exists():
                self._regenerate_s2(season2)
            else:
                self.stdout.write("  S2 fixtures already match division membership, skipped")
            self._backfill_transfers(season1, season2)

        self.stdout.write(self.style.SUCCESS("\nfix_season_transitions complete!"))

    def _configure_zones(self, league):
        for season in league.seasons.all():
            for division in season.divisions.all():
                if division.order == 1:
                    division.playoff_zone_start = None
                    division.playoff_zone_end = None
                    division.promotion_zone_start = 19
                    division.promotion_zone_end = 19
                    division.relegation_zone_start = 20
                    division.relegation_zone_end = 20
                else:
                    division.playoff_zone_start = 2
                    division.playoff_zone_end = 9
                    division.promotion_zone_start = 19
                    division.promotion_zone_end = 19
                    division.relegation_zone_start = 20
                    division.relegation_zone_end = 20
                division.has_relegation = True
                division.save(update_fields=[
                    "playoff_zone_start", "playoff_zone_end",
                    "promotion_zone_start", "promotion_zone_end",
                    "relegation_zone_start", "relegation_zone_end",
                    "has_relegation",
                ])
        self.stdout.write("  Zone configs normalized (Primera: 19 promo/20 desc; Segunda+: 2-9 reducido)")

    def _fix_titles(self, league, season1):
        primera = season1.divisions.get(order=1)
        champion = Standing.objects.get(
            season=season1, division=primera, position=1
        ).club_season.club

        titles = ClubTitle.objects.filter(
            season=season1, title_type=ClubTitle.TitleType.CHAMPION
        )
        for title in titles.exclude(club=champion):
            self.stdout.write(f"  Removed wrong S1 title from {title.club.name}")
            title.delete()

        if titles.filter(club=champion).exists():
            self.stdout.write(f"  S1 title already on {champion.name}")
            return

        admin = User.objects.filter(role=User.Role.SUPERADMIN).first()
        if not admin:
            self.stdout.write(self.style.WARNING("  No SUPERADMIN user, title not created"))
            return

        ClubTitle.objects.create(
            club=champion, season=season1, division=primera,
            title_type=ClubTitle.TitleType.CHAMPION,
            name=f"Campeon {league.name} {season1.name}",
            awarded_at=timezone.now() + timedelta(
                days=S1_J1_OFFSET + (S1_MATCHDAYS - 1) * 7
            ),
            awarded_by=admin,
        )
        self.stdout.write(f"  Awarded S1 title to {champion.name}")

    def _apply_transitions(self, season1, season2):
        primera1 = season1.divisions.get(order=1)
        segunda1 = season1.divisions.get(order=2)
        primera2 = season2.divisions.get(order=1)
        segunda2 = season2.divisions.get(order=2)

        relegated = Standing.objects.get(
            season=season1, division=primera1, position=20
        ).club_season.club
        promoted = Standing.objects.get(
            season=season1, division=segunda1, position=1
        ).club_season.club

        moved = 0

        cs_down = ClubSeason.objects.get(club=relegated, season=season2)
        if cs_down.division_id != segunda2.id:
            cs_down.division = segunda2
            cs_down.status = ClubSeason.Status.RELEGATED
            cs_down.save(update_fields=["division", "status"])
            moved += 1
            self.stdout.write(f"  {relegated.name}: Primera -> Segunda (descenso)")
        else:
            self.stdout.write(f"  {relegated.name}: already in Segunda")

        cs_up = ClubSeason.objects.get(club=promoted, season=season2)
        if cs_up.division_id != primera2.id:
            cs_up.division = primera2
            cs_up.status = ClubSeason.Status.PROMOTED
            cs_up.save(update_fields=["division", "status"])
            moved += 1
            self.stdout.write(f"  {promoted.name}: Segunda -> Primera (ascenso)")
        else:
            self.stdout.write(f"  {promoted.name}: already in Primera")

        return moved

    def _is_stale(self, season2):
        return (
            Match.objects.filter(season=season2)
            .exclude(home_club_season__division=F("division"))
            .exists()
            or Match.objects.filter(season=season2)
            .exclude(away_club_season__division=F("division"))
            .exists()
        )

    def _backfill_transfers(self, season1, season2):
        if Transfer.objects.filter(to_club_season__season=season2).exists():
            self.stdout.write("  Transfers registry already backfilled")
            return
        admin = User.objects.filter(role=User.Role.SUPERADMIN).first()
        s1_stints = {
            h.player_id: h
            for h in PlayerClubHistory.objects.filter(
                club_season__season=season1, left_at__isnull=False
            ).select_related("club_season__club")
        }
        created = 0
        s2_stints = PlayerClubHistory.objects.filter(
            club_season__season=season2, left_at=None
        ).select_related("club_season__club", "club_season__season")
        for h in s2_stints:
            old = s1_stints.get(h.player_id)
            if old is None or old.club_season.club_id == h.club_season.club_id:
                continue
            Transfer.objects.create(
                player_id=h.player_id,
                from_club_season=old.club_season,
                to_club_season=h.club_season,
                date=h.joined_at.date(),
                registered_by=admin,
            )
            created += 1
        self.stdout.write(f"  Backfilled {created} transfer records from S1->S2 moves")

    def _regenerate_s2(self, season2):
        season_id = season2.id
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM matches_matchevent "
                "WHERE match_id IN (SELECT id FROM matches_match WHERE season_id = %s)",
                [season_id],
            )
            cursor.execute(
                "DELETE FROM matches_matchplayer "
                "WHERE match_id IN (SELECT id FROM matches_match WHERE season_id = %s)",
                [season_id],
            )
            cursor.execute("DELETE FROM matches_match WHERE season_id = %s", [season_id])
        self.stdout.write("  S2 matches deleted (matchdays/dates preserved)")

        for division in season2.divisions.all():
            club_seasons = list(division.club_seasons.all().order_by("id"))
            finished, events = create_matchdays(
                season2, division, club_seasons, s2_matchday_date,
                1, S2_PLAYED_MATCHDAYS, finished=True,
            )
            scheduled, _ = create_matchdays(
                season2, division, club_seasons, s2_matchday_date,
                S2_TOTAL_MATCHDAYS, S2_TOTAL_MATCHDAYS, finished=False,
            )
            recalculate_standings(season2, division)
            self.stdout.write(
                f"  {division.name}: {len(club_seasons)} clubs, {finished} finished "
                f"({events} events), {scheduled} scheduled, standings recalculated"
            )
