# Creating a Custom Monitor for PrefixCtl

This document describes how to implement a custom monitor for PrefixCtl, a Django-based tool for monitoring network prefixes and ASNs.

## Overview

A monitor in PrefixCtl is a component that tracks the status of network elements based on user-defined criteria. To create a custom monitor, you need to understand the following key components:

1. **Monitor Model**: Defines the data model for your monitor, including its relationship to other PrefixCtl models like PrefixSet.
2. **Monitor Logic**: Contains the core logic that the monitor will execute.
3. **Monitor Task**: A scheduled task that triggers the monitor logic.
4. **REST Serializer**: Handles the serialization of monitor data for API interactions.
5. **Frontend Integration**: Includes the necessary JavaScript and HTML to add a user interface for the monitor in PrefixCtl's web application.


## Module structure explained

Below is the file structure of the example monitor implementation with links to source files:

- [apps.py](/examples/monitor_example/apps.py) - Defines the Django app configuration.
- [__init__.py](/examples/monitor_example/__init__.py) - An empty file that makes sure Python handles this directory as a package.
- migrations
  - [0001_initial.py](/examples/monitor_example/migrations/0001_initial.py) - Defines the initial database migrations for the monitor models.
  - [__init__.py](/examples/monitor_example/migrations/__init__.py) - An empty file that makes sure Python handles the migrations directory as a package.
- [models.py](/examples/monitor_example/models.py) - Contains the monitor model and task worker model definitions.
- [monitor.py](/examples/monitor_example/monitor.py) - Holds the custom monitor logic.
- [serializers.py](/examples/monitor_example/serializers.py) - Defines the REST API serializer for the monitor.
- static
  - monitor-example
    - [monitor.css](/examples/monitor_example/static/monitor-example/monitor.css) - CSS for the monitor frontend.
    - [monitor.js](/examples/monitor_example/static/monitor-example/monitor.js) - JavaScript for the monitor frontend.
- templates
  - prefixctl
    - v2
      - [base.html](/examples/monitor_example/templates/prefixctl/v2/base.html) - Base HTML template for the monitor UI.
      - tool
        - prefix_sets
          - [example-monitor-form.html](/examples/monitor_example/templates/prefixctl/v2/tool/prefix_sets/example-monitor-form.html) - Form template for creating and editing monitors.
          - [list.html](/examples/monitor_example/templates/prefixctl/v2/tool/prefix_sets/list.html) - Template to list prefix sets and their monitors.
          - [main.html](/examples/monitor_example/templates/prefixctl/v2/tool/prefix_sets/main.html) - Main template including the monitor form.


Make sure to run migrations and register all components properly for them to be recognized by PrefixCtl.

## Step 1: Define Your Monitor Model

Create a Django model that inherits from `Monitor` and register it with PrefixCtl. Define necessary fields and methods specific to your monitor's operation and configure its task scheduling. The following example includes class and method stubs you should implement:

```python
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

```

Define fields such as `instance`, `prefix_set`, and `task_schedule`. Implement methods like `schedule_interval` and `schedule_task_config` to configure the task scheduling.

Decorate the model class with `@grainy_model` to handle permissions, and use `@register_prefix_monitor` to make PrefixCtl aware of your new monitor model.

## Step 2: Implement Monitor Logic

Write the core logic for your monitor in a separate function or module. This code will be executed by the task worker during the monitoring process. The function should accept a `PrefixSet` instance and return the monitoring result. Here’s a basic stub for the monitor logic:

```python
from django_prefixctl.models import PrefixSet


def example_monitor_logic(self, prefix_set:PrefixSet) -> str:
    """
    This is the logic of your monitor.

    This is where you write the code that will be executed when the monitor
    runs.

    Arguments:

    - prefix_set: The PrefixSet model instance that the monitor is running for.
    """

    # do something interesting here...

    return "some result"
```

## Step 3: Set Up Monitor Task

Define a task model that inherits from `Task` and register it with `@register_task`. This model represents the task worker that will execute the monitor's logic. The task should define its unique properties and methods. Begin with a class definition, unique `HandleRef` tag, and implement the `run` method where you’ll call your monitor's logic function. Here's an example structure for the task worker model:

```python
from fullctl.django.models import Task, TaskSchedule, Instance
from fullctl.django.tasks import register as register_task

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

```

## Step 4: Create REST Serializer

Set up a serializer class for your monitor that extends from `MonitorCreationMixin` and `ModelSerializer`. This class is responsible for serialization and deserialization of monitor instances for the REST API, which allows for creation, retrieval, updating, and deletion of monitor data. You need to define the fields and methods relevant to your monitor. Include your monitor type choices and default. Here's an example serializer stub:

```python
from rest_framework import serializers
from fullctl.django.rest.serializers import ModelSerializer
from fullctl.django.rest.decorators import serializer_registry
from django_prefixctl.rest.serializers.monitor import register_prefix_monitor, MonitorCreationMixin

import monitor_example.models as models

Serializers, register = serializer_registry()

# register the monitor with prefixctl
@register_prefix_monitor
# add the monitor to the serializer registry, afterwards it
# will be available as Serializers.example_monitor, purely for convenience
@register
class ExampleMonitor(MonitorCreationMixin, ModelSerializer):

    """
    A bare minimum monitor REST serializer for our example monitor.
    """

    # set the monitor type choices and default
    # to the reference tag of the monitor model
    monitor_type = serializers.ChoiceField(
        choices=["example_monitor"], default="example_monitor"
    )
    instance = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = models.ExampleMonitor
        fields = [
            "instance",
            "prefix_set",
            "monitor_type",
        ]
```

Use the `@register` decorator to add it to the serializer registry.

## Step 5: Integrate with Frontend

Implement JavaScript logic to manage the behavior of your monitor within the web application's user interface. This should include modal interactions and API requests that fulfill operations such as creating, updating, or deleting monitors. Provide functions to open and interact with the monitor based on the provided prefix set and any existing monitor data. Use jQuery and the frameworks provided by PrefixCtl. Here is a skeleton example to get you started:

```javascript
(function ($, $tc, $ctl) {

    /**
     * Example monitor modal, used for creating and editing example monitors
     */
    $ctl.application.Prefixctl.ModalExampleMonitor = $tc.extend(
        "ModalExampleMonitor",
        {
            ModalExampleMonitor: function (prefix_set, monitor) {
                // set properties
                this.prefix_set = prefix_set;
                this.monitor = monitor;
                this.name = "example_monitor";

                // get a form instance for the monitor set up form
                this.init_form(monitor);

                // init example monitor as a prefix-set monitor
                this.init_prefix_set_monitor()
            }
        },

        // extend from base monitor class
        $ctl.application.Prefixctl.ModalMonitorBase
    )

    // register the monitor
    $ctl.application.Prefixctl.PrefixSetMonitors.register(
        {
            // same as django model handle-ref tag
            name: "example_monitor",
            // what namespaces does the viewing user need to be permissioned
            // to to view this monitor
            permissions: ["prefix_monitor"],
            // what is the display name of the monitor
            label: "Example Monitor",
            // function that opens the monitor modal for creation or editing
            modal: function (prefix_set, monitor) {
                return new $ctl.application.Prefixctl.ModalExampleMonitor(prefix_set, monitor);
            }
        }
    );

})(jQuery, twentyc.cls, fullctl);
```

Include the necessary HTML templates and JavaScript files in the `static` and `templates` directories of your application.

For a fully functional example, inspect the JavaScript and HTML templates provided within the `monitor_example` directory, as they contain practical implementations of a custom monitor UI. It's important to adapt these templates and script files to fit the specific logic and presentation of your monitor.

Remember to manage static files according to Django's best practices, using `collectstatic` to gather them in the appropriate static file directory defined in your settings.

## Conclusion

After following these steps, you should have a fully functional custom monitor integrated into PrefixCtl. For more detailed examples, refer to the monitor_example application included in this directory.
