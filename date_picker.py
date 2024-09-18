import tkinter as tk
from tkinter import ttk
from tkcalendar import Calendar
from datetime import datetime


def get_selected_date():
    selected_date = cal.get_date()
    root.withdraw()  # Hide the popup window

    selected_date = datetime.strptime(selected_date, "%m/%d/%y")
    # Format the datetime object to the desired format
    selected_date = selected_date.strftime("%Y-%m-%d")
    print("Selected Date:", selected_date)

    return selected_date


# Create the main window
root = tk.Tk()
root.title("Date Selection")

# Create a Calendar widget
cal = Calendar(root, selectmode="day", year=2024, month=1, day=1)

# Add an "OK" button to get the selected date
ok_button = ttk.Button(root, text="OK", command=get_selected_date)

# Pack the Calendar and OK button
cal.pack(padx=10, pady=10)
ok_button.pack(pady=10)

# Start the main loop
root.mainloop()
