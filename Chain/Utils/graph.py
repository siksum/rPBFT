import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load the Excel file
file_path = '../data/240830-115211-rpbft-latency-data.xlsx'  # Update with your file path
df = pd.read_excel(file_path)

# Assume the columns are named 'Time', 'Latency', and 'Consensus success rate'
time = df['Time']
latency = df['Latency']
# consensus_rate = df['Consensus success rate']

# Create the figure and axes
fig, ax1 = plt.subplots()

# Plot Latency on the left y-axis
ax1.plot(time, latency, color='teal', label='Latency')
ax1.set_xlabel('Time')
ax1.set_ylabel('Latency (s)', color='teal')
ax1.tick_params(axis='y', labelcolor='teal')
ax1.set_ylim(0, 0.1)
ax1.set_yticks(np.arange(0, 0.1, 0.015))
# Create a second y-axis for the Consensus success rate
# ax2 = ax1.twinx()
# ax2.plot(time, color='blue', label='Consensus success rate')
# ax2.set_ylabel('Consensus success rate (%)', color='blue')
# ax2.tick_params(axis='y', labelcolor='blue')

# Set the title
plt.title('Infant Mortality')

# Show grid and layout adjustment
ax1.grid(True)
fig.tight_layout()

# Show the plot
plt.show()
