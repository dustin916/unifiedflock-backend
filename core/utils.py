from .models import Church, ChurchUser


def is_church_admin(user, church):
    return (
        user.is_superuser or
        ChurchUser.objects.filter(
            user=user,
            church=church,
            role='admin'
        ).exists()
    )
