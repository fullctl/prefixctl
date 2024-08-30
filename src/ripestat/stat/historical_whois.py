"""Provides the Historical Whois endpoint."""
from collections import namedtuple
from datetime import datetime

from ripestat.validators import Validators


class HistoricalWhois:
    """
    This data call provides information on objects that are stored in the RIPE DB. The result is aligned to a specific object, which
    is identified by an object type and an object key, which is similar to the Whois data call.

    Reference: `<https://stat.ripe.net/docs/02.data-api/historical-whois.html>`_
    =================================== =============================================================================================
    Property                            Description
    =================================== =============================================================================================
    ``num_versions``                    Number of total version for the selected object.
    ``resource, type and version``      Shows which resource, object type and version is returned.
    ``database``                        Defines from which RIR database the data is fetched. Currently only the RIPE DB is supported.
    ``suggestions``                     In cases the lookup does not match exactly, suggestions are provided.
    ``versions``                        Contains a list of historical changes represented as version.
    ``terms_and_conditions``            Terms and conditions of the RIPE DB and for using this data.
    ``objects``                         Details for the object in the selected version.
    ``referencing``                     All objects that contains references to the object in focus.
    ``referenced_by``                   All objects that are referenced by the object in focus.
    =================================== =============================================================================================
    .. code-block:: python
        import ripestat
        ripe = ripestat.RIPEstat()
        history = ripe.historical_whois('193.0.20.0/24')
    """

    PATH = "/historical-whois"
    VERSION = "1.0"

    def __init__(
        self,
        RIPEstat,
        resource,
        version=None,
    ):
        """
        Initialize and request the Whois data call.

        :param resource: Defines the resource that the query. (This is a prefix (v4/v6),
            an AS number, or a string of the format "object-type:object-key" for looking
            up generic database objects.
        :param version: Defines the version to load details for. (numerical value (e.g.
            version=4) or as time-based value)

        .. code-block:: python
            history = ripe.historical_whois('193.0.18.0-193.0.21.255')
            history = ripe.historical_whois('3333')
            history = ripe.historical_whois('person:BRD-RIPE')
        """

        params = {
            "preferred_version": HistoricalWhois.VERSION,
            "resource": str(resource),
        }

        if version:
            if Validators._validate_datetime(version):
                if not isinstance(version, datetime):
                    params["version"] = version
                else:
                    params["version"] = version.isoformat()
            elif isinstance(version, int):
                params["version"] = str(version)
            else:
                raise ValueError("version expected to be int or datetime")

        self._api = RIPEstat._get(HistoricalWhois.PATH, params)

    def __repr__(self):
        """Return the resource (prefix (v4/v6), an AS number, or a string of the format "object-type:object-key") and data as representation of the object."""
        return f"Resource {str(self.resource)} => {str(self.data)}"

    def __str__(self):
        """Return the resource (prefix (v4/v6), an AS number, or a string of the format "object-type:object-key") as string representation of the object."""
        return str(self.resource)

    # TODO: add __getitem__, __iter__
    def __len__(self):
        """
        Get the number of objects in historical whois.

        .. code-block:: python

            import ripestat

            ripe = ripestat.RIPEstat()
            histories = ripe.historical_whois('3333')

            print(len(histories))
        """
        return len(self.versions)

    @property
    def data(self):
        """Holds all the output data."""
        return self._api.data

    @property
    def num_versions(self):
        """Number of total version for the selected object."""
        return self._api.data["num_versions"]

    @property
    def resource(self):
        """Shows which resource is returned."""
        return self._api.data["resource"]

    @property
    def type(self):
        """Shows which object type is returned."""
        try:
            return self._api.data["type"]
        except KeyError:
            return None

    @property
    def version(self):
        """Shows which version is returned."""
        return self._api.data["version"]

    @property
    def database(self):
        """Defines from which RIR database the data is fetched. Currently only the RIPE DB is supported."""
        return self._api.data["database"]

    @property
    def suggestions(self):
        """In cases the lookup does not match exactly, suggestions are provided."""
        suggestions = []
        Suggestions = namedtuple(
            "Suggestions",
            ["type", "key", "attributes", "from_time", "version", "latest", "deleted"],
        )
        Attributes = namedtuple("Attributes", ["attribute", "value"])

        for suggestion in self._api.data["suggestions"]:
            type = suggestion["type"]
            key = suggestion["key"]
            attributes = []
            try:
                from_time = datetime.fromisoformat(suggestion["from_time"])
            except TypeError:
                from_time = suggestion["from_time"]
            version = suggestion["version"]
            latest = suggestion["latest"]
            deleted = suggestion["deleted"]

            for attr in suggestion["attributes"]:
                attribute = attr["attribute"]
                value = attr["value"]

                attributes.append(Attributes(attribute=attribute, value=value))

            tuple_data = {
                "type": type,
                "key": key,
                "attributes": attributes,
                "from_time": from_time,
                "version": version,
                "latest": latest,
                "deleted": deleted,
            }
            suggestions.append(Suggestions(**tuple_data))

        return suggestions

    @property
    def versions(self):
        """A list of of historical changes represented as version."""
        versions = []
        Versions = namedtuple(
            "Versions",
            ["from_time", "to_time", "version"],
        )

        for data in self._api.data["versions"]:
            from_time = datetime.fromisoformat(data["from_time"])
            to_time = datetime.fromisoformat(data["to_time"])
            version = data["version"]

            tuple_data = {
                "from_time": from_time,
                "to_time": to_time,
                "version": version,
            }
            versions.append(Versions(**tuple_data))

        return versions

    @property
    def terms_and_conditions(self):
        """Terms and conditions of the RIPE DB and for using this data."""
        return self._api.data["terms_and_conditions"]

    @property
    def objects(self):
        """A list of details for the object in the selected version."""
        objects = []
        Objects = namedtuple(
            "Objects",
            ["type", "key", "attributes", "from_time", "version", "latest", "deleted"],
        )
        Attributes = namedtuple("Attributes", ["attribute", "value"])

        for object in self._api.data["objects"]:
            type = object["type"]
            key = object["key"]
            attributes = []
            from_time = datetime.fromisoformat(object["from_time"])
            version = object["version"]
            latest = object["latest"]
            deleted = object["deleted"]

            for attr in object["attributes"]:
                attribute = attr["attribute"]
                value = attr["value"]

                attributes.append(Attributes(attribute=attribute, value=value))

            tuple_data = {
                "type": type,
                "key": key,
                "attributes": attributes,
                "from_time": from_time,
                "version": version,
                "latest": latest,
                "deleted": deleted,
            }
            objects.append(Objects(**tuple_data))

        return objects

    @property
    def referencing(self):
        """A list of all objects that contains references to the object in focus."""
        referencing = []
        Referencing = namedtuple(
            "Referencing",
            ["type", "key", "from_time", "version", "latest"],
        )

        for data in self._api.data["referencing"]:
            result = []
            for value in range(len(data)):
                type = data[value]["type"]
                key = data[value]["key"]
                from_time = datetime.fromisoformat(data[value]["from_time"])
                version = data[value]["version"]
                latest = data[value]["latest"]

                tuple_data = {
                    "type": type,
                    "key": key,
                    "from_time": from_time,
                    "version": version,
                    "latest": latest,
                }
                result.append(Referencing(**tuple_data))
            referencing.append(result)

        return referencing

    @property
    def referenced_by(self):
        """All objects that are referenced by the object in focus."""
        return self._api.data["referenced_by"]
