# Smart Comfort Climate

A Home Assistant custom integration that provides intelligent climate control based on "feels-like" temperature and dew point comfort science.

Perfect for oversized AC units that short-cycle when using traditional temperature-only control!

## Features

- **Feels-Like Temperature Control**: Set your target comfort level (e.g., "I want it to feel like 72°F")
- **Humidity-First Logic**: Prioritizes dehumidification over cooling to avoid muggy conditions
- **Dew Point Science**: Uses psychrometric calculations for optimal comfort
- **Smart Mode Selection**: Automatically chooses between dry, cool, fan, or off modes
- **Comprehensive Sensors**: Provides dew point, feels-like temperature, and comfort status sensors

## How It Works

Instead of just looking at temperature, this integration considers both temperature and humidity to determine how the air actually *feels*. It then prioritizes getting the humidity right first (using dry mode), and only uses AC cooling when humidity is already controlled.

**Comfort Zones Based on Dew Point:**
- **65°F+**: Oppressive (aggressive dehumidification)
- **60-65°F**: Muggy (dry mode preferred)
- **55-60°F**: Slightly humid (dry mode for warmth)
- **45-55°F**: Comfortable (AC okay when needed)
- **Below 45°F**: Dry (careful with AC)

This prevents the common problem where oversized AC units cool the air too quickly without removing enough humidity, leaving you with cold, clammy air.

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots menu → "Custom repositories"
4. Add this repository URL with category "Integration"
5. Click "Install"
6. Restart Home Assistant

### Manual Installation

1. Download the `smart_comfort_climate` folder
2. Copy it to `custom_components/smart_comfort_climate/` in your Home Assistant config directory
3. Restart Home Assistant

## Configuration

1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "Smart Comfort Climate"
4. Configure:
   - **Name**: Friendly name for your climate system
   - **Climate Entity**: Your existing AC/heat pump (e.g., `climate.bedroom_minisplit`)
   - **Temperature Sensor**: External temperature sensor (e.g., `sensor.bedroom_temperature`)
   - **Humidity Sensor**: External humidity sensor (e.g., `sensor.bedroom_humidity`)
   - **Target Feels-Like Temperature**: Initial comfort target (default: 72°F)

## Entities Created

After setup, you'll get:

### Climate Entity
- `climate.smart_comfort_climate_[name]`: Main climate control
  - **Target Temperature**: Actually "feels-like" temperature
  - **Current Temperature**: Current "feels-like" temperature
  - **Modes**: Auto (smart control) or Off

### Sensor Entities
- `sensor.[name]_dew_point`: Current dew point temperature
- `sensor.[name]_feels_like`: Current feels-like temperature
- `sensor.[name]_comfort_status`: Human-readable comfort level

### Additional Attributes
Each entity includes helpful attributes like:
- `actual_temperature`: Raw temperature reading
- `humidity`: Current humidity percentage
- `comfort_status`: Comfort description
- `humidity_priority`: Whether dehumidification is prioritized
- `underlying_hvac_mode`: What mode your AC is actually running

## Dashboard Examples

### Simple Thermostat Card
```yaml
type: thermostat
entity: climate.smart_comfort_climate_bedroom
```

### Detailed Entities Card
```yaml
type: entities
title: Bedroom Comfort Control
entities:
  - entity: climate.smart_comfort_climate_bedroom
    name: Smart Climate Control
  - type: divider
  - entity: sensor.bedroom_feels_like
    name: Feels Like Temperature
  - entity: sensor.bedroom_comfort_status
    name: Comfort Level
  - entity: sensor.bedroom_dew_point
    name: Dew Point
  - type: divider
  - entity: sensor.lumi_lumi_weather_temperature
    name: Actual Temperature
  - entity: sensor.lumi_lumi_weather_humidity
    name: Humidity
```

## Usage Tips

1. **Set Your Comfort Target**: Use the thermostat to set what you want it to "feel like" (typically 70-74°F)

2. **Let It Work**: The system will automatically choose the best mode:
   - High humidity → Dry mode first
   - Good humidity but warm → AC mode
   - Perfect conditions → Fan only

3. **Monitor Dew Point**: Watch the dew point sensor - this is the key metric for comfort:
   - 45-55°F = Very comfortable
   - 55-60°F = Slightly humid
   - 60°F+ = Time for dehumidification

4. **Trust the Process**: It might take a cycle or two to reach optimal comfort, especially if starting from very humid conditions

## Troubleshooting

**The integration doesn't control my AC:**
- Check that your climate entity supports the modes: `cool`, `dry`, `fan_only`, `off`
- Verify your temperature and humidity sensors have numeric values

**Readings seem wrong:**
- Ensure your temperature sensor is in Fahrenheit
- Check that humidity sensor reports 0-100% values
- Make sure sensors are properly calibrated

**AC runs in wrong mode:**
- Check the logbook for Smart Climate entries explaining decisions
- Verify your target feels-like temperature is reasonable (68-76°F typically)

## Why This Works Better

Traditional thermostats only look at temperature. But comfort is really about how heat transfers from your body, which depends on both temperature AND humidity.

**Example:** 
- 75°F at 40% humidity feels comfortable
- 75°F at 70% humidity feels muggy and warm
- This integration knows the difference!

By controlling humidity first, you can often be comfortable at slightly higher temperatures, saving energy while improving comfort.

## Contributing

Found a bug or want to contribute? Please open an issue or pull request on GitHub!

## Credits

Based on psychrometric science and real-world experience with oversized HVAC systems. Inspired by the need for better comfort control in modern homes.