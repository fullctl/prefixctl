import ipaddress

from fullctl.django.models import Task
from fullctl.django.tasks import register as register_task

import prefix_meta.sources as sources


@register_task
class LocationUpdateTask(Task):
    """
    Task that runs location check on a prefix set
    """

    class Meta:
        proxy = True

    class TaskMeta:
        limit = 1

    class HandleRef:
        tag = "task_prefix_location"

    @property
    def prefix(self):
        return self.param["args"][0]

    @property
    def generate_limit_id(self):
        return self.prefix

    def run(self, *args, **kwargs):
        prefix = ipaddress.ip_network(self.prefix)
        sources.IP2Location.request(prefix)
