import json

from fullctl.django.models import Task
from fullctl.django.tasks import register

from django_prefixctl.irr import perform_irr_import
from django_prefixctl.models.prefixctl import PrefixSet

__all__ = [
    "IRRImportTask",
]


@register
class IRRImportTask(Task):
    """
    Task for importing IP network prefixes from IRR sources into a PrefixSet.

    Attributes:
    TaskMeta: Configuration for the task, including execution limits.
    HandleRef: Reference handling for the task, including its tag.
    """

    class TaskMeta:
        limit = 1

    class HandleRef:
        tag = "task_irr_import"

    class Meta:
        proxy = True

    @property
    def generate_limit_id(self):
        """
        Generates a limit ID for the task, based on the PrefixSet ID.

        Returns:
        An identifier that limits task execution based on the PrefixSet ID.
        """
        return self.prefix_set.id

    @property
    def prefix_set(self):
        """
        Retrieves the PrefixSet associated with this task.

        Returns:
        The PrefixSet object identified by the parameter passed to the task.
        """
        return PrefixSet.objects.get(id=self.param["args"][0])

    def run(self, *args, **kwargs):
        """
        Executes the task to import IP network prefixes from IRR sources into the associated PrefixSet.

        Arguments:
        - args: Additional positional arguments (unused).
        - kwargs: Additional keyword arguments (unused).

        Returns:
        A JSON string representing the import result.
        """
        prefix_set = self.prefix_set

        as_set = prefix_set.irr_as_set
        sources = prefix_set.irr_sources
        result = perform_irr_import(self.prefix_set, as_set, sources)
        return json.dumps(result)
