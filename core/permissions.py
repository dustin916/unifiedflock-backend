from .models import ChurchUser



def can_delete_prayer(user, prayer):

    membership = ChurchUser.objects.filter(
        user=user,
        church=prayer.church
    ).first()

    if not membership:
        return False

    if membership.role in ["admin", "leader"]:
        return True

    return prayer.created_by == user