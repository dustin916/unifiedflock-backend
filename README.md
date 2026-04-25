# Unified Flock Backend/WebApp

A multi-tenant SaaS backend built with Django for managing churches and small group communities. It supports membership management, real-time communication, prayer request tracking with privacy controls, and event/announcement broadcasting to streamline community engagement.

## Tech Stack
- Framework: Python (Django)
- API: Django REST Framework (DRF)
- Real-Time: Django Channels (WebSockets)
- ASGI Server: Daphne
- Database: SQLite (Default) / PostgreSQL ready
- Authentication: Token-Based (for Mobile) and Session-based (for Web)

## Key Features
- Multi-Tenant Management: Fully isolated data per organization with role-based access control (Admin, Leader, Member) and a structured join request workflow for managing membership.
- Prayer Wall: A community prayer system with privacy controls (private, public, or anonymous), moderation workflows for content approval, and the ability to mark prayers as answered to track community support.
- Event & Announcement Engine: A scheduling and communication system supporting recurring events, automated cleanup of expired events, and pinned announcements for highlighting important updates.
- Real-Time Communication: Real-time group messaging powered by WebSockets via Django Channels, along with live notifications for member activity and system updates.

## What I Learned
- Building multi-tenant systems: How to structure a database so that all data (events, prayers, chat messages) is tied to a specific church, ensuring complete data separation between organizations.
- Real-time features with Django Channels: How to use WebSockets to build live chat and notifications, moving beyond the standard request/response cycle.
- Complex business logic in Django: How to implement recurring events (weekly, bi-weekly, monthly) and automatically clean up expired data.
- Supporting multiple authentication styles: How to combine session-based login for a web dashboard with token-based authentication for a mobile app in the same backend.
- Content moderation systems: How to design approval workflows (pending/approved states) for user-generated content like prayer requests to maintain community standards.

## Status
The website portion, aside from styling, is complete. The backend portion is essentially complete, but will be edited as necessary while building the mobile portion of the app.

## Demo Video



https://github.com/user-attachments/assets/c6ea80e4-c221-4375-82ee-e433aa5ad770

