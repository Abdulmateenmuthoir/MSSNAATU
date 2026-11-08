"""Populate the database with a realistic demo dataset.

    python manage.py seed_demo

It is safe to run more than once: records are looked up before they are
created, and nothing is deleted.
"""

import io
import os
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import (
    ROLE_ADMIN,
    ROLE_EDITOR,
    ROLE_EVENTS,
    ROLE_FINANCE,
    ROLE_LIBRARY,
    ROLE_MEMBER,
    ROLE_SUPER,
    Student,
)
from apps.blog.models import Comment, Post
from apps.core.models import (
    Announcement,
    Committee,
    CommitteeMember,
    Department,
    Executive,
    Faculty,
)
from apps.events.models import Event, Registration
from apps.finance.models import DuesCycle, Payment
from apps.library.models import PastQuestion

SESSION = "1448/1449 AH"
DEMO_PASSWORD = "MssnDemo2026!"

FACULTIES = [
    (
        "Faculty of Computing and Information Technology",
        "SCICT",
        [
            ("Computer Science", "CSC"),
            ("Cyber Security", "CYB"),
            ("Information Technology", "IFT"),
            ("Software Engineering", "SEN"),
        ],
    ),
    (
        "Faculty of Engineering",
        "ENG",
        [
            ("Mechanical Engineering", "MEE"),
            ("Electrical & Electronics Engineering", "EEE"),
            ("Civil Engineering", "CVE"),
            ("Mechatronics Engineering", "MCT"),
        ],
    ),
    (
        "Faculty of Science",
        "SCI",
        [
            ("Applied Biology", "BIO"),
            ("Applied Chemistry", "CHM"),
            ("Applied Physics", "PHY"),
            ("Mathematics & Statistics", "MTH"),
        ],
    ),
    (
        "Faculty of Management and Business Studies",
        "MGT",
        [
            ("Business Administration", "BUA"),
            ("Accounting", "ACC"),
            ("Mass Communication", "MAC"),
            ("Entrepreneurship", "ENT"),
        ],
    ),
    (
        "Faculty of Environmental Studies",
        "ENV",
        [
            ("Architecture", "ARC"),
            ("Urban & Regional Planning", "URP"),
            ("Quantity Surveying", "QTS"),
        ],
    ),
    (
        "Faculty of Agriculture",
        "AGR",
        [("Agricultural Technology", "AGT")],
    ),
]

EXECUTIVES = [
    ("Ahmad Olanrewaju Bello", "Amir (President)", 0),
    ("Aisha Adebimpe Yusuf", "Amirah (Vice President, Sisters' Wing)", 1),
    ("Ibrahim Oluwaseun Salami", "General Secretary", 2),
    ("Fatimah Ayomide Ogunleye", "Public Relations Officer", 3),
    ("Yusuf Adewale Bakare", "Treasurer", 4),
    ("Maryam Titilayo Ajayi", "Welfare Director", 5),
    ("Abdulrahman Opeyemi Sanni", "Academic Director", 6),
    ("Khadijah Morenike Adeyemi", "Da'wah Director", 7),
    ("Muhammad Inioluwa Adebayo", "Social Director", 8),
    ("Zainab Folake Abdulkarim", "Auditor", 9),
]

COMMITTEES = [
    (
        "Da'wah & Programmes",
        "Coordinates halaqah, lectures, Ramadan programmes and campus da'wah activity.",
        [
            ("Khadijah Morenike Adeyemi", "Chairperson"),
            ("Habeeb Ayomide Lawal", "Secretary"),
            ("Sumayyah Bolanle Afolabi", "Member"),
        ],
    ),
    (
        "Academics & Library",
        "Runs the past questions library, study circles and academic support for members.",
        [
            ("Abdulrahman Opeyemi Sanni", "Chairperson"),
            ("Aisha Adebimpe Yusuf", "Member"),
            ("Tunde Ibrahim Oyelaran", "Member"),
        ],
    ),
    (
        "Welfare",
        "Supports members in need, coordinates visitation and manages the welfare fund.",
        [
            ("Maryam Titilayo Ajayi", "Chairperson"),
            ("Zainab Folake Abdulkarim", "Member"),
            ("Sulaiman Adegoke Ojo", "Member"),
        ],
    ),
    (
        "Media & Publicity",
        "Tells the society's story through the newsroom, photography and social media.",
        [
            ("Fatimah Ayomide Ogunleye", "Chairperson"),
            ("Ahmad Olanrewaju Bello", "Member"),
            ("Rukayat Aduke Adeleke", "Member"),
        ],
    ),
    (
        "Finance",
        "Keeps the books, collects dues and presents a transparent account to the council.",
        [
            ("Yusuf Adewale Bakare", "Chairperson"),
            ("Ibrahim Oluwaseun Salami", "Secretary"),
        ],
    ),
    (
        "Events",
        "Plans and delivers the society's programmes, from logistics to hospitality.",
        [
            ("Muhammad Inioluwa Adebayo", "Chairperson"),
            ("Habeeb Ayomide Lawal", "Member"),
            ("Aminah Folasade Oseni", "Member"),
        ],
    ),
]

STUDENTS = [
    # name, matric, email, gender, faculty, department, level
    ("Aisha Bello", "AATU/CSC/22/001", "aisha.bello@example.com", "F", "SCICT", "CSC", "200"),
    ("Yusuf Ibrahim", "AATU/MEE/22/014", "yusuf.ibrahim@example.com", "M", "ENG", "MEE", "200"),
    ("Maryam Adeyemi", "AATU/BUA/23/008", "maryam.adeyemi@example.com", "F", "MGT", "BUA", "100"),
    ("Abdulrahman Sanni", "AATU/CSC/21/003", "abdulrahman.sanni@example.com", "M", "SCICT", "CSC", "300"),
    ("Fatimah Ogunleye", "AATU/MAC/21/002", "fatimah.ogunleye@example.com", "F", "MGT", "MAC", "300"),
    ("Ibrahim Salami", "AATU/EEE/20/011", "ibrahim.salami@example.com", "M", "ENG", "EEE", "400"),
    ("Khadijah Adeyemi", "AATU/BIO/22/006", "khadijah.adeyemi@example.com", "F", "SCI", "BIO", "200"),
    ("Muhammad Adebayo", "AATU/CVE/21/009", "muhammad.adebayo@example.com", "M", "ENG", "CVE", "300"),
    ("Zainab Abdulkarim", "AATU/ACC/22/004", "zainab.abdulkarim@example.com", "F", "MGT", "ACC", "200"),
    ("Habeeb Lawal", "AATU/CYB/23/012", "habeeb.lawal@example.com", "M", "SCICT", "CYB", "100"),
    ("Sumayyah Afolabi", "AATU/CHM/21/007", "sumayyah.afolabi@example.com", "F", "SCI", "CHM", "300"),
    ("Tunde Oyelaran", "AATU/PHY/22/010", "tunde.oyelaran@example.com", "M", "SCI", "PHY", "200"),
    ("Rukayat Adeleke", "AATU/IFT/23/015", "rukayat.adeleke@example.com", "F", "SCICT", "IFT", "100"),
    ("Sulaiman Ojo", "AATU/ARC/20/005", "sulaiman.ojo@example.com", "M", "ENV", "ARC", "400"),
    ("Aminah Oseni", "AATU/URP/22/017", "aminah.oseni@example.com", "F", "ENV", "URP", "200"),
    ("Abdulbasit Alabi", "AATU/MCT/23/019", "abdulbasit.alabi@example.com", "M", "ENG", "MCT", "100"),
    ("Halimah Balogun", "AATU/MTH/21/013", "halimah.balogun@example.com", "F", "SCI", "MTH", "300"),
    ("Ismail Raji", "AATU/AGT/22/020", "ismail.raji@example.com", "M", "AGR", "AGT", "200"),
    ("Nafisah Giwa", "AATU/ACC/23/021", "nafisah.giwa@example.com", "F", "MGT", "ACC", "100"),
    ("Abdulhakeem Yusuf", "AATU/SEN/21/022", "abdulhakeem.yusuf@example.com", "M", "SCICT", "SEN", "300"),
    ("Ruqayyah Mustapha", "AATU/QTS/20/023", "ruqayyah.mustapha@example.com", "F", "ENV", "QTS", "400"),
    ("Musa Danjuma", "AATU/EEE/23/024", "musa.danjuma@example.com", "M", "ENG", "EEE", "100"),
    ("Aminat Suleiman", "AATU/MAC/22/025", "aminat.suleiman@example.com", "F", "MGT", "MAC", "200"),
    ("Abdulsamad Tijani", "AATU/CSC/20/026", "abdulsamad.tijani@example.com", "M", "SCICT", "CSC", "400"),
]

STAFF_ACCOUNTS = [
    ("Super Admin", "AATU/ADM/00/001", "admin@mssnaatu.org", "M", ROLE_SUPER),
    ("Editorial Board", "AATU/ADM/00/002", "editor@mssnaatu.org", "F", ROLE_EDITOR),
    ("Events Office", "AATU/ADM/00/003", "events@mssnaatu.org", "M", ROLE_EVENTS),
    ("Finance Office", "AATU/ADM/00/004", "finance@mssnaatu.org", "M", ROLE_FINANCE),
    ("Library Office", "AATU/ADM/00/005", "library@mssnaatu.org", "F", ROLE_LIBRARY),
    ("Membership Office", "AATU/ADM/00/006", "membership@mssnaatu.org", "M", ROLE_ADMIN),
]

POSTS = [
    {
        "title": "MSSN AATU opens the 1448/1449 session with a call to knowledge and character",
        "category": "news",
        "excerpt": "The society formally welcomed new and returning students at the opening halaqah, with the Amir urging members to pursue excellence in both faith and scholarship.",
        "content": """The Muslim Students' Society of Nigeria, AATU chapter, has formally opened its activities for the **1448/1449 AH** session with an opening halaqah at the Main Auditorium.

In his address, the Amir, Ahmad Olanrewaju Bello, welcomed freshers and returning students, and reminded the gathering that the society exists to help every Muslim student grow in faith, excel academically and serve the campus with character.

> The best of you are those who are most beneficial to people.

## What the session holds

The executive council outlined a full calendar: weekly halaqah, the annual Qur'an competition, academic clinics before examinations, welfare visits and the Ramadan programme. The academic committee also announced that the past questions library will be expanded department by department.

## A home for every student

Membership records are now managed through the member portal. Every student can sign in to view their dues status, register for programmes and download past questions.

Students who have not received their login details should contact the Office of the Public Relations Officer.
""",
        "days_ago": 4,
        "author": "editor@mssnaatu.org",
    },
    {
        "title": "Five habits that will carry you through the semester",
        "category": "editorial",
        "excerpt": "Small, consistent routines beat last-minute cramming. Here is a practical guide to balancing coursework, worship and rest.",
        "content": """Every semester begins with good intentions. The difference between a calm examination period and a frantic one is rarely intelligence — it is routine.

## 1. Pray, then plan

Begin the day with Fajr and a short, honest look at what must be done. A written plan of three priorities is more useful than an anxious mental list of twenty.

## 2. Study in blocks

Fifty minutes of focused work, then a ten-minute break, is kinder to your attention than three hours of half-studying with a phone nearby.

## 3. Use the library

Past questions are a map, not a substitute for understanding. Work through them after you have read the material, and note the topics that keep appearing.

## 4. Protect your sleep

Late nights borrow energy from tomorrow at a terrible interest rate. Most students need seven to eight hours.

## 5. Stay connected

Join a study circle, attend halaqah, and check on a friend. You are not meant to carry the semester alone.

May Allah make the work easy and bless the effort.
""",
        "days_ago": 9,
        "author": "editor@mssnaatu.org",
    },
    {
        "title": "Annual Qur'an competition returns this November",
        "category": "society",
        "excerpt": "Registration is now open for the brothers' and sisters' categories. The competition holds at the Main Auditorium.",
        "content": """The annual Qur'an competition returns this November, and registration is now open to all members.

## Categories

- **Hifz** — memorisation of selected portions
- **Tilawah** — beautiful recitation with tajweed
- **Tafsir** — understanding and explanation

Brothers and sisters compete separately, and judges will be announced on the day.

## How to take part

Sign in to the member portal, open the programme page and register. Places are limited, so early registration is encouraged. A confirmation email will be sent immediately.

We ask Allah to bless the participants and make the competition a means of drawing closer to His Book.
""",
        "days_ago": 14,
        "author": "editor@mssnaatu.org",
    },
    {
        "title": "Welfare committee visits members in the teaching hospital",
        "category": "campus",
        "excerpt": "The welfare team spent the afternoon with two members receiving treatment, delivering provisions and du'a.",
        "content": """The Welfare Committee visited two members receiving treatment at the university teaching hospital this week.

The team delivered provisions, checked on the families and spent time with the students. The Welfare Director, Maryam Titilayo Ajayi, thanked members who contributed to the welfare fund.

> Visiting the sick is a right upon a Muslim.

Members who know of a brother or sister in need are encouraged to reach the committee through the PRO office. Confidentiality is guaranteed.
""",
        "days_ago": 22,
        "author": "editor@mssnaatu.org",
    },
    {
        "title": "Draft: plans for the Ramadan programme",
        "category": "deen",
        "excerpt": "An early draft outline of the Ramadan 1449 programme, pending council approval.",
        "content": """This is a working draft and is not yet published.

The outline includes tafsir circles, iftar coordination, tahajjud arrangements and a community outreach day. Details will be confirmed by the executive council before publication.
""",
        "days_ago": 1,
        "author": "editor@mssnaatu.org",
        "published": False,
    },
]

EVENTS = [
    {
        "title": "Annual Qur'an Competition",
        "summary": "A day of recitation, memorisation and tafsir across the brothers' and sisters' categories.",
        "description": """The annual Qur'an competition brings the best of the society's reciters together for a day of worship, learning and healthy competition.

## Categories

- **Hifz** — memorisation of selected portions
- **Tilawah** — recitation with tajweed
- **Tafsir** — explanation and understanding

## What to expect

Judges from within and outside the university will assess participants. Families and friends are welcome to attend and support the competitors.

Refreshments will be served after the programme. Registration is required for participants only.
""",
        "days": 9,
        "venue": "AATU Main Auditorium",
        "capacity": 120,
        "eligibility": "all",
        "deadline_days": 7,
    },
    {
        "title": "Brothers' Halaqah: The Ethics of Seeking Knowledge",
        "summary": "A weekly circle on adab, intention and excellence in study, led by the Da'wah Committee.",
        "description": """An intimate circle for brothers on the manners and ethics of seeking knowledge.

We will discuss:

- Purifying intention before study
- The adab of the student with teachers and peers
- Balancing deen and academic ambition
- Practical habits for a blessed semester

Bring a notebook and a question. Tea and dates will be provided.
""",
        "days": 16,
        "venue": "Faculty of Science Lecture Theatre 2",
        "capacity": 45,
        "eligibility": "brothers",
        "deadline_days": 15,
    },
    {
        "title": "Sisters' Study Circle: Navigating Campus Life",
        "summary": "A supportive circle for sisters on friendship, boundaries, wellbeing and academic balance.",
        "description": """A facilitated conversation for sisters on the realities of campus life.

Topics include:

- Building healthy friendships
- Setting boundaries with confidence
- Managing stress and examination pressure
- Finding support when things are difficult

The circle is led by the Sisters' Wing and the Welfare Committee. Everything shared remains confidential.
""",
        "days": 23,
        "venue": "Sisters' Common Room, Student Centre",
        "capacity": 40,
        "eligibility": "sisters",
        "deadline_days": 21,
    },
    {
        "title": "Academic Clinic: Examination Preparation",
        "summary": "Past questions, study plans and peer tutoring ahead of the first semester examinations.",
        "description": """The Academic Committee hosts an open clinic for members preparing for examinations.

Come with:

- A course you are finding difficult
- Past questions you want to work through
- A study plan you would like feedback on

Senior colleagues and tutors will be available across departments. The past questions library will also be open for downloads on the day.
""",
        "days": 34,
        "venue": "University Library, Reading Room A",
        "capacity": None,
        "eligibility": "all",
        "deadline_days": 32,
    },
    {
        "title": "Opening Halaqah and Freshers' Welcome",
        "summary": "The society's opening gathering for the session, with a welcome for new students.",
        "description": """The opening halaqah welcomed new and returning students to the 1448/1449 session.

The Amir spoke on the society's mission, the executive council was introduced, and freshers met their departmental representatives. The programme closed with du'a and refreshments.
""",
        "days": -26,
        "venue": "AATU Main Auditorium",
        "capacity": 200,
        "eligibility": "all",
        "deadline_days": -27,
    },
]

QUESTIONS = [
    ("SCICT", "CSC", "200", "CSC 201", "Computer Programming II", "2024/2025"),
    ("SCICT", "CSC", "200", "CSC 203", "Discrete Structures", "2024/2025"),
    ("SCICT", "CSC", "300", "CSC 301", "Data Structures and Algorithms", "2023/2024"),
    ("SCICT", "CYB", "200", "CYB 201", "Introduction to Cyber Security", "2024/2025"),
    ("ENG", "MEE", "200", "MEE 201", "Engineering Thermodynamics", "2024/2025"),
    ("ENG", "EEE", "300", "EEE 301", "Circuit Theory II", "2023/2024"),
    ("ENG", "CVE", "200", "CVE 205", "Strength of Materials", "2024/2025"),
    ("SCI", "BIO", "200", "BIO 201", "Cell Biology", "2024/2025"),
    ("SCI", "CHM", "100", "CHM 101", "General Chemistry I", "2024/2025"),
    ("SCI", "MTH", "200", "MTH 201", "Mathematical Methods I", "2023/2024"),
    ("MGT", "ACC", "200", "ACC 201", "Financial Accounting I", "2024/2025"),
    ("MGT", "BUA", "100", "BUA 101", "Introduction to Business", "2024/2025"),
    ("ENV", "ARC", "300", "ARC 301", "Architectural Design III", "2023/2024"),
    ("AGR", "AGT", "200", "AGT 201", "Principles of Crop Production", "2024/2025"),
]


def make_pdf(title, subtitle, lines):
    """Build a small, valid one-page PDF without external dependencies."""

    def escape(text):
        return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    content = ["BT", "/F1 20 Tf", "60 780 Td", f"({escape(title)}) Tj", "/F1 12 Tf", "0 -28 Td", f"({escape(subtitle)}) Tj", "/F1 11 Tf"]
    y = 0
    for line in lines:
        y -= 20
        content.append(f"0 {y} Td" if y == -20 else f"0 -20 Td")
        content.append(f"({escape(line)}) Tj")
    content.append("ET")
    stream = "\n".join(content).encode("latin-1", "replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]

    pdf = io.BytesIO()
    pdf.write(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(pdf.tell())
        pdf.write(f"{index} 0 obj\n".encode())
        pdf.write(obj)
        pdf.write(b"\nendobj\n")
    xref_start = pdf.tell()
    pdf.write(f"xref\n0 {len(objects) + 1}\n".encode())
    pdf.write(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.write(f"{offset:010d} 00000 n \n".encode())
    pdf.write(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF\n".encode()
    )
    return pdf.getvalue()


class Command(BaseCommand):
    help = "Create a realistic demo dataset for MSSN AATU."

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            default=DEMO_PASSWORD,
            help="Password assigned to every demo account (default: MssnDemo2026!).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        password = options["password"]
        now = timezone.now()

        #--------------------------------------------------------------
        # Academic structure
        #--------------------------------------------------------------
        faculties = {}
        departments = {}
        for order, (name, code, department_rows) in enumerate(FACULTIES):
            faculty, _ = Faculty.objects.get_or_create(
                code=code, defaults={"name": name, "order": order}
            )
            faculties[code] = faculty
            for dept_order, (dept_name, dept_code) in enumerate(department_rows):
                department, _ = Department.objects.get_or_create(
                    faculty=faculty,
                    code=dept_code,
                    defaults={"name": dept_name, "order": dept_order},
                )
                departments[dept_code] = department
        self.stdout.write(f"Faculties: {len(faculties)} · Departments: {len(departments)}")

        #--------------------------------------------------------------
        # People
        #--------------------------------------------------------------
        staff = {}
        for full_name, matric, email, gender, role in STAFF_ACCOUNTS:
            first, last = full_name.split(" ", 1)
            student = Student.objects.filter(matric_no=matric).first()
            if student is None:
                student = Student.objects.create_user(
                    matric_no=matric,
                    email=email,
                    password=password,
                    first_name=first,
                    last_name=last,
                    gender=gender,
                    role=role,
                    must_change_password=False,
                )
            staff[email] = student

        admin = staff["admin@mssnaatu.org"]
        admin.is_superuser = True
        admin.is_staff = True
        admin.save()

        demo_members = []
        for full_name, matric, email, gender, faculty_code, dept_code, level in STUDENTS:
            first, last = full_name.split(" ", 1)
            student = Student.objects.filter(matric_no=matric).first()
            if student is None:
                student = Student.objects.create_user(
                    matric_no=matric,
                    email=email,
                    password=password,
                    first_name=first,
                    last_name=last,
                    gender=gender,
                    faculty=faculties[faculty_code],
                    department=departments[dept_code],
                    level=level,
                    role=ROLE_MEMBER,
                    must_change_password=True,
                )
            demo_members.append(student)
        self.stdout.write(f"Students: {Student.objects.count()}")

        #--------------------------------------------------------------
        # Leadership & committees
        #--------------------------------------------------------------
        for full_name, position, order in EXECUTIVES:
            Executive.objects.get_or_create(
                full_name=full_name,
                position=position,
                session=SESSION,
                defaults={"order": order, "is_current": True, "bio": ""},
            )
        for order, (name, description, members) in enumerate(COMMITTEES):
            committee, _ = Committee.objects.get_or_create(
                name=name,
                session=SESSION,
                defaults={"description": description, "order": order},
            )
            for member_order, (member_name, role) in enumerate(members):
                CommitteeMember.objects.get_or_create(
                    committee=committee,
                    full_name=member_name,
                    defaults={"role": role, "order": member_order},
                )

        #--------------------------------------------------------------
        # Announcements
        #--------------------------------------------------------------
        Announcement.objects.get_or_create(
            title="Dues for 1448/1449 are now open",
            defaults={
                "body": "Pay from your dashboard in under a minute. Receipts are issued automatically by email.",
                "is_active": True,
            },
        )
        Announcement.objects.get_or_create(
            title="Past questions library updated",
            defaults={
                "body": "New resources for Computer Science, Mechanical Engineering and Accounting have been uploaded.",
                "is_active": True,
            },
        )

        #--------------------------------------------------------------
        # Newsroom
        #--------------------------------------------------------------
        posts = {}
        for item in POSTS:
            author = staff.get(item["author"], admin)
            slug_source = item["title"].lower().replace(" ", "-")
            post = Post.objects.filter(title=item["title"]).first()
            if post is None:
                post = Post(
                    title=item["title"],
                    category=item["category"],
                    excerpt=item["excerpt"],
                    content=item["content"],
                    author=author,
                    is_published=item.get("published", True),
                )
                if post.is_published:
                    post.published_at = now - timedelta(days=item["days_ago"])
                post.save()
            posts[item["title"]] = post

        if demo_members:
            first_post = posts.get(POSTS[0]["title"])
            if first_post:
                Comment.objects.get_or_create(
                    post=first_post,
                    author=demo_members[0],
                    defaults={"body": "Jazakumullahu khairan for the warm welcome. Looking forward to the session."},
                )
                Comment.objects.get_or_create(
                    post=first_post,
                    author=demo_members[2],
                    defaults={"body": "Alhamdulillah. Please share the halaqah timetable when it is ready."},
                )

        #--------------------------------------------------------------
        # Programmes
        #--------------------------------------------------------------
        events = {}
        for item in EVENTS:
            starts_at = now + timedelta(days=item["days"])
            starts_at = starts_at.replace(hour=10, minute=0, second=0, microsecond=0)
            deadline = now + timedelta(days=item["deadline_days"]) if item["deadline_days"] is not None else None
            event = Event.objects.filter(title=item["title"]).first()
            if event is None:
                event = Event.objects.create(
                    title=item["title"],
                    summary=item["summary"],
                    description=item["description"],
                    starts_at=starts_at,
                    ends_at=starts_at + timedelta(hours=3),
                    venue=item["venue"],
                    capacity=item["capacity"],
                    eligibility=item["eligibility"],
                    registration_deadline=deadline,
                    is_published=True,
                    created_by=staff["events@mssnaatu.org"],
                )
            events[item["title"]] = event

        quran_event = events.get("Annual Qur'an Competition")
        if quran_event and demo_members:
            for student in demo_members[:8]:
                Registration.objects.get_or_create(event=quran_event, student=student)
        brothers_event = events.get("Brothers' Halaqah: The Ethics of Seeking Knowledge")
        if brothers_event:
            for student in demo_members:
                if student.gender == "M":
                    Registration.objects.get_or_create(event=brothers_event, student=student)
        sisters_event = events.get("Sisters' Study Circle: Navigating Campus Life")
        if sisters_event:
            for student in demo_members:
                if student.gender == "F":
                    Registration.objects.get_or_create(event=sisters_event, student=student)

        #--------------------------------------------------------------
        # Past questions
        #--------------------------------------------------------------
        media_root = settings.MEDIA_ROOT
        for faculty_code, dept_code, level, course_code, course_title, session in QUESTIONS:
            department = departments.get(dept_code)
            if department is None:
                continue
            faculty = faculties.get(faculty_code) or department.faculty
            question = PastQuestion.objects.filter(
                course_code=course_code,
                session=session,
                department=department,
                level=level,
            ).first()
            if question is not None:
                continue
            relative = f"past-questions/{faculty.code}/{department.code}/{level}/{course_code.replace(' ', '')}.pdf"
            absolute = os.path.join(media_root, relative)
            os.makedirs(os.path.dirname(absolute), exist_ok=True)
            payload = make_pdf(
                course_title,
                f"{course_code} · {department.name} · {level} Level · {session}",
                [
                    "MUSLIM STUDENTS' SOCIETY OF NIGERIA",
                    "Abiola Ajimobi Technical University, Ibadan",
                    "",
                    "PAST EXAMINATION QUESTIONS",
                    "",
                    "Instructions: Answer all questions in Section A and any",
                    "three questions from Section B. Time allowed: 2 hours.",
                    "",
                    "SECTION A",
                    "1. (a) Define the core concepts covered in this course.",
                    "   (b) With a clear diagram, explain the process discussed",
                    "       in the second half of the syllabus.",
                    "",
                    "2. Discuss, with examples, the practical applications of",
                    "   the principles introduced during the semester.",
                    "",
                    "SECTION B",
                    "3. Write short notes on any three of the following topics.",
                    "4. Evaluate the methods used in the case study, stating",
                    "   their strengths and limitations.",
                    "5. Explain how the course content connects to the wider",
                    "   field and to professional practice.",
                    "",
                    "This is a demo document created for the MSSN AATU portal.",
                ],
            )
            question = PastQuestion(
                faculty=faculty,
                department=department,
                level=level,
                course_code=course_code,
                course_title=course_title,
                session=session,
                uploaded_by=staff["library@mssnaatu.org"],
                downloads=12 + (hash(course_code) % 40),
            )
            question.file.save(relative.split("/")[-1], ContentFile(payload), save=False)
            question.save()
        self.stdout.write(f"Past questions: {PastQuestion.objects.count()}")

        #--------------------------------------------------------------
        # Dues
        #--------------------------------------------------------------
        cycle, _ = DuesCycle.objects.get_or_create(
            session=SESSION,
            defaults={
                "amount": Decimal("2000.00"),
                "due_date": now.date() + timedelta(days=60),
                "note": "Dues support halaqah, welfare, academic resources and the work of the society.",
                "is_active": True,
            },
        )
        if not cycle.is_active:
            cycle.is_active = True
            cycle.save(update_fields=["is_active"])

        payment_count = 0
        for index, student in enumerate(demo_members[:11]):
            payment, created = Payment.objects.get_or_create(
                student=student,
                cycle=cycle,
                defaults={
                    "amount": cycle.amount,
                    "status": Payment.SUCCESS,
                    "gateway": "paystack",
                    "gateway_reference": f"DEMO-{index:04d}",
                    "paid_at": now - timedelta(days=index + 1),
                },
            )
            if created:
                payment_count += 1
        # A couple of pending and failed attempts for realism
        if demo_members:
            Payment.objects.get_or_create(
                student=demo_members[-1],
                cycle=cycle,
                defaults={"amount": cycle.amount, "status": Payment.PENDING},
            )
            Payment.objects.get_or_create(
                student=demo_members[-2],
                cycle=cycle,
                defaults={"amount": cycle.amount, "status": Payment.FAILED},
            )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Demo data ready."))
        self.stdout.write("")
        self.stdout.write("  Super admin   admin@mssnaatu.org       / " + password)
        self.stdout.write("  Editor        editor@mssnaatu.org      / " + password)
        self.stdout.write("  Events        events@mssnaatu.org      / " + password)
        self.stdout.write("  Finance       finance@mssnaatu.org     / " + password)
        self.stdout.write("  Library       library@mssnaatu.org     / " + password)
        self.stdout.write("  Member        aisha.bello@example.com  / " + password)
        self.stdout.write("")
        self.stdout.write(f"  New payments created: {payment_count}")
        self.stdout.write(
            self.style.WARNING(
                "  Change these passwords before deploying to production."
            )
        )
