"""Constants for the Smart Comfort Climate integration."""

DOMAIN = "smart_comfort_climate"
DEFAULT_NAME = "Smart Comfort Climate"

# Configuration constants
CONF_CLIMATE_ENTITY = "climate_entity"
CONF_TEMPERATURE_SENSOR = "temperature_sensor"
CONF_HUMIDITY_SENSOR = "humidity_sensor"
CONF_TARGET_FEELS_LIKE = "target_feels_like"
CONF_TARGET_HUMIDITY = "target_humidity"

# Default values
DEFAULT_TARGET_FEELS_LIKE = 72.0
DEFAULT_TARGET_HUMIDITY = 45.0

# Comfort thresholds (dew point in °F)
DEW_POINT_OPPRESSIVE = 65
DEW_POINT_MUGGY = 60
DEW_POINT_SLIGHTLY_HUMID = 55
DEW_POINT_COMFORTABLE = 45
DEW_POINT_DRY = 35

# Comfort status strings
COMFORT_OPPRESSIVE = "Oppressive"
COMFORT_MUGGY = "Muggy"
COMFORT_SLIGHTLY_HUMID = "Slightly Humid"
COMFORT_COMFORTABLE = "Comfortable"
COMFORT_VERY_COMFORTABLE = "Very Comfortable"
COMFORT_DRY = "Dry"
COMFORT_VERY_DRY = "Very Dry"

# Climate modes
MODE_PRIORITY_DRY = "dry"
MODE_PRIORITY_COOL = "cool"
MODE_PRIORITY_FAN = "fan_only"
MODE_PRIORITY_OFF = "off"