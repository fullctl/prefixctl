from fullctl.django.rest.api_schema import BaseSchema

from django_prefixctl.rest.serializers.monitor import (
    ASN_MONITOR_CLASSES,
    MONITOR_CLASSES,
    PREFIX_MONITOR_CLASSES,
)


def monitor_response(cls_list=None):
    if not cls_list:
        cls_list = MONITOR_CLASSES

    return {
        "oneOf": [
            {"$ref": f"#/components/schemas/{cls.__name__}"}
            for cls in cls_list.values()
        ]
    }


def monitor_array_response(cls_list=None):
    if not cls_list:
        cls_list = MONITOR_CLASSES

    return {
        "type": "array",
        "items": {
            "oneOf": [
                {"$ref": f"#/components/schemas/{cls.__name__}"}
                for cls in cls_list.values()
            ]
        },
    }


class ASNSetSchema(BaseSchema):
    @property
    def field_monitors(self):
        return monitor_array_response(ASN_MONITOR_CLASSES)

    def get_request_body(self, path, method):
        schema = super().get_request_body(path, method)

        if method == "POST" and path == "/api/asn_set/{org_tag}/{id}/add_monitor/":
            schema["content"]["application/json"]["schema"] = monitor_response(
                ASN_MONITOR_CLASSES
            )

        return schema

    def get_responses(self, path, method):
        schema = super().get_responses(path, method)

        # list array of monitors (array of oneOf mixed typing)

        if method == "GET" and path == "/api/asn_set/{org_tag}/{id}/monitors/":
            schema["200"]["content"]["application/json"][
                "schema"
            ] = monitor_array_response(ASN_MONITOR_CLASSES)

        elif method == "POST" and path == "/api/asn_set/{org_tag}/{id}/add_monitor/":
            schema["201"]["content"]["application/json"][
                "schema"
            ] = monitor_array_response(ASN_MONITOR_CLASSES)

        return schema


class PrefixSetSchema(BaseSchema):
    @property
    def field_num_prefixes(self):
        return {"type": "integer", "description": "Number of prefixes in the set"}

    @property
    def field_num_monitors(self):
        return {"type": "integer", "description": "Number of monitors in the set"}

    @property
    def field_monitors(self):
        return monitor_array_response(PREFIX_MONITOR_CLASSES)

    def get_path_parameters(self, path, method):
        params = super().get_path_parameters(path, method)

        if method == "GET" and path == "/api/prefix_set/{org_tag}/search_prefix/":
            # add `q` param
            params.append(
                {
                    "name": "q",
                    "in": "query",
                    "required": True,
                    "schema": {"type": "string", "description": "Search query"},
                }
            )
        return params

    def get_request_body(self, path, method):
        schema = super().get_request_body(path, method)

        if method == "POST" and path == "/api/prefix_set/{org_tag}/{id}/add_monitor/":
            schema["content"]["application/json"]["schema"] = monitor_response(
                PREFIX_MONITOR_CLASSES
            )

        return schema

    def get_responses(self, path, method):
        schema = super().get_responses(path, method)

        # list array of monitors (array of oneOf mixed typing)

        if method == "GET" and path == "/api/prefix_set/{org_tag}/{id}/monitors/":
            schema["200"]["content"]["application/json"][
                "schema"
            ] = monitor_array_response(PREFIX_MONITOR_CLASSES)

        elif method == "POST" and path == "/api/prefix_set/{org_tag}/{id}/add_monitor/":
            schema["201"]["content"]["application/json"][
                "schema"
            ] = monitor_array_response(PREFIX_MONITOR_CLASSES)

        return schema


class MonitorSchema(BaseSchema):

    """
    Customized OpenAPI Schema for Monitor end point so we can show
    OneOf for each MONITOR_CLASSES as the payload
    """

    def get_components(self, path, method):
        components = super().get_components(path, method)
        if path == "/api/monitor/{org_tag}/":
            for cls in MONITOR_CLASSES.values():
                components.setdefault(
                    self.get_component_name(cls()), self.map_serializer(cls())
                )

        return components

    def get_request_body(self, path, method):
        schema = super().get_request_body(path, method)

        if method in "POST" and path == "/api/monitor/{org_tag}/":
            schema["content"]["application/json"]["schema"] = monitor_response()
        elif method in "PUT" and path == "/api/monitor/{org_tag}/{id}/":
            schema["content"]["application/json"]["schema"] = monitor_response()

        return schema

    def get_responses(self, path, method):
        schema = super().get_responses(path, method)

        # create response

        if method == "POST" and path == "/api/monitor/{org_tag}/":
            schema["201"]["content"]["application/json"][
                "schema"
            ] = monitor_array_response()

        # put response

        elif method == "PUT" and path == "/api/monitor/{org_tag}/{id}/":
            schema["200"]["content"]["application/json"][
                "schema"
            ] = monitor_array_response()

        # list array of monitors (array of oneOf mixed typing)

        elif method == "GET" and path == "/api/monitor/{org_tag}/":
            schema["200"]["content"]["application/json"][
                "schema"
            ] = monitor_array_response()

        return schema
