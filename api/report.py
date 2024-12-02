from kerykeion import Report as BaseReport
from zoneinfo import ZoneInfo
# import swisseph as swe
from datetime import datetime, timedelta
import pytz
from timezonefinder import TimezoneFinder
from django.templatetags.static import static

class Report(BaseReport):
    def __init__(self, instance):
        self.instance = instance
        self.ascendant_sign = self.instance.ascendant_sign
        self.ascendant_degree = self.instance.ascendant_degree
        self.house_names = {
            "First_House": 1,
            "Second_House": 2,
            "Third_House": 3,
            "Fourth_House": 4,
            "Fifth_House": 5,
            "Sixth_House": 6,
            "Seventh_House": 7,
            "Eighth_House": 8,
            "Ninth_House": 9,
            "Tenth_House": 10,
            "Eleventh_House": 11,
            "Twelfth_House": 12,
        }
        self.sign_names = {
            "Ari": "Aries",
            "Tau": "Taurus",
            "Gem": "Gemini",
            "Can": "Cancer",
            "Leo": "Leo",
            "Vir": "Virgo",
            "Lib": "Libra",
            "Sco": "Scorpio",
            "Sag": "Sagittarius",
            "Cap": "Capricorn",
            "Aqu": "Aquarius",
            "Pis": "Pisces"
        }

       
        self.planet_icons = {
            "Sun": static('images/planets/sun.svg'),
            "Moon": static('images/planets/moon.svg'),
            "Mercury": static('images/planets/mercury.svg'),
            "Venus": static('images/planets/venus.svg'),
            "Mars": static('images/planets/mars.svg'),
            "Jupiter": static('images/planets/jupiter.svg'),
            "Saturn": static('images/planets/saturn.svg'),
            "Rahu": static('images/planets/rahu.svg'),
            "Ketu": static('images/planets/ketu.svg')
        }

        self.sign_icons = {
            "Aries": static('images/signs/aries.svg'),
            "Taurus": static('images/signs/taurus.svg'),
            "Gemini": static('images/signs/gemini.svg'),
            "Cancer": static('images/signs/cancer.svg'),
            "Leo": static('images/signs/leo.svg'),
            "Virgo": static('images/signs/virgo.svg'),
            "Libra": static('images/signs/libra.svg'),
            "Scorpio": static('images/signs/scorpio.svg'),
            "Sagittarius": static('images/signs/sagittarius.svg'),
            "Capricorn": static('images/signs/capricorn.svg'),
            "Aquarius": static('images/signs/aquarius.svg'),
            "Pisces": static('images/signs/pisces.svg'),
        }

        self.get_planets_table()
        

    def get_house_number(self, house_name: str) -> int:
        return self.house_names.get(house_name, 0)

    def get_opposite_sign(self, sign: str) -> str:
        signs = list(self.sign_names.keys())
        current_index = signs.index(sign)
        opposite_index = (current_index + 6) % 12
        return signs[opposite_index]

    def get_opposite_house(self, house_name: str) -> int:
        current_house = self.get_house_number(house_name)
        opposite_house = (current_house + 5) % 12 + 1
        return opposite_house

    def get_nakshatra(self, longitude):
        nakshatras = [
            "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
            "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
            "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
            "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
            "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
        ]
        nakshatra_index = int(longitude / (360 / 27))
        return nakshatras[nakshatra_index]
    
    def get_houses_table(self) -> None:
        houses_data = [
            [self.house_names[house.name], self.sign_names[house.sign]]
            for house in self.instance.houses_list
        ]
        self.houses_table = houses_data

    def get_planets_table(self) -> None:
        excluded_planets = ['Uranus', 'Pluto', 'Neptune', 'Chiron', 'True_Node']
        planets_data = []
        rahu_data = None

        for planet in self.instance.planets_list:
            if planet.name not in excluded_planets:
                if planet.name == "Mean_Node":
                    planet_name = "Rahu"
                    rahu_data = {
                        "name": planet_name,
                        "sign": planet.sign,
                        "position": float(planet.position),
                        "house": planet.house
                    }
                else:
                    planet_name = planet.name

                sign_name = self.sign_names.get(planet.sign, planet.sign)
                actual_longitude = float(planet.position) + (list(self.sign_names.keys()).index(planet.sign) * 30)
                nakshatra = self.get_nakshatra(actual_longitude)

                planets_data.append({
                    "planet_icon": self.planet_icons.get(planet_name, ""),
                    "name": planet_name,
                    "sign_icon": self.sign_icons.get(sign_name, ""),
                    "sign": sign_name,
                    "position": round(float(planet.position), 2),
                    "house": self.get_house_number(planet.house),
                    
                })

        if rahu_data:
            ketu_sign = self.get_opposite_sign(rahu_data["sign"])
            ketu_position = ((rahu_data["position"] + 180) % 360) % 30
            ketu_house = self.get_opposite_house(rahu_data["house"])

            rahu_actual_longitude = rahu_data["position"] + (list(self.sign_names.keys()).index(rahu_data["sign"]) * 30)
            ketu_actual_longitude = (rahu_actual_longitude + 180) % 360

            rahu_nakshatra = self.get_nakshatra(rahu_actual_longitude)
            ketu_nakshatra = self.get_nakshatra(ketu_actual_longitude)

            ketu_sign_name = self.sign_names.get(ketu_sign, ketu_sign)

            planets_data.append({
                "planet_icon": self.planet_icons["Ketu"],
                "name": "Ketu",
                "sign_icon": self.sign_icons.get(ketu_sign_name, ""),
                "sign": ketu_sign_name,
                "position": round(ketu_position, 2),
                "house": ketu_house,
                
            })

        self.planets_data = planets_data

    def get_planets_with_aspects(self):
        return self.planets_data
