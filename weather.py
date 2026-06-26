#!/usr/bin/env python3
"""
Openweather - Termux OpenWeather CLI
Author: Mraprguild

Features:
- Current weather by city
- 5 day / 3 hour forecast
- Interactive Country > State > City > Village selector
- Safe API key loading from environment or config file
- No external Python packages required
"""

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

APP_NAME = "Openweather"
PROJECT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = Path.home() / ".config" / "mrapweather" / "config.env"
LOCATIONS_FILE = PROJECT_DIR / "data" / "locations.json"
WEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"
GEO_BASE_URL = "https://api.openweathermap.org/geo/1.0"


def read_api_key() -> str:
    """Read API key from environment first, then config file."""
    key = os.getenv("OPENWEATHER_API_KEY", "").strip()
    if key:
        return key

    if CONFIG_FILE.exists():
        for line in CONFIG_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("OPENWEATHER_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")

    return ""


def request_json(url: str) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=25) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        try:
            body = json.loads(error.read().decode("utf-8"))
            message = body.get("message", "Unknown OpenWeather error")
        except Exception:
            message = f"HTTP {error.code}"
        print(f"❌ OpenWeather API error: {message}")
        sys.exit(1)
    except urllib.error.URLError as error:
        print(f"❌ Network error: {error}")
        sys.exit(1)
    except json.JSONDecodeError:
        print("❌ Invalid JSON response from OpenWeather.")
        sys.exit(1)


def request_json_list(url: str) -> list:
    data = request_json(url)
    if isinstance(data, list):
        return data
    return []


def unit_symbol(units: str) -> str:
    if units == "imperial":
        return "°F"
    if units == "standard":
        return "K"
    return "°C"


def wind_symbol(units: str) -> str:
    if units == "imperial":
        return "mph"
    return "m/s"


def show_header(title: str):
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"🌦  {APP_NAME.upper()} - {title}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


def show_current(data: dict, units: str):
    symbol = unit_symbol(units)
    wind_unit = wind_symbol(units)

    city = data.get("name", "Unknown")
    country = data.get("sys", {}).get("country", "")
    weather = data.get("weather", [{}])[0]
    main = data.get("main", {})
    wind = data.get("wind", {})

    show_header("CURRENT WEATHER")
    print(f"📍 Location     : {city}, {country}")
    print(f"☁️  Condition    : {weather.get('description', 'N/A').title()}")
    print(f"🌡  Temperature  : {main.get('temp', 'N/A')}{symbol}")
    print(f"🤔 Feels Like   : {main.get('feels_like', 'N/A')}{symbol}")
    print(f"⬇️  Min Temp     : {main.get('temp_min', 'N/A')}{symbol}")
    print(f"⬆️  Max Temp     : {main.get('temp_max', 'N/A')}{symbol}")
    print(f"💧 Humidity     : {main.get('humidity', 'N/A')}%")
    print(f"🔽 Pressure     : {main.get('pressure', 'N/A')} hPa")
    print(f"💨 Wind Speed   : {wind.get('speed', 'N/A')} {wind_unit}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


def show_forecast(data: dict, units: str):
    symbol = unit_symbol(units)
    city_info = data.get("city", {})
    city = city_info.get("name", "Unknown")
    country = city_info.get("country", "")

    show_header("5 DAY / 3 HOUR FORECAST")
    print(f"📍 Location: {city}, {country}")
    print("")

    items = data.get("list", [])
    if not items:
        print("No forecast rows found.")
        return

    for row in items:
        dt_txt = row.get("dt_txt", "")
        temp = row.get("main", {}).get("temp", "N/A")
        humidity = row.get("main", {}).get("humidity", "N/A")
        desc = row.get("weather", [{}])[0].get("description", "N/A").title()
        print(f"📅 {dt_txt} | 🌡 {temp}{symbol} | 💧 {humidity}% | {desc}")

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


def build_weather_url(endpoint: str, api_key: str, units: str, city: str = "", lat: str = "", lon: str = "", limit: int = 0) -> str:
    params = {"appid": api_key, "units": units}

    if lat and lon:
        params["lat"] = lat
        params["lon"] = lon
    elif city:
        params["q"] = city
    else:
        print("❌ Provide city or latitude/longitude.")
        sys.exit(1)

    if limit:
        params["cnt"] = str(limit)

    return f"{WEATHER_BASE_URL}/{endpoint}?{urllib.parse.urlencode(params)}"


def build_geo_url(api_key: str, query: str, country_code: str = "", limit: int = 5) -> str:
    q = query.strip()
    if country_code and country_code not in q:
        q = f"{q},{country_code}"

    params = {
        "q": q,
        "limit": str(limit),
        "appid": api_key,
    }
    return f"{GEO_BASE_URL}/direct?{urllib.parse.urlencode(params)}"


def load_locations() -> dict:
    if not LOCATIONS_FILE.exists():
        return {"countries": []}

    try:
        return json.loads(LOCATIONS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"countries": []}


def choose_from_list(title: str, items: list, label_key: str = "name"):
    print("")
    print(f"📌 Select {title}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    for index, item in enumerate(items, start=1):
        if isinstance(item, dict):
            label = item.get(label_key, "Unknown")
        else:
            label = str(item)
        print(f"{index}. {label}")
    print("0. Manual type")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    while True:
        choice = input(f"Enter {title} number: ").strip()
        if choice == "0":
            manual = input(f"Type {title}: ").strip()
            return manual

        if choice.isdigit():
            number = int(choice)
            if 1 <= number <= len(items):
                return items[number - 1]

        print("❌ Invalid choice. Try again.")


def ask_yes_no(question: str, default: str = "y") -> bool:
    answer = input(f"{question} [{'Y/n' if default == 'y' else 'y/N'}]: ").strip().lower()
    if not answer:
        answer = default
    return answer.startswith("y")


def interactive_location_select(api_key: str):
    locations = load_locations()
    countries = locations.get("countries", [])

    show_header("LOCATION SELECT")
    print("Select Country → State → City → Village")
    print("Tip: edit data/locations.json to add your own places.")
    print("")

    country_result = choose_from_list("Country", countries)
    if isinstance(country_result, dict):
        country_name = country_result.get("name", "")
        country_code = country_result.get("code", "")
        states = country_result.get("states", [])
    else:
        country_name = country_result
        country_code = input("Type country code, example IN, US, GB: ").strip().upper()
        states = []

    if states:
        state_result = choose_from_list("State", states)
    else:
        state_result = input("Type State: ").strip()

    if isinstance(state_result, dict):
        state_name = state_result.get("name", "")
        cities = state_result.get("cities", [])
    else:
        state_name = state_result
        cities = []

    if cities:
        city_result = choose_from_list("City", cities)
    else:
        city_result = input("Type City: ").strip()

    if isinstance(city_result, dict):
        city_name = city_result.get("name", "")
        villages = city_result.get("villages", [])
    else:
        city_name = city_result
        villages = []

    use_village = ask_yes_no("Select village/area also?", "y")
    village_name = ""

    if use_village:
        if villages:
            village_result = choose_from_list("Village / Area", villages)
            village_name = village_result if isinstance(village_result, str) else str(village_result)
        else:
            village_name = input("Type Village / Area: ").strip()

    print("")
    show_header("SELECTED LOCATION")
    print(f"🌍 Country : {country_name} ({country_code})")
    print(f"🏞 State   : {state_name}")
    print(f"🏙 City    : {city_name}")
    if village_name:
        print(f"🏡 Village : {village_name}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # Use most specific place first. If village is not found by OpenWeather geocoding,
    # automatically fallback to city, state, country.
    search_candidates = []
    if village_name:
        search_candidates.append(f"{village_name},{city_name},{state_name}")
        search_candidates.append(f"{village_name},{state_name}")
    search_candidates.append(f"{city_name},{state_name}")
    search_candidates.append(city_name)

    resolved = None
    for query in search_candidates:
        geo_url = build_geo_url(api_key, query, country_code, limit=5)
        results = request_json_list(geo_url)
        if results:
            resolved = results[0]
            break

    if not resolved:
        print("❌ Location not found in OpenWeather geocoding.")
        print("Try manual city command:")
        print(f'  mrapweather current --city "{city_name},{country_code}"')
        sys.exit(1)

    lat = str(resolved.get("lat"))
    lon = str(resolved.get("lon"))
    resolved_name = resolved.get("name", city_name)
    resolved_state = resolved.get("state", state_name)
    resolved_country = resolved.get("country", country_code)

    print("")
    print("✅ OpenWeather location matched:")
    print(f"📍 {resolved_name}, {resolved_state}, {resolved_country}")
    print(f"🧭 lat={lat}, lon={lon}")
    print("")

    return {
        "lat": lat,
        "lon": lon,
        "display": f"{resolved_name}, {resolved_state}, {resolved_country}",
    }


def run_weather(mode: str, api_key: str, units: str, city: str = "", lat: str = "", lon: str = "", limit: int = 10):
    endpoint = "weather" if mode == "current" else "forecast"
    request_limit = limit if mode == "forecast" else 0
    url = build_weather_url(
        endpoint=endpoint,
        api_key=api_key,
        units=units,
        city=city,
        lat=lat,
        lon=lon,
        limit=request_limit
    )
    data = request_json(url)

    if mode == "forecast":
        show_forecast(data, units)
    else:
        show_current(data, units)


def main():
    parser = argparse.ArgumentParser(
        prog="mrapweather",
        description="Termux OpenWeather command line weather app."
    )

    parser.add_argument(
        "mode",
        nargs="?",
        default="current",
        choices=["current", "forecast", "select"],
        help="Use current, forecast, or select mode."
    )
    parser.add_argument("-c", "--city", help='City name, example: "Chennai,IN"')
    parser.add_argument("--lat", help="Latitude, example: 13.0827")
    parser.add_argument("--lon", help="Longitude, example: 80.2707")
    parser.add_argument("-u", "--units", default="metric", choices=["metric", "imperial", "standard"],
                        help="metric = Celsius, imperial = Fahrenheit, standard = Kelvin")
    parser.add_argument("--limit", type=int, default=10,
                        help="Forecast rows to show. Each row is about 3 hours. Default: 10")

    args = parser.parse_args()
    api_key = read_api_key()

    if not api_key:
        print("❌ Missing OpenWeather API key.")
        print("")
        print("Set key with:")
        print("  mrapweather-key YOUR_API_KEY")
        print("")
        print("Or manually:")
        print('  export OPENWEATHER_API_KEY="YOUR_API_KEY"')
        sys.exit(1)

    if args.mode == "select":
        location = interactive_location_select(api_key)

        print("")
        print("1. Current weather")
        print("2. Forecast")
        weather_choice = input("Select weather type: ").strip()

        mode = "forecast" if weather_choice == "2" else "current"
        run_weather(
            mode=mode,
            api_key=api_key,
            units=args.units,
            lat=location["lat"],
            lon=location["lon"],
            limit=args.limit
        )
        return

    run_weather(
        mode=args.mode,
        api_key=api_key,
        units=args.units,
        city=args.city or "",
        lat=args.lat or "",
        lon=args.lon or "",
        limit=args.limit
    )


if __name__ == "__main__":
    main()
