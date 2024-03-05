import json
import subprocess

from django_prefixctl.models import PrefixSet

__all__ = [
    "perform_irr_import",
]


def perform_irr_import(prefix_set: PrefixSet, as_set: str, sources=None):
    """
    Perform an IRR import for the given prefix set.

    Arguments:
    - prefix_set: the prefix set to import into
    - as_set: the AS set to import from
    - sources: the sources to use (optional)

    Example:

    >>> from django_prefixctl.models import PrefixSet
    >>> prefix_set = PrefixSet.objects.get(name="my-prefix-set")
    >>> perform_irr_import(prefix_set, "AS-EXAMPLE")
    """

    if not prefix_set.irr_import:
        return {"error": "irr import disabled"}

    command = ["bgpq4", "-j", as_set]
    if sources:
        command += ["-S", sources]

    print("COMMAND", command)
    result = subprocess.run(command, capture_output=True)

    if result.stderr:
        raise Exception(result.stderr.decode())

    output = result.stdout.decode()
    data = json.loads(output)

    old_prefixes = [prefix for prefix in prefix_set.prefix_set.all()]

    prefixes = {row["prefix"]: row["exact"] for row in data.get("NN")}

    result = {"added": [], "updated": [], "removed": []}

    for prefix, exact in list(prefixes.items()):
        if exact is True:
            mask_length_range = "exact"
        else:
            mask_length_range = ""
        added, updated = prefix_set.add_or_update_prefix(prefix, mask_length_range)
        if added:
            result["added"].append((prefix, mask_length_range))
        elif updated:
            result["updated"].append((prefix, mask_length_range))

    for prefix in old_prefixes:
        if prefix.prefix not in prefixes.keys():
            result["removed"].append((str(prefix.prefix), prefix.mask_length_range))
            prefix.delete()

    return result
