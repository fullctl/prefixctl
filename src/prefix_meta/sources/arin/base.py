from urllib.parse import urljoin

import xmltodict
from django.conf import settings
from fullctl.django.models.concrete.meta import Request

__all__ = [
    "ArinAPIRequest",
]


class ArinAPIRequest(Request):
    """
    ARIN API request
    """

    class Meta:
        proxy = True

    class Config(Request.Config):
        source_name = "arin-api"
        api_url = "https://reg.arin.net/rest/"
        api_url_test = "https://reg.ote.arin.net/rest/"
        api_path = "/"
        cache_expiry = 10
        xml_lists = ["messages", "attachments"]

    @classmethod
    def url_param(cls, target):
        api_key = getattr(settings, "ARIN_API_KEY", "")
        return f"?apikey={api_key}"

    @classmethod
    def target_parts(cls, target):
        return {"target": target}

    @classmethod
    def target_to_url(cls, target):
        url = urljoin(
            cls.config("api_url"),
            cls.config("api_path").format(**cls.target_parts(target)),
        )
        url_param = cls.url_param(target)
        return f"{url}{url_param}"

    @classmethod
    def target_to_type(cls, target):
        return "live"

    @classmethod
    def send(cls, target):
        """
        Send request to third party api to retrieve data for target.

        In some cases it may make sense to override this in an extended class
        to implemnt more complex fetching logic.

        In this impementation a GET request is sent off using the `requests`
        module and expecting a json response.
        """

        url = cls.target_to_url(target)
        _resp = cls.send_request(url)

        return cls.process(
            target,
            url,
            _resp.status_code,
            lambda: xmltodict.parse(_resp.content, force_list=cls.config("xml_lists")),
            content=_resp.content,
        )
