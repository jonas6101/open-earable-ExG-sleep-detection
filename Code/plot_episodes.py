import os
import pandas as pd
import matplotlib.pyplot as plt
from scipy.fftpack import fft
import numpy as np

# Load the data
file_path = 'recordings/OpenEarableEEG_BLE_20240901_020844.csv'  # Replace with your actual file path
data = pd.read_csv(file_path)

# Convert the time column to datetime
data['time'] = pd.to_datetime(data['time'])

# Set the time as the index
data.set_index('time', inplace=True)

# Define the time interval for each episode
time_interval = '30s'

# Resample the data into 30-second intervals
resampled_data = data['filtered_data'].resample(time_interval)

# Create a directory to save the plots
output_dir = 'plots_with_frequency'
os.makedirs(output_dir, exist_ok=True)

# Define the limits for the plots
time_domain_ylim = (-200, 200)  # Adjust this based on your data's range
frequency_band_limit = (0.5, 40)  # EEG relevant frequency range in Hz

# Create individual plots for each 30-second episode
for i, (interval, episode) in enumerate(resampled_data):
    plt.figure(figsize=(12, 8))

    # Time-domain plot
    plt.subplot(2, 1, 1)
    plt.plot(episode.index, episode, label='Filtered Data')
    plt.title(f'Episode {i+1}: {interval} to {interval + pd.to_timedelta(time_interval)} (Time Domain)')
    plt.xlabel('Time')
    plt.ylabel('Filtered Data Value')
    plt.ylim(time_domain_ylim)  # Set consistent y-axis limits
    plt.legend()

    # Frequency-domain plot
    plt.subplot(2, 1, 2)
    n = len(episode)
    freq = np.fft.fftfreq(n, d=(episode.index[1] - episode.index[0]).total_seconds())
    fft_values = np.abs(fft(episode.to_numpy()))  # Convert to NumPy array

    # Filter the frequencies to the relevant EEG band
    relevant_freq_indices = np.where((freq >= frequency_band_limit[0]) & (freq <= frequency_band_limit[1]))
    plt.plot(freq[relevant_freq_indices], fft_values[relevant_freq_indices], label='Frequency Spectrum')
    plt.title('Frequency Domain')
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Amplitude')
    plt.xlim(frequency_band_limit)  # Limit x-axis to EEG frequency range
    plt.legend()

    # Save the plot
    plot_filename = os.path.join(output_dir, f'episode_{i+1}.png')
    plt.savefig(plot_filename)
    plt.close()

print(f"Plots saved in the '{output_dir}' directory.")

