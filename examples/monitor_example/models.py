from typing import Union
from django.db import models
from django_grainy.decorators import grainy_model
from fullctl.django.models import Task, TaskSchedule, Instance
from fullctl.django.tasks import register as register_task

from django_prefixctl.models import PrefixSet, register_prefix_monitor, Monitor
from monitor_example.monitor import example_monitor_logic

# Create your models here.

# Define permission namespace for your monitor, only users
# scoped to this namespace will be able to interact with your monitor
#
# NOTE: for standalone instances of prefixctl that are NOT authing against
# aaactl you can ignore this entirely.
#
# If you are authing against aaactl for now use the prefix_monitor and asn_monitor
# namespaces. In the future we will be adding a way to define your own namespaces
PERMISSION_NAMESPACE = "prefix_monitor"
PERMISSION_NAMESPACE_INSTANCE = "prefix_monitor.{instance.instance.org.permission_id}"


# monitor model needs to be register with prefixctl
@register_prefix_monitor
# and we use the grainy_model decorator to permission it
@grainy_model(PERMISSION_NAMESPACE, namespace_instance=PERMISSION_NAMESPACE_INSTANCE)
class ExampleMonitor(Monitor):

    """
    Describes per prefix-set instance of your monitor.
    """

    # organization workspace intance
    instance = models.ForeignKey(
        Instance, related_name="example_monitors", on_delete=models.CASCADE
    )

    # the prefix set that the monitor is running for
    prefix_set = models.OneToOneField(
        PrefixSet, related_name="example_monitors", on_delete=models.CASCADE
    )

    # task scheduler
    task_schedule = models.OneToOneField(
        TaskSchedule,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        help_text="The task schedule for this monitor",
    )

    class Meta:
        db_table = "prefixctl_example_monitor"
        verbose_name = "Prefix Example Monitor"
        verbose_name_plural = "Prefix Example Monitor"

    class HandleRef:
        # a unique identifier for the monitor model
        tag = "example_monitor"

    @property
    def schedule_interval(self):
        """
        The schedule interval for the task worker.
        For this example we are running the task worker once a day.
        """
        return 86400

    @property
    def schedule_task_config(self):
        """
        Defines the task worker configuration, letting you specify
        the arguments and keyword arguments that will be passed to the task worker
        creation method.

        Finally you also specify the task worker class that will be used to run the monitor,
        using the `op` key set to the task worker class HandleRef tag.
        """

        return {
            "tasks": [
                {
                    # the task worker class HandleRef tag
                    # which we used to register the ExampleMonitorTask class
                    "op": "monitor_example_task",
                    # create_task arguments
                    "param": {
                        # in this case we are just passing the prefix set id
                        "args": [self.prefix_set.id],
                    },
                }
            ]
        }


# TASK WORKER MODEL


# Task worker models need to be registered with fullctl so they
# are available to the task worker.
@register_task
class ExampleMonitorTask(Task):

    """
    A task worker model.

    This is a proxied model running on the same table as the fullctl
    Task base.

    Additional documentation on fullctl task classes can be found at:

    https://github.com/fullctl/fullctl/blob/main/docs/tasks.md

    This is were the logic of your monitor is executed.

    The create_task arguments should be documented, they describe what positional and keyword
    arguments the task will be created with. They are arbitrary and can be anything you want.

    For this example we are just interested in the prefix set.

    `create_task` arguments:
        - prefix_set_id: int - The PrefixSet model instance id that the monitor is running for.
    """

    class Meta:
        proxy = True

    class HandleRef:
        # a unique identifier for the task
        tag = "monitor_example_task"

    class TaskMeta:
        """
        The task metadata.

        Configure the task worker here.
        """

        # only one instance per limiter is allowed to run at a time
        # the limiter valus is defined via the generate_limit_id property
        limit = 1

    @property
    def prefix_set_id(self) -> int:
        """
        Helper function to get the prefix set id from the create_task arguments.
        """
        return self.param["args"][0]

    @property
    def prefix_set(self) -> PrefixSet:
        """
        Helper function to get the prefix set model instance from the create_task arguments.
        """
        return PrefixSet.objects.get(id=self.prefix_set_id)

    @property
    def generate_limit_id(self) -> Union[str, int]:
        """
        Helper function to generate the limit id for the task worker.

        In this case we just want to limit the instances of this task running for a given prefix set.
        """
        return self.prefix_set_id

    def run(self, *args, **kwargs):
        """
        The run method is called by the task worker.

        Arguments:

        - args: A list of arguments passed to the task through `create_task`
        - kwargs: A dictionary of keyword arguments passed to the task through `create_task`
        """
        self.output = example_monitor_logic(self.prefix_set)
        return self.output
