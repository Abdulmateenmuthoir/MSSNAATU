# cPanel deployment notes

The project uses Django migrations and static/media files. Because this cPanel account has no interactive terminal, prepare a release ZIP locally that excludes `.env`, `.venv`, `.git`, and local database files, upload/extract it in cPanel File Manager, and configure the cPanel Python application to use its virtual environment. Keep secrets in the Python application's environment variables, not in the ZIP.

## Brevo settings

Add these variables to the cPanel Python application's environment configuration:

- `BREVO_API_KEY`
- `BREVO_SENDER_EMAIL`
- `BREVO_SENDER_NAME`
- `SITE_URL` (the HTTPS public site URL)

The same Brevo sender is used for article announcements, newsletters, dues reminders, and account emails.

## Automatic dues reminders

Add a job under **cPanel → Cron Jobs** to run `manage.py send_dues_reminders`. Use the full path to the application's virtual-environment Python executable and the deployed project directory, for example:

```sh
cd /home/CPANEL_USER/path/to/MSSNAATU && /home/CPANEL_USER/virtualenv/path/to/python manage.py send_dues_reminders
```

Set the cron schedule to run daily. The command skips members who received a reminder in the previous 14 days, so each unpaid member is emailed at most once per two-week period. It uses the active dues cycle and only targets active member accounts that have not paid. Configure `DJANGO_SETTINGS_MODULE` or other environment values through cPanel's Python application setup as needed.

Before enabling the job, run `send_dues_reminders --dry-run` in a shell if one becomes available, or verify the active dues cycle, member emails, Brevo sender, and API key in the deployed application settings.
