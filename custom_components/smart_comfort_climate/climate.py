"""Smart Comfort Climate entity."""
from __future__ import annotations

import logging
import math
from typing import Any

from homeassistant.components.climate import (
    ATTR_HVAC_MODE,
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_TEMPERATURE,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_CLIMATE_ENTITY,
    CONF_HUMIDITY_SENSOR,
    CONF_TARGET_FEELS_LIKE,
    CONF_TEMPERATURE_SENSOR,
    DOMAIN,
    DEW_POINT_OPPRESSIVE,
    DEW_POINT_MUGGY,
    DEW_POINT_SLIGHTLY_HUMID,
    DEW_POINT_COMFORTABLE,
    MODE_PRIORITY_DRY,
    MODE_PRIORITY_COOL,
    MODE_PRIORITY_FAN,
    MODE_PRIORITY_OFF,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Smart Comfort Climate."""
    config = hass.data[DOMAIN][config_entry.entry_id]
    
    async_add_entities([
        SmartComfortClimate(
            hass,
            config_entry.entry_id,
            config[CONF_CLIMATE_ENTITY],
            config[CONF_TEMPERATURE_SENSOR],
            config[CONF_HUMIDITY_SENSOR],
            config.get(CONF_TARGET_FEELS_LIKE, 72.0),
            config_entry.title,
        )
    ])


class SmartComfortClimate(ClimateEntity):
    """Smart Comfort Climate entity."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        climate_entity_id: str,
        temperature_sensor_id: str,
        humidity_sensor_id: str,
        target_feels_like: float,
        name: str,
    ) -> None:
        """Initialize the Smart Comfort Climate."""
        self.hass = hass
        self._entry_id = entry_id
        self._climate_entity_id = climate_entity_id
        self._temperature_sensor_id = temperature_sensor_id
        self._humidity_sensor_id = humidity_sensor_id
        self._target_feels_like = target_feels_like
        self._name = name
        
        self._attr_unique_id = f"{DOMAIN}_{entry_id}"
        self._attr_name = name
        self._attr_temperature_unit = UnitOfTemperature.FAHRENHEIT
        self._attr_target_temperature_step = 0.5
        self._attr_min_temp = 65
        self._attr_max_temp = 85
        
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE |
            ClimateEntityFeature.TURN_ON |
            ClimateEntityFeature.TURN_OFF
        )
        
        self._attr_hvac_modes = [
            HVACMode.OFF,
            HVACMode.AUTO,
        ]
        
        # Internal state
        self._current_temperature = None
        self._current_humidity = None
        self._feels_like_temperature = None
        self._dew_point = None
        self._comfort_status = None
        self._hvac_mode = HVACMode.AUTO
        self._is_on = True
        
        # Track underlying climate entity state
        self._underlying_hvac_mode = None

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()
        
        # Track state changes of source entities
        entity_ids = [
            self._temperature_sensor_id,
            self._humidity_sensor_id,
            self._climate_entity_id,
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
        # Get current readings
        temp_state = self.hass.states.get(self._temperature_sensor_id)
        humidity_state = self.hass.states.get(self._humidity_sensor_id)
        climate_state = self.hass.states.get(self._climate_entity_id)
        
        if not temp_state or not humidity_state or not climate_state:
            return
            
        if temp_state.state in [STATE_UNKNOWN, STATE_UNAVAILABLE]:
            return
            
        if humidity_state.state in [STATE_UNKNOWN, STATE_UNAVAILABLE]:
            return
            
        try:
            self._current_temperature = float(temp_state.state)
            self._current_humidity = float(humidity_state.state)
        except (ValueError, TypeError):
            return
            
        # Calculate comfort metrics
        self._dew_point = self._calculate_dew_point(
            self._current_temperature, self._current_humidity
        )
        self._feels_like_temperature = self._calculate_feels_like_temperature(
            self._current_temperature, self._current_humidity
        )
        self._comfort_status = self._get_comfort_status(self._dew_point)
        
        # Track underlying climate state
        self._underlying_hvac_mode = climate_state.state
        
        # Execute comfort control logic if in auto mode
        if self._hvac_mode == HVACMode.AUTO and self._is_on:
            await self._async_execute_comfort_control()

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

    def _calculate_feels_like_temperature(self, temp_f: float, humidity: float) -> float:
        """Calculate feels-like temperature (heat index or comfort adjustment)."""
        if temp_f >= 80 and humidity >= 40:
            # Use heat index for hot conditions
            return self._calculate_heat_index(temp_f, humidity)
        else:
            # Use dew point adjustment for cooler conditions
            dew_point = self._calculate_dew_point(temp_f, humidity)
            if dew_point > 65:
                return temp_f + (dew_point - 55) * 0.4
            elif dew_point > 55:
                return temp_f + (dew_point - 55) * 0.2
            else:
                return temp_f

    def _calculate_heat_index(self, temp_f: float, humidity: float) -> float:
        """Calculate heat index."""
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

    def _get_comfort_status(self, dew_point: float) -> str:
        """Get comfort status based on dew point."""
        if dew_point > 65:
            return "Oppressive"
        elif dew_point > 60:
            return "Muggy"
        elif dew_point > 55:
            return "Slightly Humid"
        elif dew_point > 50:
            return "Comfortable"
        elif dew_point > 45:
            return "Very Comfortable"
        elif dew_point > 35:
            return "Dry"
        else:
            return "Very Dry"

    async def _async_execute_comfort_control(self) -> None:
        """Execute the comfort control logic."""
        if not all([
            self._current_temperature is not None,
            self._current_humidity is not None,
            self._feels_like_temperature is not None,
            self._dew_point is not None,
        ]):
            return
            
        feels_like_diff = self._feels_like_temperature - self._target_feels_like
        
        # Determine action based on dew point and feels-like difference
        target_mode, target_temp, reason = self._determine_climate_action(
            self._dew_point, feels_like_diff, self._current_temperature
        )
        
        # Execute the action
        if target_mode != self._underlying_hvac_mode:
            await self.hass.services.async_call(
                "climate",
                "set_hvac_mode",
                {
                    "entity_id": self._climate_entity_id,
                    "hvac_mode": target_mode,
                },
            )
            
        if target_temp and target_mode in ["cool", "dry"]:
            await self.hass.services.async_call(
                "climate",
                "set_temperature",
                {
                    "entity_id": self._climate_entity_id,
                    "temperature": target_temp,
                },
            )
        
        # Log the action
        _LOGGER.info(
            "%s: %s - Feels like: %.1f°F (target: %.1f°F), Dew point: %.1f°F",
            self._name,
            reason,
            self._feels_like_temperature,
            self._target_feels_like,
            self._dew_point,
        )

    def _determine_climate_action(
        self, dew_point: float, feels_like_diff: float, current_temp: float
    ) -> tuple[str, float | None, str]:
        """Determine the appropriate climate action."""
        
        # Oppressive humidity (dew point > 65°F)
        if dew_point > DEW_POINT_OPPRESSIVE:
            if feels_like_diff > 0:
                return (
                    MODE_PRIORITY_COOL,
                    min(current_temp - 3, self._target_feels_like - 2),
                    "AC mode (oppressive humidity + hot)"
                )
            else:
                return (
                    MODE_PRIORITY_DRY,
                    self._target_feels_like,
                    "DRY mode (oppressive humidity)"
                )
        
        # Muggy conditions (dew point 60-65°F)
        elif dew_point > DEW_POINT_MUGGY:
            if feels_like_diff > 2:
                return (
                    MODE_PRIORITY_COOL,
                    min(current_temp - 2, self._target_feels_like - 1),
                    "AC mode (muggy + warm)"
                )
            else:
                return (
                    MODE_PRIORITY_DRY,
                    self._target_feels_like,
                    "DRY mode (muggy humidity)"
                )
        
        # Slightly humid (dew point 55-60°F)
        elif dew_point > DEW_POINT_SLIGHTLY_HUMID:
            if feels_like_diff > 3:
                return (
                    MODE_PRIORITY_COOL,
                    current_temp - 1,
                    "AC mode (slightly humid + warm)"
                )
            elif feels_like_diff > 1:
                return (
                    MODE_PRIORITY_DRY,
                    self._target_feels_like,
                    "DRY mode (slightly humid)"
                )
            elif feels_like_diff > 2:
                return (
                    MODE_PRIORITY_COOL,
                    current_temp - 1,
                    "AC mode (humidity OK, need cooling)"
                )
            else:
                return (
                    MODE_PRIORITY_FAN,
                    None,
                    "FAN mode (maintaining)"
                )
        
        # Good humidity (dew point 45-55°F)
        elif dew_point >= DEW_POINT_COMFORTABLE:
            if feels_like_diff > 2:
                return (
                    MODE_PRIORITY_COOL,
                    current_temp - 1,
                    "AC mode (good humidity, cooling needed)"
                )
            elif feels_like_diff > 1:
                return (
                    MODE_PRIORITY_FAN,
                    None,
                    "FAN mode (good humidity, slight cooling)"
                )
            elif feels_like_diff < -4:
                return (
                    MODE_PRIORITY_OFF,
                    None,
                    "OFF (good humidity, too cold)"
                )
            else:
                return (
                    MODE_PRIORITY_FAN,
                    None,
                    "FAN mode (perfect conditions)"
                )
        
        # Dry conditions (dew point < 45°F)
        else:
            if feels_like_diff > 3:
                return (
                    MODE_PRIORITY_COOL,
                    current_temp - 1,
                    "AC mode (dry air, cooling needed)"
                )
            elif feels_like_diff < -3:
                return (
                    MODE_PRIORITY_OFF,
                    None,
                    "OFF (dry and cold)"
                )
            else:
                return (
                    MODE_PRIORITY_FAN,
                    None,
                    "FAN mode (dry air, temp OK)"
                )

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature (feels-like)."""
        return self._feels_like_temperature

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature (feels-like)."""
        return self._target_feels_like

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return current operation."""
        return self._hvac_mode

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = {}
        if self._current_temperature is not None:
            attrs["actual_temperature"] = self._current_temperature
        if self._current_humidity is not None:
            attrs["humidity"] = self._current_humidity
        if self._dew_point is not None:
            attrs["dew_point"] = round(self._dew_point, 1)
        if self._comfort_status is not None:
            attrs["comfort_status"] = self._comfort_status
        if self._feels_like_temperature is not None:
            attrs["feels_like_difference"] = round(
                self._feels_like_temperature - self._target_feels_like, 1
            )
        attrs["underlying_hvac_mode"] = self._underlying_hvac_mode
        attrs["humidity_priority"] = self._dew_point > DEW_POINT_SLIGHTLY_HUMID if self._dew_point else False
        return attrs

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature (feels-like)."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return
            
        self._target_feels_like = temperature
        
        # Trigger immediate re-evaluation
        if self._hvac_mode == HVACMode.AUTO and self._is_on:
            await self._async_execute_comfort_control()
            
        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        self._hvac_mode = hvac_mode
        
        if hvac_mode == HVACMode.OFF:
            self._is_on = False
            # Turn off underlying climate
            await self.hass.services.async_call(
                "climate",
                "set_hvac_mode",
                {
                    "entity_id": self._climate_entity_id,
                    "hvac_mode": "off",
                },
            )
        elif hvac_mode == HVACMode.AUTO:
            self._is_on = True
            # Trigger comfort control
            await self._async_execute_comfort_control()
            
        self.async_write_ha_state()

    async def async_turn_on(self) -> None:
        """Turn the entity on."""
        await self.async_set_hvac_mode(HVACMode.AUTO)

    async def async_turn_off(self) -> None:
        """Turn the entity off."""
        await self.async_set_hvac_mode(HVACMode.OFF)