"""Provides the RPKI Validation Status endpoint."""


class RPKIValidationStatus:
    """
    This data call returns the RPKI validity state for a combination of prefix and Autonomous System. This combination will be used to perform the lookup against the RPKI validator Routinator (opens new window), and then return its RPKI validity state

    Reference: `<https://stat.ripe.net/docs/02.data-api/rpki-validation.html>`_

    .. code-block:: python

        import ripestat

        ripe = ripestat.RIPEstat()
        rir = ripe.rpki_validation_status("193.0.0.0/16")

    """

    PATH = "/rpki-validation"
    VERSION = "0.1"

    def __init__(
        self,
        RIPEstat,
        resource,
        prefix,
    ):
        """
        Initialize and request the RIR(s).

        :param resource: The ASN used to perform the RPKI validity state lookup.
        :param prefix: The prefix to perform the RPKI validity state lookup. Note the prefix's length is also taken from this field.

        .. code-block:: python
            rir = ripe.rpki_validation_status("AS1905", "193.0.0.0/16")

        """
        params = {
            "preferred_version": RPKIValidationStatus.VERSION,
            "resource": str(resource),
            "prefix": str(prefix),
        }

        self._api = RIPEstat._get(RPKIValidationStatus.PATH, params)

    def __repr__(self):
        """Return the resource ASN and returned data as representation of the object."""
        return f"Resource {str(self.resource)} => {str(self.data)}"

    def __str__(self):
        """Return the resource ASN representation of the object."""
        return f"{self.resource} - {self.prefix}"

    @property
    def data(self):
        """Holds all the output data."""
        return self._api.data

    @property
    def resource(self):
        """
        Defines the resource to be queried. The result contains resources that are more
        or less specific to the queried resource.
        """
        return self._api.data["resource"]

    @property
    def prefix(self):
        """
        Defines the prefix to be queried.
        """
        return self._api.data["prefix"]

    @property
    def rpki_validation_status(self):
        return self._api.data["status"]
