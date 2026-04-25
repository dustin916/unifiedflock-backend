from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.utils import timezone

from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Church, Member, Announcement, Event, PrayerRequest, ChurchUser, JoinRequest, Notification, ChatMessage
from .forms import ChurchForm, CustomUserCreationForm, EventForm, PrayerRequestForm, AnnouncementForm
from .utils import is_church_admin

# Authentication

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data["email"]
            user.first_name = form.cleaned_data["first_name"]
            user.last_name = form.cleaned_data["last_name"]
            user.save()
            
            login(request, user) # automatically log in after signup
            return redirect('user_dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'signup.html', {
        'form': form
    })


# Dashboards

@login_required
def user_dashboard(request):
    memberships = request.user.memberships.select_related("church")
    notifications = list(Notification.objects.filter(user=request.user, is_read=False).order_by('-created'))

    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    
    if request.method == "POST":
        church_id = request.POST.get("church_id")

        #  Security check
        if memberships.filter(church_id=church_id).exists():
            request.session["church_id"] = church_id
            return redirect("church_dashboard")

    return render(request, "user_dashboard.html", {
        "memberships": memberships,
        'notifications': notifications
    })


@login_required
def church_dashboard(request):
    church_id = request.session.get("church_id")

    if not church_id:
        return redirect("user_dashboard")

    membership = ChurchUser.objects.filter(
        user=request.user,
        church_id=church_id
    ).first()

    if not membership:
        return redirect("user_dashboard")

    church = membership.church
    is_admin = membership.role == 'admin'

    
    latest_announcement = Announcement.objects.filter(church=church).order_by('-is_pinned', '-created').first()
    events = Event.objects.filter(church=church).order_by("start")[:3]
    prayers = PrayerRequest.objects.filter(church=church, approved=True).order_by("-created")[:3]
    members = Member.objects.filter(church=church).order_by("name")[:10]

    pending_join_requests = JoinRequest.objects.filter(
        church=church,
        approved=None
    ).exists()

    pending_join_requests_count = JoinRequest.objects.filter(
        church=church,
        approved=None
    ).count()

    pending_prayers = PrayerRequest.objects.filter(
        church=church,
        approved=None
    ).exists()

    pending_prayer_count = PrayerRequest.objects.filter(
        church=church,
        approved=None
    ).count()

    context = {
        "church": church,
        "members": members,
        "latest_announcement": latest_announcement,
        "events": events,   
        "prayers": prayers,
        "member_count": Member.objects.filter(church=church).count(),
        "event_count": Event.objects.filter(church=church).count(),
        "prayer_count": PrayerRequest.objects.filter(church=church).count(),
        'is_admin': is_admin,
        'pending_join_requests': pending_join_requests,
        'pending_join_requests_count': pending_join_requests_count,
        'pending_prayers': pending_prayers,
        'pending_prayer_count': pending_prayer_count,
    }

    return render(request, "church_dashboard.html", context)

#Create/join Churches

@login_required
def create_church(request):
    if request.method == 'POST':
        form = ChurchForm(request.POST)
        if form.is_valid():
            church = form.save(commit=False)
            church.owner = request.user
            church.save()
            #make the creator an admin in ChurchUser
            ChurchUser.objects.create(user=request.user, church=church, role='admin')
            #save in session for dashboard
            request.session['church_id'] = church.id
            return redirect('church_dashboard')
    else:
        form = ChurchForm()
    
    return render(request, 'create_church.html', {'form': form})

@login_required
def request_join(request):
    if request.method == "POST":
        church_id = request.POST.get("church_id")
        message = request.POST.get("message", "")
        church = Church.objects.get(id=church_id)
        # Prevent duplicate requests
        if not JoinRequest.objects.filter(user=request.user, church=church, approved=None).exists():
            JoinRequest.objects.create(user=request.user, church=church, message=message)
        return redirect('user_dashboard')

    churches = Church.objects.all()  # could filter by code if using one
    return render(request, 'request_join.html', {'churches': churches})

@login_required
def manage_join_requests(request):
    church_id = request.session.get('church_id')
    church = get_object_or_404(Church, id=church_id)

    if not is_church_admin(request.user, church):
        return redirect('user_dashboard')
    
    requests = JoinRequest.objects.filter(church=church, approved=None)

    return render(request, 'manage_requests.html', {
        'requests': requests,
        'church': church,
    })

@login_required
def handle_join_request(request, request_id, action):
    church_id = request.session.get('church_id')
    church = get_object_or_404(Church, id=church_id)

    if not is_church_admin(request.user, church):
        return redirect('user_dashboard')
    
    join_request = get_object_or_404(JoinRequest, id=request_id, church=church)

    if action == 'approve':

        membership, created = ChurchUser.objects.get_or_create(
            user=join_request.user,
            church=church,
            defaults={'role': 'member'}
        )

        if created:
            join_request.approved = True
            join_request.save()

            Notification.objects.create(
                user=join_request.user,
                message=f'Your request to join {church.name} has been approved.'
            )
        else:
            Notification.objects.create(
                user=join_request.user,
                message=f'You are already a member of {church.name}.'
            )
            messages.warning(request, f"{join_request.user} is already a member.")

    elif action == 'deny':
        join_request.approved = False
        join_request.save()
    
        Notification.objects.create(
            user=join_request.user,
            message=f'Your request to join {church.name} has been Denied.'
            )
    join_request.delete()

    return redirect('manage_requests')

@login_required
def promote_member(request, membership_id):
    church_id = request.session.get('church_id')
    church = get_object_or_404(Church, id=church_id)

    if not is_church_admin(request.user, church):
        return redirect('user_dashboard')

    membership = get_object_or_404(ChurchUser, id=membership_id, church=church)

    membership.role = 'admin'
    membership.save()

    return redirect('members')

@login_required
def demote_member(request, membership_id):
    church_id = request.session.get('church_id')
    church = get_object_or_404(Church, id=church_id)

    if not is_church_admin(request.user, church):
        return redirect('user_dashboard')

    membership = get_object_or_404(ChurchUser, id=membership_id, church=church)

    # Prevent demoting yourself
    if membership.user == request.user:
        messages.error(request, 'You cannot demote yourself.')
        return redirect('members')

    # Prevent removing last admin
    if membership.role == 'admin':
        admin_count = ChurchUser.objects.filter(church=church, role='admin').count()
        if admin_count <= 1:
            messages.error(request, 'You cannot demote the last admin.')
            return redirect('members')

    membership.role = 'member'
    membership.save()

    return redirect('members')

@login_required
def remove_member(request, membership_id):
    church_id = request.session.get('church_id')
    church = get_object_or_404(Church, id=church_id)

    if not is_church_admin(request.user, church):
        return redirect('user_dashboard')

    membership = get_object_or_404(ChurchUser, id=membership_id, church=church)

    # Prevent removing yourself
    if membership.user == request.user:
        messages.error(request, "You cannot remove yourself.")
        return redirect('members')

    # Prevent removing last admin
    if membership.role == 'admin':
        admin_count = ChurchUser.objects.filter(church=church, role='admin').count()
        if admin_count <= 1:
            messages.error(request, 'You cannot remove the last admin.')
            return redirect('members')

    membership.delete()

    return redirect('members')

@login_required
def quit_church(request, church_id):
    church = get_object_or_404(Church, id=church_id)
    membership = get_object_or_404(ChurchUser, user=request.user, church=church)

    # Prevent last admin from quitting
    if membership.role == 'admin':
        admin_count = ChurchUser.objects.filter(church=church, role='admin').count()
        if admin_count <= 1:
            messages.error(request, "You are the only admin. You cannot leave without assigning another admin first.")
            return redirect('members')
    
    membership.delete()

    church_name = membership.church.name
        
    admins = ChurchUser.objects.filter(church_id=church_id, role='admin')
    for admin in admins:
        Notification.objects.create(user=admin.user, message=f"{request.user.first_name} {request.user.last_name} has left {church_name}.")

    if str(request.session.get('church_id')) == str(church_id):
        del request.session['church_id']

    messages.success(request, f"You have left {church.name}.")
    return redirect('user_dashboard')

#Church Views

# Announcements 
@login_required
def create_announcement(request):
    church = get_object_or_404(Church, id=request.session.get('church_id'))

    if not is_church_admin(request.user, church):
        return redirect('church_dashboard')

    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.church = church
            announcement.created_by = request.user
            announcement.save()

            messages.success(request, "Announcement created successfully.")

            members = ChurchUser.objects.filter(church=church).exclude(user=request.user)

            for member in members:
                Notification.objects.create(
                    user=member.user,
                    message=f'New announcement in {church.name}.',
                    link=reverse('announcements_page') + f'?church_id={church.id}'
                )

            return redirect('announcements_page')
    else:
        form = AnnouncementForm()

    return render(request, 'create_announcement.html', {'form': form})

@login_required
def edit_announcement(request, announcement_id):
    church = get_object_or_404(Church, id=request.session.get('church_id'))

    if not is_church_admin(request.user, church):
        return redirect('announcements_page')

    announcement = get_object_or_404(Announcement, id=announcement_id, church=church)

    if request.method == 'POST':
        form = AnnouncementForm(request.POST, instance=announcement)
        if form.is_valid():
            form.save()
            messages.success(request, "Announcement has been updated.")
            return redirect('announcements_page')
    else:
        form = AnnouncementForm(instance=announcement)

    return render(request, 'edit_announcement.html', {
        'form': form,
        'announcement': announcement
    })
            
@login_required
def announcements_page(request):
    church_id = request.GET.get('church_id') or request.session.get('church_id')

    if not church_id:
        return redirect('user_dashboard')

    church = get_object_or_404(Church, id=church_id)

    request.session['church_id'] = church_id

    announcements_list = Announcement.objects.filter(church=church).order_by('-is_pinned', '-created')

    paginator = Paginator(announcements_list, 5)
    page_number = request.GET.get('page')
    announcements = paginator.get_page(page_number)

    return render(request, 'announcements.html', {
        'announcements': announcements,
        'church': church,
        'is_admin': is_church_admin(request.user, church)
    })

@login_required
def delete_announcement(request, announcement_id):
    church = get_object_or_404(Church, id=request.session.get('church_id'))

    if not is_church_admin(request.user, church):
        return redirect('announcements_page')

    announcement = get_object_or_404(Announcement, id=announcement_id, church=church)

    if request.method == 'POST':
        announcement.delete()
        messages.success(request, "This announcement has been deleted.")
        return redirect('announcements_page')

    return render(request, 'delete_announcement.html', {
        'announcement': announcement
    })

# Events 

@login_required
def events_page(request):
    church_id = request.session.get("church_id")
    if not church_id:
        return redirect('user_dashboard')
    
    church = get_object_or_404(Church, id=church_id)
    is_admin = is_church_admin(request.user, church)

    events_list = Event.objects.filter(church=church).order_by('start')
    paginator = Paginator(events_list, 5)
    page_number = request.GET.get('page')
    events = paginator.get_page(page_number)

    return render(request, 'events_page.html', {
        "events": events,
        "church": church,
        'is_admin': is_admin,
    })

# Add Events
@login_required
def add_event(request):
    church_id = request.session.get('church_id')
    link = reverse('events_page')
    if not church_id:
        return redirect('user_dashboard')

    church = get_object_or_404(Church, id=church_id)

    if not is_church_admin(request.user, church):
        return redirect('user_dashboard')

    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.church = church
            event.save()
            memberships = ChurchUser.objects.filter(church=church).select_related('user')

            for membership in memberships:
                Notification.objects.create(
                    user=membership.user,
                    message=f"New event posted: {event.name}",
                    link=link
                )
            return redirect('events_page')
    else:
        form = EventForm()

    return render(request, 'add_event.html', {'form': form})

# Edit Events

@login_required
def edit_event(request, event_id):
    church_id = request.session.get('church_id')
    church = get_object_or_404(Church, id=church_id)

    if not is_church_admin(request.user, church):
        return redirect('events_page')

    event = get_object_or_404(Event, id=event_id, church=church)

    form = EventForm(request.POST or None, instance=event)

    if form.is_valid():
        form.save()
        return redirect('events_page')

    return render(request, 'add_event.html', {'form': form})

@login_required
def delete_event(request, event_id):
    church_id = request.session.get('church_id')
    church = get_object_or_404(Church, id=church_id)

    if not is_church_admin(request.user, church):
        return redirect('events_page')

    event = get_object_or_404(Event, id=event_id, church=church)

    if request.method == 'POST':
        event.delete()
        return redirect('events_page')

    return render(request, 'confirm_delete.html', {'event': event})

@login_required
def event_detail(request, event_id):
    church_id = request.session.get('church_id')
    church = get_object_or_404(Church, id=church_id)

    if not ChurchUser.objects.filter(user=request.user, church=church).exists():
        return redirect('user_dashboard')

    event = get_object_or_404(Event, id=event_id, church=church)

    return render(request, 'event_detail.html', {
        'event': event,
        'church': church,
        'is_admin': is_church_admin(request.user, church)
    })

# Members
@login_required
def members_page(request):
    church_id = request.session.get('church_id')
    church = get_object_or_404(Church, id=church_id)

    if not ChurchUser.objects.filter(user=request.user, church=church).exists():
        return redirect('user_dashboard')

    members_list = ChurchUser.objects.filter(church=church).select_related('user').order_by('user__last_name', 'user__first_name')
    paginator = Paginator(members_list, 20)
    page_number = request.GET.get('page')
    members = paginator.get_page(page_number)

    return render(request, 'members.html', {
        'church': church,
        'members': members,
        'is_admin': is_church_admin(request.user, church)
    })


# Prayer 

@login_required
def create_prayer_request(request):
    church_id = request.session.get('church_id')
    church = get_object_or_404(Church, id=church_id)

    if request.method == 'POST':
        form = PrayerRequestForm(request.POST)
        if form.is_valid():
            prayer = form.save(commit=False)
            prayer.church = church
            prayer.created_by = request.user
            prayer.approved = None
            prayer.save()

            # Notify admins
            admins = ChurchUser.objects.filter(church=church, role='admin').exclude(user=request.user)

            for admin in admins:
                Notification.objects.create(
                    user=admin.user,
                    message=f'New prayer request needs approval for {church.name}'
                )

            return redirect('prayer_requests')
    else:
        form = PrayerRequestForm()

    return render(request, 'create_prayer.html', {'form': form})

@login_required
def handle_prayer_request(request, prayer_id, action):
    church_id = request.session.get('church_id')
    church = get_object_or_404(Church, id=church_id)

    if not is_church_admin(request.user, church):
        return redirect('user_dashboard')

    prayer = get_object_or_404(PrayerRequest, id=prayer_id, church=church)

    link = reverse('prayer_requests')

    if action == 'approve':
        prayer.approved = True
        prayer.save()

        members = ChurchUser.objects.filter(church=church)

        for member in members:
            Notification.objects.create(
                user=member.user,
                message=f'New prayer request posted in {church.name}',
                link=link
            )

    elif action == 'deny':
        prayer.approved = False
        prayer.save()

        Notification.objects.create(
            user=prayer.created_by,
            message=f'Your prayer request in {church.name} was denied',
            link=link
        )

    return redirect('manage_prayers')

@login_required
def manage_prayers(request):
    church_id = request.session.get('church_id')
    church = get_object_or_404(Church, id=church_id)

    if not is_church_admin(request.user, church):
        return redirect('user_dashboard')

    prayers = PrayerRequest.objects.filter(
        church=church,
        approved=None
    ).order_by('-created')

    return render(request, 'manage_prayers.html', {
        'prayers': prayers,
        'church': church,
    })

@login_required
def edit_prayer(request, prayer_id):
    prayer = get_object_or_404(PrayerRequest, id=prayer_id)

    if prayer.created_by != request.user:
        return redirect('prayer_requests')

    if request.method == 'POST':
        form = PrayerRequestForm(request.POST, instance=prayer)
        if form.is_valid():
            prayer = form.save(commit=False)
            prayer.approved = None
            prayer.last_edited = timezone.now()
            prayer.save()

            # notify admins again
            admins = ChurchUser.objects.filter(church=prayer.church, role='admin')

            for admin in admins:
                Notification.objects.create(
                    user=admin.user,
                    message='A prayer request was edited and needs approval',
                    link=reverse('prayer_requests') 
                )

            return redirect('prayer_requests')
    else:
        form = PrayerRequestForm(instance=prayer)

    return render(request, 'create_prayer.html', {'form': form})

@login_required
def delete_prayer(request, prayer_id):
    church_id = request.session.get('church_id')
    church = get_object_or_404(Church, id=church_id)

    if not is_church_admin(request.user, church):
        return redirect('prayer_requests')

    prayer = get_object_or_404(PrayerRequest, id=prayer_id, church=church)

    prayer.delete()

    return redirect('prayer_requests')

@login_required
def mark_prayer_answered(request, prayer_id):
    prayer = get_object_or_404(PrayerRequest, id=prayer_id)

    if prayer.created_by != request.user:
        return redirect('prayer_requests')

    prayer.answered = True
    prayer.save()

    members = ChurchUser.objects.filter(church=prayer.church)

    for member in members:
        Notification.objects.create(
            user=member.user,
            message='A prayer request has been answered',
            link=reverse('prayer_requests')
        )

    return redirect('prayer_requests')

@login_required
def prayer_page(request):
    church_id = request.session.get("church_id")
    if not church_id:
        return redirect('user_dashboard')
    
    church = get_object_or_404(Church, id=church_id)
    is_admin = is_church_admin(request.user, church)

    prayer_list = PrayerRequest.objects.filter(church=church).filter(Q(approved=True) | Q(created_by=request.user)).order_by('-created')
    
    paginator = Paginator(prayer_list, 5)
    page_number = request.GET.get('page')
    prayers = paginator.get_page(page_number)


    return render(request, 'prayers_page.html', {
        "prayers": prayers,
        "church": church,
        'is_admin': is_admin,
    })

# Live Chat
@login_required
def chat_page(request, church_id):
    church = get_object_or_404(Church, id=church_id)

    chat_messages = ChatMessage.objects.filter(church=church).order_by('-created')[:50]

    chat_messages = list(chat_messages)[::-1] 

    return render(request, 'chat.html', {
        'church': church,
        'chat_messages': chat_messages
    })

@login_required
def load_more_messages(request, church_id):
    offset = int(request.GET.get('offset', 50))

    chat_messages = ChatMessage.objects.filter(church_id=church_id).order_by('-created')[offset:offset + 50]

    data = []
    for msg in chat_messages:
        data.append({
            "full_name": f"{msg.user.first_name} {msg.user.last_name}",
            "message": msg.message,
            "timestamp": msg.created.strftime("%b %d, %H:%M")
        })

    return JsonResponse({"messages": data})

@login_required
def chat_redirect(request):
    membership = ChurchUser.objects.filter(user=request.user).first()

    if not membership:
        return redirect('user_dashboard')

    return redirect('chat', church_id=membership.church.id)

