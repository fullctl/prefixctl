from django_prefixctl.models import PrefixSet


def example_monitor_logic(self, prefix_set: PrefixSet) -> str:
    """
    This is the logic of your monitor.

    This is where you write the code that will be executed when the monitor
    runs.

    Arguments:

    - prefix_set: The PrefixSet model instance that the monitor is running for.
    """

    # do something interesting here...

    return "some result"
