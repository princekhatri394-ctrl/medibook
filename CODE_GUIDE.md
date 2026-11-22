# MediBook – Code Guide

This explains every part of the Django project: what each file does, which technology/Django feature it uses, and where it came from in the old PHP version.

---

## 1. Technologies used

| Layer | Technology | Where |
|---|---|---|
| Backend language | **Python 3.10+** | all `.py` files |
| Web framework | **Django 4.2 (LTS)** | whole project |
| Database (default) | **SQLite** – a single file `db.sqlite3`, no server needed | `medibook/settings.py` |
| Database (optional) | **MySQL / MariaDB** (your XAMPP one) via `mysqlclient` | `medibook/settings.py` (`DB_ENGINE=mysql`) |
| Database access | **Django ORM** (Python classes instead of SQL strings) | `*/models.py`, `*/views.py` |
| Login / passwords | **django.contrib.auth** (PBKDF2 password hashing, sessions) | `accounts/` |
| Forms & validation | **Django Forms** | `*/forms.py` |
| HTML pages | **Django Template Language** (`{{ }}`, `{% %}`) | `templates/` |
| Styling | **CSS3** (your original styles, moved into files) + Google Fonts | `static/css/` |
| Browser scripts | **Plain JavaScript** (`fetch()` for booked slots, calendar, presets) | inside `templates/*.html` |
| Admin panel | **django.contrib.admin** | `*/admin.py`, URL `/admin/` |
| Tests | **Django TestCase** (built on Python `unittest`) | `tests/test_flows.py` |

---

## 2. How a request flows (the big picture)

```
Browser  →  medibook/urls.py  →  app urls.py  →  view function (views.py)
                                                   │  uses models.py (database)
                                                   │  uses forms.py (validation)
                                                   ▼
                                             template (.html) + static CSS  →  HTML back to browser
```

Example: patient opens `/patient/book/3/`
1. `medibook/urls.py` sees `patient/` → hands over to `patients/urls.py`.
2. `patients/urls.py` matches `book/<int:doctor_id>/` → calls `views.book_appointment(request, doctor_id=3)`.
3. The view loads Doctor 3 from the DB (`models.py`), checks the user is a patient (`@role_required`).
4. It renders `templates/patients/book_appointment.html` with the doctor's data.

In PHP each `.php` file did all of this at once (SQL + logic + HTML). Django splits it into **URL → View → Model → Template** (this pattern is called MVT).

---

## 3. Folder by folder

### `manage.py`
Django's command-line tool. You use it for:
- `python manage.py runserver` – start the website (replaces Apache)
- `python manage.py migrate` – create/update database tables (replaces importing the `.sql` file)
- `python manage.py seed_demo` – add demo doctors/patient/admin
- `python manage.py createsuperuser` – make an admin account
- `python manage.py test tests` – run automated tests

### `medibook/` – project configuration
| File | What it does |
|---|---|
| `settings.py` | All configuration. **Replaces `includes/db.php`.** Lists installed apps, middleware (security layers), templates folder, static folder, database, timezone `Asia/Kolkata`, and `AUTH_USER_MODEL = "accounts.User"` (tells Django to use our own User). Reads secrets/DB settings from environment variables so no password is hard-coded. |
| `urls.py` | The main address book: `/auth/…` → accounts, `/doctor/…` → doctors, `/patient/…` → patients, `/admin/` → admin, `/` → `index` (sends you to login or your dashboard). |
| `wsgi.py`, `asgi.py` | Entry points used when deploying to a real server. You don't need to touch them. |

Important pieces in `settings.py`:
- **`MIDDLEWARE`** – code that runs on every request:
  - `SessionMiddleware` – keeps you logged in (replaces `session_start()`)
  - `CsrfViewMiddleware` – blocks forged form submissions (PHP had none)
  - `AuthenticationMiddleware` – puts the logged-in user in `request.user` (replaces `$_SESSION['user_id']`)
  - `MessageMiddleware` – the green/red pop-up messages ("Appointment updated.")
- **`AUTH_PASSWORD_VALIDATORS`** – min 6 chars, not a common password, not only numbers.
- **`DATABASES`** – SQLite by default; MySQL if `DB_ENGINE=mysql`.

---

### `accounts/` – users, login, register, logout (replaces `auth/` + parts of `includes/db.php`)

| File | What it does |
|---|---|
| `models.py` | **`User`** model = your old `users` table. Fields: `name`, `email` (unique, used to log in), `phone`, `role` (`patient` / `doctor` / `admin`), plus Django's built-ins (`password` hash, `is_active`, `is_staff`, `date_joined`, `last_login`). `UserManager` creates users with hashed passwords (`set_password` replaces `password_hash()`). |
| `decorators.py` | `redirect_by_role(user)` – sends admin → `/admin/`, doctor → doctor dashboard, patient → patient dashboard (**replaces PHP `redirectByRole()`**). `@role_required("doctor")` – put above a view to say "must be logged in AND be a doctor" (**replaces `requireLogin()` + manual role checks**). |
| `forms.py` | `RegisterForm` – validates name/email/phone/password, checks email not already used, passwords match, password strong enough, doctor fields (specialization, experience, fees). `UserProfileForm` – edit name/phone. `first_error()` – picks the first error to show in your existing red alert box. |
| `views.py` | `index` – home redirect. `login_view` – uses `authenticate()` (replaces `password_verify()`) and `login()` (creates a fresh session ID – PHP didn't). `register_view` – creates the User **and** the Doctor/Patient row inside `transaction.atomic()` (both saved or neither), logs in, sends to the location step. `logout_view` – ends session. |
| `urls.py` | `/auth/login/`, `/auth/register/`, `/auth/logout/` |
| `admin.py` | How users appear in `/admin/` (columns, filters, search). |
| `management/commands/seed_demo.py` | Custom `manage.py seed_demo` command: makes 1 admin, 3 doctors, 1 patient (password `demo1234`). |
| `migrations/` | Auto-generated files that create the `User` table. |

---

### `doctors/` – everything for doctors (replaces `doctor/*.php`)

**`models.py`**
| Name | What it is |
|---|---|
| `Doctor` | = old `doctors` table. Linked 1-to-1 with `User`. Fields: specialization, experience, fees, bio, clinic city/area/name/address/description, **`office_timings`** (a `JSONField`, e.g. `{"Mon": "9:00 AM - 6:00 PM"}` – a missing day means closed). |
| `Doctor.slots_for(day)` | Returns the 30-minute slots for that date from office timings. Used to validate bookings. |
| `Doctor.active_subscription()` | Current active, non-expired plan (or none). |
| `SubscriptionPlan` | = old `subscription_plans` table (name, price, days, limits, features). |
| `DoctorSubscription` | = old `doctor_subscriptions` table (which doctor is on which plan, start/end date, status). |
| `generate_slots()` / `parse_display_time()` | Helpers: turn `"9:00 AM - 6:00 PM"` into `9:00, 9:30, … 5:30`. |
| `DAYS`, `SPECIALIZATIONS`, `SLOT_MINUTES = 30` | Constants shared across the app. |

**`views.py`**
| View | URL | Replaces | What it does |
|---|---|---|---|
| `location` | `/doctor/location/` | `doctor/select-location.php` | Saves clinic city/area, then goes to clinic details (first time) or dashboard. |
| `clinic_details` | `/doctor/clinic-details/` | `doctor/clinic-details.php` | Saves clinic name/address/description and office hours. `_parse_timings()` checks every ticked day has a valid open < close time. Then goes to plan selection. |
| `select_plan` | `/doctor/select-plan/` | `doctor/select-plan.php` (**was missing**) | Lists plans; choosing one cancels the old subscription and creates a new one (start today, end today + plan days). |
| `dashboard` | `/doctor/dashboard/` | `doctor/dashboard.php` | Profile, clinic info, timings, subscription, and all appointments with counts (total, today, pending, completed). Tabs via `?tab=`. |
| `update_appointment_status` | `/doctor/appointments/<id>/status/` | status form in `dashboard.php` | POST only. Only the doctor's **own** appointment, and only `pending/confirmed/completed/cancelled` are accepted. |
| `edit_profile` | `/doctor/edit-profile/` | `doctor/edit-profile.php` (**was missing**) | Edit name, phone, specialization, experience, fees, bio. |

Other files: `forms.py` (`DoctorProfileForm`), `admin.py` (doctors/plans/subscriptions in `/admin/`), `urls.py`, `migrations/0001_initial.py` (tables) and **`migrations/0002_seed_plans.py`** (automatically inserts Basic ₹0, Standard ₹499, Premium ₹999 when you run `migrate`).

---

### `patients/` – everything for patients (replaces `patient/*.php`)

**`models.py`**
| Name | What it is |
|---|---|
| `Patient` | = old `patients` table. 1-to-1 with `User`. Date of birth, gender, blood group, **`patient_city` / `patient_area`** (PHP only kept these in the session – now saved). |
| `Appointment` | = old `appointments` table. patient, doctor, date, time slot, reason, status, created time. `Status` choices limit the allowed values. **`UniqueConstraint`** – the database itself refuses two active bookings for the same doctor + date + time. |

**`views.py`**
| View | URL | Replaces | What it does |
|---|---|---|---|
| `location` | `/patient/location/` | `patient/location.php` | Saves city/area to the database ("All" clears it). |
| `dashboard` | `/patient/dashboard/` | `patient/dashboard.php` | Profile, doctor list sorted nearest first (same area → same city → others, using `Case/When` in the query), each doctor's hours today, your appointments and counts. |
| `book_appointment` | `/patient/book/<doctor_id>/` | `patient/book-appointment.php` | Shows calendar + slots. On submit `_booking_error()` rejects past dates, closed days, times outside hours, times already passed today. Then inside a transaction it locks and re-checks the slot (`select_for_update`) and creates the appointment. `IntegrityError` catches the rare case of two people clicking at the same moment. |
| `booked_slots` | `/patient/book/<doctor_id>/slots/?date=YYYY-MM-DD` | `?fetch_slots=1` part of `book-appointment.php` | Returns JSON list of taken times, e.g. `["10:00:00"]`. The page's JavaScript `fetch()` calls this to grey out booked slots. |
| `cancel_appointment` | `/patient/appointments/<id>/cancel/` | cancel form in `dashboard.php` | POST only. Only your **own** pending/confirmed appointment. |
| `edit_profile` | `/patient/edit-profile/` | `patient/edit-profile.php` (**was missing**) | Edit name, phone, DOB, gender, blood group. |

Other files: `forms.py` (`PatientProfileForm`), `admin.py`, `urls.py`, `migrations/`.

---

### `templates/` – the HTML (from your PHP pages)

Your HTML/CSS design is unchanged; only the PHP bits were replaced with Django template tags:

| PHP | Django template |
|---|---|
| `<?= htmlspecialchars($doctor['name']) ?>` | `{{ doctor.name }}` (auto-escaped – safe by default) |
| `<?php if ($error): ?> … <?php endif; ?>` | `{% if error %} … {% endif %}` |
| `<?php foreach ($appointments as $a): ?>` | `{% for a in appointments %} … {% endfor %}` |
| `href="dashboard.php"` | `href="{% url 'patients:dashboard' %}"` |
| `<?= json_encode($timings) ?>` | `{{ timings\|json_script:"doc-timings" }}` (safe JSON for JavaScript) |
| *(nothing)* | `{% csrf_token %}` in every POST form |

| File | Page |
|---|---|
| `base.html` | Shared layout: `<head>`, Google Fonts, pop-up messages (toasts). Every page `{% extends "base.html" %}`. |
| `edit_profile.html` | One edit-profile page shared by doctors and patients. |
| `accounts/login.html`, `register.html` | Login and registration (role toggle shows doctor fields). |
| `doctors/location.html`, `clinic_details.html`, `select_plan.html`, `dashboard.html` | Doctor onboarding steps + dashboard. |
| `patients/location.html`, `dashboard.html`, `book_appointment.html` | Patient pages. |

JavaScript still lives inside the templates (same as before): city/area picker, office-hour presets, character counter, calendar, slot loading with `fetch()`.

### `static/css/` – styles
Each page's old `<style>` block moved into its own file (e.g. `patients_dashboard.css`), loaded with `{% static 'css/…' %}`. `extra.css` holds the styles for the new plan and edit-profile pages.

### `tests/test_flows.py` – automated tests (10 tests)
Checks: patient register → location → dashboard; doctor register → location → clinic → plan; duplicate email / password mismatch; login redirect by role and wrong password; patients can't open doctor pages; booking rules (double booking, outside hours, past date, JSON slots); closed day; cancel + only valid statuses; another patient can't cancel your appointment; every page loads.

---

## 4. Old PHP table → new Django model

| PHP table | Django model | File |
|---|---|---|
| `users` | `User` | `accounts/models.py` |
| `doctors` | `Doctor` | `doctors/models.py` |
| `patients` | `Patient` | `patients/models.py` |
| `appointments` | `Appointment` | `patients/models.py` |
| `subscription_plans` | `SubscriptionPlan` | `doctors/models.py` |
| `doctor_subscriptions` | `DoctorSubscription` | `doctors/models.py` |
| `time_slots` | *(not needed)* – slots are calculated from `office_timings` | `doctors/models.py` → `slots_for()` |

## 5. Security: before vs after

| Problem in PHP | How Django handles it |
|---|---|
| SQL built from strings (`"... WHERE id='$id'"`) | ORM sends values separately → no SQL injection |
| No CSRF protection | `CsrfViewMiddleware` + `{% csrf_token %}` |
| Session ID not changed after login | `login()` rotates it |
| `htmlspecialchars` before saving (double escaping) | Raw text saved; templates escape on output |
| root user with empty password in code | DB settings read from environment variables |
| Any status value accepted | Only `Appointment.Status` values allowed |
| Anyone could act on any appointment ID | Views filter by the logged-in doctor/patient (404 otherwise) |
| Double booking possible | Row lock + database unique constraint |
