from django.contrib import admin

from django_prefixctl.models import (
    AlertGroup,
    AlertLog,
    AlertLogRecipient,
    AlertRecipient,
    AlertTask,
    ASNMonitor,
    ASNSet,
    Prefix,
    PrefixSet,
    PrefixSetIRRImporter,
)

# Register your models here.


class TaskAdmin(admin.ModelAdmin):
    list_display = ("org", "instance", "op", "status", "created", "updated")
    readonly_fields = ("org", "instance")

    def org(self, obj):
        return obj.owner.instance.org

    def instance(self, obj):
        return obj.owner.instance


class AlertRecipientInline(admin.TabularInline):
    model = AlertRecipient
    extra = 0
    fields = ("typ", "recipient", "status")


@admin.register(AlertGroup)
class AlertGroupAdmin(admin.ModelAdmin):
    list_display = ("instance", "name")
    inlines = (AlertRecipientInline,)
    readonly_fields = ("version",)


@admin.register(AlertTask)
class AlertTaskAdmin(admin.ModelAdmin):
    list_display = ("instance", "group", "status", "created")
    readonly_fields = ("instance", "group")

    def group(self, obj):
        return obj.owner.name

    def instance(self, obj):
        return obj.owner.instance


class AlertLogRecipientInline(admin.TabularInline):
    model = AlertLogRecipient
    extra = 0


@admin.register(AlertLog)
class AlertLogAdmin(admin.ModelAdmin):
    list_display = ("instance", "group", "subject", "recipients", "created")
    readonly_fields = ("instance", "group")
    inlines = (AlertLogRecipientInline,)

    def group(self, obj):
        return obj.alertgrp.name

    def instance(self, obj):
        return obj.alertgrp.instance

    def recipients(self, obj):
        return obj.alert_log_recipient_set.all().count()


@admin.register(Prefix)
class PrefixAdmin(admin.ModelAdmin):
    list_display = (
        "prefix_set",
        "prefix",
        "mask_length_range",
        "created",
        "updated",
    )
    readonly_fields = ("prefix_set", "created", "updated")


@admin.register(PrefixSetIRRImporter)
class PrefixSetIRRImporterAdmin(admin.ModelAdmin):
    list_display = ("prefix_set", "instance", "task_schedule")


class PrefixInline(admin.TabularInline):
    model = Prefix
    extra = 0
    fields = ("prefix", "mask_length_range", "created", "updated")
    readonly_fields = ("created", "updated")


class IRRImporterInline(admin.TabularInline):
    model = PrefixSetIRRImporter
    extra = 0


@admin.register(PrefixSet)
class PrefixSetAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "slug",
        "org",
        "instance",
        "name",
        "irr_import",
        "irr_as_set",
        "irr_sources",
        "created",
    )
    readonly_fields = ("org", "instance")
    search_fields = ("name", "instance__org__name")
    inlines = (
        IRRImporterInline,
        PrefixInline,
    )

    def org(self, obj):
        return obj.instance.org


@admin.register(ASNMonitor)
class ASNMonitorAdmin(admin.ModelAdmin):
    list_display = (
        "asn_set",
        "instance",
        "created",
    )


@admin.register(ASNSet)
class ASNSetAdmin(admin.ModelAdmin):
    list_display = (
        "org",
        "instance",
        "name",
        "created",
    )
    readonly_fields = ("org", "instance")
    search_fields = ("name", "instance__org__name")

    def org(self, obj):
        return obj.instance.org

    def instance(self, obj):
        return obj.instance
