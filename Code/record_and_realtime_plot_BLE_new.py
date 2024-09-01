import asyncio
from bleak import BleakClient
import struct
from datetime import datetime, timedelta
import threading
import digitalfilter
import sys
import signal
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.animation as animation

BLE_ADDRESS = "73:4C:69:84:C4:E4"
CHARACTERISTIC_UUID = "20a4a273-c214-4c18-b433-329f30ef7275"

# Plotting configuration
dataList = []
max_datapoints_to_display = 700
min_buffer_uV = 150
inamp_gain = 50
sample_rate = 256
filters = digitalfilter.get_Biopotential_filter(order=4, cutoff=[1, 30], btype="bandpass", fs=256, output="sos")
enable_filters = True
write_to_file = False
autoscale = False

# Set fixed axis limits
time_domain_ylim = (-min_buffer_uV, min_buffer_uV)  # Fixed y-axis limits for time-domain plot
freq_domain_xlim = (0, sample_rate / 2)  # Fixed x-axis limits for frequency-domain plot
freq_domain_ylim = (0, 1e7)  # Set this according to the expected power range

current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"OpenEarableEEG_BLE_{current_time}.csv"

if write_to_file:
    recording_file = open("./recordings/" + filename, 'w')
    recording_file.write("time,raw_data,filtered_data\n")

fig, (ax_time, ax_freq) = plt.subplots(2, 1)
line_time, = ax_time.plot([], [])
line_freq, = ax_freq.plot([], [])

exit_event = threading.Event()

last_valid_timestamp = None

def init():
    line_time.set_data([], [])
    ax_time.set_xlim(0, max_datapoints_to_display)
    ax_time.set_ylim(time_domain_ylim)  # Apply fixed y-axis limits for the time-domain plot
    ax_time.set_title("Biopontential Data from OpenEarable EEG")
    ax_time.set_ylabel("Voltage (µV)")
    ax_time.set_xlabel("Samples")

    line_freq.set_data([], [])
    ax_freq.set_xlim(freq_domain_xlim)  # Apply fixed x-axis limits for the frequency-domain plot
    ax_freq.set_ylim(freq_domain_ylim)  # Apply fixed y-axis limits for the frequency-domain plot
    ax_freq.set_title("Frequency Spectrum")
    ax_freq.set_ylabel("Power")
    ax_freq.set_xlabel("Frequency (Hz)")

    return line_time, line_freq

def animate(frame):
    global dataList

    # Update the time-domain plot
    dataList = dataList[-max_datapoints_to_display:]  # Keep only the latest data points
    line_time.set_data(range(1, len(dataList) + 1), dataList)

    # Update the frequency-domain plot
    if len(dataList) > 1:
        freqs, power_spectrum = calculate_fft(dataList)
        line_freq.set_data(freqs, power_spectrum)

    return line_time, line_freq

def calculate_fft(data):
    # Calculate the FFT of the time-domain data
    n = len(data)
    fft_result = np.fft.rfft(data)
    freqs = np.fft.rfftfreq(n, d=1/sample_rate)
    power_spectrum = np.abs(fft_result)**2
    return freqs, power_spectrum

def notification_handler(sender, data):
    global dataList
    global enable_filters
    global sample_rate
    global last_valid_timestamp

    readings = struct.unpack('<5f', data)
    timestamp = datetime.now()

    if last_valid_timestamp is None:
        last_valid_timestamp = timestamp - timedelta(seconds=5 * 1/sample_rate)

    for i, float_value in enumerate(readings):
        # Calculate the correct timestamp for each reading
        if i == 4:
            timestamp_for_float_value = timestamp
        else:
            time_diff = (timestamp - last_valid_timestamp) / 5
            timestamp_for_float_value = last_valid_timestamp + (i + 1) * time_diff
        
        filtered_data = filters(float_value)

        # Convert to µV
        filtered_data = (filtered_data / inamp_gain) * 1e6  
        raw_data = (float_value / inamp_gain) * 1e6
        
        if enable_filters:
            dataList.append(filtered_data)
        else:
            dataList.append(raw_data)

        if write_to_file:
            recording_file.write(f"{timestamp_for_float_value.strftime('%H:%M:%S.%f')},{raw_data},{filtered_data}\n")

    # Update last_valid_timestamp to be the timestamp for the 5th float
    last_valid_timestamp = timestamp

def insert_datapoint():
    global dataList
    global enable_filters
    global sample_rate

    timestamp = datetime.now()
    timestamp_for_float_value = timestamp.strftime("%H:%M:%S.%f")

    filtered_data = 1000000
    raw_data = 1000000

    if enable_filters:
        dataList.append(filtered_data)
    else:
        dataList.append(raw_data)

    if write_to_file:
        recording_file.write(f"{timestamp_for_float_value},{raw_data},{filtered_data}\n")

async def run_ble_client():
    async with BleakClient(BLE_ADDRESS) as client:
        await client.start_notify(CHARACTERISTIC_UUID, notification_handler)
        print("Connected and receiving data...")

        while not exit_event.is_set():
            await asyncio.sleep(1)

def start_async_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_ble_client())

def cleanup(*args):
    exit_event.set()
    if write_to_file:
        recording_file.close()
    plt.close(fig)

def handle_close(evt):
    cleanup()
    sys.exit(0)

def handle_key_press(event):
    global cmd_pressed
    if event.key == 'g':
        insert_datapoint()

def handle_key_release(event):
    global cmd_pressed
    if event.key == 'cmd' or event.key == 'control':
        insert_datapoint()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    fig.canvas.mpl_connect('close_event', handle_close)
    fig.canvas.mpl_connect('key_press_event', handle_key_press)
    fig.canvas.mpl_connect('key_release_event', handle_key_release)
    
    threading.Thread(target=start_async_loop, daemon=True).start()

    ani = animation.FuncAnimation(fig, animate, init_func=init, interval=5, save_count=max_datapoints_to_display)
    plt.show()
