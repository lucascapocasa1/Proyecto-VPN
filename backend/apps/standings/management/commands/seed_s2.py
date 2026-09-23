import random
from datetime import timedelta

from django.utils import timezone
from django.core.management.base import BaseCommand

from apps.competitions.models import Country, Season
from apps.clubs.models import ClubTitle
from apps.players.models import PlayerClubHistory
from apps.matches.models import Matchday, Match
from apps.standings.services import recalculate_standings
from apps.standings.management.commands._seed_helpers import (
    S1_J1_OFFSET,
    S1_MATCHDAYS,
    S2_J1_OFFSET,
    S2_PLAYED_MATCHDAYS,
    S2_TOTAL_MATCHDAYS,
    s1_matchday_date,
    s2_matchday_date,
    joined_at_s1,
    left_at_s1,
    joined_at_s2,
    create_matchdays,
    apply_transfers,
    pick_forced_transfer_ids,
)


class Command(BaseCommand):
    help = (
        "Idempotent upgrade of the existing seed to an ACTIVE Season 2: "
        "past dates, realistic transfers, 10 played matchdays + matchday 11 scheduled."
    )

    def handle(self, *args, **options):
        random.seed(42)
        countries = Country.objects.filter(code__in=["AR", "UY"])
        if not countries.exists():
            self.stdout.write(self.style.ERROR("No seeded countries found. Run seed_data first."))
            return

        for country in countries:
            self.stdout.write(f"\n=== {country.name} ===")
            self._upgrade_country(country)

        self.stdout.write(self.style.SUCCESS("\nSeason 2 upgrade complete!"))

    def _upgrade_country(self, country):
        league = country.leagues.first()
        if not league:
            self.stdout.write("  No league found, skipping.")
            return

        season1 = league.seasons.filter(number=1).first()
        season2 = league.seasons.filter(number=2).first()
        if not season1 or not season2:
            self.stdout.write("  Seasons 1/2 not found, skipping.")
            return

        self._fix_s1_dates(season1)
        self._activate_s2(season2)
        self._fix_history_dates(season1, season2)
        self._apply_transfers_once(country, season1, season2)
        self._create_s2_matchdays(season2)

        for division in season2.divisions.all():
            recalculate_standings(season2, division)
        self.stdout.write("  Standings recalculated for Season 2")

    def _fix_s1_dates(self, season1):
        today = timezone.now().date()
        fixed_md = 0
        for matchday in Matchday.objects.filter(season=season1):
            if matchday.date is None or matchday.date > today:
                matchday.date = s1_matchday_date(matchday.number)
                matchday.save(update_fields=["date"])
                fixed_md += 1
            new_date = matchday.date
            for match in matchday.matches.all():
                if match.date is None or match.date > today:
                    match.date = new_date
                    match.save(update_fields=["date"])
        for match in Match.objects.filter(season=season1, matchday__isnull=True):
            if match.date is None or match.date > today:
                match.date = today - timedelta(days=7)
                match.save(update_fields=["date"])

        titles = ClubTitle.objects.filter(season=season1, title_type=ClubTitle.TitleType.CHAMPION)
        for title in titles:
            if title.awarded_at.date() > today:
                target = timezone.now() + timedelta(days=S1_J1_OFFSET + (S1_MATCHDAYS - 1) * 7)
                title.awarded_at = target
                title.save(update_fields=["awarded_at"])

        if fixed_md:
            self.stdout.write(f"  S1: normalized {fixed_md} future matchday dates to the past")

    def _activate_s2(self, season2):
        if season2.status != Season.Status.ACTIVE:
            season2.status = Season.Status.ACTIVE
            season2.save(update_fields=["status"])
            self.stdout.write("  S2: status -> ACTIVE")
        else:
            self.stdout.write("  S2: already ACTIVE")

    def _fix_history_dates(self, season1, season2):
        now = timezone.now()
        s2_start_target = now + timedelta(days=S2_J1_OFFSET)
        updated = 0
        for pch in PlayerClubHistory.objects.filter(club_season__season=season1):
            needs = (
                pch.joined_at > now
                or (pch.left_at is not None and pch.left_at > now)
                or (pch.left_at is not None and pch.left_at > s2_start_target)
            )
            if needs:
                pch.joined_at = joined_at_s1()
                pch.left_at = left_at_s1()
                pch.save(update_fields=["joined_at", "left_at"])
                updated += 1
        for pch in PlayerClubHistory.objects.filter(club_season__season=season2):
            changes = []
            if pch.joined_at > now:
                pch.joined_at = joined_at_s2()
                changes.append("joined_at")
            if pch.left_at is not None:
                pch.left_at = None
                changes.append("left_at")
            if changes:
                pch.save(update_fields=changes)
                updated += 1
        if updated:
            self.stdout.write(f"  History dates normalized ({updated} rows)")

    def _apply_transfers_once(self, country, season1, season2):
        if Matchday.objects.filter(season=season2).exists():
            self.stdout.write("  S2 matchdays already exist, transfers skipped")
            return

        forced_ids = pick_forced_transfer_ids(country, season1, count=5, top_limit=10)
        transfers = apply_transfers(country, season2, forced_player_ids=forced_ids)
        self.stdout.write(
            f"  S2: {transfers} transfers applied ({len(forced_ids)} forced top scorers)"
        )

    def _create_s2_matchdays(self, season2):
        for division in season2.divisions.all():
            club_seasons = list(division.club_seasons.all().order_by("id"))

            finished_matches, finished_events = create_matchdays(
                season2, division, club_seasons, s2_matchday_date,
                1, S2_PLAYED_MATCHDAYS, finished=True,
            )
            scheduled_matches, _ = create_matchdays(
                season2, division, club_seasons, s2_matchday_date,
                S2_TOTAL_MATCHDAYS, S2_TOTAL_MATCHDAYS, finished=False,
            )
            total_md = Matchday.objects.filter(season=season2, division=division).count()
            self.stdout.write(
                f"  {division.name}: created {finished_matches} finished "
                f"({finished_events} events), {scheduled_matches} scheduled "
                f"[{total_md} matchdays total]"
            )
