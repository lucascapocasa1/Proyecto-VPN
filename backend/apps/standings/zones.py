"""
Competition zone service.
Determines the competitive zone for a standing based on division configuration.
"""


class ZoneType:
    CHAMPION = "CHAMPION"
    PLAYOFF = "PLAYOFF"
    PROMOTION = "PROMOTION"
    RELEGATION = "RELEGATION"
    NORMAL = "NORMAL"


def get_zone(standing):
    """
    Determine the competitive zone for a standing.
    Zones are derived from Division configuration.
    """
    division = standing.division
    pos = standing.position

    if pos == 1:
        return ZoneType.CHAMPION

    if (
        division.playoff_zone_start is not None
        and division.playoff_zone_end is not None
        and division.playoff_zone_start <= pos <= division.playoff_zone_end
    ):
        return ZoneType.PLAYOFF

    if (
        division.promotion_zone_start is not None
        and division.promotion_zone_end is not None
        and division.promotion_zone_start <= pos <= division.promotion_zone_end
    ):
        return ZoneType.PROMOTION

    if (
        division.relegation_zone_start is not None
        and division.relegation_zone_end is not None
        and division.relegation_zone_start <= pos <= division.relegation_zone_end
    ):
        return ZoneType.RELEGATION

    return ZoneType.NORMAL


def get_zone_display(zone):
    """
    Return display text for a zone.
    """
    displays = {
        ZoneType.CHAMPION: "CAMPEÓN",
        ZoneType.PLAYOFF: "REDUCIDO",
        ZoneType.PROMOTION: "PROMOCIÓN",
        ZoneType.RELEGATION: "DESCENSO",
        ZoneType.NORMAL: None,
    }
    return displays.get(zone)


def get_playoff_participants(standings):
    """
    Get the clubs that qualify for the playoff zone.
    Returns a list of standings in playoff positions.
    """
    participants = []
    for standing in standings:
        zone = get_zone(standing)
        if zone == ZoneType.PLAYOFF:
            participants.append(standing)
    return participants


def get_champion(standings):
    """
    Get the champion from standings (position 1).
    """
    for standing in standings:
        if standing.position == 1:
            return standing
    return None


def get_relegated(standings):
    """
    Get the relegated clubs from standings.
    """
    relegated = []
    for standing in standings:
        zone = get_zone(standing)
        if zone == ZoneType.RELEGATION:
            relegated.append(standing)
    return relegated
