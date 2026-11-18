from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_safe

from accounts.models import User
from .forms import CaseForm, ZoneForm
from .models import ACTIVE_STATUSES, CaseStatusHistory, LostPetCase, Zone


@login_required
@require_safe
def case_list(request):
    is_admin = request.user.role == User.Role.ADMIN
    cases = LostPetCase.objects.select_related("zone").defer("photo_data")
    if not is_admin:
        cases = cases.filter(status__in=ACTIVE_STATUSES)
    return render(request, "cases/list.html", {"cases": cases, "is_admin": is_admin})


@login_required
@require_safe
def case_detail(request, pk):
    cases = LostPetCase.objects.select_related("zone").defer("photo_data")
    if request.user.role != User.Role.ADMIN:
        cases = cases.filter(Q(owner=request.user) | Q(status__in=ACTIVE_STATUSES))
    case = get_object_or_404(cases, pk=pk)
    return render(request, "cases/detail.html", {"case": case})


@login_required
@require_http_methods(["GET", "POST"])
def case_create(request):
    if request.user.role != User.Role.MEMBER:
        raise PermissionDenied

    form = CaseForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            case = form.save(commit=False)
            case.owner = request.user
            case.save()
            CaseStatusHistory.objects.create(
                case=case, new_status=case.status, changed_by=request.user,
            )
        messages.success(request, "Lost-pet case created.")
        return redirect("cases:detail", pk=case.pk)

    return render(request, "cases/form.html", {"form": form, "has_zones": Zone.objects.exists()})


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
            if not Zone.objects.filter(zone_name=form.cleaned_data["zone_name"]).exists():
                raise
            form.add_error("zone_name", "That zone name already exists.")
        else:
            messages.success(request, "Zone saved.")
            return redirect("cases:zones")

    return render(request, "cases/zones.html", {
        "form": form, "zone": zone, "zones": Zone.objects.all(),
    })
