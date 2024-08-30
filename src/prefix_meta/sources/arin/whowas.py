"""
Implements querying, downloading, unpacking and normalizing
of ARIN whowas reports.
"""
import datetime
import io
import logging
import tempfile
import time
import zipfile

import fullctl.django.tasks
import structlog
from django.conf import settings
from fullctl.django.models.concrete import Task
from fullctl.django.tasks.qualifiers import ConcurrencyLimit
from prefix_meta_arin.parser import Parser

from prefix_meta.models import Data, Request

from .base import ArinAPIRequest

log = structlog.get_logger("django")

__all__ = [
    "ArinWhoWasData",
    "ArinWhoWasRequest",
    "ArinWhoWasTask",
    "ArinAPIRequestWhoWas",
    "ArinAPIRequestTicketSummary",
    "ArinAPIRequestTicketDetails",
    "ArinAPIRequestAttachment",
]

log = logging.getLogger(__name__)


class ArinApiError(IOError):
    """
    Raised on arin api errors
    """

    pass


class ArinApiThrottled(IOError):
    """
    Raised when arin api respons with a TOO MANY REQUESTS
    response
    """

    pass


@fullctl.django.tasks.register
class ArinWhoWasTask(Task):
    """
    ARIN WhoWas task
    """

    class Meta:
        proxy = True

    class HandleRef:
        tag = "arin_whowas_task"

    class TaskMeta:
        # limit to 1 WhoWas task per ip
        limit = 1

        qualifiers = [
            # limit how many WhoWas report tasks can be
            # worked on at the same time, since ARIN seems to
            # picky about how many requests we make and there
            # can be prefix-sets with 100+ blocks queued at once
            # this number should be really low as to not
            ConcurrencyLimit(2),
        ]

    @classmethod
    def create_task(cls, ip):
        # check if we already have WhoWas data for that ip
        # no need to request it again, if so
        return super().create_task(f"{ip}")

    @property
    def ip(self):
        return self.param["args"][0]

    @property
    def generate_limit_id(self):
        return self.ip

    @property
    def name(self):
        return "ARIN WhoWas"

    def run(self, ip, *args, **kwargs):
        """
        Run the task
        """

        if getattr(settings, "ARIN_WHOWAS_DISABLED", False):
            msg = "WHOWAS TASKS DISABLED - {ip} - NOT ACTUALLY DOING ANYTHING - UNSET ARIN_WHOWAS_DISABLED TO ACTUALLY RUN"
            log.info(msg)
            return msg

        ArinWhoWasRequest.request(ip)


class ArinWhoWasData(Data):
    """
    ARIN WhoWas data
    """

    class Meta:
        proxy = True

    class Config(Data.Config):
        source_name = "arin-whowas"
        type = "whowas"
        period = 86400

    class HandleRef:
        tag = "arin_whowas_data"

    @classmethod
    def get_prefix_queryset(cls, prefix):
        return (
            super()
            .get_prefix_queryset(prefix)
            .filter(type=cls.config("type"), source_name=cls.config("source_name"))
        )

    @property
    def net_entries(self):
        r = {}

        for k, v in self.data.items():
            if "net_name" in v[0]:
                r[k] = v

        return r

    @property
    def org_entries(self):
        r = {}

        for k, v in self.data.items():
            if "org_name" in v[0]:
                r[k] = v

        return r

    def entity_data(self, handle, name):
        if handle not in self.data:
            return None

        for entity in self.data[handle]:
            if name in entity:
                return entity[name]

        return None

    def determine_rir(self, action):
        # get RIR by scanning for "POCs" in the action data
        # and then attempt to extract the RIR from the POC handle
        # TODO: is there a better way?

        for k, v in action.items():
            if "_pocs" in k and v:
                return v.split("-")[-1]

        return None

    def registration_history(self, net_handle, rir_fallback=None):
        if net_handle.lower() not in self.data:
            return []

        registrations = []
        org_handle = None

        for action in self.data[net_handle.lower()]:
            if action["organization"] != org_handle:
                registrations.append(
                    {
                        "date": datetime.datetime.strptime(
                            action["action_date"], "%m-%d-%Y"
                        ),
                        "org_name": self.entity_data(
                            action["organization"].lower(), "org_name"
                        ),
                        "org_handle": action["organization"],
                        "rir": self.determine_rir(action) or rir_fallback,
                    }
                )
                org_handle = action["organization"]

        # return list sorted by datetime formatted from "Action Date"
        # MM-DD-YYYY timestamp

        return sorted(registrations, key=lambda x: x["date"])


class ArinWhoWasRequest(Request):
    class Meta:
        proxy = True

    class Config(Request.Config):
        max_prefixlen_4 = 1
        max_prefixlen_6 = 1
        min_prefixlen_4 = 32
        min_predixlen_6 = 128

        arin_whowas_path = None
        source_name = "arin-whowas"
        meta_data_cls = ArinWhoWasData

    @classmethod
    def cache_expiry(cls, target):
        """
        cache forever
        """
        # check if cache expiry is set in settings
        try:
            return cls.cache_expiry_from_settings(target)
        except AttributeError:
            # otherwise cache forever
            return None

    @classmethod
    def authenticate(cls, session):
        """
        Authenticates to ARIN WhoWas
        """
        pass

    @classmethod
    def target_to_url(cls, target):
        return f"RegWS-API:{target}"

    @classmethod
    def send_request(cls, target):
        """
        Sends a request to ARIN WhoWas
        """

        ip = target[0]

        # Open Whowas ticket

        # This request might get throttled so we need
        # to set up for potential retries

        max_tries = 30
        tries = 0
        ticket_no = None

        while tries < max_tries:
            tries += 1
            try:
                ArinAPIRequestWhoWas.request(ip)
                ticket_no = ArinAPIRequestWhoWas.ticket_number(ip)
                break
            except ArinApiThrottled:
                log.debug("arin_whowas", throttled="waiting 15 seconds")
                # TODO: fullctl-core should implment specific shorter
                # caching times for throttled requests (status=429)
                #
                # for now, just kill the request cache
                # and wait 15 seconds

                cache = ArinAPIRequestWhoWas.get_cache(ip)
                if cache:
                    cache.delete()

                time.sleep(15)

        if ticket_no is None:
            raise OSError(
                f"Unable to open ticket for ARIN WhoWas request (tried {tries} times)"
            )

        log.debug("arin_whowas", ticket_no=ticket_no)

        log.debug("arin_whowas", status="Waiting for ticket to be processed")

        # Wait for ticket to be processed

        ArinAPIRequestTicketSummary.request(ticket_no)

        ticket_status = ArinAPIRequestTicketSummary.ticket_status(ticket_no)

        # max attempts at checking ticket status
        # status will be checked every 15 seconds for N retries
        retries = 100
        retry = 0

        while ticket_status != "CLOSED" and retry < retries:
            time.sleep(15)
            ArinAPIRequestTicketSummary.request(ticket_no)
            ticket_status = ArinAPIRequestTicketSummary.ticket_status(ticket_no)
            retry += 1

        if ticket_status != "CLOSED":
            # ticket not processed in time
            return

        log.debug("arin_whowas", ticket_status=ticket_status)

        # request ticket details and retrieve attachment ids

        ArinAPIRequestTicketDetails.request(ticket_no)

        attachment = ArinAPIRequestTicketDetails.attachment(ticket_no)

        log.debug("arin_whowas", attachment=attachment)
        attachment_target = (
            f"{ticket_no}:{attachment['message_id']}:{attachment['attachment_id']}"
        )
        results = ArinAPIRequestAttachment.request(attachment_target)

        # unpack the compressed data and extract the files
        # to a temporary directory and then use the prefix-meta-arin Parser
        # to parse the data and return a dict

        attachment = results[attachment_target].response.attachments.first()

        with tempfile.TemporaryDirectory() as tmpdirname:
            file_data = bytes(attachment.file_data)
            with zipfile.ZipFile(io.BytesIO(file_data), "r") as zip_file:
                zip_file.extractall(tmpdirname)

            data = Parser().parse(tmpdirname)

            return data

    @classmethod
    def send(cls, target):
        url = cls.target_to_url(target)

        log.debug("arin_whowas", requesting=url, target=target)
        _resp = cls.send_request(target)

        return cls.process(target, url, 200, lambda: _resp)

    def prepare_data(self, data):
        """
        Recursively ensures all dict keys in data are lowercase
        and use underscores instead of spaces
        """

        if isinstance(data, dict):
            return {
                k.lower().replace(" ", "_").replace("/", "_"): self.prepare_data(v)
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [self.prepare_data(v) for v in data]
        else:
            return data


class ArinAPIRequestWhoWas(ArinAPIRequest):

    """
    Starts the process of requesting data from ARIN WhoWas
    """

    class Meta:
        proxy = True

    class HandleRef:
        tag = "arin_whowas_request"

    class Config(ArinAPIRequest.Config):
        source_name = "arin-api-whowas"
        api_path = "report/whoWas/net/{target}"

    @classmethod
    def ticket_number(cls, ip):
        """
        Returns the arin ticket number for a WhoWas report request

        Will return `None` if no request has been made for the given IP
        """

        entry = (
            cls.objects.filter(identifier=ip, source=cls.config("source_name"))
            .order_by("-updated")
            .first()
        )

        if not entry:
            return

        if entry.response.data.get("error"):
            if entry.response.data["error"]["code"] == "E_TOO_MANY_REQUESTS":
                raise ArinApiThrottled("Too many requests to ARIN API")
            else:
                raise ArinApiError(entry.response.data["error"]["message"])

        return entry.response.data["ticket"]["ticketNo"]

    @classmethod
    def cache_expiry(cls, target):
        """
        We only want to request reports for an IP once and then never
        again

        TODO: maybe a year is more reasonable? Since the data will eventually
        get new entries?

        TODO: should come from settings
        """
        return None


class ArinAPIRequestTicketSummary(ArinAPIRequest):

    """
    Requests the status of an ARIN ticket. This can be used to
    check if a WhoWas report has been generated for a given IP
    and is ready to be downloaded.
    """

    class Meta:
        proxy = True

    class HandleRef:
        tag = "arin_api_ticket_summary"

    class Config(ArinAPIRequest.Config):
        source_name = "arin-api-ticket-summary"
        api_path = "ticket/{target}/summary"
        cache_expiry = 10

    @classmethod
    def ticket_status(cls, ticket_number):
        """
        Returns the status of the ticket with the specified number
        """

        entry = (
            cls.objects.filter(
                identifier=ticket_number, source=cls.config("source_name")
            )
            .order_by("-updated")
            .first()
        )

        if not entry:
            return

        return entry.response.data["ticket"]["webTicketStatus"]

    @classmethod
    def cache_expiry(cls, target):
        """
        Cache expiry will be dynamic
        """

        if cls.ticket_status(target) == "CLOSED":
            # ticket already closed, cache forever
            return None

        return cls.config("cache_expiry")


class ArinAPIRequestTicketDetails(ArinAPIRequest):

    """
    Requests the details of an ARIN ticket. This can be used to
    aidentify the attachments for the WhoWas report for a given IP from the ticket number
    """

    class Meta:
        proxy = True

    class HandleRef:
        tag = "arin_api_ticket_details"

    class Config(ArinAPIRequest.Config):
        source_name = "arin-api-ticket-details"
        api_path = "ticket/{target}"

    @classmethod
    def url_param(cls, target):
        param = super().url_param(target)
        return f"{param}&msgRefs=true"

    @classmethod
    def attachment(cls, ticket_number):
        """
        will return dict(message_id, attachment_id, attachment_name)

        will return None if there is no attachment
        """

        entry = (
            cls.objects.filter(
                identifier=ticket_number, source=cls.config("source_name")
            )
            .order_by("-updated")
            .first()
        )

        if not entry:
            return

        message_id = entry.response.data["ticket"]["messageReferences"][
            "messageReference"
        ]["messageId"]
        attachment = entry.response.data["ticket"]["messageReferences"][
            "messageReference"
        ]["attachmentReferences"]["attachmentReference"]

        return {
            "message_id": message_id,
            "attachment_id": attachment["attachmentId"],
            "attachment_name": attachment["attachmentFilename"],
        }

    @classmethod
    def cache_expiry(cls, target):
        return None


class ArinAPIRequestAttachment(ArinAPIRequest):

    """
    Requests the attachment of an ARIN ticket. This can be used to
    download the WhoWas report for a given IP from the ticket number
    """

    class Meta:
        proxy = True

    class HandleRef:
        tag = "arin_whowas_attachment"

    class Config(ArinAPIRequest.Config):
        source_name = "arin-api-attachment"
        api_path = (
            "ticket/{ticket_number}/message/{message_id}/attachment/{attachment_id}"
        )

    @classmethod
    def cache_expiry(cls, target):
        """
        Only ever download report once, cache forever
        """
        return None

    @classmethod
    def target_parts(cls, target):
        ticket_number, message_id, attachment_id = target.split(":")

        return {
            "target": target,
            "message_id": message_id,
            "attachment_id": attachment_id,
            "ticket_number": ticket_number,
        }

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

        log.debug("arin_whowas", requesting=url, target=target)

        _resp = cls.send_request(url)

        request = cls.process(target, url, _resp.status_code, {})
        request.response.add_attachment(
            "report.zip", _resp.content, _resp.headers.get("Content-Type", "text/text")
        )

        return request
