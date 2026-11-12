# cPanel deployment notes

The project uses Django migrations and static/media files. Because this cPanel account has no interactive terminal, prepare a release ZIP locally that excludes `.env`, `.venv`, `.git`, and local database files, upload/extract it in cPanel File Manager, and configure the cPanel Python application to use its virtual environment. Keep secrets in the Python application's environment variables, not in the ZIP.

## Brevo settings

Add these variables to the cPanel Python application's environment configuration:

- `BREVO_API_KEY`
- `BREVO_SENDER_EMAIL`
- `BREVO_SENDER_NAME`
- `SITE_URL` (the HTTPS public site URL)

The same Brevo sender is used for article announcements, newsletters, dues reminders, and account emails.

You do not need to upload a `.env` file to cPanel. Add these names and values under **cPanel → Setup Python App → Environment variables**. The app also reads a `.env` file from the project root if you choose to create one with File Manager, but keep it out of `public_html` and never put it in a release ZIP. Brevo transactional email uses the REST API key, not the SMTP password. The sender address must be verified in Brevo.

## Paystack live keys

After Paystack verifies the account, add `PAYSTACK_PUBLIC_KEY` and `PAYSTACK_SECRET_KEY` from the Paystack dashboard to the Python application's environment variables (or the private project-root `.env`). Use the live `pk_live_…` and `sk_live_…` keys for live charges. Set `SITE_URL=https://mssnaatu.org` and `PAYSTACK_CALLBACK_URL=https://mssnaatu.org/dues/callback/`, then restart the app. Keep the secret key private; do not put it in source code or GitHub.

## Automatic dues reminders

Add a job under **cPanel → Cron Jobs** to run `manage.py send_dues_reminders`. Use the full path to the application's virtual-environment Python executable and the deployed project directory, for example:

```sh
cd /home/CPANEL_USER/path/to/MSSNAATU && /home/CPANEL_USER/virtualenv/path/to/python manage.py send_dues_reminders
```

Set the cron schedule to run daily. The command skips members who received a reminder in the previous 14 days, so each unpaid member is emailed at most once per two-week period. It uses the active dues cycle and only targets active member accounts that have not paid. Configure `DJANGO_SETTINGS_MODULE` or other environment values through cPanel's Python application setup as needed.

Before enabling the job, run `send_dues_reminders --dry-run` in a shell if one becomes available, or verify the active dues cycle, member emails, Brevo sender, and API key in the deployed application settings.
