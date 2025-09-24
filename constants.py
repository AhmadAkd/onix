from enum import Enum

PROXY_HOST = "127.0.0.1"
PROXY_PORT = 1081
PROXY_SERVER_ADDRESS = f"{PROXY_HOST}:{PROXY_PORT}"
PROXY_BYPASS = "localhost;127.0.0.1;[::1];<local>"
CONFIG_FILENAME = "temp_config.json"
SETTINGS_FILE = "settings.json"
ICON_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAIaSURBVDhPlZJBSFRRFIb/Z+68WXe3pk0WSiSoCERiBAnDxJr05aJCNy20aFE7V0FERBAVoZsgRIpGkW40bYp2C0kRIkIhK4Udd2fmv7szM6/fj/vAOfdc7j3nO+f/3wlxHD8Mw3DMNM2f9kznPO01rfX2ZVm2r4/3gXw+PzExMXl5eb3e3t7efr+/+7s/aABSSsuyPM/zPF+v1/uP20Kh0HEcxzEajWaz2WAw6Pf7s9msUCg0Go1KpaLRaNpsNp1Oh8/n0+l0NBqNZrMhCAIAkGU5Ho/DNE1ZlpNzc3Nz8wjg8/lQVRWJRIJGo5FIRCQSiWw2G4vFwmaz2Ww2nU4HgwGfz4dpmgwGA6BBEARBEMhms4FA4PDw8Pj4+Ozs7NLS0tLSUsdxPA4A8Dw/Nze3s7MTQRCz2Wxvb+/s7Ow0Gg0ODg4PDw+Hh4eHh4ff399/f3+DwSAQCAKBwGaz4XnebrebzeYnJyfz8/Ozs7OjoyOfz+fn51dWVhYXF/f392fSNOu6rutyudxut1sYhsPhsN1u5/P5er0Oh8PhcDh2u51SqVRKpaLRaNDr9Xq9Hk3Ttm3bto/HcTAYDAQCkUgkEokEAJzP59PplM/n8/l8Pp9vNpsdHx9/e3v76Ojo+Ph4c3NzZWVldXW1hYWFubk5m80Gn88HAMdx3G53LBaLx+NBkqSmaagqiiJ4nhcKhVwuh2VZp9MpFouZTqeua7quCxqN1mq1Ojs7MzMzk5OTU1NTQ0NDSUlJdXV1RUVFXl5elUolSRLbtiAIoiiKoiiKosB/FP4D3WQd507QyLAAAAAASUVORK5CYII="

APP_FONT = ("Segoe UI", 12)


class LogLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    DEBUG = "debug"


# --- UI Text Constants ---
NO_GROUPS = "No Groups"
# Appearance
APPEARANCE_MODE_LIGHT = "Light"
APPEARANCE_MODE_DARK = "Dark"
APPEARANCE_MODE_SYSTEM = "System"
THEME_GREEN = "green"
THEME_BLUE = "blue"
THEME_DARK_BLUE = "dark-blue"
# Tabs
TAB_CONNECTION = "Connection"
TAB_SETTINGS = "Settings"
# Labels
LBL_SERVERS = "Servers"
LBL_SUB_LINK = "Subscription Link:"
LBL_GROUP_NAME = "Group Name (Optional):"
LBL_ADD_SERVER = "Add Single Server:"
LBL_STATUS = "Status:"
LBL_IP_ADDRESS = "IP Address:"
LBL_LATENCY = "Latency:"
LBL_APPEARANCE_SETTINGS = "Appearance Settings"
LBL_NETWORK_SETTINGS = "Network Settings"
LBL_DNS_SERVERS = "DNS Servers:"
LBL_BYPASS_DOMAINS = "Bypass Domains:"
LBL_BYPASS_IPS = "Bypass IPs:"
# Placeholders
PLACEHOLDER_SUB_LINK = "Paste your subscription link here"
PLACEHOLDER_GROUP_NAME = "e.g., My Servers"
PLACEHOLDER_MANUAL_ADD = "Paste vmess://, vless://, etc."
# Buttons
BTN_UPDATE = "Update"
BTN_PING_GROUP = "Ping Group"
BTN_URL_TEST_GROUP = "URL Test Group"
BTN_SORT_BY_PING = "Sort by Ping"
BTN_URL_TEST_ACTIVE = "URL Test (Active)"
BTN_ADD_SERVER = "Add Server"
BTN_START = "Start"
BTN_STOP = "Stop"
# Status
STATUS_NO_SERVER_SELECTED = "No Server Selected"
STATUS_SELECTED = "Selected: {}"
STATUS_CONNECTING = "Connecting..."
STATUS_CONNECTED = "Running: {}"
STATUS_CONN_SUCCESS = "Connection successful! Latency: {} ms."
STATUS_CONN_FAILED = "Connection Failed"
STATUS_DISCONNECTED = "Disconnected"
STATUS_ERROR_CONN_TEST_FAILED = "Error: Connection test failed. Check server config."
# Other
MSG_TCP_PING_ALL = "Starting TCP ping for all visible servers..."
MSG_URL_TEST_ALL = (
    "Starting URL test. This process is SLOW and may take several minutes."
)
MSG_URL_TEST_SUCCESS = "URL Test successful! Response time: {} ms"
MSG_URL_TEST_FAILED = "URL Test failed: Could not reach test URL via proxy."
MSG_SORT_SUCCESS = "Servers sorted by ping (fastest first)."
# Tray
TRAY_SHOW = "Show"
TRAY_QUIT = "Quit"
TRAY_TITLE = "Sing-box Client"
# Default values
DEFAULT_DNS_SERVERS = "1.1.1.1,8.8.8.8"
DEFAULT_BYPASS_DOMAINS = "*.ir,*.local"
DEFAULT_BYPASS_IPS = "192.168.0.0/16,127.0.0.1"
# N/A
NA = "N/A"

# --- Timeouts ---
TCP_PING_TIMEOUT = 2
URL_TEST_TIMEOUT = 5
GET_EXTERNAL_IP_TIMEOUT = 5
WAIT_FOR_PROXY_TIMEOUT = 5
WAIT_FOR_PROXY_INTERVAL = 0.1

# --- URLs ---
URL_TEST_DEFAULT_URL = "http://www.gstatic.com/generate_204"
GET_EXTERNAL_IP_URL = "https://api.ipify.org"
GEOIP_RULE_SET_URL = (
    "https://raw.githubusercontent.com/soffchen/sing-geoip/rule-set/geoip-{code}.srs"
)
GEOSITE_RULE_SET_URL = (
    "https://raw.githubusercontent.com/soffchen/sing-geosite/rule-set/{code}.srs"
)
IRAN_GEOIP_RULE_SET_URL = "https://raw.githubusercontent.com/Chocolate4U/Iran-sing-box-rules/rule-set/geoip-ir.srs"
IRAN_GEOSITE_RULE_SET_URL = "https://raw.githubusercontent.com/Chocolate4U/Iran-sing-box-rules/rule-set/geosite-ir.srs"

# --- Singbox Manager Constants ---
CONNECTION_STOP_DELAY = 0.5
CONNECTION_CHECK_DELAY = 2000
