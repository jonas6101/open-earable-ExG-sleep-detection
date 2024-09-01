import asyncio
from bleak import BleakClient, BleakScanner
import struct

# The name of the BLE device you're trying to connect to
DEVICE_NAME = "OpenEarable-C4E4"

# The UUID of the characteristic we want to read/subscribe to
CHARACTERISTIC_UUID = "20a4a273-c214-4c18-b433-329f30ef7275"

def notification_handler(sender, data):
    """Handles incoming notifications from the BLE device."""
    expected_length = 20  # We expect 20 bytes for 5 floats (4 bytes each)
    
    if len(data) == expected_length:
        readings = struct.unpack('<5f', data)
        print(f"Notification from {sender}: {readings}")
    else:
        print(f"Unexpected data length: {len(data)} bytes. Data: {data}")

async def run():
    print(f"Scanning for device with name '{DEVICE_NAME}'...")
    devices = await BleakScanner.discover()

    device = None
    for d in devices:
        if d.name == DEVICE_NAME:
            device = d
            break

    if device is None:
        print(f"Device named '{DEVICE_NAME}' not found.")
        return

    async with BleakClient(device) as client:
        print(f"Connected to {device.name} ({device.address})")

        await client.start_notify(CHARACTERISTIC_UUID, notification_handler)
        print(f"Subscribed to characteristic {CHARACTERISTIC_UUID}")

        # Keep the script running to continue receiving notifications
        await asyncio.sleep(30)  # Adjust time as needed

        await client.stop_notify(CHARACTERISTIC_UUID)
        print(f"Unsubscribed from characteristic {CHARACTERISTIC_UUID}")

if __name__ == "__main__":
    asyncio.run(run())

