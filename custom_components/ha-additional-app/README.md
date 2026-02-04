# HA AA - Android Alarm Integration

A Home Assistant custom integration that receives alarm data from an Android device via webhook and provides a sensor for the next upcoming alarm time.

## Features

- 🔔 **Real-time alarm tracking** - Receive alarm events from your Android device
- 📡 **Webhook-based** - Local push integration, no polling required
- 🎯 **Next alarm sensor** - Automatically displays the timestamp of the next upcoming alarm
- 🌐 **Flexible URL support** - Works with both local and public Home Assistant URLs
- 🔐 **QR code configuration** - Easy setup with QR code display in the UI
- 🔄 **Automatic time zone handling** - Respects device timezone settings

## Installation

### Via HACS

1. Go to HACS → Integrations
2. Search for "HA AA" or "HA AA"
3. Click Install
4. Restart Home Assistant

### Manual Installation

1. Copy the `ha-additional-app` folder to `custom_components/`
2. Restart Home Assistant

## Configuration

### Step 1: Add the Integration

1. Go to Settings → Devices & Services → Create Integration
2. Search for "HA AA"
3. Select your preferred URL type:
   - **Local URL** - For devices on the same network (recommended)
   - **Public URL** - For remote access to Home Assistant

### Step 2: Get the Webhook URL

After selecting your URL type, you'll see:
- A QR code that can be scanned by the Android app
- The webhook URL in text format
- Share either the QR code or URL with your Android device

### Step 3: Configure Android App

Use the companion Android app to:
1. Scan the QR code or paste the webhook URL
2. Grant permissions for alarm access
3. The app will automatically send alarm updates to Home Assistant

## Entities

### Sensor: Next Alarm

**Entity ID:** `sensor.next_alarm`

Displays the timestamp of the next upcoming alarm set on the Android device.

- **State:** ISO format datetime string (e.g., `2026-02-04T07:30:00`)
- **Updates:** Whenever alarms change or every 60 seconds
- **Unit:** Timestamp
- **Icon:** `mdi:alarm`

Example use in automations:

```yaml
automation:
  - alias: "Morning notification"
    trigger:
      platform: time
      at: "06:30:00"
    condition:
      condition: state
      entity_id: sensor.next_alarm
      state: "< 1 hour"
    action:
      service: notify.mobile_app_phone
      data:
        message: "Good morning! Your alarm is set for {{ state_attr('sensor.next_alarm', 'alarm_time') }}"
```

## How It Works

1. **Webhook Registration** - When you add the integration, a unique webhook URL is generated and registered
2. **Android App Sends Data** - The companion Android app sends alarm data to this webhook endpoint
3. **Data Processing** - The integration processes the alarm data and updates the `AlarmCoordinator`
4. **Sensor Update** - The next alarm sensor reflects the timestamp of the soonest upcoming alarm
5. **Periodic Refresh** - The integration refreshes the next alarm calculation every 60 seconds to account for time passing

## Webhook Payload Format

The Android app should send a POST request to the webhook URL with the following JSON format:

```json
{
  "alarms": [
    {
      "enabled": true,
      "hour": 7,
      "minute": 30,
      "days": ["MON", "TUE", "WED", "THU", "FRI"]
    },
    {
      "enabled": true,
      "hour": 22,
      "minute": 0,
      "days": ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    }
  ],
  "timezone": "America/New_York"
}
```

## Troubleshooting

### Sensor Not Updating

- Verify the Android app is successfully sending data to the webhook URL
- Check Home Assistant logs for any webhook errors
- Ensure the integration is properly configured and enabled

### Webhook URL Not Working

- If using **Local URL**, both devices must be on the same network
- If using **Public URL**, ensure your Home Assistant instance is publicly accessible
- Check your reverse proxy/firewall configuration

### Timezone Issues

- Ensure your Android device has the correct timezone set
- The integration will use the timezone provided by the Android app
- Home Assistant will display times in your local timezone

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for development information.

## Support

For issues, feature requests, or questions:
- [GitHub Issues](https://github.com/hacs/integration/issues)
- [GitHub Discussions](https://github.com/hacs/integration/discussions)

## License

This integration is part of the HACS project and follows the same licensing.

## Credits

- Created by [@LucasRomier](https://github.com/LucasRomier)
- Built as a Home Assistant custom component
