from django.db import models
from django.contrib.auth.models import User

#Hierarchy
#Church
    #Members
    #Prayer Requests
    #Events
    #Etc

class Church(models.Model):
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=120)
    created = models.DateTimeField(auto_now_add=True)

    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    #add Denomination , website, address, phone, etc

    def __str__(self):
        return self.name

class Member(models.Model):
    church = models.ForeignKey(Church, on_delete=models.CASCADE)

    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)

    joined = models.DateField(null=True, blank=True)

    notes = models.TextField(blank=True)

    #add Family, Birthday, ministry, attendance

    def __str__(self):
        return self.name

class ChurchUser(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('leader', 'Leader'),
        ('member', 'Member'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    church = models.ForeignKey(Church, on_delete=models.CASCADE, related_name='memberships')

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    joined = models.DateTimeField(auto_now_add=True)

    

    class Meta:
        unique_together = ("user", "church")

    def __str__(self):
        return f'{self.user} - {self.church} ({self.role})'


class JoinRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    church = models.ForeignKey(Church, on_delete=models.CASCADE)
    message = models.TextField(blank=True)
    approved = models.BooleanField(null=True)  # None = pending
    created = models.DateTimeField(auto_now_add=True)


class PrayerRequest(models.Model):
    church = models.ForeignKey(Church, on_delete=models.CASCADE)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    request = models.TextField()

    answered = models.BooleanField(default=False)

    is_private = models.BooleanField(default=False)
    is_anonymous = models.BooleanField(default=False)

    approved = models.BooleanField(null=True)  # None = pending
    updated = models.DateTimeField(auto_now=True)

    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.is_anonymous:
            return "Anonymous Prayer Request"
        return f'{self.created_by } Prayer Request'


class Announcement(models.Model):
    church = models.ForeignKey(Church, on_delete=models.CASCADE)
    
    title = models.CharField(max_length=255)
    message = models.TextField()

    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    is_pinned = models.BooleanField(default=False)

class Event(models.Model):
    church = models.ForeignKey(Church, on_delete=models.CASCADE)

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    #time range
    start = models.DateTimeField()
    end = models.DateTimeField()

    #recurrence
    is_recurring = models.BooleanField(default=False)

    REPEAT_CHOICES = [
        ('weekly', 'Weekly'),
        ('biweekly', 'Every 2 Weeks'),
        ('monthly', 'Monthly'),
    ]

    repeat_type = models.CharField(max_length=20, choices=REPEAT_CHOICES, blank=True)

    repeat_until = models.DateTimeField(null=True, blank=True)

    #auto Cleanup
    auto_delete_after_days = models.IntegerField(null=True, blank=True)


    def __str__(self):
        return self.name
    

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True)  # 👈 ADD THIS
    is_read = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.message}"

class ChatMessage(models.Model):
    church = models.ForeignKey(Church, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created = models.DateTimeField(auto_now_add=True)