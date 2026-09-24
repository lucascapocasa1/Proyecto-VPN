"""Crea MatchPerformance realistas para las apariciones de partidos finalizados.

- Idempotente: por defecto solo completa las apariciones que todavía no tienen
  rendimiento. Con --reset borra todo y regenera.
- Consistente con la fuente de verdad: goals/assists se derivan de los
  MatchEvent reales, asi los rankings (goleadores/asistencias) y la seccion
  de rendimiento no se contradicen.
- Determinista: el RNG de cada fila se siembra con --seed y el id de la
  aparicion, por lo que re-ejecutar produce los mismos valores.
"""
import random
from collections import defaultdict

from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.matches.models import MatchEvent, MatchPerformance, MatchPlayer

BATCH_SIZE = 1000

RANGES = {
    # (min, max) por posicion
    "shots":        {"ARQ": (0, 1), "DEF": (0, 2), "MED": (1, 4), "DEL": (2, 6)},
    "passes":       {"ARQ": (8, 30), "DEF": (20, 50), "MED": (35, 70), "DEL": (12, 35)},
    "pass_acc":     {"ARQ": (55, 85), "DEF": (72, 90), "MED": (78, 94), "DEL": (68, 88)},
    "dribbles":     {"ARQ": (0, 1), "DEF": (0, 3), "MED": (1, 5), "DEL": (2, 7)},
    "tackles":      {"ARQ": (0, 1), "DEF": (2, 6), "MED": (2, 5), "DEL": (0, 2)},
    "offsides":     {"ARQ": (0, 0), "DEF": (0, 1), "MED": (0, 1), "DEL": (0, 3)},
    "fouls":        {"ARQ": (0, 2), "DEF": (1, 4), "MED": (1, 4), "DEL": (1, 3)},
    "poss_won":     {"ARQ": (1, 4), "DEF": (3, 9), "MED": (4, 12), "DEL": (2, 8)},
    "poss_lost":    {"ARQ": (1, 5), "DEF": (3, 10), "MED": (4, 12), "DEL": (3, 10)},
}
POSITION_RATING_BONUS = {"DEL": 0.25, "MED": 0.2, "DEF": 0.1, "ARQ": 0.15}


class Command(BaseCommand):
    help = (
        "Crea rendimientos (MatchPerformance) realistas para apariciones de "
        "partidos finalizados. Idempotente; goals/assists salen de los "
        "MatchEvent reales."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--seed", type=int, default=42,
            help="Semilla del RNG (default: 42).",
        )
        parser.add_argument(
            "--reset", action="store_true",
            help="Borra todos los rendimientos antes de regenerar.",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            deleted, _ = MatchPerformance.objects.all().delete()
            self.stdout.write(f"Borradas {deleted} performances.")

        goal_counts: dict[int, int] = defaultdict(int)
        assist_counts: dict[int, int] = defaultdict(int)
        events = (
            MatchEvent.objects.filter(match__status="FINISHED")
            .values_list("match_player_id", "event_type")
        )
        for mp_id, event_type in events:
            if event_type == MatchEvent.EventType.GOAL:
                goal_counts[mp_id] += 1
            elif event_type == MatchEvent.EventType.ASSIST:
                assist_counts[mp_id] += 1

        qs = (
            MatchPlayer.objects.filter(
                match__status="FINISHED",
                player__isnull=False,
                performance__isnull=True,
            )
            .select_related("player")
            .iterator(chunk_size=2000)
        )

        created = 0
        batch = []
        with transaction.atomic():
            for mp in qs:
                rng = random.Random(f"{options['seed']}-{mp.id}")
                stats = self._stats(
                    mp, goal_counts[mp.id], assist_counts[mp.id], rng
                )
                batch.append(MatchPerformance(match_player=mp, **stats))
                if len(batch) >= BATCH_SIZE:
                    MatchPerformance.objects.bulk_create(batch)
                    created += len(batch)
                    batch = []
            if batch:
                MatchPerformance.objects.bulk_create(batch)
                created += len(batch)

        cache.clear()
        total = MatchPerformance.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f"{created} rendimientos creados ({total} en total)."
        ))

    def _stats(self, mp, goals, assists, rng) -> dict:
        pos = mp.player.position

        if rng.random() < 0.12:
            minutes = rng.randint(30, 60)  # cambio temprano / lesion
        else:
            minutes = rng.randint(62, 90)

        rating = 5.8 + goals * 0.7 + assists * 0.45
        rating += POSITION_RATING_BONUS.get(pos, 0.1)
        rating += rng.uniform(-0.6, 0.8)
        if minutes < 70:
            rating -= 0.3
        rating = round(min(9.7, max(5.0, rating)), 1)

        shots = max(goals, rng.randint(*RANGES["shots"][pos]))
        shot_acc = 0 if shots == 0 else min(
            100, rng.randint(30, 80) + (15 if goals else 0)
        )

        passes = rng.randint(*RANGES["passes"][pos])
        pass_acc = rng.randint(*RANGES["pass_acc"][pos])
        dribbles = rng.randint(*RANGES["dribbles"][pos])
        dribble_acc = rng.randint(40, 85) if dribbles > 0 else 0
        tackles = rng.randint(*RANGES["tackles"][pos])
        tackle_acc = rng.randint(50, 85) if tackles > 0 else 0
        offsides = rng.randint(*RANGES["offsides"][pos])
        fouls = rng.randint(*RANGES["fouls"][pos])
        poss_won = rng.randint(*RANGES["poss_won"][pos])
        poss_lost = rng.randint(*RANGES["poss_lost"][pos])

        km_per_min = rng.uniform(0.05, 0.07) if pos == "ARQ" else rng.uniform(0.10, 0.13)
        distance = round(minutes * km_per_min, 1)
        sprint = round(min(distance, distance * rng.uniform(0.18, 0.30)), 1)

        return {
            "rating": rating,
            "goals": goals,
            "assists": assists,
            "shots": shots,
            "shot_accuracy_pct": shot_acc,
            "passes": passes,
            "pass_accuracy_pct": pass_acc,
            "dribbles": dribbles,
            "dribble_success_pct": dribble_acc,
            "tackles": tackles,
            "tackle_success_pct": tackle_acc,
            "offsides": offsides,
            "fouls": fouls,
            "possession_won": poss_won,
            "possession_lost": poss_lost,
            "minutes_played": minutes,
            "distance_km": distance,
            "sprint_distance_km": sprint,
        }
