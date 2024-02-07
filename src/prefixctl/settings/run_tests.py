STATIC_URL = "/s/test"
PACKAGE_VERSION = "test"
SERVER_EMAIL = "default@localhost"
EMAIL_DEFAULT_FROM = "default@localhost"
EMAIL_NOREPLY = "noreply@localhost"
USE_LOCAL_PERMISSIONS = True
DEBUG = True
BILLING_INTEGRATION = False

SECURE_SSL_REDIRECT = False

PDBCTL_URL = "cache://pdbctl"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "stderr": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "": {"handlers": ["stderr"], "level": "DEBUG", "propagate": False},
    },
}
