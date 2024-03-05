from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver


from django_prefixctl.models import PrefixSet, PrefixSetIRRImporter


@receiver(post_save, sender=PrefixSet)
def prefix_set_post_save(sender, **kwargs):
    """
    Signal receiver for post-save actions on a PrefixSet.

    Ensures that if IRR import is enabled for a PrefixSet, an associated IRR importer object is created or updated.
    If IRR import is not enabled, any existing associated IRR importer object is deleted.

    Arguments:
    sender: The model class that sent the signal.
    kwargs: Keyword arguments including 'instance' of the PrefixSet.
    """
    prefix_set = kwargs.get("instance")

    if prefix_set.irr_import:
        try:
            prefix_set.prefix_set_irr_importer
        except PrefixSetIRRImporter.DoesNotExist:
            PrefixSetIRRImporter.objects.create(
                instance=prefix_set.instance, prefix_set=prefix_set
            )
        prefix_set.prefix_set_irr_importer.require_task_schedule
    else:
        try:
            prefix_set.prefix_set_irr_importer.delete()
        except PrefixSetIRRImporter.DoesNotExist:
            pass


@receiver(pre_delete, sender=PrefixSet)
def prefix_set_pre_delete(sender, **kwargs):
    """
    Signal receiver for pre-delete actions on a PrefixSet.

    Deletes the associated PrefixSetIRRImporter when a PrefixSet is being deleted.

    Arguments:
    sender: The model class that sent the signal.
    kwargs: Keyword arguments including 'instance' of the PrefixSet being deleted.
    """
    prefix_set = kwargs.get("instance")

    try:
        prefix_set.prefix_set_irr_importer.delete()
    except PrefixSetIRRImporter.DoesNotExist:
        pass
