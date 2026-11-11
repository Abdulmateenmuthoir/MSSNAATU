# MSSN AATU — Member Portal

The official web application of the **Muslim Students' Society of Nigeria, Abiola Ajimobi Technical University, Ibadan** — a Django + MySQL platform for membership, news, programmes, a past-questions library and annual dues.

## Features

- **Student-only sign-in** — no public registration. The office creates every profile and emails the login details (matric number or email + password).
- **Forced password setup** — first-time sign-ins are asked to replace their temporary password (or continue with it for that session, with a persistent dashboard reminder).
- **Change password & forgot password** — full self-service reset by matric number or email.
- **Newsroom** — markdown articles with categories, moderated member comments and optional Brevo email announcements.
- **Programmes** — events with capacity, gender eligibility (brothers / sisters / everyone), registration deadlines, confirmation & reminder emails and CSV attendee export.
- **Past-questions library** — faculty/department/level browsing with protected downloads and a download counter.
- **Dues** — Paystack checkout, automatic confirmation callback, printable receipts and a finance dashboard with export.
- **Membership admin** — add students individually or by CSV import, issue/reset credentials, promote levels, activate/deactivate accounts.
- **Role-based access** — Super User, Administrator, Content Editor, Events Manager, Finance Officer, Library Manager, Member.
- **Public site** — home, about, executives, committees, news, programmes, library catalogue and contact form with newsletter signup.
- **Light/dark mode** — remembered per device, defaults to the OS preference.

## Stack

| Layer      | Choice                                        |
| ---------- | --------------------------------------------- |
| Backend    | Django 5.2 (custom `Student` user model)      |
| Database   | MySQL 8.4 (utf8mb4) via PyMySQL               |
| Frontend   | Tailwind CSS 3 built locally, vanilla JS      |
| Email      | Console (dev) / Brevo API (production)        |
| Payments   | Paystack                                      |
| Static     | WhiteNoise (hashed + compressed in production)|

## Quick start

```bash
# 1. Python environment
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 2. MySQL on port 3307 (Docker)
docker compose up -d

# 3. Environment
cp .env.example .env        # then edit values

# 4. Database
.venv/bin/python manage.py migrate

# 5. Demo data (optional but recommended)
.venv/bin/python manage.py seed_demo

# 6. Tailwind CSS
npm install
npm run css:build           # or: npm run css:watch while theming

# 7. Run
.venv/bin/python manage.py runserver
```

Open <http://localhost:8000>.

## Demo credentials

Created by `seed_demo` — **change every password before any real deployment**.

| Account            | Email                        | Password        | Role            |
| ------------------ | ---------------------------- | --------------- | --------------- |
| Super admin        | `admin@mssnaatu.org`         | `MssnDemo2026!` | Super User      |
| Editor             | `editor@mssnaatu.org`        | `MssnDemo2026!` | Content Editor  |
| Events             | `events@mssnaatu.org`        | `MssnDemo2026!` | Events Manager  |
| Finance            | `finance@mssnaatu.org`       | `MssnDemo2026!` | Finance Officer |
| Library            | `library@mssnaatu.org`       | `MssnDemo2026!` | Library Manager |
| Membership         | `membership@mssnaatu.org`    | `MssnDemo2026!` | Administrator   |
| Student            | `aisha.bello@example.com`    | `MssnDemo2026!` | Member          |

Seed data includes 6 faculties, 20 departments, 30 students, 14 past questions (generated PDFs), 5 posts, 5 programmes, 6 committees and an active dues cycle. The command is idempotent — safe to run again.

## Environment variables

All configuration lives in `.env` (see `.env.example`):

| Variable                   | Purpose                                                            |
| -------------------------- | ------------------------------------------------------------------ |
| `DJANGO_SECRET_KEY`        | Long random string                                                 |
| `DJANGO_DEBUG`             | `True` in development only                                         |
| `DJANGO_ALLOWED_HOSTS`     | Comma-separated hosts                                              |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Comma-separated origins                                         |
| `SITE_URL`                 | Absolute base URL used in emails                                   |
| `DB_*`                     | MySQL connection (matches `docker-compose.yml`)                    |
| `PAYSTACK_PUBLIC_KEY` / `PAYSTACK_SECRET_KEY` | Enable online dues (leave blank to disable the pay button) |
| `PAYSTACK_CALLBACK_URL`    | Where Paystack returns the student (`{SITE_URL}/dues/callback/`)   |
| `BREVO_API_KEY` / `BREVO_SENDER_EMAIL` / `BREVO_SENDER_NAME` | Transactional + campaign email    |
| `DEFAULT_FROM_EMAIL`       | Fallback sender for console/SMTP email                             |

## CSV import format

**Dashboard → Students → Import CSV.** Header names are flexible (e.g. `matric_no` or `matric`), names may be a single `full_name` column, and gender accepts `M/F`, `male/female`, `brother/sister`.

```csv
full_name,matric_no,email,gender,level,faculty,department
Halimah Balogun,AATU/MTH/21/013,halimah.balogun@example.com,Female,200,SCI,MTH
Musa Danjuma,AATU/EEE/23/024,musa.danjuma@example.com,Male,100,ENG,EEE
```

Faculty/department match by **code or name**; a temporary password is generated per student, credentials can be emailed, and every row is reported on the result screen.

## Tests

```bash
.venv/bin/python manage.py test
```

Covers authentication, the password-setup flow, permissions, event eligibility, dues payments/receipts and library downloads.

## Dues reminders (cron)

```bash
cd /path/to/MSSNAATU && /path/to/python manage.py send_dues_reminders
```

Emails each active member who has not paid the active cycle, at most once per 14 days (`--dry-run` previews the recipients). See [CPANEL_DEPLOYMENT.md](CPANEL_DEPLOYMENT.md) for the production (cPanel) setup, including Brevo variables and the cron entry.

## Project layout

```
mssnaatu/          settings, urls, wsgi/asgi
apps/accounts/     Student model, auth flows, student admin, CSV import
apps/core/         public pages, dashboard overview, executives/committees
apps/blog/         newsroom + email campaigns
apps/events/       programmes, registration, attendee export
apps/library/      past questions, protected downloads
apps/finance/      dues cycles, Paystack, receipts, reminders
templates/         public, dashboard, auth, finance, email templates
static/            Tailwind source (src/) + built CSS + app.js
```
