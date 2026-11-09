"""Load the 2026/2027 executive roster and bye-law committee summaries."""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.core.models import Committee, Department, Executive


SESSION = "2026/2027"

# Names and academic details are transcribed from the executive posters supplied
# by the society. Phone numbers and gender icons are intentionally left blank.
ROSTER = [
    ("Bolarinwa Idris", "400", "Chemical Engineering", "Amir"),
    ("Abdulrahman Mas'ud", "300", "Chemical Engineering", "Naibul Amir"),
    ("Olanrewaju Kawthar", "400", "Biomedical Engineering", "Amirah"),
    ("Qosim Mujeebah", "300", "Microbiology", "Naibatul Amirah"),
    ("Al-Ameen Akinade", "300", "Software Engineering", "General Secretary"),
    ("Adedeji Fathia", "300", "Quantity Surveying", "Assistant General Secretary"),
    ("Abdulazeez Abdullah", "200", "Cyber Security", "Dawah Officer 1"),
    ("Bamoore Ridwan", "300", "Industrial Chemistry", "Dawah Officer 2"),
    ("Ibrahim Mustapha", "300", "Estate Management", "Dawah Officer 3"),
    ("Olona Zainab", "300", "Biochemistry", "Treasurer"),
    ("Omirinde Abdullah", "400", "Civil Engineering", "Financial Secretary"),
    ("Rajim Mubaraq", "400", "Civil Engineering", "Business Chairman"),
    ("Abdulhammed Abdulroqeeb", "400", "Biomedical Engineering", "Director of Studies 1"),
    ("Adeyanju Zainab", "400", "Urban and Regional Planning", "Director of Studies 2"),
    ("Shittu Ummulkhoyr", "300", "Cyber Security", "Director of Studies 3"),
    ("Muthoir Abdulmateen Opeyemi", "300", "Mechatronics Engineering", "Public Relations Officer 1"),
    ("Ayantola Abdussamad Ayankunle", "300", "Civil Engineering", "Public Relations Officer 2"),
    ("Murtadho Muslimah", "300", "Food Science and Technology", "Public Relations Officer 1"),
    ("Olaniyi Hameedah", "300", "Biochemistry", "Public Relations Officer 2"),
    ("Hussein Abdultawwab", "300", "Civil Engineering", "Asset Maintenance Officer"),
    ("Akinlabi Abdulmalik", "300", "Mechatronics Engineering", "Assistant Asset Maintenance Officer"),
    ("Olanrewaju Fathia", "300", "Mathematics", "Assistant Asset Maintenance Officer"),
    ("Kamaldeen Uswah", "200", "Biotechnology", "Assistant Asset Maintenance Officer"),
    ("Adeleke Sulaimon", "300", "Microbiology", "Chief Security Officer 1"),
    ("Abdulazeez Ibullah", "300", "Cyber Security", "Chief Security Officer 2"),
    ("Abdullahi Dandi", "400", "Civil Engineering", "Welfare Officer 1"),
    ("Ibrahim Ismail", "300", "Software Engineering", "Welfare Officer 2"),
    ("Ogunsola Mardiyah", "400", "Building Technology", "Welfare Officer 3"),
    ("Qosim Husnah", "300", "Biochemistry", "Welfare Officer 4"),
    ("Ridollah Adeshina", "300", "Chemical Engineering", "Editor-in-Chief"),
    ("Raji Muhibudeen", "400", "Mechatronics Engineering", "Council Director of Studies 1"),
    ("Adeshina Mardiyah", "300", "Biochemistry", "Council Director of Studies 2"),
    ("Faheemah Abdulwasi", "400", "Estate Management", "Sister Circle Coordinator"),
    ("Bakare Muhammed", "400", "Surveying and Geoinformatics", "Librarian 1"),
    ("Akingboye Azeezah", "400", "Biomedical Engineering", "Librarian 2"),
    ("Sikiru Hassan", "400", "Surveying and Geoinformatics", "Auditor"),
    ("Hammed Muslim", "400", "Civil Engineering", "Faculty Coordinator, Engineering"),
    ("Abdulqudus Abdulrazaq", "300", "Physics with Electronics", "Faculty Coordinator, Applied Sciences"),
    ("Abdullateef Ibrahim", "400", "Surveying and Geoinformatics", "Faculty Coordinator, Environmental Design and Management"),
    ("Abdulrasheed Abdullahi", "200", "Petroleum Engineering", "Secondary Schools Coordinator"),
    ("Olagunju Toheeb", "300", "Mechanical Engineering", "Hospital Visitation Committee Chairman"),
    ("Ogunwande Islamiyah", "300", "Biomedical Engineering", "Hospital Visitation Committee Secretary"),
    ("Daud Zainab", "300", "Biochemistry", "Hospital Visitation Committee Member"),
    ("Owoyemi Na'eemah", "300", "Microbiology", "Secretary to Business Committee"),
    ("Isiaq Zainab", "300", "Industrial and Production Engineering", "Assistant Secretary to Business Committee"),
]

COMMITTEES = [
    ("Central Da'wah Committee", "Coordinates the branch da'wah and programme calendar. The Naibul Ameer leads the committee with the Ameerah, Public Relations Officer, Dawah Officers, hostel and faculty coordinators, and Circle of Learning coordinators. Programmes are subject to Executive Council approval."),
    ("Hospital Visitation Committee", "Organises visits to University College Hospital and Jaja Clinic, shares Islamic materials and basic support, and identifies patients who may need assistance. It can recommend bill support through Al-Ansar Foundation after consultation with the Ameer and Executive Council."),
    ("Welfare Committee", "Coordinates welfare support for members, including support delivered through welfare representatives in hostels and faculties."),
    ("Publicity Committee and Editorial Board", "Led by the Public Relations Officer with hostel and faculty publicity officers. The committee shares branch information, raises awareness and produces publications such as the branch magazine and newsletters."),
    ("Business Committee", "Oversees the day-to-day running of branch business ventures. Its working group includes the Business Committee chair, secretary, unit heads and branch Treasurer."),
    ("Educational Committee", "Coordinates the branch's academic work, including extramural classes and other learning support. The Director of Studies leads the committee."),
    ("Financial Committee", "Led by the Financial Secretary with hostel and faculty financial secretaries. It coordinates dues, members' financial obligations and fundraising in collaboration with the Executive Council."),
    ("Maintenance Committee", "Looks after branch assets at the central mosque, hostels and faculties, as well as the mosque surroundings. Asset Maintenance Officers lead the work with hall representatives."),
    ("Security Committee (MSSO)", "Coordinates security and protection for the branch and its members."),
    ("Executive Council", "The branch's highest decision-making body. It is chaired by the Ameer and meets at least weekly to coordinate and decide society matters."),
    ("Convert-Revert Committee", "Supports convert and revert matters among students on campus and in nearby communities."),
]


class Command(BaseCommand):
    help = "Import the 2026/2027 executive roster and standing committee details."

    @transaction.atomic
    def handle(self, *args, **options):
        # Only records from this new session are replaced; archived sessions stay intact.
        Executive.objects.filter(is_current=True).exclude(session=SESSION).update(is_current=False)
        missing_departments = set()
        for order, (name, level, department_name, position) in enumerate(ROSTER, start=1):
            department = Department.objects.filter(name__iexact=department_name).order_by("id").first()
            if department is None:
                missing_departments.add(department_name)
            Executive.objects.update_or_create(
                full_name=name,
                position=position,
                session=SESSION,
                defaults={
                    "level": level,
                    "department": department,
                    "department_label": department_name,
                    "phone": "",
                    "email": "",
                    "avatar_icon": "",
                    "bio": "",
                    "order": order,
                    "is_current": True,
                },
            )

        for order, (name, description) in enumerate(COMMITTEES, start=1):
            Committee.objects.update_or_create(
                name=name,
                session=SESSION,
                defaults={"description": description, "order": order},
            )

        self.stdout.write(self.style.SUCCESS(f"Loaded {len(ROSTER)} executives and {len(COMMITTEES)} committee summaries for {SESSION}."))
        if missing_departments:
            self.stdout.write(self.style.WARNING("Departments not found (left blank for admin assignment): " + ", ".join(sorted(missing_departments))))
