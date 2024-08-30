# PrefixCtl Settings

- `USE_LOCAL_PERMISSIONS` - used for prefixctl standalone mode (Default is True), turning this off will require a fullctl aaactl instance to be running to handle permissions and authentication.

## PrefixCtl Meta - external source setup

### IP2Location

- `IP2LOCATION_API_KEY`
- `IP2LOCATION_PACKAGE` (default=WS25) - which package to query
- `IP2LOCATION_CACHE_EXPIRY` (default=30 days, value is in seconds) - how long is location cache valid

### Rdap

- `RDAP_BOOTSTRAP_URL` (default="https://rdap.org/")
- `RDAP_CACHE_EXPIRY` (default=86400) - rdap result cache in seconds

### IRRExplorer

- `IRREXPLORER_CACHE_EXPIRY` (default=86400) - IRRExplorer result cache in seconds

### RipeStat

If `prefix-meta-ripestat` is installed:

- `RIPESTAT_HISTORICALWHOIS_CACHE_EXPIRY` (default=86400) - RipeStat Historical Whois cache in seconds
- `RIPESTAT_BGPUPDATES_CACHE_EXPIRY` (default=21600) - RipeStat BGP Updates cache in seconds
- `RIPESTAT_ROUTINGSTATUS_CACHE_EXPIRY` (default=43200) - RipeStat Routing Status cache in seconds
- `RIPESTAT_RIRSTATSCOUNTRY_CACHE_EXPIRY` (default=86400) - RipeStat RIR Stats Country cache in seconds
- `RIPESTAT_RIR_CACHE_EXPIRY` (default=86400) - RipeStat RIR cache in seconds