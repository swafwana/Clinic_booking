# 🏥 MedCare Clinic Booking System

A full-stack clinic and appointment scheduling platform built with **Django 5** and **Django REST Framework (DRF)**. It provides a secure, role-based workflow for **Patients**, **Doctors**, and **Clinic Administrators** with a modern, responsive healthcare UI.

---

## ✨ Features

### 👤 Patient Portal
* **Self-Service Registration & Login:** Create a patient account with secure password validation and session authentication.
* **Specialist Directory:** Browse active doctors, view medical specialties, and read practitioner bios.
* **Dynamic Slot Booking:** Real-time calculation of available consultation slots based on doctor working hours, slot duration, and scheduled leaves.
* **Appointment Management:** Track upcoming and historical visits, review consultation notes, and cancel appointments with immediate slot release.

### 🩺 Doctor Portal
* **Daily Schedule & Roster:** View all booked patient consultations with patient details and visit reasons.
* **Appointment Actions:** Mark visits as **Completed** or **No-Show** directly from the schedule.
* **Self-Service Time-Off & Leaves:** Schedule vacations, conferences, or personal leaves. Days marked as time off automatically block appointment slots from patient bookings.
* **Free Slots Inspector:** Check open consultation slots on any calendar date.

### ⚡ Administrator Dashboard
* **Performance Overview (KPIs):** Real-time analytics displaying total visits, appointments today, and status breakdowns (Booked, Completed, Cancelled, No-Show).
* **Doctor Workload Metrics:** Table displaying total consultations and currently active bookings per practitioner.
* **Master Appointment Registry:** Full database registry with filtering by Doctor, Status, Date, and Sort Order (Ascending / Descending).

---

## 🛠️ Tech Stack

* **Backend:** Python 3.11+, Django 5.2, Django REST Framework (DRF)
* **Database:** PostgreSQL (with `psycopg3` driver)
* **Static Assets & Server:** WhiteNoise, Gunicorn
* **Frontend:** Django Templates, Vanilla JavaScript (ES6+ Fetch API)
* **Design & Styling:** Custom CSS3 Healthcare Design System, Google Fonts (*Plus Jakarta Sans*), Font Awesome 6 Icons

---

## 📁 Project Structure

```text
Clinic_booking/
├── accounts/               # User authentication, custom User model, roles & permissions
│   ├── models.py           # Custom User with Role enum (Patient, Doctor, Admin)
│   ├── permissions.py      # IsPatient, IsDoctor, IsAdminRole DRF permissions
│   ├── serializers.py      # RegisterSerializer, LoginSerializer, UserSerializer
│   └── views.py            # Login, Logout, and Register API views
├── clinic/                 # Clinic management & scheduling logic
│   ├── models.py           # Doctor, Availability, TimeOff, Appointment models
│   ├── serializers.py      # Doctor, Appointment, TimeOff serializers
│   ├── services.py         # Slot generation engine (get_free_slots) & dashboard stats
│   └── views.py            # API views for booking, cancellations, leaves, dashboard
├── config/                 # Project settings & root URL configurations
├── static/
│   └── css/
│       └── style.css       # Complete modern healthcare UI stylesheet & design tokens
├── templates/              # HTML Templates
│   ├── base.html           # Master layout with navigation header & footer
│   ├── accounts/           # Login and Registration pages
│   └── clinic/             # Doctors list, booking, schedule, dashboard, appointments
├── manage.py
└── requirements.txt
```

---

## 🚀 Getting Started

### 1. Prerequisites
* **Python 3.11+** installed
* **PostgreSQL** running locally or in the cloud (Neon, Supabase, Railway, etc.)

### 2. Clone and Setup Environment

```powershell
# Clone the repository
git clone https://github.com/your-username/Clinic_booking.git
cd Clinic_booking

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate   # On Windows (PowerShell)
# source venv/bin/activate # On macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-django-secret-key-here
DEBUG=True
DB_NAME=clinic_db
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432
```

### 4. Database Migrations

```powershell
python manage.py migrate
```

### 5. Create an Administrator Account

```powershell
python manage.py createsuperuser
```
*(Make sure to set the `role` to `admin` in the database or shell for admin dashboard access).*

### 6. Run the Development Server

```powershell
python manage.py runserver
```

Open **`http://127.0.0.1:8000/`** in your browser.

---

## 🔌 API Endpoints Reference

### Authentication (`/api/auth/`)
| Method | Endpoint | Description | Access |
|---|---|---|---|
| `POST` | `/api/auth/register/` | Register a new patient account | Public |
| `POST` | `/api/auth/login/` | Sign in (creates session cookie) | Public |
| `POST` | `/api/auth/logout/` | Sign out (destroys session) | Authenticated |

### Patient Endpoints
| Method | Endpoint | Description | Access |
|---|---|---|---|
| `GET` | `/api/doctors/` | List all active doctors (optional `?specialty=`) | Authenticated |
| `GET` | `/api/doctors/<id>/slots/?date=YYYY-MM-DD` | Get available time slots for a doctor on a date | Authenticated |
| `GET` | `/api/appointments/` | List current patient's appointments (`?order=asc/desc`) | Patient |
| `POST` | `/api/appointments/` | Book a consultation slot | Patient |
| `POST` | `/api/appointments/<id>/cancel/` | Cancel an upcoming booking | Patient |

### Doctor Endpoints (`/api/doctor/`)
| Method | Endpoint | Description | Access |
|---|---|---|---|
| `GET` | `/api/doctor/appointments/` | View patient schedule (`?order=asc/desc`) | Doctor |
| `POST` | `/api/doctor/appointments/<id>/complete/` | Mark visit as Completed | Doctor |
| `POST` | `/api/doctor/appointments/<id>/no-show/` | Mark visit as No-Show | Doctor |
| `GET` | `/api/doctor/slots/?date=YYYY-MM-DD` | Inspect open slots on a specific date | Doctor |
| `GET` | `/api/doctor/time-off/` | List doctor's scheduled leaves | Doctor |
| `POST` | `/api/doctor/time-off/` | Submit a new leave / time-off | Doctor |
| `DELETE`| `/api/doctor/time-off/<id>/` | Cancel / remove a scheduled leave | Doctor |

### Admin Endpoints (`/api/dashboard/`)
| Method | Endpoint | Description | Access |
|---|---|---|---|
| `GET` | `/api/dashboard/stats/` | Overview counts and per-doctor workload | Admin |
| `GET` | `/api/dashboard/appointments/` | Filter appointments (`?doctor=&status=&date=&order=`) | Admin |

---

## 🔒 Security Highlights

* **Role-Based Access Control (RBAC):** Permissions are verified on every DRF view (`IsPatient`, `IsDoctor`, `IsAdminRole`).
* **Database Unique Constraints:** Uses PostgreSQL conditional unique constraints (`condition=Q(status="booked")`) preventing double-booking race conditions at the database level.
* **Safe Mass Assignment:** Public registration endpoint strictly hardcodes the `patient` role, eliminating privilege escalation risks.
* **IDOR Prevention:** Doctors and Patients can only access, modify, or delete their own appointments and leave requests.

---


