# Run Community Kenya

Web-first community platform for discovering nearby walking/running crews, joining scheduled sessions, checking in/out, and later tracking activities with GPS.

## Current Increment

This scaffold includes:

- Flask backend with auth, crews, and sessions APIs.
- SQLAlchemy models for users, crews, memberships, sessions, attendance, activities, and route points.
- React/Vite frontend with auth, home, discover, crews, activity, and profile pages.
- GPS tracking utilities started in `frontend/src/tracking`.
- Safety foundations for reports, blocks, organizer session permissions, and user-owned activity deletion.
- IndexedDB persistence for active activities and pending activity uploads.
- PWA manifest, service worker, offline shell, and install prompt support.
- Profile onboarding for neighborhood and approximate discovery coordinates.
- Manual activity entry for walks/runs when GPS is unavailable.
- State-aware session flow with organizer cancel/complete/no-show controls.

## V1 Privacy And Safety Rules

- Only crew organizers/admins can create sessions.
- Users can report or block other users from crew member lists.
- Users cannot report or block themselves.
- Users can delete their own saved activities and route points.
- Session actions are state-aware: join, check in, start activity, check out, completed.
- Crew organizers/admins can cancel sessions, complete sessions, and mark no-shows.
- Activity routes are returned only to the activity owner.
- Active GPS activity data is persisted locally in IndexedDB while tracking.
- Failed activity uploads are kept as pending sync records in IndexedDB.
- Saved profile coordinates are used only for nearby discovery and are returned only to the authenticated user.

## Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
flask --app run.py db init
flask --app run.py db migrate -m "initial schema"
flask --app run.py db upgrade
python seed.py
flask --app run.py run --debug
```

The backend defaults to SQLite for quick local development if no `.env` is present. Set `DATABASE_URL` to a PostgreSQL connection string, such as a Neon pooled URL, when using a hosted database.

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_BASE_URL` if the backend is not running on `http://localhost:5000`.

## Email Setup

Configure SMTP in `backend/.env` to enable welcome emails, password recovery, and admin broadcasts:

```env
APP_PUBLIC_URL=https://yourdomain.com
MAIL_SERVER=mail.yourdomain.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_USERNAME=no-reply@yourdomain.com
MAIL_PASSWORD=your-email-password
MAIL_DEFAULT_SENDER=no-reply@yourdomain.com
```

For cPanel email accounts, create the mailbox first, then copy its SMTP host, port, username, and password from cPanel's email client configuration screen. Use port `465` with `MAIL_USE_SSL=true` if your host requires SSL instead of TLS.

Service worker registration only runs in production builds. To test the install/offline behavior locally:

```bash
cd frontend
npm run build
npm run preview
```
