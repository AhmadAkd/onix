from enum import Enum
from PySide6.QtCore import QCoreApplication

PROXY_HOST = "127.0.0.1"
PROXY_PORT = 2082
STATS_API_PORT = 9090
PROXY_SERVER_ADDRESS = f"{PROXY_HOST}:{PROXY_PORT}"
PROXY_BYPASS = "localhost;127.0.0.1;[::1];<local>"
CONFIG_FILENAME = "temp_config.json"
SETTINGS_FILE = "settings.json"
XRAY_LOG_FILE = "xray_core.log"
SINGBOX_LOG_FILE = "singbox_core.log"
APP_VERSION = "1.0.0"

# --- Settings that require a restart to apply ---
RESTART_REQUIRED_SETTINGS = {"appearance_mode", "theme_color"}

APP_FONT = ("Segoe UI", 12)


class LogLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    DEBUG = "debug"


# --- UI Text Constants ---
def tr(text):
    """Helper function for translating constants."""
    return QCoreApplication.translate("Constants", text)


NO_GROUPS = tr("No Groups")
# Appearance
APPEARANCE_MODE_LIGHT = tr("Light")
APPEARANCE_MODE_DARK = tr("Dark")
APPEARANCE_MODE_SYSTEM = tr("System")
THEME_GREEN = "green"
THEME_BLUE = "blue"
THEME_PURPLE = "purple"
THEME_ROSE = "rose"
# Tabs
TAB_CONNECTION = tr("Connection")
TAB_SETTINGS = tr("Settings")
TAB_ROUTING = tr("Routing")
# Labels
LBL_STATUS = tr("Status:")
LBL_IP_ADDRESS = tr("IP Address:")
LBL_LATENCY = tr("Latency:")
LBL_APPEARANCE_SETTINGS = tr("Appearance Settings")
LBL_THEME_COLOR = tr("Theme Color:")
LBL_NETWORK_SETTINGS = tr("Network Settings")
LBL_DNS_SERVERS = tr("DNS Servers:")
LBL_BYPASS_DOMAINS = tr("Bypass Domains:")
LBL_BYPASS_IPS = tr("Bypass IPs:")
LBL_CONNECTION_MODE = tr("Connection Mode:")
LBL_ENABLE_TUN = tr("Enable TUN Mode (System-wide Proxy)")
LBL_PROFILE_MANAGEMENT = tr("Profile Management")
LBL_UPDATES = tr("Updates")
MODE_RULE_BASED = tr("Rule-Based")
MODE_GLOBAL = tr("Global")
# Placeholders
PLACEHOLDER_SUB_LINK = tr("Paste your subscription link here")
PLACEHOLDER_GROUP_NAME = tr("e.g., My Servers")
PLACEHOLDER_MANUAL_ADD = tr("Paste vmess://, vless://, etc.")
# Buttons
BTN_START = tr("Start")
BTN_STOP = tr("Disconnect")  # Changed from Stop for clarity
BTN_MANAGE_SUBSCRIPTIONS = tr("Subscriptions")
BTN_UPDATE_ALL_SUBSCRIPTIONS = tr("Update All Subscriptions")
BTN_CANCEL = tr("Cancel")
BTN_SCAN_QR = tr("Scan QR from Screen")
BTN_IMPORT_PROFILE = tr("Import Profile")
BTN_EXPORT_PROFILE = tr("Export Profile")
BTN_CHECK_FOR_UPDATES = tr("Check for Core Updates")
BTN_ABOUT = tr("About Onix")
# Status
STATUS_NO_SERVER_SELECTED = tr("No Server Selected")
STATUS_SELECTED = tr("Selected: {}")
STATUS_CONNECTING = tr("Connecting...")
STATUS_CONNECTED = tr("Connected")
STATUS_CONN_SUCCESS = tr("Connection successful! Latency: {} ms.")
STATUS_CONN_FAILED = tr("Connection Failed")
STATUS_DISCONNECTED = tr("Disconnected")
STATUS_ERROR_CONN_TEST_FAILED = tr(
    "Error: Connection test failed. Check server config.")
# Other
MSG_SORT_SUCCESS = tr("Servers sorted by ping (fastest first).")
# Tray
TRAY_SHOW = tr("Show")
TRAY_QUIT = tr("Quit")
TRAY_TITLE = tr("Onix Client")
# Default values
DEFAULT_DNS_SERVERS = "1.1.1.1,8.8.8.8"
DEFAULT_BYPASS_DOMAINS = "*.ir,*.local"
DEFAULT_BYPASS_IPS = "192.168.0.0/16,127.0.0.1"
# N/A
NA = "N/A"

# --- Dialogs and Prompts ---
TITLE_EDIT_SERVER = tr("Edit Server Name")
PROMPT_NEW_SERVER_NAME = tr("Enter new server name:")
TITLE_CONFIRM_DELETE = tr("Confirm Delete")
MSG_CONFIRM_DELETE_SERVER = tr("Are you sure you want to delete server '{}'?")
MSG_CONFIRM_DELETE_RULE = tr("Are you sure you want to delete this rule?")
TITLE_QR_CODE = tr("QR Code for {}")
TITLE_ADD_ROUTING_RULE = tr("Add Routing Rule")
TITLE_EDIT_ROUTING_RULE = tr("Edit Routing Rule")
LBL_RULE_TYPE = tr("Type:")
LBL_RULE_VALUE = tr("Value:")
LBL_RULE_ACTION = tr("Action:")
BTN_ADD_RULE = tr("Add Rule")
BTN_SAVE_CHANGES = tr("Save Changes")
TITLE_SUB_MANAGER = tr("Subscription Manager")
LBL_SUBSCRIPTIONS = tr("Subscriptions")
BTN_ADD = tr("Add")
BTN_CLOSE = tr("Close")
BTN_EDIT = tr("Edit")
BTN_DELETE = tr("Delete")
TITLE_ADD_SUB = tr("Add Subscription")
TITLE_EDIT_SUB = tr("Edit Subscription")
LBL_NAME = tr("Name:")
LBL_URL = tr("URL:")
BTN_SAVE = tr("Save")
MSG_INPUT_ERROR_EMPTY = tr("Name and URL cannot be empty.")
TITLE_ABOUT = tr("About Onix")
LBL_VERSION = tr("Version: {}")
LBL_GITHUB_RELEASES = tr("GitHub Releases Page")
BTN_OK = tr("OK")

MSG_RESTART_REQUIRED = tr(
    "Some settings have been changed that require a restart to take effect. Please restart Onix.")

# --- Languages (for translation extraction) ---
LANG_ENGLISH = tr("English")
LANG_PERSIAN = tr("Persian (فارسی)")
LANG_RUSSIAN = tr("Russian (Русский)")
LANG_ARABIC = tr("Arabic (العربية)")
LANG_CHINESE = tr("Chinese (简体中文)")

# --- Theme Names (for translation extraction) ---
THEME_NAME_GREEN = tr("Green")
THEME_NAME_BLUE = tr("Blue")
THEME_NAME_DARK_BLUE = tr("Dark Blue")

# --- Timeouts ---
TCP_PING_TIMEOUT = 4  # Increased from 2 to 4 seconds
URL_TEST_TIMEOUT = 8  # Increased from 5 to 8 seconds
GET_EXTERNAL_IP_TIMEOUT = 5
WAIT_FOR_PROXY_TIMEOUT = 5
WAIT_FOR_PROXY_INTERVAL = 0.1

# --- URLs ---
URL_TEST_DEFAULT_URL = "http://www.gstatic.com/generate_204"
GET_EXTERNAL_IP_URL = "https://api.ipify.org"
GITHUB_RELEASES_URL = "https://github.com/AhmadAkd/onix/releases"
GEOIP_DB_DOWNLOAD_URL = (
    "https://github.com/SagerNet/sing-geoip/releases/latest/download/geoip.db"
)
GEOIP_RULE_SET_URL = (
    "https://raw.githubusercontent.com/soffchen/sing-geoip/rule-set/geoip-{code}.srs"
)
GEOSITE_RULE_SET_URL = (
    "https://raw.githubusercontent.com/soffchen/sing-geosite/rule-set/{code}.srs"
)
IRAN_GEOIP_RULE_SET_URL = "https://raw.githubusercontent.com/Chocolate4U/Iran-sing-box-rules/rule-set/geoip-ir.srs"
IRAN_GEOSITE_RULE_SET_URL = "https://raw.githubusercontent.com/Chocolate4U/Iran-sing-box-rules/rule-set/geosite-ir.srs"

# --- GitHub API Constants ---
GITHUB_SINGBOX_RELEASE_API = (
    "https://api.github.com/repos/SagerNet/sing-box/releases/latest"
)
GITHUB_XRAY_RELEASE_API = (
    "https://api.github.com/repos/XTLS/Xray-core/releases/latest"
)

SINGBOX_WINDOWS_ASSET_KEYWORD = "windows-amd64"
DEFAULT_USER_AGENT = "Mozilla/5.0"

# --- Singbox Download Constants ---
SINGBOX_ASSET_KEYWORDS = {
    "windows_amd64": "windows-amd64",
    "linux_amd64": "linux-amd64",
    "linux_arm64": "linux-arm64",
    "darwin_amd64": "darwin-amd64",
    "darwin_arm64": "darwin-arm64",
}
SINGBOX_EXECUTABLE_NAMES = {
    "windows": "sing-box.exe",
    "linux": "sing-box",
    "darwin": "sing-box",
}

# --- Xray Download Constants ---
XRAY_ASSET_KEYWORDS = {
    "windows_amd64": "windows-64",
    "linux_amd64": "linux-64",
    "linux_arm64": "linux-arm64",
    "darwin_amd64": "macos-64",
    "darwin_arm64": "macos-arm64",
}
XRAY_EXECUTABLE_NAMES = {
    "windows": "xray.exe",
    "linux": "xray",
    "darwin": "xray",
}

# --- Singbox Manager Constants ---
CONNECTION_STOP_DELAY = 0.5
CONNECTION_CHECK_DELAY = 2000

# --- Test Configuration Constants ---
# Test endpoints
TEST_ENDPOINTS = {
    "tcp": {
        "host": "8.8.8.8",
        "port": 53,
        "timeout": TCP_PING_TIMEOUT
    },
    "url": {
        "url": URL_TEST_DEFAULT_URL,
        "timeout": URL_TEST_TIMEOUT
    }
}

# Concurrency limits
MAX_CONCURRENT_TESTS = 10
MAX_CONCURRENT_CORE_TESTS = 5

# Health check settings
HEALTH_CHECK_INTERVAL = 30  # seconds
HEALTH_CHECK_EMA_ALPHA = 0.3  # EMA smoothing factor
HEALTH_CHECK_MAX_BACKOFF = 60  # seconds
HEALTH_CHECK_MIN_BACKOFF = 1  # seconds

# Test retry settings
TEST_RETRY_COUNT = 1
TEST_RETRY_DELAY = 0.5  # seconds between retries

# Core test settings
CORE_TEST_STARTUP_DELAY = 2  # seconds to wait for core to start
CORE_TEST_SHUTDOWN_DELAY = 1  # seconds to wait for core to stop
