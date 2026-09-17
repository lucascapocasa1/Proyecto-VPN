import itertools
from django.core.management.base import BaseCommand, CommandError
from apps.competitions.models import Season, Division, CompetitionFormat
from apps.clubs.models import ClubSeason
from apps.matches.models import Matchday, Match


class Command(BaseCommand):
    help = "Generate fixtures (matchdays and matches) for a season and division"

    def add_arguments(self, parser):
        parser.add_argument(
            "--season",
            type=int,
            required=True,
            help="Season ID",
        )
        parser.add_argument(
            "--division",
            type=int,
            required=True,
            help="Division ID",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be created without actually creating it",
        )

    def handle(self, *args, **options):
        try:
            season = Season.objects.get(pk=options["season"])
        except Season.DoesNotExist:
            raise CommandError(f"Season with ID {options['season']} does not exist.")

        try:
            division = Division.objects.get(pk=options["division"], season=season)
        except Division.DoesNotExist:
            raise CommandError(
                f"Division with ID {options['division']} does not exist in this season."
            )

        clubs = list(
            ClubSeason.objects.filter(
                season=season,
                division=division,
                status=ClubSeason.Status.ACTIVE,
            )
        )

        if len(clubs) < 2:
            raise CommandError("Need at least 2 clubs to generate fixtures.")

        format_type = season.format.format_type

        if format_type == CompetitionFormat.FormatType.DOUBLE_ROUND_ROBIN:
            fixtures = self._generate_double_round_robin(clubs)
        elif format_type == CompetitionFormat.FormatType.ROUND_ROBIN:
            fixtures = self._generate_round_robin(clubs)
        else:
            raise CommandError(
                f"Format '{format_type}' is not supported for automatic fixture generation."
            )

        if options["dry_run"]:
            self.stdout.write(f"Would create {len(fixtures)} matchdays:")
            for i, matchday in enumerate(fixtures, 1):
                self.stdout.write(f"  Matchday {i}:")
                for home, away in matchday:
                    self.stdout.write(f"    {home.club.name} vs {away.club.name}")
            return

        Matchday.objects.filter(season=season, division=division).delete()

        created_matchdays = 0
        created_matches = 0

        for matchday_number, matchday_fixtures in enumerate(fixtures, 1):
            matchday = Matchday.objects.create(
                season=season,
                division=division,
                number=matchday_number,
                name=f"Jornada {matchday_number}",
            )
            created_matchdays += 1

            for home, away in matchday_fixtures:
                Match.objects.create(
                    season=season,
                    division=division,
                    matchday=matchday,
                    home_club_season=home,
                    away_club_season=away,
                    status=Match.Status.SCHEDULED,
                )
                created_matches += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {created_matchdays} matchdays "
                f"with {created_matches} matches."
            )
        )

    def _generate_round_robin(self, clubs):
        """
        Generate round-robin fixtures (each team plays every other team once).
        Uses the circle method for even scheduling.
        """
        n = len(clubs)
        if n % 2 != 0:
            clubs.append(None)
            n += 1

        fixtures = []
        rotated = clubs[:]

        for _ in range(n - 1):
            matchday = []
            for i in range(n // 2):
                home = rotated[i]
                away = rotated[n - 1 - i]
                if home is not None and away is not None:
                    matchday.append((home, away))
            fixtures.append(matchday)
            rotated = [rotated[0]] + [rotated[-1]] + rotated[1:-1]

        return fixtures

    def _generate_double_round_robin(self, clubs):
        """
        Generate double round-robin fixtures (home and away).
        First half: normal fixtures. Second half: reversed home/away.
        """
        first_half = self._generate_round_robin(clubs)

        second_half = []
        for matchday in first_half:
            reversed_matchday = [(away, home) for home, away in matchday]
            second_half.append(reversed_matchday)

        return first_half + second_half
