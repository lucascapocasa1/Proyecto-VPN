from django.core.management.base import BaseCommand, CommandError
from apps.competitions.models import Season, Division
from apps.standings.services import recalculate_standings, recalculate_all_standings


class Command(BaseCommand):
    help = "Recalculate standings for a season and division (or all divisions)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--season",
            type=int,
            help="Season ID to recalculate",
        )
        parser.add_argument(
            "--division",
            type=int,
            help="Division ID to recalculate (optional, recalculates all if not specified)",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Recalculate standings for all active seasons",
        )

    def handle(self, *args, **options):
        if options["all"]:
            seasons = Season.objects.filter(status=Season.Status.ACTIVE)
            if not seasons.exists():
                self.stdout.write(self.style.WARNING("No active seasons found."))
                return

            for season in seasons:
                self.stdout.write(f"Recalculating standings for {season}...")
                results = recalculate_all_standings(season)
                for division_id, standings in results.items():
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  Division {division_id}: {len(standings)} positions calculated"
                        )
                    )
            return

        if not options["season"]:
            raise CommandError("Please provide --season ID or use --all")

        try:
            season = Season.objects.get(pk=options["season"])
        except Season.DoesNotExist:
            raise CommandError(f"Season with ID {options['season']} does not exist.")

        if options["division"]:
            try:
                division = Division.objects.get(pk=options["division"])
            except Division.DoesNotExist:
                raise CommandError(f"Division with ID {options['division']} does not exist.")

            self.stdout.write(f"Recalculating standings for {season} - {division}...")
            standings = recalculate_standings(season, division)
            self.stdout.write(
                self.style.SUCCESS(f"Successfully recalculated {len(standings)} positions.")
            )
        else:
            self.stdout.write(f"Recalculating all divisions for {season}...")
            results = recalculate_all_standings(season)
            total = 0
            for division_id, standings in results.items():
                count = len(standings)
                total += count
                self.stdout.write(
                    self.style.SUCCESS(f"  Division {division_id}: {count} positions")
                )
            self.stdout.write(
                self.style.SUCCESS(f"Total: {total} positions recalculated.")
            )
