# Sign-up with Email OTP + Google Sign-In

## How the sign-up works

1. **Register** - fill in the form and press *Create account & send OTP*.
2. A 6-digit code is emailed to the address you registered with.
3. The **Check your email** page opens. Type the code (it submits by itself after 6 digits).
4. Correct code -> you are sent to the **Login** page with your username already filled in.
5. Wrong code -> you see how many attempts are left. After 5 wrong tries, or after 10 minutes, ask for a new code.
6. Small **Resend OTP** button (wait 30 seconds between sends) sends a fresh code; the old code stops working.
7. If someone tries to log in before verifying, they are taken back to the OTP page.

The account stays locked (`is_active = False`) until the code is correct.

## Quick test without any email setup

Do nothing. Run `python manage.py runserver`, register, and look at the **terminal**:
the email (with the 6-digit code) is printed there. The OTP page shows a small
"Testing mode" note when this is the case.

## Send real emails with Gmail

1. Turn on 2-Step Verification for the Gmail account that will send the codes.
2. Create a Google **App Password** for it (Google Account -> Security -> App passwords).
3. In the project folder, copy `.env.example` to a new file named `.env` and fill it in:

```
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=yourgmail@gmail.com
EMAIL_HOST_PASSWORD=your-16-character-app-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=yourgmail@gmail.com
```

4. Restart `python manage.py runserver`. Codes are now emailed to the registered address.

(`.env` is read automatically and is ignored by git, so your password is not uploaded.)

## Continue with Google (account chooser)

The button is already on the Login and Register pages. To make it work you need free Google credentials:

1. Open https://console.cloud.google.com and create/select a project.
2. APIs & Services -> OAuth consent screen -> set it up (External, add your email as a test user).
3. Credentials -> Create credentials -> **OAuth client ID** -> *Web application*.
4. Under **Authorized redirect URIs** add exactly: `http://127.0.0.1:8000/accounts/google/callback/`
5. Put the values in your `.env` file:

```
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://127.0.0.1:8000/accounts/google/callback/
```

6. Restart the server and click **Continue with Google**. Google shows its account chooser,
   and a verified Google email either creates a new Tenant account or signs in to the existing
   account with that email. Google sign-in needs no OTP because Google already verified the email.

Until the credentials are added, the button shows a friendly "not set up yet" message.

## Run the tests

```
python manage.py test
```
