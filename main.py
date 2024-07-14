from tkinter import *
from tkinter import colorchooser, font, messagebox, simpledialog
import requests
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from configure import API_KEY, BASE_URL

'''
This app shows weather data for cities, using the OpenWeatherMap API. 
It stores the data in a SQLite database and displays it using matplotlib charts.
'''

# initialize the SQLite database and create the hourly_weather table if it doesn't exist
def initialize_db():
    try:
        conn = sqlite3.connect('weather.db')
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS hourly_weather (
                          id INTEGER PRIMARY KEY AUTOINCREMENT,
                          city_name TEXT,
                          temperature REAL,
                          weather_description TEXT,
                          timestamp TEXT)''')
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"An error occurred: {e}")
        status_var.set(f"Database error: {e}")

# fetch and store weather data for a specified city
def fill_command():
    try:
        city_name = simpledialog.askstring("City Name", "Enter the city name:")
        if not city_name:
            messagebox.showerror("Error", "Please enter a city name")
            return

        # Geocode the city name to get latitude and longitude
        geocode_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={API_KEY}"
        geocode_response = requests.get(geocode_url).json()
        if len(geocode_response) == 0:
            messagebox.showerror("Error", "City not found")
            status_var.set("City not found.")
            return

        lat = round(geocode_response[0]['lat'], 2)
        lon = round(geocode_response[0]['lon'], 2)
        print(f'City: {city_name} -> lat: {lat}, lon: {lon}')  # debug

        weather_data = fetch_hourly_weather(lat, lon)
        if weather_data:
            store_hourly_weather(weather_data, city_name)
            status_var.set(f"Weather data for {city_name} has been stored in the database.")
            messagebox.showinfo("Success", f"Weather data for {city_name} has been stored in the database.")
            update_display()
        else:
            status_var.set("Failed to fetch data for the specified city.")
            messagebox.showerror("Error", "Failed to fetch data for the specified city")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
        status_var.set(f"An error occurred: {e}")

# fetch hourly weather data for the given latitude and longitude from the OpenWeatherMap API
def fetch_hourly_weather(lat, lon):
    url = f"{BASE_URL}?lat={lat}&lon={lon}&exclude=minutely,daily,alerts&units=metric&appid={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
        data = response.json()
        return data
    except requests.exceptions.HTTPError as http_err:
        messagebox.showerror("HTTP Error", f"HTTP error occurred: {http_err}")
        status_var.set(f"HTTP error occurred: {http_err}")
    except requests.exceptions.ConnectionError as conn_err:
        messagebox.showerror("Connection Error", f"Connection error occurred: {conn_err}")
        status_var.set(f"Connection error occurred: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        messagebox.showerror("Timeout Error", f"Timeout error occurred: {timeout_err}")
        status_var.set(f"Timeout error occurred: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        messagebox.showerror("Error", f"An error occurred: {req_err}")
        status_var.set(f"An error occurred: {req_err}")
    return None

# store hourly weather data in the SQLite database
def store_hourly_weather(data, city_name):
    try:
        conn = sqlite3.connect('weather.db')
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS hourly_weather (
                          id INTEGER PRIMARY KEY AUTOINCREMENT,
                          city_name TEXT,
                          temperature REAL,
                          weather_description TEXT,
                          timestamp TEXT)''')
        
        for hour_data in data['hourly']:
            timestamp = datetime.fromtimestamp(hour_data['dt'])
            cursor.execute('''INSERT INTO hourly_weather (
                              city_name, temperature, weather_description, timestamp)
                              VALUES (?, ?, ?, ?)''',
                           (city_name, hour_data['temp'], hour_data['weather'][0]['description'], timestamp))

        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"An error occurred: {e}")
        status_var.set(f"Database error: {e}")

# clear all data from the hourly_weather table in the database
def clear_command():
    try:
        result = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete all data from the database?")
        if result:
            conn = sqlite3.connect('weather.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM hourly_weather')
            conn.commit()
            conn.close()
            status_var.set("The database has been cleared.")
            messagebox.showinfo("Success", "The database has been cleared")
            update_display()
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"An error occurred: {e}")
        status_var.set(f"Database error: {e}")

# change the background color of the application
def change_background(root):
    try:
        color = colorchooser.askcolor()[1]
        if color:
            root.config(bg=color)
            status_var.set(f"Background color changed to {color}.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
        status_var.set(f"An error occurred: {e}")

# change the font of the application
def change_font(widget, font_name, font_var):
    try:
        if isinstance(widget, Menu):
            return
        font_var.set(font_name)
        custom_font = font.Font(family=font_name, size=11)
        widget.configure(font=custom_font)
        status_var.set(f"Font changed to {font_name}.")
        for child in widget.winfo_children():
            change_font(child, font_name, font_var)
    except TclError as e:
        messagebox.showerror("Font Error", f"An error occurred: {e}")
        status_var.set(f"Font error: {e}")

# change the text color of the application
def change_text_color(widget, color=None):
    try:
        if isinstance(widget, Menu) or not hasattr(widget, 'cget'):
            return
        if color:
            widget.configure(fg=color)
            status_var.set(f"Text color changed to {color}.")
        for child in widget.winfo_children():
            change_text_color(child, color)
    except TclError as e:
        messagebox.showerror("Color Error", f"An error occurred: {e}")
        status_var.set(f"Color error: {e}")

# reset the application to default settings
def reset_to_default(widget, font_var):
    try:
        if isinstance(widget, Menu):
            return
        widget.config(bg='SystemButtonFace')
        default_font = font.Font(family="Helvetica")
        widget.config(fg='black', font=default_font)
        for child in widget.winfo_children():
            reset_to_default(child, font_var)
        font_var.set("Helvetica")
        status_var.set("Reset to default settings.")
    except TclError as e:
        messagebox.showerror("Reset Error", f"An error occurred: {e}")
        status_var.set(f"Reset error: {e}")

def create_menu(root, font_var):
    """
    Create the menu bar with options for filling the database, clearing the database, and changing settings.
    """
    app_menu = Menu(root)
    root.config(menu=app_menu)

    # Fill the database with data downloaded from the Internet
    fill_menu = Menu(app_menu)
    app_menu.add_cascade(label='Fill', menu=fill_menu)
    fill_menu.add_command(label='Add data to the database', command=fill_command)

    # Clear the content of the database.
    clear_menu = Menu(app_menu)
    app_menu.add_cascade(label='Clear', menu=clear_menu)
    clear_menu.add_command(label='Clear the database', command=clear_command)

    # Set some additional options or properties for your app (e.g. colours, fonts etc.).
    options_menu = Menu(app_menu)
    app_menu.add_cascade(label='Options', menu=options_menu)
        # Change background color
    options_menu.add_command(label='Set the background colour', command=lambda: change_background(root))
        # Change font
    font_names = ["Helvetica", "Arial", "Times New Roman", "Courier New", "Verdana", "Impact"]
    font_menu = Menu(options_menu)
    for font_name in font_names:
        font_menu.add_radiobutton(label=font_name, command=lambda f=font_name: change_font(root, f, font_var), variable=font_var, value=font_name)
    options_menu.add_cascade(label='Set the font', menu=font_menu)
        # Change text color
    options_menu.add_command(label='Set the text colour', command=lambda: change_text_color(root, colorchooser.askcolor()[1]))
        # Reset to default
    options_menu.add_command(label='Reset to default', command=lambda: reset_to_default(root, font_var))

def calculate_average_temperature():
    """
    Calculate and display the average temperature from the stored data.
    """
    try:
        conn = sqlite3.connect('weather.db')
        cursor = conn.cursor()
        cursor.execute('SELECT AVG(temperature) FROM hourly_weather')
        avg_temp = cursor.fetchone()[0]
        conn.close()
        if avg_temp is not None:
            aggregation_label.config(text=f"Average Temperature: {avg_temp:.2f}°C")
            status_var.set("Calculated the average temperature.")
        else:
            aggregation_label.config(text="Average Temperature: N/A")
            status_var.set("No data available to calculate.")
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"An error occurred: {e}")
        status_var.set(f"Database error: {e}")

# Display a chart of temperature data over time for different cities
def display_chart():
    try:
        conn = sqlite3.connect('weather.db')
        cursor = conn.cursor()
        cursor.execute('SELECT city_name, timestamp, temperature FROM hourly_weather ORDER BY city_name, timestamp')
        data = cursor.fetchall()
        conn.close()
        
        fig, ax = plt.subplots()
        if data:
            city_data = {}
            
            for city_name, timestamp, temperature in data:
                if city_name not in city_data:
                    city_data[city_name] = {'times': [], 'temps': []}
                city_data[city_name]['times'].append(datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S'))
                city_data[city_name]['temps'].append(temperature)

            for city_name, values in city_data.items():
                ax.plot(values['times'], values['temps'], marker='o', label=city_name)

            ax.set(xlabel='Time', ylabel='Temperature (°C)', title='Temperature Over Time')
            ax.legend()
            ax.grid()

        else:
            ax.set(xlabel='Time', ylabel='Temperature (°C)', title='Temperature Over Time')
            ax.text(0.5, 0.5, 'No data available', horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)

        for widget in chart_frame.winfo_children():
            widget.destroy()

        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
        status_var.set("Displayed the temperature chart.")
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"An error occurred: {e}")
        status_var.set(f"Database error: {e}")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
        status_var.set(f"An error occurred: {e}")

# update the display with the average temperature and the temperature chart
def update_display():
    calculate_average_temperature()
    display_chart()

# main function to run the Tkinter application
def run():
    global aggregation_label, status_var, chart_frame

    root = Tk()
    root.title('Weather App')
    root.geometry('800x600')

    font_var = StringVar(value="Helvetica")
    default_font = font.nametofont("TkDefaultFont")
    default_font.configure(family="Helvetica", size=11)
    root.option_add("*Font", default_font)

    status_var = StringVar(value="Ready")

    create_menu(root, font_var)

    main_frame = Frame(root)
    main_frame.pack(pady=10, padx=10, fill=BOTH, expand=True)

    Button(main_frame, text="Calculate Average Temperature", command=calculate_average_temperature).pack(pady=5)
    aggregation_label = Label(main_frame, text="Average Temperature: N/A")
    aggregation_label.pack(pady=5)

    Button(main_frame, text="Display Temperature Chart", command=display_chart).pack(pady=5)
    
    chart_frame = Frame(main_frame)
    chart_frame.pack(pady=10, padx=10, fill=BOTH, expand=True)

    status_label = Label(root, textvariable=status_var, bd=1, relief=SUNKEN, anchor=W)
    status_label.pack(side=BOTTOM, fill=X)

    initialize_db()
    update_display()
    root.mainloop()

if __name__ == '__main__':
    run()
