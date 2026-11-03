# Rental Property Management Platform 

A Django-based rental property management platform with Admin, Property Owner, Tenant, and Technician roles.

## Features

- Role-based authentication and authorization
- Owner property/room/image/amenity management
- Tenant property discovery, search, rent filters, sorting, and saved-property shortlist
- Admin-reviewed property verification status and document submission; the public verified badge is only shown after admin approval
- Rental requests (move-in date and rental duration of 1-60 months) and owner approval/rejection
- Booking management, including the rental duration and stay end date
- Mock payments with transaction history
- Maintenance ticket workflow: Open → Assigned → Accepted → In Progress → Resolved → Closed, with rejected jobs available for reassignment
- Maintenance evidence photos before and after repair, plus technician resolution notes
- Technician assignment and technician dashboard
- Property reporting and admin review
- Responsive landing page, clearer role-based navigation, and featured listing cards
- Email notifications using Django's console email backend
- Bootstrap responsive UI with a light / dark mode button in the menu bar
- Tested with Django 6.1 (`requirements.txt` allows Django 5.0 up to, but not including, 7.0)
- Form validation, CSRF protection, access control, and automated tests
- Custom 403/404/500 pages

## Project apps

- `accounts` — authentication, profiles, roles
- `properties` — properties, rooms, images, amenities
- `bookings` — rental requests and bookings
- `payments` — mock payments
- `maintenance` — technicians and maintenance tickets
- `core` — home page, admin dashboard, property reports

## Setup

```bash
python -m venv venv
venv\\Scripts\\activate       # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

> **After you copy in new project files, always run `python manage.py migrate` again.**
> New features can add database columns (for example the rental duration). If the
> database is not migrated, pages that use the new columns show a "no such column" error.

## Light and dark mode

Click the moon / sun button in the menu bar to switch. The choice is remembered in
your browser. The first time you visit, the site follows your computer's own
light/dark setting.

How it works (in case you want to change it):

- `templates/base.html` - a tiny script in the `<head>` picks the theme before the page
  is drawn, and the `<html>` tag carries `data-bs-theme="light"` or `"dark"`. The
  button is in the navbar.
- `static/js/script.js` - makes the button switch the theme and saves the choice.
- `static/css/style.css` - the colors live in variables at the top. The block called
  `[data-bs-theme="dark"]` holds the dark colors. Change a color there and the whole
  site follows.
- When you add new pages, prefer theme-aware Bootstrap classes such as `bg-body`,
  `bg-body-tertiary` and `text-body` instead of `bg-white`, `bg-light` and `text-dark`,
  because those three stay light in dark mode.

## Verification

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

`run_checks.py` can also be used as a convenience wrapper.

## Development email

The project uses Django's console email backend. During development, email messages are printed in the terminal rather than sent externally.

## Mock payments

No real money is processed. Card/CVV values are used for mock validation only. Full card numbers and CVV values are not stored; successful card payments retain only the last four digits.

Email verification and Google sign-in setup

1. Copy .env.example values into your Windows environment variables.
2. For Gmail OTP email, use a Gmail address with 2-Step Verification and create a Google App Password. Put that App Password in EMAIL_HOST_PASSWORD.
3. Restart the Django server after setting the email variables.
4. Registration now creates an inactive account, sends a 6-digit OTP, and opens the verification page. The account becomes active only after the correct OTP is entered.
5. The verification code expires after 10 minutes. A Resend OTP option is available with a short resend delay.
6. For Google sign-in, create OAuth 2.0 Web Application credentials in Google Cloud Console. Add http://127.0.0.1:8000/accounts/google/callback/ as an authorized redirect URI, then set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.
7. Google sign-in uses the verified Google email. A new Google account is created as a Tenant; an existing account with the same email is signed in.


## New verification and saved-property workflow

1. An owner opens a property from the owner dashboard and uploads a PDF/JPG/PNG proof document (up to 8 MB).
2. An administrator opens **Properties** in Django Admin, checks the submitted documents, then changes the property's verification status to **Verified** or **Needs changes**. Add a short review note when more information is needed.
3. The verified label is shown publicly only when an administrator has approved the listing. Uploading a new document returns a non-verified listing to pending review.
4. Tenant accounts can save and remove listings, visit **Saved** in the navbar, and sort property search results by rent or name.

## Database updates

After extracting this version, activate your virtual environment and run:

```bash
python manage.py migrate
python manage.py check
python manage.py test
```

The maintenance lifecycle now separates **Accept Job** from **Start Work**. A technician must accept an assignment before starting it. Tenants can attach an issue photo, and technicians can optionally attach a completion photo with their resolution note.

Payment features are demo/mock payments and must not be used to process real money without a payment-provider integration and verified server-side webhooks.

## Rental expiry reminders and automatic rental closure

The application includes two daily management commands:

- `python manage.py send_expiry_reminders` sends an in-app notification and email five days before a confirmed rental's end date. A database record prevents duplicate reminders for the same rental end date.
- `python manage.py close_expired_rentals` marks rentals as completed after their agreed end date and releases the room or property for future requests.

On Windows, run `run_daily_rental_tasks.bat` once per day using Windows Task Scheduler (for example, at 8:00 AM). Set the task's **Start in** folder to the project folder. The project must have its virtual environment and email settings configured. On Linux hosting, schedule the two commands with cron or your hosting provider's scheduler.

## Important setup notes

1. Create and activate a virtual environment, then install packages with `pip install -r requirements.txt`.
2. Copy `.env.example` to `.env` and enter your own secret key and email settings. Do not share the real `.env` file.
3. Run `python manage.py migrate` after extracting an updated project.
4. Run `python manage.py collectstatic` when deploying with static-file hosting.
5. The payment flow in this learning project is a simulated payment flow. It does not process real money. Connect a verified payment gateway before accepting real payments.
6. Before public deployment, set `DEBUG=False`, configure `ALLOWED_HOSTS`, HTTPS and `CSRF_TRUSTED_ORIGINS`, and use a production database and secure file storage.
