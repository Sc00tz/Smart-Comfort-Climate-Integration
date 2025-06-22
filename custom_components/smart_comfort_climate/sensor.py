"""Smart Comfort Climate sensor entities."""
from __future__ import annotations

import logging
import math
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_HUMIDITY_SENSOR,
    CONF_TEMPERATURE_SENSOR,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Smart Comfort Climate sensors."""
    config = hass.data[DOMAIN][config_entry.entry_id]
    
    sensors = [
        DewPointSensor(
            hass,
            config_entry.entry_id,
            config[CONF_TEMPERATURE_SENSOR],
            config[CONF_HUMIDITY_SENSOR],
            config_entry.title,
        ),
        FeelsLikeSensor(
            hass,
            config_entry.entry_id,
            config[CONF_TEMPERATURE_SENSOR],
            config[CONF_HUMIDITY_SENSOR],
            config_entry.title,
        ),
        ComfortStatusSensor(
            hass,
            config_entry.entry_id,
            config[CONF_TEMPERATURE_SENSOR],
            config[CONF_HUMIDITY_SENSOR],
            config_entry.title,
        ),
    ]
    
    async_add_entities(sensors)


class ComfortSensorBase(SensorEntity):
    """Base class for comfort sensors."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        temperature_sensor_id: str,
        humidity_sensor_id: str,
        base_name: str,
        sensor_type: str,
    ) -> None:
        """Initialize the comfort sensor."""
        self.hass = hass
        self._entry_id = entry_id
        self._temperature_sensor_id = temperature_sensor_id
        self._humidity_sensor_id = humidity_sensor_id
        
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{sensor_type}"
        self._attr_name = f"{base_name} {sensor_type.replace('_', ' ').title()}"
        
        self._current_temperature = None
        self._current_humidity = None

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        
        # Track state changes of source entities
        entity_ids = [
            self._temperature_sensor_id,
            self._humidity_sensor_id,
        ]
        
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, entity_ids, self._async_state_changed
            )
        )
        
        # Initial update
        await self._async_update_state()

    @callback
    async def _async_state_changed(self, event) -> None:
        """Handle state changes of tracked entities."""
        await self._async_update_state()
        self.async_write_ha_state()

    async def _async_update_state(self) -> None:
        """Update the state based on source entities."""
        temp_state = self.hass.states.get(self._temperature_sensor_id)
        humidity_state = self.hass.states.get(self._humidity_sensor_id)
        
        if not temp_state or not humidity_state:
            return
            
        if temp_state.state in [STATE_UNKNOWN, STATE_UNAVAILABLE]:
            self._current_temperature = None
            return
            
        if humidity_state.state in [STATE_UNKNOWN, STATE_UNAVAILABLE]:
            self._current_humidity = None
            return
            
        try:
            self._current_temperature = float(temp_state.state)
            self._current_humidity = float(humidity_state.state)
        except (ValueError, TypeError):
            self._current_temperature = None
            self._current_humidity = None
            return
            
        # Update sensor-specific calculations
        await self._async_calculate_value()

    async def _async_calculate_value(self) -> None:
        """Calculate the sensor value - to be implemented by subclasses."""
        pass

    def _calculate_dew_point(self, temp_f: float, humidity: float) -> float:
        """Calculate dew point using Magnus formula."""
        if humidity <= 0 or humidity > 100:
            return 0
            
        # Convert to Celsius
        temp_c = (temp_f - 32) * 5 / 9
        
        # Magnus formula constants
        a = 17.625
        b = 243.04
        
        # Calculate dew point
        alpha = math.log(humidity / 100) + (a * temp_c) / (b + temp_c)
        dew_point_c = (b * alpha) / (a - alpha)
        
        # Convert back to Fahrenheit
        return (dew_point_c * 9 / 5) + 32

    def _calculate_heat_index(self, temp_f: float, humidity: float) -> float:
        """Calculate heat index."""
        if temp_f < 80 or humidity < 40:
            return temp_f
            
        hi = (
            -42.379 + 
            2.04901523 * temp_f + 
            10.14333127 * humidity - 
            0.22475541 * temp_f * humidity - 
            0.00683783 * temp_f * temp_f - 
            0.05481717 * humidity * humidity + 
            0.00122874 * temp_f * temp_f * humidity + 
            0.00085282 * temp_f * humidity * humidity - 
            0.00000199 * temp_f * temp_f * humidity * humidity
        )
        return hi


class DewPointSensor(ComfortSensorBase):
    """Dew Point sensor."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        temperature_sensor_id: str,
        humidity_sensor_id: str,
        base_name: str,
    ) -> None:
        """Initialize the dew point sensor."""
        super().__init__(
            hass, entry_id, temperature_sensor_id, humidity_sensor_id, base_name, "dew_point"
        )
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
        self._attr_icon = "mdi:water-thermometer"

    async def _async_calculate_value(self) -> None:
        """Calculate dew point value."""
        if self._current_temperature is None or self._current_humidity is None:
            self._attr_native_value = None
            return
            
        dew_point = self._calculate_dew_point(self._current_temperature, self._current_humidity)
        self._attr_native_value = round(dew_point, 1)


class FeelsLikeSensor(ComfortSensorBase):
    """Feels Like Temperature sensor."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        temperature_sensor_id: str,
        humidity_sensor_id: str,
        base_name: str,
    ) -> None:
        """Initialize the feels like sensor."""
        super().__init__(
            hass, entry_id, temperature_sensor_id, humidity_sensor_id, base_name, "feels_like"
        )
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
        self._attr_icon = "mdi:thermometer-auto"

    async def _async_calculate_value(self) -> None:
        """Calculate feels like temperature value."""
        if self._current_temperature is None or self._current_humidity is None:
            self._attr_native_value = None
            return
            
        if self._current_temperature >= 80 and self._current_humidity >= 40:
            # Use heat index for hot conditions
            feels_like = self._calculate_heat_index(self._current_temperature, self._current_humidity)
        else:
            # Use dew point adjustment for cooler conditions
            dew_point = self._calculate_dew_point(self._current_temperature, self._current_humidity)
            if dew_point > 65:
                feels_like = self._current_temperature + (dew_point - 55) * 0.4
            elif dew_point > 55:
                feels_like = self._current_temperature + (dew_point - 55) * 0.2
            else:
                feels_like = self._current_temperature
                
        self._attr_native_value = round(feels_like, 1)


class ComfortStatusSensor(ComfortSensorBase):
    """Comfort Status sensor."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        temperature_sensor_id: str,
        humidity_sensor_id: str,
        base_name: str,
    ) -> None:
        """Initialize the comfort status sensor."""
        super().__init__(
            hass, entry_id, temperature_sensor_id, humidity_sensor_id, base_name, "comfort_status"
        )
        self._attr_icon = "mdi:weather-partly-cloudy"

    async def _async_calculate_value(self) -> None:
        """Calculate comfort status value."""
        if self._current_temperature is None or self._current_humidity is None:
            self._attr_native_value = None
            return
            
        dew_point = self._calculate_dew_point(self._current_temperature, self._current_humidity)
        
        if dew_point > 65:
            status = "Oppressive"
        elif dew_point > 60:
            status = "Muggy"
        elif dew_point > 55:
            status = "Slightly Humid"
        elif dew_point > 50:
            status = "Comfortable"
        elif dew_point > 45:
            status = "Very Comfortable"
        elif dew_point > 35:
            status = "Dry"
        else:
            status = "Very Dry"
            
        self._attr_native_value = status

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = {}
        if self._current_temperature is not None:
            attrs["temperature"] = self._current_temperature
        if self._current_humidity is not None:
            attrs["humidity"] = self._current_humidity
        if self._current_temperature is not None and self._current_humidity is not None:
            dew_point = self._calculate_dew_point(self._current_temperature, self._current_humidity)
            attrs["dew_point"] = round(dew_point, 1)
            attrs["humidity_priority"] = dew_point > 55
        return attrs