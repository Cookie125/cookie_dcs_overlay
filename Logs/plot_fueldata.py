
import pandas as pd
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import FuncFormatter
import sys
import os

# Check if the CSV file exists
csv_file = 'server-fueldata.csv'
if not os.path.exists(csv_file):
    print(f"Error: The file '{csv_file}' was not found in the current directory ({os.getcwd()}).")
    print("Please ensure the CSV file is in the same directory as this script or provide the correct path.")
    input("Press Enter to exit...")
    sys.exit(1)

try:
    # Load the CSV file
    df = pd.read_csv(csv_file)

    # Function to convert time string to seconds
    def time_to_seconds(t):
        try:
            h, m, s = map(int, t.split(':'))
            return h * 3600 + m * 60 + s
        except ValueError:
            print(f"Error: Invalid time format in CSV: {t}")
            return 0

    # Add a Time_sec column
    df['Time_sec'] = df['Time'].apply(time_to_seconds)

    # Check if required columns exist
    required_columns = ['Time', 'Player', 'Fuel_Percent', 'Speed', 'Gun_Ammo', 'Pos_X', 'Pos_Y', 'Pos_Z']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"Error: Missing required columns in CSV: {missing_columns}")
        input("Press Enter to exit...")
        sys.exit(1)

    # Get unique players
    players = df['Player'].unique().tolist()
    if not players:
        print("Error: No players found in the CSV file.")
        input("Press Enter to exit...")
        sys.exit(1)

    # Charts list
    charts = ['Fuel', 'Speed', 'Gun', 'Position']

    # Create the Tkinter window
    root = tk.Tk()
    root.title("Player Data Viewer")
    root.geometry("1000x700")  # Set a larger initial window size

    # Control frame for dropdown and buttons
    control_frame = tk.Frame(root)
    control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

    # Player selection dropdown
    tk.Label(control_frame, text="Select Player:", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
    player_combo = ttk.Combobox(control_frame, values=players, state="readonly", width=30, font=("Arial", 12))
    player_combo.current(0)
    player_combo.pack(side=tk.LEFT, padx=5)

    # Buttons for cycling charts
    prev_button = tk.Button(control_frame, text="Previous Chart", command=lambda: change_chart(-1), font=("Arial", 12))
    prev_button.pack(side=tk.LEFT, padx=5)
    next_button = tk.Button(control_frame, text="Next Chart", command=lambda: change_chart(1), font=("Arial", 12))
    next_button.pack(side=tk.LEFT, padx=5)

    # Matplotlib figure
    fig = plt.Figure(figsize=(8, 6))
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    # Track current chart index
    current_chart_index = 0

    # Function to format seconds to MM:SS
    def seconds_to_mmss(x, pos):
        mins = int(x // 60)
        secs = int(x % 60)
        return f"{mins:02d}:{secs:02d}"

    # Function to change chart
    def change_chart(direction):
        global current_chart_index
        current_chart_index = (current_chart_index + direction) % len(charts)
        update_plot()

    # Function to update the plot
    def update_plot(*args):
        current_player = player_combo.get()
        df_player = df[df['Player'] == current_player]
        chart = charts[current_chart_index]

        fig.clear()  # Clear the figure to switch between 2D and 3D

        if chart == 'Position':
            ax = fig.add_subplot(111, projection='3d')
            scatter = ax.scatter(df_player['Pos_X'], df_player['Pos_Y'], df_player['Pos_Z'], 
                                 c=df_player['Speed'], cmap='YlOrRd', marker='o')
            ax.set_title(f'3D Position for {current_player}', fontsize=14)
            ax.set_xlabel('Pos_X', fontsize=12)
            ax.set_ylabel('Pos_Y', fontsize=12)
            ax.set_zlabel('Pos_Z', fontsize=12)
            fig.colorbar(scatter, ax=ax, label='Speed (Yellow: Low, Red: High)')
        else:
            ax = fig.add_subplot(111)
            if chart == 'Fuel':
                ax.plot(df_player['Time_sec'], df_player['Fuel_Percent'], marker='o', linestyle='-')
                ax.set_title(f'Fuel over Time for {current_player}', fontsize=14)
                ax.set_xlabel('Time (MM:SS)', fontsize=12)
                ax.set_ylabel('Fuel Percent', fontsize=12)
            elif chart == 'Speed':
                ax.plot(df_player['Time_sec'], df_player['Speed'], marker='o', linestyle='-')
                ax.set_title(f'Speed over Time for {current_player}', fontsize=14)
                ax.set_xlabel('Time (MM:SS)', fontsize=12)
                ax.set_ylabel('Speed', fontsize=12)
            elif chart == 'Gun':
                ax.plot(df_player['Time_sec'], df_player['Gun_Ammo'], marker='o', linestyle='-')
                ax.set_title(f'Gun Ammo over Time for {current_player}', fontsize=14)
                ax.set_xlabel('Time (MM:SS)', fontsize=12)
                ax.set_ylabel('Gun Ammo', fontsize=12)

            ax.xaxis.set_major_formatter(FuncFormatter(seconds_to_mmss))
            ax.grid(True)

        canvas.draw()

    # Bind the combobox selection event
    player_combo.bind("<<ComboboxSelected>>", update_plot)

    # Initial plot update
    update_plot()

    # Run the Tkinter main loop
    root.mainloop()

except Exception as e:
    print(f"An unexpected error occurred: {str(e)}")
    input("Press Enter to exit...")
    sys.exit(1)
