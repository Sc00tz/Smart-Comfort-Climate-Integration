"""Config flow for Smart Comfort Climate integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_CLIMATE_ENTITY,
    CONF_HUMIDITY_SENSOR,
    CONF_TARGET_FEELS_LIKE,
    CONF_TARGET_HUMIDITY,
    CONF_TEMPERATURE_SENSOR,
    DEFAULT_NAME,
    DEFAULT_TARGET_FEELS_LIKE,
    DEFAULT_TARGET_HUMIDITY,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class SmartComfortClimateConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smart Comfort Climate."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate the input
            if await self._validate_input(user_input):
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input,
                )
            errors["base"] = "invalid_input"

        # Get available entities for selectors
        climate_entities = [
            entity_id
            for entity_id in self.hass.states.async_entity_ids("climate")
        ]
        
        temperature_sensors = [
            entity_id
            for entity_id in self.hass.states.async_entity_ids("sensor")
            if self.hass.states.get(entity_id).attributes.get("device_class") == "temperature"
        ]
        
        humidity_sensors = [
            entity_id
            for entity_id in self.hass.states.async_entity_ids("sensor")
            if self.hass.states.get(entity_id).attributes.get("device_class") == "humidity"
        ]

        data_schema = vol.Schema({
            vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
            vol.Required(CONF_CLIMATE_ENTITY): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="climate",
                    multiple=False,
                )
            ),
            vol.Required(CONF_TEMPERATURE_SENSOR): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="sensor",
                    device_class="temperature",
                    multiple=False,
                )
            ),
            vol.Required(CONF_HUMIDITY_SENSOR): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="sensor",
                    device_class="humidity",
                    multiple=False,
                )
            ),
            vol.Optional(
                CONF_TARGET_FEELS_LIKE, 
                default=DEFAULT_TARGET_FEELS_LIKE
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=65,
                    max=85,
                    step=0.5,
                    unit_of_measurement="°F",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Optional(
                CONF_TARGET_HUMIDITY,
                default=DEFAULT_TARGET_HUMIDITY
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=30,
                    max=70,
                    step=1,
                    unit_of_measurement="%",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def _validate_input(self, user_input: dict[str, Any]) -> bool:
        """Validate the user input."""
        # Check if entities exist and are valid
        climate_entity = self.hass.states.get(user_input[CONF_CLIMATE_ENTITY])
        temp_sensor = self.hass.states.get(user_input[CONF_TEMPERATURE_SENSOR])
        humidity_sensor = self.hass.states.get(user_input[CONF_HUMIDITY_SENSOR])

        if not climate_entity:
            _LOGGER.error("Climate entity not found: %s", user_input[CONF_CLIMATE_ENTITY])
            return False

        if not temp_sensor:
            _LOGGER.error("Temperature sensor not found: %s", user_input[CONF_TEMPERATURE_SENSOR])
            return False

        if not humidity_sensor:
            _LOGGER.error("Humidity sensor not found: %s", user_input[CONF_HUMIDITY_SENSOR])
            return False

        # Check if temperature sensor has numeric state
        try:
            float(temp_sensor.state)
        except (ValueError, TypeError):
            _LOGGER.error("Temperature sensor does not have numeric state: %s", temp_sensor.state)
            return False

        # Check if humidity sensor has numeric state
        try:
            float(humidity_sensor.state)
        except (ValueError, TypeError):
            _LOGGER.error("Humidity sensor does not have numeric state: %s", humidity_sensor.state)
            return False

        return True

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Smart Comfort Climate config flow options handler."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        super().__init__()
        self.config_entry = config_entry  # ← Keep this line!  

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_TARGET_FEELS_LIKE,
                        default=self.config_entry.options.get(  # ← Use self.config_entry
                            CONF_TARGET_FEELS_LIKE, 
                            self.config_entry.data.get(CONF_TARGET_FEELS_LIKE, DEFAULT_TARGET_FEELS_LIKE)
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=65,
                            max=85,
                            step=0.5,
                            unit_of_measurement="°F",
                            mode=selector.NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Required(
                        CONF_TARGET_HUMIDITY,
                        default=self.config_entry.options.get(  # ← Use self.config_entry
                            CONF_TARGET_HUMIDITY,
                            self.config_entry.data.get(CONF_TARGET_HUMIDITY, DEFAULT_TARGET_HUMIDITY)
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=30,
                            max=70,
                            step=1,
                            unit_of_measurement="%",
                            mode=selector.NumberSelectorMode.BOX,
                        )
                    ),
                }
            ),
        )