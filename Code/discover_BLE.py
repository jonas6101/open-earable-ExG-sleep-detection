import asyncio
from bleak import BleakScanner

async def scan_ble_devices():
    print("Scanning for Bluetooth LE devices...")
    
    devices = await BleakScanner.discover()
    
    if len(devices) == 0:
        print("No devices found")
    else:
        print(f"Found {len(devices)} devices:")
        for idx, device in enumerate(devices):
            print(f"{idx + 1}: Device Name: {device.name}, Device Address: {device.address}")

if __name__ == "__main__":
    asyncio.run(scan_ble_devices())

