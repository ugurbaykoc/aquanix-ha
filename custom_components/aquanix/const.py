DOMAIN = "aquanix"

CONF_DEVICE_ID = "device_id"
CONF_PASSWORD = "password"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL = 60

BASE_URL = "https://deselbulut.com/aquanix-sistem/public/api"
MESSAGES_ENDPOINT = f"{BASE_URL}/device/mesajlari_oku"
DELETE_ENDPOINT = f"{BASE_URL}/device/delete"

# Vendor app's own shared API credential, recovered from a captured request
# (not a per-user secret; every installation of the official app sends this
# same header). See README for how it was found.
AUTH_HEADER = "Basic RGVzQXF1NTgyM3h4ejphZGdqbHh2bjg1NjRRQXp0"

MESSAGE_NO_RECORD = "Kayit_yok"
MESSAGE_WATER_LOW = "Akvaryum yedek depoda su bitti."
