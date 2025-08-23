import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, RadioButtons
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
    required_columns = ['Time', 'Player', 'Fuel_Percent', 'Speed', 'Gun_Ammo']
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

    # Initial selections
    current_player = players[0]
    charts = ['Fuel', 'Speed', 'Gun']
    current_chart_index = 0

    # Function to plot the current chart
    def plot_current():
        plt.clf()  # Clear the current figure
        df_player = df[df['Player'] == current_player]
        
        if charts[current_chart_index] == 'Fuel':
            plt.plot(df_player['Time_sec'], df_player['Fuel_Percent'])
            plt.title(f'Fuel over Time for {current_player}')
            plt.xlabel('Time (seconds)')
            plt.ylabel('Fuel Percent')
        elif charts[current_chart_index] == 'Speed':
            plt.plot(df_player['Time_sec'], df_player['Speed'])
            plt.title(f'Speed over Time for {current_player}')
            plt.xlabel('Time (seconds)')
            plt.ylabel('Speed')
        elif charts[current_chart_index] == 'Gun':
            plt.plot(df_player['Time_sec'], df_player['Gun_Ammo'])
            plt.title(f'Gun Ammo over Time for {current_player}')
            plt.xlabel('Time (seconds)')
            plt.ylabel('Gun Ammo')
        
        plt.draw()

    # Function for next chart
    def next_chart(event):
        global current_chart_index
        current_chart_index = (current_chart_index + 1) % len(charts)
        plot_current()

    # Function for previous chart
    def prev_chart(event):
        global current_chart_index
        current_chart_index = (current_chart_index - 1) % len(charts)
        plot_current()

    # Function to change player
    def change_player(label):
        global current_player
        current_player = label
        plot_current()

    # Set up the figure and adjust layout for widgets
    fig, ax = plt.subplots()
    plt.subplots_adjust(left=0.25, bottom=0.2)

    # Initial plot
    plot_current()

    # Add buttons for cycling charts
    ax_prev = plt.axes([0.7, 0.05, 0.1, 0.075])
    ax_next = plt.axes([0.81, 0.05, 0.1, 0.075])
    button_next = Button(ax_next, 'Next Chart')
    button_next.on_clicked(next_chart)
    button_prev = Button(ax_prev, 'Prev Chart')
    button_prev.on_clicked(prev_chart)

    # Add radio buttons for player selection
    ax_radio = plt.axes([0.025, 0.1, 0.2, 0.8], facecolor='lightgoldenrodyellow')
    radio = RadioButtons(ax_radio, players, active=0)
    radio.on_clicked(change_player)

    # Show the plot
    plt.show()

except Exception as e:
    print(f"An unexpected error occurred: {str(e)}")
    input("Press Enter to exit...")
    sys.exit(1)
