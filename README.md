# SmartStudy Backend API

Production-style Django REST backend for an AI-powered study platform with authentication, chat tutoring, image scanning, profile progression, personal learning library, and optional two-factor authentication.

This project is designed to demonstrate backend engineering strengths for interviews: modular architecture, secure auth flows, API consistency, pagination, indexing strategy, and third-party AI service integration.

## What This Backend Solves

- Secure user onboarding with OTP email verification.
- JWT-based session management for API clients.
- Subject-aware AI tutoring via chat and image scan workflows.
- User profile progression tracking (study minutes, activity days, solved problems, badges, levels).
- Personal library for notes, images, and documents with folder organization and quota tracking.
- Optional 2FA verification flow.

## Tech Stack

- Python, Django, Django REST Framework
- JWT auth with djangorestframework-simplejwt
- OpenAPI/Swagger docs with drf-yasg
- SQLite (current default), PostgreSQL-ready dependency included
- AI integrations through HTTP APIs (OpenAI, Claude)
- CORS support, WhiteNoise middleware, pagination/filtering/throttling

## Architecture Overview

The codebase follows an app-per-domain Django structure:

- authapp: signup, OTP verification, login, logout, password reset
- profileapp: profile setup, profile fetch, study activity updates, badge/level logic
- chatapp: chat sessions, threaded chat history, AI replies, quick ask history
- scanapp: image upload + subject-aware AI explanation + scan history
- libraryapp: folders, notes, images, files, search, overview, storage accounting
- twofapp: send OTP, verify OTP, check 2FA status
- coreapp: reusable response mixin and standard pagination

## Key Backend Design Decisions

- Consistent API envelope
	All major endpoints return a unified response shape with success flag, message, data, and timestamp.

- Domain separation by Django apps
	Each business area has its own models, serializers, urls, and views for maintainability.

- UUID primary keys
	Entity IDs are UUIDs for better distribution and safer external exposure.

- Ownership-safe data access
	Query patterns are scoped to request.user for privacy and multi-tenant safety.

- Index-first modeling
	Models include indexes for frequent filters (user, subject, created_at, session) to support scalable list queries.

- Bounded list endpoints
	Standard pagination avoids unbounded responses and protects service performance.

- Environment-based secrets
	API keys and sensitive settings are loaded from environment variables, not hardcoded.

## Main API Surface

Base route groups:

- /auth/
- /chat/
- /scan/
- /profile/
- /library/
- /2fa/

### Authentication

- POST /auth/signup/
- POST /auth/verify-otp/
- POST /auth/resend-otp/
- POST /auth/login/
- POST /auth/logout/
- POST /auth/forgot-password/
- POST /auth/reset-password/

### Chat

- POST /chat/start/
- GET /chat/sessions/
- POST /chat/{session_id}/message/
- GET /chat/{session_id}/messages/
- POST /chat/ask/

### Scan

- POST /scan/
- GET /scan/history/

### Profile

- POST /profile/setup/
- GET /profile/
- PATCH /profile/activity/

### Library

- Folder CRUD style endpoints
- Note create/list/detail endpoints
- Image and file upload/detail/delete endpoints
- Search and overview endpoints
- Folder contents endpoint

### Two-Factor Authentication

- POST /2fa/send/
- POST /2fa/verify/
- GET /2fa/status/

## Swagger API Docs

Swagger is available per major module:

- /auth/swagger/
- /chat/swagger/
- /scan/swagger/
- /profile/swagger/

JSON schema endpoints are also exposed for these modules.

## Data Model Snapshot

- User + OTP
	Custom user model with verification state and OTP lifecycle.

- UserProfile
	One-to-one profile with progress metrics and computed badges/levels.

- ChatSession + ChatMessage + AskChatHistory
	Conversation threads, ordered messages, and quick ask history.

- ScanHistory
	Uploaded image, subject, question, AI response, and created time.

- Folder + Note + LibraryImage + LibraryFile + UserStorageUsage
	Organized personal knowledge base and per-user storage accounting.

## Local Setup

1. Clone repository and move into project root.
2. Create and activate virtual environment.
3. Install dependencies.
4. Configure environment variables.
5. Run migrations.
6. Start development server.

Example commands:

```bash
python -m venv venv
# Windows PowerShell
venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Environment Variables

Set these in your environment or .env file:

- SECRET_KEY
- ALLOWED_HOSTS
- CSRF_TRUSTED_ORIGINS
- OPENAI_API_KEY
- CLAUDE_API_KEY

## Security and Reliability Notes

- JWT authentication enabled via DRF SimpleJWT.
- Throttling configured for anonymous and authenticated users.
- OTP flows include expiration and one-time usage controls.
- User-scoped query filtering protects cross-user data access.

## Recruiter-Focused Highlights

If discussing this project in interviews, emphasize:

- Built a modular, domain-driven Django backend with clean separation of concerns.
- Implemented full auth lifecycle: signup, OTP verify, JWT login/logout, password reset.
- Integrated multi-provider AI workflows (chat + vision) with resilient error handling.
- Designed scalable list endpoints with pagination and indexed query patterns.
- Created consistent API contracts to simplify frontend and mobile integration.
- Added profile gamification logic (badges/levels) as computed backend business rules.

## Future Improvements

- Move AI calls to Celery background tasks for better latency and reliability under load.
- Add comprehensive automated tests per app (unit + API integration).
- Add role-based permissions for admin/reporting features.
- Add observability (structured logging, tracing, metrics).

## Project Status

Active backend project suitable for portfolio and backend interview discussion.
