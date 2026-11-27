from django.conf import settings
from django.db import models
from django.utils import timezone


class Species(models.TextChoices):
    DOG = "DOG", "Dog"
    CAT = "CAT", "Cat"
    OTHER = "OTHER", "Other"


class Status(models.TextChoices):
    LOST = "LOST", "Lost"
    FOUND = "FOUND", "Found"
    STALE = "STALE", "Stale"
    CLOSED = "CLOSED", "Closed"


ACTIVE_STATUSES = (Status.LOST, Status.STALE)
CASE_SUBMISSION_CONSTRAINT = "cases_owner_submission_key_unique"
STATUS_TRANSITIONS = {
    Status.LOST: (Status.FOUND, Status.STALE, Status.CLOSED),
    Status.STALE: (Status.LOST, Status.FOUND, Status.CLOSED),
    Status.FOUND: (Status.CLOSED,),
    Status.CLOSED: (),
}


class Zone(models.Model):
    id = models.BigAutoField(primary_key=True, db_column="zone_id")
    zone_name = models.CharField("zone name", max_length=100, unique=True)

    class Meta:
        db_table = "zones"
        ordering = ["zone_name"]

    def __str__(self):
        return self.zone_name


class LostPetCase(models.Model):
    id = models.BigAutoField(primary_key=True, db_column="case_id")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, models.PROTECT)
    zone = models.ForeignKey(Zone, models.PROTECT)
    submission_key = models.UUIDField(null=True, blank=True, editable=False)
    pet_name = models.CharField(max_length=100)
    species = models.CharField(max_length=10, choices=Species.choices)
    breed = models.CharField(max_length=100, blank=True)
    color = models.CharField(max_length=100)
    description = models.TextField(max_length=3000, blank=True)
    photo_data = models.BinaryField(null=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.LOST)
    lost_at = models.DateTimeField("date and time lost")
    last_known_location = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cases"
        ordering = ["-created_at", "-pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "submission_key"],
                condition=models.Q(submission_key__isnull=False),
                name=CASE_SUBMISSION_CONSTRAINT,
            ),
            models.CheckConstraint(condition=models.Q(species__in=Species.values), name="cases_species_valid"),
            models.CheckConstraint(condition=models.Q(status__in=Status.values), name="cases_status_valid"),
            models.CheckConstraint(condition=models.Q(lost_at__lte=models.F("created_at")), name="cases_lost_at_before_creation"),
        ]


class CaseStatusHistory(models.Model):
    id = models.BigAutoField(primary_key=True, db_column="history_id")
    case = models.ForeignKey(LostPetCase, models.CASCADE, related_name="status_history")
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, models.PROTECT, null=True, db_column="changed_by",
    )
    old_status = models.CharField(max_length=10, choices=Status.choices, null=True)
    new_status = models.CharField(max_length=10, choices=Status.choices)
    changed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "case_status_history"
        ordering = ["-changed_at", "-pk"]
        constraints = [
            models.CheckConstraint(condition=models.Q(old_status__in=Status.values) | models.Q(old_status__isnull=True), name="case_history_old_status_valid"),
            models.CheckConstraint(condition=models.Q(new_status__in=Status.values), name="case_history_new_status_valid"),
            models.CheckConstraint(condition=models.Q(old_status__isnull=True) | ~models.Q(old_status=models.F("new_status")), name="case_history_status_changed"),
        ]
