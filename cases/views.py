from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe, require_http_methods

from accounts.models import User
from .forms import CaseForm, ZoneForm
from .models import ACTIVE_STATUSES, CaseStatusHistory, LostPetCase, Zone


def manageable_cases(user):
    cases = LostPetCase.objects.all()
    if user.role == User.Role.ADMIN:
        return cases
    if user.role == User.Role.MEMBER:
        return cases.filter(owner=user)
    raise PermissionDenied


def managed_case(user, pk, *, lock=False):
    cases = manageable_cases(user)
    if lock:
        cases = cases.select_for_update()
    return get_object_or_404(cases, pk=pk)


@never_cache
@login_required
@require_safe
def case_list(request):
    is_admin = request.user.role == User.Role.ADMIN
    show_mine = request.GET.get("view") == "mine" and not is_admin
    cases = manageable_cases(request.user)
    if not is_admin and not show_mine:
        cases = LostPetCase.objects.filter(status__in=ACTIVE_STATUSES)
    cases = cases.select_related("zone").defer("photo_data")
    return render(request, "cases/list.html", {
        "cases": cases, "is_admin": is_admin, "show_mine": show_mine,
    })


@never_cache
@login_required
@require_safe
def case_detail(request, pk):
    case = get_object_or_404(manageable_cases(request.user).select_related("zone"), pk=pk)
    history = case.status_history.select_related("changed_by")
    return render(request, "cases/detail.html", {
        "case": case, "history": history,
    })


@never_cache
@login_required
@require_safe
def case_photo(request, pk):
    case = get_object_or_404(manageable_cases(request.user).only("photo_data"), pk=pk)
    if not case.photo_data:
        raise Http404
    return HttpResponse(bytes(case.photo_data), content_type="image/jpeg")


@never_cache
@login_required
@require_http_methods(["GET", "POST"])
def case_create(request):
    if request.user.role != User.Role.MEMBER:
        raise PermissionDenied
    form = CaseForm(request.POST, request.FILES) if request.method == "POST" else CaseForm()
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            case = form.save(commit=False)
            case.owner = request.user
            case.save()
            CaseStatusHistory.objects.create(case=case, new_status=case.status, changed_by=request.user)
        messages.success(request, "Lost-pet case created.")
        return redirect("cases:detail", pk=case.pk)
    return render(request, "cases/form.html", {"form": form})


@never_cache
@login_required
@require_http_methods(["GET", "POST"])
def case_update(request, pk):
    if request.method == "POST":
        with transaction.atomic():
            case = managed_case(request.user, pk, lock=True)
            old_status = case.status
            form = CaseForm(request.POST, request.FILES, instance=case)
            if form.is_valid():
                case = form.save()
                if case.status != old_status:
                    CaseStatusHistory.objects.create(
                        case=case, old_status=old_status, new_status=case.status, changed_by=request.user,
                    )
                messages.success(request, "Lost-pet case updated.")
                return redirect("cases:detail", pk=case.pk)
    else:
        case = managed_case(request.user, pk)
        form = CaseForm(instance=case)
    return render(request, "cases/form.html", {"form": form, "case": case})


@never_cache
@login_required
@require_http_methods(["GET", "POST"])
def case_delete(request, pk):
    if request.method == "POST":
        with transaction.atomic():
            case = managed_case(request.user, pk, lock=True)
            case.delete()
        messages.success(request, "Lost-pet case deleted.")
        if request.user.role == User.Role.ADMIN:
            return redirect("cases:list")
        return redirect(reverse("cases:list", query={"view": "mine"}))
    case = managed_case(request.user, pk)
    return render(request, "cases/delete.html", {"case": case})


@never_cache
@login_required
@require_http_methods(["GET", "POST"])
def zone_manage(request, pk=None):
    if request.user.role != User.Role.ADMIN:
        raise PermissionDenied

    zone = get_object_or_404(Zone, pk=pk) if pk is not None else None
    form = ZoneForm(request.POST if request.method == "POST" else None, instance=zone)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                form.save()
        except IntegrityError:
            duplicates = Zone.objects.filter(zone_name=form.cleaned_data["zone_name"]).exclude(
                pk=form.instance.pk,
            )
            if not duplicates.exists():
                raise
            form.add_error("zone_name", form.fields["zone_name"].error_messages["unique"])
        else:
            messages.success(request, "Zone saved.")
            return redirect("cases:zones")

    return render(request, "cases/zones.html", {
        "form": form, "zone": zone, "zones": Zone.objects.all(),
    })
