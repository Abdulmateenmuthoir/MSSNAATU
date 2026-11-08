from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.db.models import F

from apps.accounts.decorators import role_required
from apps.accounts.models import ROLE_LIBRARY
from apps.core.models import Department, Faculty, LEVEL_CHOICES

from .forms import PastQuestionForm
from .models import PastQuestion


def library_list(request):
    questions = PastQuestion.objects.select_related("faculty", "department", "uploaded_by")
    faculty_id = request.GET.get("faculty", "")
    department_id = request.GET.get("department", "")
    level = request.GET.get("level", "")
    query = (request.GET.get("q") or "").strip()
    if faculty_id:
        questions = questions.filter(faculty_id=faculty_id)
    if department_id:
        questions = questions.filter(department_id=department_id)
    if level:
        questions = questions.filter(level=level)
    if query:
        questions = questions.filter(Q(course_code__icontains=query) | Q(course_title__icontains=query))
    paginator = Paginator(questions, 12)
    page = paginator.get_page(request.GET.get("page"))
    departments = Department.objects.select_related("faculty")
    if faculty_id:
        departments = departments.filter(faculty_id=faculty_id)
    query_params = request.GET.copy()
    query_params.pop("page", None)
    return render(
        request,
        "library/list.html",
        {
            "page": page,
            "faculties": Faculty.objects.all(),
            "departments": departments,
            "levels": LEVEL_CHOICES,
            "selected_faculty": faculty_id,
            "selected_department": department_id,
            "selected_level": level,
            "query": query,
            "query_string": query_params.urlencode(),
            "total": questions.count(),
        },
    )


@login_required
def question_download(request, pk):
    question = get_object_or_404(PastQuestion, pk=pk)
    if not question.file:
        raise Http404("This file is no longer available.")
    PastQuestion.objects.filter(pk=pk).update(downloads=F("downloads") + 1)
    try:
        return FileResponse(
            question.file.open("rb"),
            as_attachment=True,
            filename=f"{question.course_code.replace(' ', '-')}-{question.session.replace('/', '-')}.{question.extension}",
        )
    except FileNotFoundError:
        raise Http404("This file is no longer available.")


def question_detail(request, pk):
    question = get_object_or_404(
        PastQuestion.objects.select_related("faculty", "department", "uploaded_by"), pk=pk
    )
    related = (
        PastQuestion.objects.filter(department=question.department)
        .exclude(pk=question.pk)
        .select_related("faculty", "department")[:4]
    )
    return render(request, "library/detail.html", {"question": question, "related": related})


# ---------------------------------------------------------------------------
# Library dashboard
# ---------------------------------------------------------------------------


@role_required(ROLE_LIBRARY)
def manage_list(request):
    questions = PastQuestion.objects.select_related("faculty", "department").order_by("-created_at")
    query = (request.GET.get("q") or "").strip()
    if query:
        questions = questions.filter(Q(course_code__icontains=query) | Q(course_title__icontains=query))
    stats = {
        "total": PastQuestion.objects.count(),
        "downloads": PastQuestion.objects.aggregate(total=Sum("downloads"))["total"] or 0,
        "faculties": Faculty.objects.count(),
    }
    return render(
        request,
        "dashboard/library/list.html",
        {"questions": questions, "query": query, "stats": stats},
    )


@role_required(ROLE_LIBRARY)
def question_create(request):
    form = PastQuestionForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        question = form.save(commit=False)
        question.uploaded_by = request.user
        question.save()
        messages.success(request, "Past question uploaded.")
        return redirect("pastquestions:list")
    return render(request, "dashboard/library/form.html", {"form": form, "question": None})


@role_required(ROLE_LIBRARY)
def question_edit(request, pk):
    question = get_object_or_404(PastQuestion, pk=pk)
    form = PastQuestionForm(request.POST or None, request.FILES or None, instance=question)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Past question updated.")
        return redirect("pastquestions:list")
    return render(request, "dashboard/library/form.html", {"form": form, "question": question})


@role_required(ROLE_LIBRARY)
@require_POST
def question_delete(request, pk):
    question = get_object_or_404(PastQuestion, pk=pk)
    label = question.course_code
    question.delete()
    messages.success(request, f"{label} was removed from the library.")
    return redirect("pastquestions:list")
