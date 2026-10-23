# Clinic Bookings

A role-based clinic appointment system built with Django 5 and Django REST Framework. Patients book visits with doctors, doctors manage their schedule and time off, and administrators monitor the clinic and create doctor accounts.

Live demo: https://clinic-booking-4y1s.onrender.com (free tier, so the first load can take up to a minute).

---

## Features

### Patients
- Register a patient account and sign in (session authentication).
- Browse active doctors, optionally filtered by specialty, and read their short bios.
- See open time slots for a doctor on a chosen date and book one.
- View appointment history (oldest or newest first) and cancel upcoming booked appointments.

### Doctors
- View their own appointments (oldest or newest first).
- Mark a booked appointment as **Completed** or **No-show**.
- Add and remove time off. Days covered by time off have no bookable slots.
- Check their own free slots for any date.

### Administrators
- Dashboard with total appointments, today's appointments and a count per status (booked, completed, cancelled, no-show).
- Doctor workload table (total and currently booked appointments per doctor).
- Master appointment registry filterable by doctor, status and date, with sort order.
- **Add Doctor** form on the dashboard. Doctors cannot register themselves; only an admin can create them.

### How slots work
Free slots are generated from the doctor's weekly `Availability` windows and `slot_minutes`. A slot is removed if it is already booked, falls on a time-off day, is in the past, or has already passed today. A database constraint also prevents two booked appointments for the same doctor, date and time.

---

## Tech stack

- Python, Django 5.2, Django REST Framework 3.18
- PostgreSQL via `psycopg` 3
- `dj-database-url` for the production database URL
- WhiteNoise for static files, Gunicorn as the server
- Django templates with vanilla JavaScript (`fetch`) calling the API
- Custom CSS, Google Fonts (Outfit, Plus Jakarta Sans, Inter) and Font Awesome 6

Time zone is `Asia/Kolkata`.

---

## Project structure

```text
Clinic_booking/
├── accounts/                 # Custom User model, auth API, role permissions
│   ├── models.py             # User with role (patient / doctor / admin) and phone
│   ├── permissions.py        # IsPatient, IsDoctor, IsAdminRole
│   ├── serializers.py        # Register, Login, User serializers
│   ├── views.py              # Register, Login, Logout views
│   └── urls.py
├── clinic/
│   ├── models.py             # Doctor, Availability, TimeOff, Appointment
│   ├── serializers.py        # Includes DoctorCreateSerializer (admin only)
│   ├── services.py           # get_free_slots() and get_dashboard_stats()
│   ├── views.py
│   ├── urls.py
│   └── management/commands/  # Demo data seed command
├── config/                   # Settings, root URLs, WSGI
├── static/css/style.css
├── templates/
│   ├── base.html             # Layout, navigation, logout
│   ├── accounts/             # login.html, register.html
│   └── clinic/               # doctors, book, my_appointments,
│                             # doctor_schedule, dashboard
├── manage.py
└── requirements.txt
```

---

## Run locally

### 1. Set up

```bash
git clone https://github.com/swafwana/Clinic_booking.git
cd Clinic_booking
python -m venv venv
venv\Scripts\activate          # Windows (cmd)
# source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

### 2. Environment variables

Create a `.env` file in the project root (never commit it):

```env
SECRET_KEY=change-me
DEBUG=True
DB_NAME=clinic_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

If `DATABASE_URL` is set, the app uses it instead of the `DB_*` values. Make sure it is **not** set when you want to use your local database.

### 3. Database and admin

```bash
python manage.py migrate
python manage.py createsuperuser
```

`createsuperuser` does not set the app's `role` field, and the admin dashboard and its API require `role = admin`. Either change the role in Django admin (`/admin/`), or run the seed command below, which sets every superuser's role to admin.

### 4. Optional demo data

```bash
python manage.py seed_demo
```

This creates four doctors, three patients, working hours, a time-off entry and sample appointments in every status. All demo users share the password `demo1234`:

- Doctors: `dr_nair`, `dr_sharma`, `dr_iyer`, `dr_verma`
- Patients: `sara`, `rahul`, `priya`

The command is safe to rerun. Use demo data for development only, and delete or change those accounts before real use.

### 5. Start the server

```bash
python manage.py runserver
```

Open http://127.0.0.1:8000/ (it redirects to the login page).

---

## Pages

| URL | Who | Purpose |
|---|---|---|
| `/login/`, `/register/` | Public | Sign in, patient sign up |
| `/doctors/` | Patient | Browse doctors |
| `/doctors/<id>/book/` | Patient | Pick a date and slot |
| `/appointments/` | Patient | Own appointments |
| `/doctor/schedule/` | Doctor | Schedule and time off |
| `/dashboard/` | Admin | Metrics, registry, Add Doctor |
| `/admin/` | Superuser | Django admin |

The templates are served as plain pages; access is enforced by the API permissions, so a user of the wrong role sees an empty or failed page rather than data.

---

## API reference

All endpoints use session authentication and are authenticated by default. POST, PUT and DELETE requests need the `X-CSRFToken` header.

### Auth (`/api/auth/`)

| Method | Endpoint | Description | Access |
|---|---|---|---|
| POST | `/api/auth/register/` | Register a patient | Public |
| POST | `/api/auth/login/` | Sign in, returns the user and role | Public |
| POST | `/api/auth/logout/` | Sign out | Authenticated |

### Doctors and patients

| Method | Endpoint | Description | Access |
|---|---|---|---|
| GET | `/api/doctors/` | Active doctors (`?specialty=`) | Authenticated |
| GET | `/api/doctors/specialties/` | List of specialties | Authenticated |
| GET | `/api/doctors/<id>/slots/?date=YYYY-MM-DD` | Free slots for a date | Authenticated |
| GET | `/api/appointments/` | Own appointments (`?order=asc\|desc`) | Patient |
| POST | `/api/appointments/` | Book a slot (`doctor`, `date`, `time`, `reason`) | Patient |
| POST | `/api/appointments/<id>/cancel/` | Cancel an upcoming booked appointment | Patient |

### Doctor (`/api/doctor/`)

| Method | Endpoint | Description | Access |
|---|---|---|---|
| GET | `/api/doctor/appointments/` | Own appointments (`?order=`) | Doctor |
| POST | `/api/doctor/appointments/<id>/complete/` | Mark completed | Doctor |
| POST | `/api/doctor/appointments/<id>/no-show/` | Mark no-show | Doctor |
| GET | `/api/doctor/slots/?date=YYYY-MM-DD` | Own free slots | Doctor |
| GET | `/api/doctor/time-off/` | List time off | Doctor |
| POST | `/api/doctor/time-off/` | Add time off | Doctor |
| DELETE | `/api/doctor/time-off/<id>/` | Remove time off | Doctor |

### Admin (`/api/dashboard/`)

| Method | Endpoint | Description | Access |
|---|---|---|---|
| GET | `/api/dashboard/stats/` | Totals, status counts, per-doctor workload | Admin |
| GET | `/api/dashboard/appointments/` | Registry (`?doctor=&status=&date=&order=`) | Admin |
| POST | `/api/dashboard/doctors/` | Create a doctor account and profile | Admin |

Creating a doctor takes `username`, `first_name`, `password`, `specialty`, and optionally `last_name`, `email`, `bio` and `slot_minutes` (5 to 120, default 30). The server sets the role to doctor, validates the password with Django's validators, and adds default working hours of Monday to Friday, 09:00 to 17:00. Hours can be changed under **Availability** in Django admin.

---

## Deploy on Render

1. Create a **PostgreSQL** instance and a **Web Service** from this repository, both in the same region.
2. Build command:
   ```
   pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
   ```
3. Start command:
   ```
   gunicorn config.wsgi:application
   ```
4. Environment variables on the web service:

   | Variable | Value |
   |---|---|
   | `DATABASE_URL` | The database's **Internal** URL |
   | `SECRET_KEY` | A new, strong secret |
   | `DEBUG` | `False` (only the text `True` turns debug on) |
   | `PYTHON_VERSION` | Optional, to pin the Python version |

5. Do not set the `DB_*` variables on Render.

To run management commands (`createsuperuser`, `seed_demo`) from your computer against the hosted database, set `DATABASE_URL` to the database's **External** URL in that terminal window only, then clear it afterwards.

Free Render databases expire after a limited period, so export your data (`dumpdata`) or upgrade the plan if you want to keep it.

---

## Security notes

- Every API view checks the user's role through `IsPatient`, `IsDoctor` or `IsAdminRole`. The admin permission checks the `role` field, not `is_superuser`.
- Roles are assigned by the server. Public registration creates patients, and doctors can only be created by an admin through the protected endpoint.
- Patients and doctors can only read or change their own appointments and time off.
- A conditional unique constraint stops two booked appointments from sharing the same doctor, date and time.
- Secrets come from environment variables. Keep `.env` out of version control.
