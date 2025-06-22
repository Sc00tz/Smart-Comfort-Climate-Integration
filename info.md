# Smart Comfort Climate

Transform your oversized AC unit into an intelligent comfort system that prioritizes how the air actually *feels*.

## The Problem

Traditional thermostats only look at temperature, but comfort depends on both temperature AND humidity. This creates issues with oversized AC units that:
- Cool air too quickly without removing enough humidity
- Leave you feeling cold and clammy
- Short-cycle and waste energy
- Never achieve true comfort

## The Solution

Smart Comfort Climate uses **dew point science** and **feels-like temperature** to deliver real comfort:

- **Humidity-First Logic**: Removes moisture before cooling air
- **Feels-Like Targets**: Set the temperature you want it to feel like (e.g., 72°F)
- **Intelligent Mode Selection**: Automatically chooses dry, cool, fan, or off
- **No More Muggy Air**: Prevents that sticky, uncomfortable feeling

## How It Works

### Traditional Control:
```
Set: 72°F → AC runs → Room: 72°F but feels muggy
```

### Smart Comfort Control:
```
Target feels-like: 72°F → Check humidity → Use dry mode first → Perfect comfort
```

## Comfort Science

The integration uses **dew point** (the most accurate humidity comfort metric):

- **🟢 45-55°F**: Very comfortable humidity
- **🟡 55-60°F**: Slightly humid (dry mode for warmth)
- **🟠 60-65°F**: Muggy (prioritize dehumidification)
- **🔴 65°F+**: Oppressive (aggressive dry mode)

## Perfect For

- **Oversized AC units** that short-cycle
- **Humid climates** where temperature alone isn't enough
- **Anyone who values comfort** over simple temperature control
- **Energy efficiency** through smarter humidity management

## What You Get

### Main Climate Entity
- Single "feels-like" temperature control
- Automatic humidity vs. temperature prioritization
- Intelligent mode explanations in logbook

### Comfort Sensors
- **Dew Point**: The key metric for humidity comfort
- **Feels-Like Temperature**: What it actually feels like right now
- **Comfort Status**: Human-readable comfort levels

### Smart Automation
- Monitors your external temperature and humidity sensors
- Controls your existing climate entity
- Logs every decision with clear explanations

## Requirements

- **External Temperature Sensor**: For accurate room readings
- **External Humidity Sensor**: Critical for dew point calculations
- **Compatible Climate Entity**: Your existing AC/heat pump
- **Home Assistant 2023.4+**: For modern integration features

*Why external sensors? Built-in AC sensors are often inaccurate due to unit placement and airflow. External sensors give much better room-level readings for optimal comfort.*

## Configuration

Simple setup through the Home Assistant UI:
1. Choose your climate entity (AC/heat pump)
2. Select temperature and humidity sensors
3. Set your default comfort target
4. Let the system optimize your comfort automatically

No YAML configuration needed - everything is done through the friendly interface.

---

**Ready for the perfect complement?** Check out the [Smart Comfort Thermostat Card](https://github.com/yourusername/smart-comfort-thermostat-card) for a beautiful dashboard interface that makes all this comfort science intuitive and elegant.