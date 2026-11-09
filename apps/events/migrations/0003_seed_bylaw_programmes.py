from django.db import migrations


PROGRAMMES = [
    ("Da’wah Enlightenment", "Weekly Islamic learning and spiritual development.", "A weekly programme for Islamic learning and spiritual development.", "weekly", 10),
    ("Spiritual Night", "Weekly worship and reflection gathering.", "A weekly gathering for worship, reflection and strengthening the campus Muslim community.", "weekly", 20),
    ("Sisters’ Circle", "Sisters’ learning and fellowship.", "A sisters’ learning programme coordinated by the Sisters’ Circle executives.", "fortnightly", 30),
    ("Brothers’ Forum", "Monthly brothers’ forum.", "A monthly forum coordinated by the Executive Council.", "monthly", 40),
    ("General Meeting", "Society-wide meeting for updates and member participation.", "A society-wide meeting for updates, consultation and member participation.", "semester", 50),
    ("Orientation Week", "Welcome programme for new students.", "Welcomes new students and introduces them to MSSN AATU and campus life.", "annual", 60),
    ("Jihad Week", "Islamic learning and community engagement.", "A yearly programme held in the second semester.", "annual", 70),
    ("Ramadan Programme", "Iftar, sahur and tafsir activities during Ramadan.", "Ramadan activities include iftar and sahur gatherings and tafsir sessions.", "annual", 80),
    ("Training Programmes", "Skills, leadership and capacity building.", "Training programmes arranged as the Executive Council deems fit.", "periodic", 90),
    ("Annual Conference", "Annual conference for reports and officer transition.", "Annual society conference for reports, consultation and the swearing-in of new officers.", "annual", 100),
    ("Public Lectures", "Public lectures on topics selected by the Executive Council.", "Public lectures scheduled by the Executive Council.", "scheduled", 110),
    ("Rural Da’wah", "Weekend outreach to surrounding communities.", "Weekend outreach to surrounding communities, including Bare, Abanla and Idi Ayunre.", "periodic", 120),
    ("Joint Sisters’ Meeting", "Joint sisters’ meeting and learning programme.", "Joint meeting and learning programme for sisters, arranged by the Executive Council.", "scheduled", 130),
    ("Special Da’wah Weekend", "Special outreach during the first semester.", "A special weekend outreach programme held during the first semester.", "annual", 140),
    ("Eid Get-together", "Society gathering after Eid-ul-Kabir.", "A society gathering after Eid-ul-Kabir for fellowship and celebration.", "annual", 150),
    ("Qur’an Competition", "Qur’an recitation and memorisation competition.", "A Qur’an competition scheduled by the Executive Council.", "scheduled", 160),
]


def seed_programmes(apps, schema_editor):
    Program = apps.get_model("events", "Program")
    for name, summary, description, frequency, order in PROGRAMMES:
        Program.objects.get_or_create(
            name=name,
            defaults={"summary": summary, "description": description, "frequency": frequency, "order": order},
        )


def remove_seeded_programmes(apps, schema_editor):
    Program = apps.get_model("events", "Program")
    Program.objects.filter(name__in=[row[0] for row in PROGRAMMES]).delete()


class Migration(migrations.Migration):
    dependencies = [("events", "0002_program")]
    operations = [migrations.RunPython(seed_programmes, remove_seeded_programmes)]
