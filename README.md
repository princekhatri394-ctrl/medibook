# MediBook (Django)

Hospital / doctor appointment booking system, migrated from plain PHP + MySQL to **Python + Django 4.2**.
The pages keep the original look (same HTML/CSS), but all backend logic is now Django.

## Features
- **Accounts** – register as patient or doctor, log in with email + password, log out. Users are sent to their own dashboard by role.
- **Patients** – choose city/area (saved in the DB), see nearby doctors first (same area → same city → others), book 30-minute slots, see and cancel appointments, edit profile.
- **Doctors** – onboarding: account → location → clinic details + office hours → choose plan. Dashboard shows appointments and lets the doctor confirm/complete/cancel them. Edit profile.
- **Plans** – Basic / Standard / Premium are seeded automatically by a migration.
- **Admin** – Django admin at `/admin/` replaces the old missing `admin/dashboard.php`.

## What was fixed compared to the PHP version
- Django ORM instead of string-built SQL; CSRF protection on every form; session is rotated on login.
- Passwords hashed with Django's hasher.
- Booking rejects past dates/times, days the doctor is closed, slots outside office hours, and double bookings (also enforced by a DB unique constraint).
- Doctor status updates accept only pending / confirmed / completed / cancelled, and only for the doctor's own appointments. Patients can only cancel their own appointments.
- Missing pages added: plan selection, edit profile (both roles), landing redirect, admin.
- Registration now leads into the location step; patient location is stored in the `patients` table.

## Project layout
```
medibook/        settings, root URLs
accounts/        custom User model (email login, role), register/login/logout, seed_demo command
doctors/         Doctor, SubscriptionPlan, DoctorSubscription; location, clinic details, plans, dashboard
patients/        Patient, Appointment; location, dashboard, booking, cancel, booked-slots JSON API
templates/       Django templates (converted from the PHP pages)
static/css/      CSS extracted from the PHP pages
tests/           automated tests (python manage.py test tests)
```

## Run it (SQLite, no setup)
```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo        # optional demo data
python manage.py runserver
```
Open http://127.0.0.1:8000/

Demo accounts (password `demo1234` for all):
| Role | Email |
|---|---|
| Admin | admin@medibook.test |
| Doctor | priya@medibook.test, arjun@medibook.test, neha@medibook.test |
| Patient | patient@medibook.test |

Create your own admin with `python manage.py createsuperuser`.

## Use MySQL / MariaDB (XAMPP) instead
```bash
pip install mysqlclient
# create an empty database first, e.g. in phpMyAdmin: CREATE DATABASE medibook CHARACTER SET utf8mb4;
export DB_ENGINE=mysql DB_NAME=medibook DB_USER=root DB_PASSWORD= DB_HOST=127.0.0.1 DB_PORT=3306
python manage.py migrate
```
(On Windows PowerShell use `$env:DB_ENGINE="mysql"` etc.)

## Settings via environment variables
| Variable | Default | Purpose |
|---|---|---|
| `DJANGO_SECRET_KEY` | dev key | **Set this in production** |
| `DJANGO_DEBUG` | `1` | Set `0` in production |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1,*` | Comma-separated hosts |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | empty | e.g. `https://example.com` |
| `DB_ENGINE` | `sqlite` | `mysql` to use MySQL/MariaDB |

## URL map (old PHP → new Django)
| PHP | Django |
|---|---|
| auth/login.php | /auth/login/ |
| auth/register.php | /auth/register/ |
| auth/logout.php | /auth/logout/ |
| patient/location.php | /patient/location/ |
| patient/dashboard.php | /patient/dashboard/ |
| patient/book-appointment.php?doctor_id=N | /patient/book/N/ |
| doctor/select-location.php | /doctor/location/ |
| doctor/clinic-details.php | /doctor/clinic-details/ |
| doctor/select-plan.php (was missing) | /doctor/select-plan/ |
| doctor/dashboard.php | /doctor/dashboard/ |
| */edit-profile.php (were missing) | /patient/edit-profile/, /doctor/edit-profile/ |
| admin/dashboard.php (was missing) | /admin/ |

## Deployment
Production checklist (all done through environment variables, no code changes):
- `DJANGO_DEBUG=0`
- `DJANGO_SECRET_KEY=<long random string>`
- `DJANGO_ALLOWED_HOSTS=yourdomain.com` and `DJANGO_CSRF_TRUSTED_ORIGINS=https://yourdomain.com`
- `DATABASE_URL=postgres://...` (or keep SQLite on hosts with a persistent disk)
- Build: `./build.sh` (installs packages, `collectstatic`, `migrate`)
- Start: `gunicorn medibook.wsgi:application` (see `Procfile`)

CSS is served by WhiteNoise, so no separate web server config is needed.

**Render (free):** push the project to GitHub, then Render Dashboard -> New -> Blueprint -> choose the repo. `render.yaml` creates the web service and a PostgreSQL database and sets all variables. After the first deploy, open the Render Shell and run `python manage.py createsuperuser` (and optionally `python manage.py seed_demo`).

**PythonAnywhere (free):** upload the zip, create a virtualenv and `pip install -r requirements.txt`, add a "Manual configuration" web app pointing its WSGI file to `medibook.wsgi`, set the environment variables above in the WSGI file, map `/static/` to the `staticfiles` folder, then run `python manage.py collectstatic` and `python manage.py migrate`.

## Tests
```bash
python manage.py test tests
```
