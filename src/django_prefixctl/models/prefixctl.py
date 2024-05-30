import secrets

import fullctl.service_bridge.pdbctl as pdbctl
import reversion
import structlog
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_grainy.decorators import grainy_model
from fullctl.django.inet.validators import validate_masklength_range
from fullctl.django.models.abstract.alert import AlertGroup as AlertGroupBase
from fullctl.django.models.abstract.alert import AlertLog as AlertLogBase
from fullctl.django.models.abstract.alert import AlertRecipient as AlertRecipientBase
from fullctl.django.models.abstract.base import HandleRefModel, SlugModel
from fullctl.django.models.concrete import Instance
from fullctl.django.models.concrete.tasks import Monitor, Task, TaskSchedule
from fullctl.django.validators import validate_alphanumeric, validate_alphanumeric_list
from netfields import CidrAddressField

__all__ = (
    "ASNSet",
    "ASN",
    "PrefixSet",
    "PrefixSetIRRImporter",
    "Prefix",
    "Monitor",
    "MonitorTaskMixin",
    "ASNMonitor",
    "AlertGroup",
    "AlertTask",
    "AlertRecipient",
    "AlertLog",
    "AlertLogRecipient",
    "Instance",
    "register_prefix_monitor",
    "PREFIX_MONITOR_CLASSES",
)

PREFIX_MONITOR_CLASSES = {}

log = structlog.get_logger("django")


def register_prefix_monitor(cls):
    """
    Registers a prefix monitor class.

    Arguments:
    cls: The class to register as a prefix monitor.

    Returns:
    The class that was registered.

    Raises:
    KeyError: If a prefix monitor with the same tag is already registered.
    ValueError: If the monitor model does not inherit from HandleRefModel.
    """
    try:
        if cls.HandleRef.tag in PREFIX_MONITOR_CLASSES:
            raise KeyError(
                f"Already registered a prefix monitor with tag `{cls.HandleRef.tag}`"
            )
    except AttributeError:
        raise ValueError("Monitor model needs to be a HandleRef model")

    PREFIX_MONITOR_CLASSES[cls.HandleRef.tag] = {
        "tag": cls.HandleRef.tag,
        "cls": cls,
        "title": cls._meta.verbose_name,
    }
    return cls


def generate_secret():
    """
    Generates a URL-safe secret token.

    Returns:
    A URL-safe secret token as a string.
    """
    return f"{secrets.token_urlsafe()}"


class TaskContainer(models.Model):
    """
    A container model for tasks.
    """

    pass


@grainy_model(related="instance")
@reversion.register
class ASNSet(SlugModel):
    """
    Represents a set of Autonomous System Numbers (ASN).

    Attributes:
    instance: Foreign key to an environment instance, indicating the instance this ASN set belongs to.
    name: Name of the ASN set.
    description: Description of the ASN set, optional.
    """

    instance = models.ForeignKey(
        Instance,
        related_name="asn_set_set",
        on_delete=models.CASCADE,
        help_text=_("Environment instance id"),
    )

    name = models.CharField(max_length=255, help_text=_("name of the asn set"))
    description = models.CharField(
        max_length=255, null=True, blank=True, help_text=_("description of the asn set")
    )

    class Meta:
        db_table = "prefixctl_asnset"
        unique_together = (("instance", "name"), ("instance", "slug"))

    class HandleRef:
        tag = "asn_set"

    def __str__(self):
        return f"{self.instance}: {self.name} ({self.id})"


@grainy_model(related="asn_set")
@reversion.register
class ASN(HandleRefModel):
    """
    Represents an Autonomous System Number (ASN) within a set.

    Attributes:
    asn: The autonomous system number.
    asn_set: Foreign key to the ASNSet this ASN belongs to.
    """

    asn = models.PositiveIntegerField()
    asn_set = models.ForeignKey(
        ASNSet, related_name="asn_set", on_delete=models.CASCADE
    )

    class Meta:
        db_table = "prefixctl_asn"
        unique_together = ("asn_set", "asn")

    class HandleRef:
        tag = "asn"

    @property
    def ref(self):
        """
        Retrieves the network reference based on the ASN.

        Returns:
        The network reference object.
        """
        if not hasattr(self, "_ref"):
            self._ref = pdbctl.Network().first(asn=self.asn)
        return self._ref


@grainy_model(
    namespace="prefix",
    namespace_instance="prefix.{instance.org.permission_id}.{instance.id}",
)
@reversion.register(follow=['prefix_set'])
class PrefixSet(SlugModel):
    """
    Represents a set of IP network prefixes.

    Attributes:
    instance: Foreign key to an environment instance, indicating the instance this prefix set belongs to.
    name: Name of the prefix set.
    description: Description of the prefix set, optional.
    irr_import: Boolean indicating if automatic import of prefixes is enabled.
    irr_sources: Comma-separated sources for prefix list import.
    irr_as_set: Specifies the AS-SET for importing prefixes.
    ux_keep_list_open: UX preference, whether to keep the prefix list expanded.
    """

    instance = models.ForeignKey(
        Instance,
        related_name="prefix_set_set",
        on_delete=models.CASCADE,
        help_text=_("Environment instance id"),
    )

    name = models.CharField(max_length=255, help_text=_("name of the prefix set"))
    description = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text=_("description of the prefix set"),
    )

    irr_import = models.BooleanField(
        default=False, help_text=_("enable automatic import of prefixes")
    )
    irr_sources = models.CharField(
        max_length=255,
        default=None,
        blank=True,
        null=True,
        help_text=_("specify sources for prefixlist import (comma separated)"),
        validators=(validate_alphanumeric_list,),
    )
    irr_as_set = models.CharField(
        max_length=255,
        default=None,
        blank=True,
        null=True,
        help_text=_("import prefixes for AS-SET"),
        validators=(validate_alphanumeric,),
    )

    # TODO: user centric preferences?
    ux_keep_list_open = models.BooleanField(
        default=False, help_text=_("UX Preference: Keep prefix list expanded")
    )

    class Meta:
        db_table = "prefixctl_prefix_set"
        unique_together = (("instance", "name"), ("instance", "slug"))

    class HandleRef:
        tag = "prefix_set"

    @property
    def org(self):
        """
        Retrieves the organization associated with this prefix set.

        Returns:
        The organization object.
        """
        return self.instance.org

    def __str__(self):
        return f"{self.instance}: {self.name} ({self.id})"

    @property
    def irr_import_status(self) -> str:
        """
        Will return the IRR import status as one of the following

        - pending
        - completed
        - error
        - disabled
        """

        if not self.irr_import:
            return "disabled"

        try:
            importer = self.prefix_set_irr_importer
        except PrefixSetIRRImporter.DoesNotExist:
            log.error("IRR import enabled but no importer found", prefix_set=self)
            return "error"

        try:
            importer.task_schedule
        except TaskSchedule.DoesNotExist:
            log.error("IRR import enabled but no task schedule found", prefix_set=self)
            return "error"

        recent_task = importer.task_schedule.tasks.order_by("-created").first()

        if not recent_task:
            return "pending"

        return recent_task.status

    def add_or_update_prefix(self, prefix, mask_length_range):
        """
        Add or update a prefix in this prefix set

        Arguments:
            - prefix (str): a valid ip_network prefix string
            - max_length_range(str): "exact" or "[0-9]..[0-9]"

        Returns:
            - tuple(created(bool), updated(bool))
        """

        created = False
        updated = False

        try:
            # retrieve the existing prefix
            obj = Prefix.objects.get(prefix_set=self, prefix=prefix)

            # did mask length range change?
            if obj.mask_length_range != mask_length_range:
                obj.mask_length_range = mask_length_range
                updated = True

            # is the status of the existing prefix not "ok" ?
            # set it to ok
            if obj.status != "ok":
                obj.status = "ok"
                updated = True

            # if any changes were made save the prefix
            if updated:
                obj.save()
        except Prefix.DoesNotExist:
            # prefix does not exist yet, created it
            obj = Prefix.objects.create(
                prefix_set=self,
                prefix=prefix,
                status="ok",
                mask_length_range=mask_length_range,
            )
            created = True

        return created, updated


class PrefixSetIRRImporter(Monitor):
    """
    Manages the import of IP network prefixes into a PrefixSet from IRR sources.

    Attributes:
    instance: Foreign key to an environment instance linked with this importer.
    prefix_set: OneToOne relationship to the PrefixSet being imported into.
    task_schedule: OneToOne relationship to the task schedule for this importer.
    """

    instance = models.ForeignKey(
        Instance, related_name="prefix_set_irr_importers", on_delete=models.CASCADE
    )

    prefix_set = models.OneToOneField(
        PrefixSet, related_name="prefix_set_irr_importer", on_delete=models.CASCADE
    )

    task_schedule = models.OneToOneField(
        TaskSchedule,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        help_text=_("The task schedule for the irr importer"),
    )

    class Meta:
        db_table = "prefixctl_prefix_set_irr_importer"

    class HandleRef:
        tag = "prefix_set_irr_importer"

    @property
    def schedule_interval(self):
        """
        Retrieves the scheduled interval for the IRR importer task.

        Returns:
        The scheduled interval setting from Django settings.
        """
        return settings.IRR_IMPORT_FREQUENCY

    @property
    def schedule_task_config(self):
        """
        Configures the scheduled task for the IRR importer.

        Returns:
        A dictionary containing the task configuration.
        """
        param = {
            "args": [self.prefix_set.id],
            "kwargs": {},
        }
        return {
            "tasks": [
                {
                    "op": "task_irr_import",
                    "param": param,
                }
            ]
        }


@grainy_model(
    namespace="prefix",
    namespace_instance="prefix.{instance.prefix_set.org.permission_id}.{instance.prefix_set_id}.{instance.id}",
)
@reversion.register(follow=['prefix_set'])
class Prefix(HandleRefModel):
    """
    Represents an IP network prefix within a set.

    Attributes:
    prefix_set: Foreign key to the PrefixSet this prefix belongs to.
    prefix: The IP network prefix.
    mask_length_range: Specifies the permissible mask length range for the prefix.
    """

    prefix_set = models.ForeignKey(
        PrefixSet, related_name="prefix_set", on_delete=models.CASCADE
    )
    prefix = CidrAddressField()

    mask_length_range = models.CharField(
        max_length=255, default="exact", validators=[validate_masklength_range]
    )

    class Meta:
        db_table = "prefixctl_prefix"
        unique_together = ("prefix_set", "prefix")

    class HandleRef:
        tag = "prefix"


class MonitorTaskMixin:
    """
    Mixin providing utility methods for monitor tasks.

    Methods:
    alert_groups: Returns the alert groups associated with the monitor.
    queue_notify_event: Queues an event notification for all associated alert groups.
    """

    @property
    def alert_groups(self):
        """
        Retrieves the alert groups associated with this monitor.

        Returns:
        A queryset of AlertGroup objects related to this monitor.
        """
        # FIXME: currently always returns the "main" alert group
        return AlertGroup.objects.filter(instance=self.owner.instance, name="main")

    def queue_notify_event(self, event_name):
        for alert_group in self.alert_groups:
            alert_group.start_task("notify", event_name)


@grainy_model(
    "asn_monitor",
    namespace_instance="asn_monitor.{instance.instance.org.permission_id}.{instance.id}",
)
@reversion.register
class ASNMonitor(Monitor):
    """
    A monitor for tracking new prefix detections associated with ASNs.

    Attributes:
    instance: Foreign key to an environment instance this monitor belongs to.
    asn_set: Foreign key to the ASNSet being monitored.
    new_prefix_detection: Indicates if the monitor is set to detect new prefixes.
    task_schedule: OneToOne relationship to the task schedule for this monitor.
    """

    instance = models.ForeignKey(
        Instance, related_name="asn_monitor_set", on_delete=models.CASCADE
    )
    asn_set = models.ForeignKey(
        ASNSet, related_name="asn_monitor_set", on_delete=models.CASCADE
    )

    new_prefix_detection = models.BooleanField(help_text=_("New prefix detection"))

    task_schedule = models.OneToOneField(
        TaskSchedule,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        help_text=_("The task schedule for this monitor"),
    )

    class Meta:
        db_table = "prefixctl_asn_monitor"

    class HandleRef:
        tag = "asn_monitor"


@grainy_model(related="instance")
@reversion.register
class AlertGroup(AlertGroupBase):
    """
    Represents an alert group for the organization, extending base alert group functionality.

    Attributes:
    instance: Foreign key to the Instance this alert group is associated with.
    """

    instance = models.ForeignKey(
        Instance, related_name="alertgrp_set", on_delete=models.CASCADE
    )

    class Meta:
        db_table = "prefixctl_alertgrp"
        unique_together = (("instance", "name"),)

    @property
    def task_class(self):
        return AlertTask

    @property
    def log_class(self):
        return AlertLog

    @property
    def log_recipient_class(self):
        return AlertLogRecipient

    @property
    def recipients(self):
        return self.alertrcp_set.filter(status="ok")

    def __str__(self):
        return f"{self.instance}: {self.name}"


@grainy_model(related="owner")
class AlertTask(Task):
    """
    Task model for handling alert notifications.

    This is a proxy model inheriting from Task, with a custom limit property.
    """

    limit = -1

    class Meta(Task.Meta):
        proxy = True

    class HandleRef:
        tag = "alert_task"

    @property
    def owner(self):
        return None

    def op_notify(self, event):
        log = self.owner.notify(f"Event: {event}", f"Test message for event {event}")

        return f"{log}"


@grainy_model(related="alertgrp")
@reversion.register
class AlertRecipient(AlertRecipientBase):
    """
    Represents an alert recipient within an alert group.

    Attributes:
    alertgrp: Foreign key to the AlertGroup this alert recipient is associated with.
    """

    alertgrp = models.ForeignKey(
        AlertGroup, related_name="alertrcp_set", on_delete=models.CASCADE
    )

    class Meta:
        db_table = "prefixctl_alertrcp"
        unique_together = (("alertgrp", "typ", "recipient"),)


@grainy_model(related="alertgrp")
@reversion.register
class AlertLog(AlertLogBase):
    """
    Represents an alert log within an alert group.

    Attributes:
    alertgrp: Foreign key to the AlertGroup associated with this log.
    """

    alertgrp = models.ForeignKey(
        AlertGroup, related_name="alertlog_set", on_delete=models.CASCADE
    )

    class Meta:
        db_table = "prefixctl_alertlog"


@grainy_model(related="alertlog")
@reversion.register
class AlertLogRecipient(AlertRecipientBase):
    """
    Represents an alert log recipient, extending the base alert recipient functionality.

    Attributes:
    alertlog: Foreign key to the AlertLog this recipient is associated with.
    """

    alertlog = models.ForeignKey(
        AlertLog, related_name="alert_log_recipient_set", on_delete=models.CASCADE
    )

    class Meta:
        db_table = "prefixctl_alert_log_recipient"

    class HandleRef:
        tag = "alert_log_recipient"
