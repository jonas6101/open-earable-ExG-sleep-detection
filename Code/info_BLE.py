import asyncio
from bleak import BleakScanner, BleakClient

async def get_device_services(device_address):
    try:
        async with BleakClient(device_address) as client:
            print(f"Connected to {device_address}")
            services = await client.get_services()

            print(f"Services and Characteristics for device {device_address}:")
            for service in services:
                print(f"Service: {service.uuid}")
                for characteristic in service.characteristics:
                    print(f"  Characteristic: {characteristic.uuid}")
                    print(f"    Properties: {characteristic.properties}")
                    if "read" in characteristic.properties:
                        try:
                            value = await client.read_gatt_char(characteristic.uuid)
                            print(f"    Value: {value}")
                        except Exception as e:
                            print(f"    Could not read value: {e}")
    except Exception as e:
        print(f"Failed to connect to device {device_address}: {e}")

async def find_device_and_get_services(device_name):
    print(f"Scanning for Bluetooth LE devices named '{device_name}'...")
    devices = await BleakScanner.discover()

    for device in devices:
        if device.name == device_name:
            print(f"Found device '{device_name}' with address {device.address}")
            print("Fetching services and characteristics...")
            await get_device_services(device.address)
            return
    
    print(f"Device named '{device_name}' not found.")

if __name__ == "__main__":
    # Device name you're looking for
    target_device_name = "OpenEarable-C4E4"
    
    # Run the async function
    asyncio.run(find_device_and_get_services(target_device_name))

