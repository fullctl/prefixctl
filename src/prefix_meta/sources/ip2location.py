import copy

from django.conf import settings

from prefix_meta.models import Request

__all__ = [
    "IP2Location",
]


class IP2Location(Request):
    class Meta:
        proxy = True

    class Config(Request.Config):
        api_url = "https://api.ip2location.com/v2/?ip={prefix}&key={api_key}&package={package}"
        source_name = "ip2location"
        min_prefixlen_4 = 24

    @classmethod
    def cache_exiry(cls):
        return settings.IP2LOCATION_CACHE_EXPIRY

    @classmethod
    def target_to_url(cls, target):
        target = target[0]
        api_key = settings.IP2LOCATION_API_KEY
        package = settings.IP2LOCATION_PACKAGE
        url = cls.config("api_url").format(
            prefix=target, api_key=api_key, package=package
        )
        return url

    def prepare_data(self, data):
        r = copy.deepcopy(data)
        del r["response"]
        del r["credits_consumed"]

        return r
