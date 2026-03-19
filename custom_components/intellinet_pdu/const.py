DOMAIN = "intellinet_pdu"
PLATFORMS = ["sensor", "switch", "button"]

DEFAULT_SCAN_INTERVAL = 30
DEFAULT_NOMINAL_VOLTAGE = 230.0
DEFAULT_OPTIMISTIC_SWITCHING = False

CONF_SCAN_INTERVAL = "scan_interval"
CONF_NOMINAL_VOLTAGE = "nominal_voltage"
CONF_OPTIMISTIC_SWITCHING = "optimistic_switching"

SERVICE_RESTART_OUTLET = "restart_outlet"
SERVICE_RESTART_ALL_OFFLINE = "restart_all_offline"
ATTR_OUTLET = "outlet"
