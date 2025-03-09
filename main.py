import os
import telebot
import requests
import json
import ast
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

try:
    with open('locations.txt', 'r') as file:
        LOCATIONS = ast.literal_eval(file.read())
except Exception as e:
    print(f"❌ Error loading location data: {e}")
    LOCATIONS = {}


"""
locations_list = ""

# For location List
for location_info in LOCATIONS.values():
    location_name = location_info['name']
    locations_list += f"• {location_name}\n"
    
"""

class WeatherBot:
    def __init__(self, token):
        self.bot = telebot.TeleBot(token)
        self.setup_commands()

    def setup_commands(self):

        @self.bot.message_handler(content_types=['new_chat_members'])
        def welcomenew_member(message):
            for new_member in message.new_chat_members:
                welcome_text = f"""🎉 User {new_member.first_name}, Welcome to Weather Group. ☁️\n
                Type /start to get started"""
                self.bot.send_message(message.chat.id, welcome_text)

        @self.bot.message_handler(content_types=['left_chat_member'])
        def goodbyemember(message):
            left_member = message.left_chat_member
            goodbye_text = f"""👋 User {left_member.first_name}, we're sorry to see you go. 🌧️\n
            We hope you visit again soon!"""
            self.bot.send_message(message.chat.id, goodbye_text)


        @self.bot.message_handler(commands=['start'])
        def send_welcome(message):
            welcome_text = {
            "👋Hello! I'm your Weather Bot!\n\n"
            "🌤️ I can provide you with the current weather of INDIAN Cities/States\n\n"
            "\t/help - Get help on how to use me"
            }

            self.bot.send_message(message.chat.id, welcome_text)
        @self.bot.message_handler(commands=['help'])
        def send_welcome(message):
            welcome_text = {
            "Here's how to use me:\n\n"
            "📍 Just send me a city or state name like this:\n"
            "\t\t/weather delhi\n"
            "\t\t/weather mumbai\n\n"

            "Try it now! 🌤️"
            }

            self.bot.send_message(message.chat.id, welcome_text)

        @self.bot.message_handler(commands=['weather'])
        def handle_weather(message):
            try:
                parts = message.text.split()
                
                # Check if the user provided a location
                if len(parts) < 2:
                    self.bot.send_message(message.chat.id, "❌ Please provide a location after the /weather command.")
                    return
                
                location = parts[1].lower()

                # Check if the location exists in the locations dictionary
                if location not in LOCATIONS:
                    self.bot.send_message(message.chat.id, "❌ Unknown location! Please choose from the available locations.")
                    return

                location_data = LOCATIONS[location]
                latitude = location_data["lat"]
                longitude = location_data["lon"]

                # Get and send the weather report
                weather_report = self.get_weather(latitude, longitude, location_data["name"])
                self.bot.send_message(message.chat.id, weather_report)

            except Exception as e:
                self.bot.send_message(message.chat.id, f"❌ Oops! Something went wrong: {e}")

    def get_weather(self, latitude, longitude, location_name):
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current_weather": "true",
            "timezone": "auto"
        }

        try:
            response = requests.get(url, params=params)
            if response.status_code != 200:
                raise Exception(f"Failed to retrieve data. Status code: {response.status_code}")
            data = response.json()

            weather_conditions = {
                0: "Clear sky",
                1: "Mainly clear",
                2: "Partly cloudy",
                3: "Mostly cloudy",
                45: "Fog",
                48: "Depositing rime fog",
                51: "Light drizzle",
                53: "Moderate drizzle",
                55: "Dense drizzle",
                56: "Light freezing drizzle",
                57: "Dense freezing drizzle",
                61: "Light rain",
                63: "Moderate rain",
                65: "Heavy rain",
                66: "Light freezing rain",
                67: "Heavy freezing rain",
                71: "Light snow",
                73: "Moderate snow",
                75: "Heavy snow",
                77: "Snow grains",
                80: "Light rain showers",
                81: "Moderate rain showers",
                82: "Heavy rain showers",
                85: "Light snow showers",
                86: "Heavy snow showers",
                95: "Thunderstorms",
                96: "Thunderstorms with light hail",
                99: "Thunderstorms with heavy hail"
            }
            
            current_weather = data['current_weather']
            temperature = current_weather['temperature']
            wind_speed = current_weather['windspeed']
            wind_direction = current_weather['winddirection']
            weather_code = current_weather['weathercode']

            weather_condition = weather_conditions.get(weather_code, "Unknown weather condition")

            # Initialize weather_report before appending data
            weather_report = f"🌍 Current Weather for {location_name}\n"
            weather_report += f"""
            🌡️ Temperature: {temperature}°C
            💨 Wind Speed: {wind_speed} m/s
            🌬️ Wind Direction: {wind_direction}°
            🌤️ Condition: {weather_condition}

            """
            
            return weather_report

        except Exception as error:
            return f"❌ Sorry, I couldn't get the weather data for {location_name}: {str(error)}"

    def start(self):
        print("🤖 Weather Bot is now running! Press Ctrl+C to stop.")
        self.bot.polling(none_stop=True)

def main():
    try:
        print("🔄 Starting Weather Bot...")
        weather_bot = WeatherBot(BOT_TOKEN)
        weather_bot.start()

    except Exception as error:
        print(f"❌ Oops! Something went wrong: {error}")

if __name__ == "__main__":
    main()
