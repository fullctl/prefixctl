import ripestat

import prefix_meta.models as prefix_meta


class RipestatData(prefix_meta.Data):

    """
    Base class for Ripestat data, all specific RipeStat endpoints should inherit from this class
    to store their data
    """

    class Meta:
        proxy = True

    class Config(prefix_meta.Data.Config):
        period = 86400
        source_name = "ripestat"
        type = "ripestat"

    class HandleRef:
        tag = "ripestat_meta_data"

    @classmethod
    def get_prefix_queryset(cls, prefix):
        return (
            super()
            .get_prefix_queryset(prefix)
            .filter(type=cls.config("type"), source_name=cls.config("source_name"))
        )


class RipestatRequest(prefix_meta.Request):

    """
    Base class for Ripestat requests, all specific RipeStat endpoints should inherit from this class
    """

    class Meta:
        proxy = True

    class Config(prefix_meta.Request.Config):
        max_prefixlen_4 = 15
        max_prefixlen_6 = 64
        min_prefixlen_4 = 32
        min_predixlen_6 = 128

        cache_expiry = 86400

        ripestat_path = None

    @classmethod
    def target_to_url(cls, target):
        return f"{ripestat.api.API_URL}{cls.config('ripestat_path')}?resource={target}"

    @classmethod
    def target_to_type(cls, target):
        # TODO support for historic queries?
        return "live"

    @classmethod
    def send(cls, target):
        url = cls.target_to_url(target)
        print("seding request to", url, " - target - ", target)
        data = cls.ripestat_request(target)
        return cls.process(target, url, 200, data.data)
