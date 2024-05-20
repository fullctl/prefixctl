import prefix_meta.models as prefix_meta
import ipaddress

__all__ = [
    "IRRExplorerData",
    "IRRExplorerRequest",
]


class IRRExplorerData(prefix_meta.Data):
    class Meta:
        proxy = True

    class Config(prefix_meta.Data.Config):
        period = 86400
        source_name = "irrexplorer"
        type = "irrexplorer"

    class HandleRef:
        tag = "irrexplorer_meta_data"

    @property
    def get_matched_subnets(self):
        for row in self.route_objects():
            yield ipaddress.ip_network(row["prefix"])

    @classmethod
    def get_prefix_queryset(cls, prefix):
        return (
            super()
            .get_prefix_queryset(prefix)
            .filter(type=cls.config("type"), source_name=cls.config("source_name"))
        )

    def _expected_in_rir_warning(self, messages, rir_name):
        """
        Checks the `messages` list for the expected in RIR warning

        ```
            {
                "category": "warning",
                "text": "Expected route object in ARIN, but only found in other IRRs"
            },
        ```

        :param messages: list of messages
        :param rir_name: RIR name
        """

        for message in messages:
            if message["category"] == "warning" and message["text"].startswith(
                f"Expected route object in {rir_name}, but only found in other IRRs"
            ):
                return True

        return False

    def _augment_route_objects(self, route_objects: list, prefix: str, dataset: str):
        """
        Add prefix key and value to each route object dictonary

        :param route_objects: list of route objects
        :param prefix: prefix
        """

        for route_object in route_objects:
            route_object["prefix"] = prefix
            route_object["ip_address"] = prefix
            route_object["dataset"] = dataset

        return route_objects

    def route_objects(self):
        if not self.data:
            return []

        collected_routes = []

        for entry in self.data:
            for dataset, routes in entry.get("irrRoutes", {}).items():
                collected_routes += self._augment_route_objects(
                    routes, entry["prefix"], dataset
                )

        return collected_routes


class IRRExplorerRequest(prefix_meta.Request):
    class Meta:
        proxy = True

    class Config(prefix_meta.Request.Config):
        max_prefixlen_4 = 1
        max_prefixlen_6 = 1
        min_prefixlen_4 = 32
        min_predixlen_6 = 128

        cache_expiry = 86400

        irrexplorer_path = None

        meta_data_cls = IRRExplorerData
        source_name = "irrexplorer"

    @classmethod
    def target_to_url(cls, target):
        return f"https://irrexplorer.nlnog.net/api/prefixes/prefix/{target}"
