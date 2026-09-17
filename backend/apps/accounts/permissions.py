from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    """Allow access only to SUPERADMIN users."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "SUPERADMIN"
        )


class IsAdminLiga(BasePermission):
    """Allow access to SUPERADMIN and ADMIN_LIGA users."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return request.user.role in ("SUPERADMIN", "ADMIN_LIGA")


class IsAdminClub(BasePermission):
    """Allow access to SUPERADMIN, ADMIN_LIGA, and ADMIN_CLUB users."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return request.user.role in ("SUPERADMIN", "ADMIN_LIGA", "ADMIN_CLUB")


class IsAdminOrPlayer(BasePermission):
    """Allow access to admins and players."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return request.user.role in (
            "SUPERADMIN", "ADMIN_LIGA", "ADMIN_CLUB", "PLAYER"
        )


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission:
    - Players can only access their own profile
    - Admins can access any profile
    """

    def has_object_permission(self, request, view, obj):
        if request.user.role in ("SUPERADMIN", "ADMIN_LIGA", "ADMIN_CLUB"):
            return True
        if request.user.role == "PLAYER":
            return hasattr(request.user, "player_profile") and obj.id == request.user.player_profile.id
        return False


class CanManageLeague(BasePermission):
    """
    Object-level permission for league-related resources.
    - SUPERADMIN can manage everything
    - ADMIN_LIGA can manage leagues they are assigned to
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.role == "SUPERADMIN":
            return True
        if request.user.role == "ADMIN_LIGA":
            return request.user.league_administrations.exists()
        return False

    def has_object_permission(self, request, view, obj):
        if request.user.role == "SUPERADMIN":
            return True
        if request.user.role == "ADMIN_LIGA":
            league_ids = request.user.league_administrations.values_list("league_id", flat=True)
            if hasattr(obj, "league_id"):
                return obj.league_id in league_ids
            if hasattr(obj, "season") and hasattr(obj.season, "league_id"):
                return obj.season.league_id in league_ids
            if hasattr(obj, "division") and hasattr(obj.division, "season"):
                return obj.division.season.league_id in league_ids
        return False


class CanManageClub(BasePermission):
    """
    Object-level permission for club-related resources.
    - SUPERADMIN can manage everything
    - ADMIN_LIGA can manage clubs in their leagues
    - ADMIN_CLUB can manage their own clubs
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.role in ("SUPERADMIN", "ADMIN_LIGA"):
            return True
        if request.user.role == "ADMIN_CLUB":
            return request.user.club_administrations.exists()
        return False

    def has_object_permission(self, request, view, obj):
        if request.user.role == "SUPERADMIN":
            return True
        if request.user.role == "ADMIN_LIGA":
            return True
        if request.user.role == "ADMIN_CLUB":
            club_ids = request.user.club_administrations.values_list("club_id", flat=True)
            if hasattr(obj, "club_id"):
                return obj.club_id in club_ids
            if hasattr(obj, "club"):
                return obj.club.id in club_ids
        return False
