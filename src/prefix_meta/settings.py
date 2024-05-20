from django.conf import settings
from fullctl.django.settings import SettingsManager

settings_manager = SettingsManager(settings.__dict__)

settings_manager.set_option("IP2LOCATION_API_KEY", "")
settings_manager.set_option("IP2LOCATION_PACKAGE", "WS25")
settings_manager.set_option("IP2LOCATION_CACHE_EXPIRY", 86400 * 30)

# ARIN API key
settings_manager.set_option("ARIN_API_KEY", "")

# Disable the ARIN who was task from actually doing anything
settings_manager.set_option("ARIN_WHOWAS_DISABLED", False)

# rdap bootstrap server
settings_manager.set_option("RDAP_BOOTSTRAP_URL", "https://rdap.org/")

# Cache expiry

# 24 hours
settings_manager.set_option("RIPESTAT_HISTORICALWHOIS_CACHE_EXPIRY", 86400)

# 6 hours
settings_manager.set_option("RIPESTAT_BGPUPDATES_CACHE_EXPIRY", 21600)

# 12 hours
settings_manager.set_option("RIPESTAT_ROUTINGSTATUS_CACHE_EXPIRY", 43200)

# 24 hours
settings_manager.set_option("RIPESTAT_RIRSTATSCOUNTRY_CACHE_EXPIRY", 86400)

# 24 hours
settings_manager.set_option("RIPESTAT_RIR_CACHE_EXPIRY", 86400)

# 24 hours
settings_manager.set_option("IRREXPLORER_CACHE_EXPIRY", 86400)

# 24 hours
settings_manager.set_option("RDAP_CACHE_EXPIRY", 86400)

# Never
settings_manager.set_option("ARIN_WHOWAS_CACHE_EXPIRY", None, envvar_type=int)
