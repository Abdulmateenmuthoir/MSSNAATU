"""Ad-hoc smoke test used during development — not part of the test suite."""
import os
import django
from django.test import Client

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mssnaatu.settings")
django.setup()

from apps.accounts.models import Student  # noqa: E402
from apps.events.models import Event  # noqa: E402
from apps.finance.models import DuesCycle, Payment  # noqa: E402
from apps.library.models import PastQuestion  # noqa: E402
from apps.blog.models import Post  # noqa: E402

PUBLIC = [
    "/", "/about/", "/executives/", "/committees/", "/contact/", "/health/",
    "/events/", "/events/?show=past", "/news/", "/library/",
]
MEMBER = ["/dashboard/", "/dashboard/events/", "/dashboard/library/", "/dashboard/news/",
          "/dashboard/finance/", "/dashboard/students/", "/accounts/profile/",
          "/accounts/password/change/", "/dues/"]
ADMIN = ["/dashboard/students/add/", "/dashboard/students/import/",
         "/dashboard/students/promote/", "/dashboard/students/credentials/",
         "/dashboard/news/new/", "/dashboard/news/comments/",
         "/dashboard/events/new/", "/dashboard/library/upload/",
         "/dashboard/finance/payments/", "/dashboard/finance/export/",
         "/django-admin/"]

c = Client(SERVER_NAME="localhost")
failures = []

def check(label, response, allowed=(200, 302)):
    status = response.status_code
    if status not in allowed:
        failures.append((label, status, response.content[:400]))
    print(f"{'OK ' if status in allowed else 'FAIL'} {status} {label}")

print("== public ==")
for url in PUBLIC:
    check(url, c.get(url))
check(f"/events/{Event.objects.first().slug}/", c.get(f"/events/{Event.objects.first().slug}/"))
check(f"/news/{Post.objects.filter(is_published=True).first().slug}/",
      c.get(f"/news/{Post.objects.filter(is_published=True).first().slug}/"))
q = PastQuestion.objects.first()
check(f"/library/{q.pk}/", c.get(f"/library/{q.pk}/"))

print("\n== member login ==")
member = Student.objects.get(email="aisha.bello@example.com")
ok = c.login(matric_no=member.matric_no, password="MssnDemo2026!")
print("login:", ok)
check("/dashboard/ after login", c.get("/dashboard/"))
for url in MEMBER:
    check(url, c.get(url))

print("\n== password setup flow ==")
c2 = Client(SERVER_NAME="localhost")
ok = c2.login(matric_no=member.matric_no, password="MssnDemo2026!")
resp = c2.get("/dashboard/", follow=False)
print("must_change redirect:", resp.status_code, resp.headers.get("Location"))
check("/accounts/password/setup/", c2.get("/accounts/password/setup/"))
check("skip prompt", c2.post("/accounts/password/setup/continue/"), (302,))
check("/dashboard/ after skip", c2.get("/dashboard/"))

print("\n== event registration / dues ==")
event = Event.objects.filter(is_published=True, starts_at__gte=django.utils.timezone.now()).first()
c3 = Client(SERVER_NAME="localhost")
fresh = Student.objects.filter(email="musa.danjuma@example.com").first()
c3.force_login(fresh)
c3.post("/accounts/password/setup/continue/")
check("register event", c3.post(f"/events/{event.slug}/register/", follow=True))
check("cancel event", c3.post(f"/events/{event.slug}/cancel/", follow=True))
cycle = DuesCycle.objects.filter(is_active=True).first()
check("initialize payment", c3.post("/dues/pay/", follow=False), (200, 302))
payment = Payment.objects.filter(student=fresh).first()
if payment:
    check(f"demo checkout {payment.reference}", c3.get(f"/dues/demo/{payment.reference}/"))
    check("confirm demo payment", c3.post(f"/dues/demo/{payment.reference}/", follow=True))
    check(f"receipt {payment.reference}", c3.get(f"/dues/receipt/{payment.reference}/"))
else:
    failures.append(("payment not created", None, b""))
check("download question", c3.get(f"/library/{q.pk}/download/"))

print("\n== forgotten password ==")
check("/accounts/password/forgot/", c.get("/accounts/password/forgot/"))
check("forgot post", c.post("/accounts/password/forgot/", {"identifier": member.email}), (302,))

print("\n== admin ==")
c4 = Client(SERVER_NAME="localhost")
admin = Student.objects.get(email="admin@mssnaatu.org")
print("admin login:", c4.login(matric_no=admin.matric_no, password="MssnDemo2026!"))
check("/dashboard/ admin", c4.get("/dashboard/"))
for url in ADMIN:
    check(url, c4.get(url), (200, 302))
check("student detail", c4.get(f"/dashboard/students/{Student.objects.first().pk}/"))
check("event registrations", c4.get(f"/dashboard/events/{event.pk}/registrations/"))
check("event export", c4.get(f"/dashboard/events/{event.pk}/registrations/export/"))
check("library edit", c4.get(f"/dashboard/library/{q.pk}/edit/"))

print("\n== 404 ==")
check("/definitely-not-a-page/", c.get("/definitely-not-a-page/"), (404,))

print("\n== failures ==")
if failures:
    for label, status, body in failures:
        print(f"\n### {label} → {status}\n{body.decode('utf-8', 'replace')}")
    raise SystemExit(1)
print("All good.")
