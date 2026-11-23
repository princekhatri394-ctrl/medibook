<<<<<<< HEAD
# MediBook (Django)

Hospital / doctor appointment booking system, migrated from plain PHP + MySQL to **Python + Django 4.2**.
The pages keep the original look (same HTML/CSS), but all backend logic is now Django.

## Features
- **Accounts** – register as patient or doctor, log in with email + password, log out. Users are sent to their own dashboard by role.
- **Patients** – choose city/area (saved in the DB), see nearby doctors first (same area → same city → others), book 30-minute slots, see and cancel appointments, edit profile.
- **Doctors** – onboarding: account → location → clinic details + office hours → choose plan. Dashboard shows appointments and lets the doctor confirm/complete/cancel them. Edit profile.
- **Plans** – Basic / Standard / Premium are seeded automatically by a migration.
- **Admin** – Django admin at `/admin/` replaces the old missing `admin/dashboard.php`.


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
<<<<<<< HEAD
Open: [medibook](https://medibook-wbq7.onrender.com/)
=======
Open https://medibook-wbq7.onrender.com
>>>>>>> 72e3032375adcae572675199c4a7713327f1692d

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
| Django |

| /auth/login/ |

| /auth/register/ |

| /auth/logout/ |

| /patient/location/ |

| /patient/dashboard/ |

| /patient/book/N/ |

| /doctor/location/ |

| /doctor/clinic-details/ |

| /doctor/select-plan/ |

| /doctor/dashboard/ |

| /patient/edit-profile/, /doctor/edit-profile/ |

| /admin/ |

## Tests
```bash
python manage.py test tests
```
=======
# medibook-
Doctor appointment booking system , it contains dual log in system for both doctor and paitent
>>>>>>> 23413a91a2d1e20d1410111b38677dd3831e3968
