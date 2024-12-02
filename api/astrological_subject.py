from kerykeion import AstrologicalSubject as BaseAstrologicalSubject
from datetime import datetime, timedelta
import swisseph as swe

def get_ascendant(date, lat, lon, sidereal_mode):
    utc_time = date - timedelta(hours=5, minutes=30)
    jd = swe.julday(utc_time.year, utc_time.month, utc_time.day, 
                    utc_time.hour + utc_time.minute/60.0 + utc_time.second/3600.0)
    
    swe.set_sid_mode(getattr(swe, f"SIDM_{sidereal_mode}"))
    
    houses = swe.houses_ex(jd, lat, lon, b'W', swe.FLG_SIDEREAL)[1]
    ascendant = houses[0] 
    return ascendant

def longitude_to_zodiac(longitude):
    signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
             "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    sign_index = int(longitude / 30)
    degree = longitude % 30
    return signs[sign_index], degree

class AstrologicalSubject(BaseAstrologicalSubject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.calculate_ascendant()
        self.houses_list = [
            self.first_house,
            self.second_house,
            self.third_house, 
            self.fourth_house,
            self.fifth_house,
            self.sixth_house,
            self.seventh_house,
            self.eighth_house,
            self.ninth_house,
            self.tenth_house,
            self.eleventh_house,
            self.twelfth_house,
        ]
        self.planets_list = [
            self.sun,
            self.moon,
            self.mercury,
            self.venus,
            self.mars,
            self.jupiter,
            self.saturn,
            self.mean_node,
        ]

    def calculate_ascendant(self):
        date = datetime(self.year, self.month, self.day, self.hour, self.minute)
        self.ascendant = get_ascendant(date, self.lat, self.lng, self.sidereal_mode)
        self.ascendant_sign, self.ascendant_degree = longitude_to_zodiac(self.ascendant)
    