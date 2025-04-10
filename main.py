import os
import telebot
import requests
import json
import re
from dotenv import load_dotenv
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

load_dotenv()
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

def load_locations_file():
    try:
        with open('locations.txt', 'r') as file:
            content = file.read()
            # Remove comments (lines starting with # and inline comments)
            content = re.sub(r'#.*$', '', content, flags=re.MULTILINE)
            # Parse the cleaned content
            return eval(content)
    except Exception as e:
        print(f"❌ Error loading location data: {e}")
        # Return empty dict if file can't be loaded
        return {}

# Load locations
LOCATIONS = load_locations_file()
if not LOCATIONS:
    print("⚠️ Warning: No locations loaded. Check your locations.txt file.")


class WeatherBot:
    def __init__(self, token):
        self.bot = telebot.TeleBot(token)
        self.setup_handlers()

    def setup_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def send_welcome(message):
            markup = InlineKeyboardMarkup(row_width=2)
            markup.add(
                InlineKeyboardButton("🌤️ Get Weather", callback_data="get_weather"),
                InlineKeyboardButton("❓ Help", callback_data="help")
            )
            
            welcome_text = (
                "👋 Hello! I'm your Weather Bot!\n\n"
                "🌤️ I can provide you with the current weather of INDIAN Cities/States\n\n"
                "Please select an option from the menu below:"
            )
            self.bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

        @self.bot.message_handler(commands=['help'])
        def help_command(message):
            help_text = (
                "📖 How to use this bot:\n\n"
                "1. Click on '🌤️ Get Weather' to see the list of available cities\n"
                "2. Select a city from the list\n"
                "3. The bot will show you the current weather for that city\n\n"
                "You can also use these commands:\n"
                "/start - Show the main menu\n"
                "/help - Show this help message"
            )
            self.bot.send_message(message.chat.id, help_text)

        @self.bot.callback_query_handler(func=lambda call: True)
        def callback_query(call):
            if call.data == "get_weather":
                self.show_categories(call.message)
            elif call.data == "help":
                help_text = (
                    "📖 How to use this bot:\n\n"
                    "1. Click on '🌤️ Get Weather' to see the list of available cities\n"
                    "2. Select a city from the list\n"
                    "3. The bot will show you the current weather for that city\n\n"
                    "You can also use these commands:\n"
                    "/start - Show the main menu\n"
                    "/help - Show this help message"
                )
                self.bot.send_message(call.message.chat.id, help_text)
            elif call.data == "cities_north":
                self.show_region_cities(call.message, "North", 
                    ["delhi", "chandigarh", "lucknow", "jaipur", "kanpur", 
                    "agra", "varanasi", "shimla", "dehradun", "amritsar"])
            elif call.data == "cities_south":
                self.show_region_cities(call.message, "South", 
                    ["bangalore", "hyderabad", "chennai", "kochi", 
                    "thiruvananthapuram", "coimbatore", "mysuru", "visakhapatnam"])
            elif call.data == "cities_east":
                self.show_region_cities(call.message, "East", 
                    ["kolkata", "patna", "ranchi", "bhubaneswar", 
                    "guwahati", "imphal", "gangtok"])
            elif call.data == "cities_west":
                self.show_region_cities(call.message, "West", 
                    ["mumbai", "pune", "ahmedabad", "surat", 
                    "vadodara", "nagpur", "panaji"])
            elif call.data == "cities_central":
                self.show_region_cities(call.message, "Central", 
                    ["bhopal", "indore", "raipur"])
            elif call.data == "states":
                self.show_states(call.message)
            elif call.data == "uts":
                self.show_union_territories(call.message)
            elif call.data.startswith("city_"):
                city_key = call.data[5:]  # Remove "city_" prefix
                if city_key in LOCATIONS:
                    location_data = LOCATIONS[city_key]
                    weather_report = self.get_weather(
                        location_data["lat"],
                        location_data["lon"],
                        location_data["name"]
                    )
                    self.bot.send_message(call.message.chat.id, weather_report)
                    
                    # Add prompt to check another location
                    self.ask_for_another_check(call.message.chat.id)
                else:
                    self.bot.send_message(call.message.chat.id, "❌ Invalid city selection!")
            
            # Answer callback query to remove the loading state
            self.bot.answer_callback_query(call.id)

    def ask_for_another_check(self, chat_id):
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("✅ Check another location", callback_data="get_weather"),
            InlineKeyboardButton("🏠 Back to main menu", callback_data="back_to_main")
        )
        
        self.bot.send_message(
            chat_id,
            "Would you like to check weather for another location?",
            reply_markup=markup
        )

    def show_categories(self, message):
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("🏙️ North India", callback_data="cities_north"),
            InlineKeyboardButton("🏙️ South India", callback_data="cities_south"),
            InlineKeyboardButton("🏙️ East India", callback_data="cities_east"),
            InlineKeyboardButton("🏙️ West India", callback_data="cities_west"),
            InlineKeyboardButton("🏙️ Central India", callback_data="cities_central"),
            InlineKeyboardButton("🗺️ States", callback_data="states"),
            InlineKeyboardButton("🏛️ Union Territories", callback_data="uts"),
            InlineKeyboardButton("🏠 Back to main menu", callback_data="back_to_main")
        )
        
        self.bot.send_message(
            message.chat.id,
            "📍 Please select a region:",
            reply_markup=markup
        )

    def show_region_cities(self, message, region_name, city_keys):
        markup = InlineKeyboardMarkup(row_width=2)
        
        for city_key in city_keys:
            if city_key in LOCATIONS:
                markup.add(InlineKeyboardButton(LOCATIONS[city_key]["name"], callback_data=f"city_{city_key}"))
        
        # Add back button
        markup.add(InlineKeyboardButton("◀️ Back", callback_data="get_weather"))
        
        self.bot.send_message(
            message.chat.id,
            f"📍 Cities in {region_name} India:",
            reply_markup=markup
        )

    def show_states(self, message):
        markup = InlineKeyboardMarkup(row_width=2)
        state_keys = [
            "andhra_pradesh", "arunachal_pradesh", "assam", "bihar", 
            "chhattisgarh", "goa", "gujarat", "haryana", "himachal_pradesh", 
            "jharkhand", "karnataka", "kerala", "madhya_pradesh", "maharashtra", 
            "manipur", "meghalaya", "mizoram", "nagaland", "odisha", "punjab", 
            "rajasthan", "sikkim", "tamil_nadu", "telangana", "tripura", 
            "uttar_pradesh", "uttarakhand", "west_bengal"
        ]
        
        for state_key in state_keys:
            if state_key in LOCATIONS:
                markup.add(InlineKeyboardButton(LOCATIONS[state_key]["name"], callback_data=f"city_{state_key}"))
        
        # Add back button
        markup.add(InlineKeyboardButton("◀️ Back", callback_data="get_weather"))
        
        self.bot.send_message(
            message.chat.id,
            "📍 Select a state:",
            reply_markup=markup
        )

    def show_union_territories(self, message):
        markup = InlineKeyboardMarkup(row_width=2)
        ut_keys = [
            "andaman_and_nicobar", "chandigarh_ut", "dadra_nagar_haveli", 
            "daman_and_diu", "delhi_ut", "jammu_and_kashmir", "ladakh", 
            "lakshadweep", "puducherry"
        ]
        
        for ut_key in ut_keys:
            if ut_key in LOCATIONS:
                markup.add(InlineKeyboardButton(LOCATIONS[ut_key]["name"], callback_data=f"city_{ut_key}"))
        
        # Add back button
        markup.add(InlineKeyboardButton("◀️ Back", callback_data="get_weather"))
        
        self.bot.send_message(
            message.chat.id,
            "📍 Select a Union Territory:",
            reply_markup=markup
        )

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