from django.db import models
from .models import CustomerDetails
import swisseph as swe
from datetime import datetime
import pytz
from timezonefinder import TimezoneFinder

class NavataraCalculator:
    def __init__(self, customer_id):
        self.customer = CustomerDetails.objects.get(id=customer_id)
        self.nakshatras = [
            "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", 
            "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", 
            "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", 
            "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", 
            "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
        ]
        self.ruling_planets = {
            "Ashwini": "Ketu", "Bharani": "Venus", "Krittika": "Sun", "Rohini": "Moon",
            "Mrigashira": "Mars", "Ardra": "Rahu", "Punarvasu": "Jupiter", "Pushya": "Saturn",
            "Ashlesha": "Mercury", "Magha": "Ketu", "Purva Phalguni": "Venus", 
            "Uttara Phalguni": "Sun", "Hasta": "Moon", "Chitra": "Mars", "Swati": "Rahu",
            "Vishakha": "Jupiter", "Anuradha": "Saturn", "Jyeshtha": "Mercury", 
            "Mula": "Ketu", "Purva Ashadha": "Venus", "Uttara Ashadha": "Sun",
            "Shravana": "Moon", "Dhanishta": "Mars", "Shatabhisha": "Rahu", 
            "Purva Bhadrapada": "Jupiter", "Uttara Bhadrapada": "Saturn", "Revati": "Mercury"
        }

    def get_local_timezone(self):
        tf = TimezoneFinder()
        return pytz.timezone(tf.timezone_at(lng=float(self.customer.longitude), lat=float(self.customer.latitude)))

    def get_birth_nakshatra(self):
        local_tz = self.get_local_timezone()
        birth_date = datetime.combine(self.customer.birth_date, self.customer.birth_time)
        birth_date = local_tz.localize(birth_date)
        utc_birth_date = birth_date.astimezone(pytz.UTC)
        
        jd = swe.julday(utc_birth_date.year, utc_birth_date.month, utc_birth_date.day, 
                        utc_birth_date.hour + utc_birth_date.minute/60.0 + utc_birth_date.second/3600.0)
        
        swe.set_sid_mode(swe.SIDM_LAHIRI) 
        
        moon_pos = swe.calc_ut(jd, swe.MOON)[0]
        ayanamsha = swe.get_ayanamsa(jd)
        moon_longitude = (moon_pos[0] - ayanamsha) % 360
        
        nakshatra_index = int(moon_longitude * 27 / 360)
        return self.nakshatras[nakshatra_index]

    def get_navatara_table(self):
        start_nakshatra = self.get_birth_nakshatra()
        taras = [
            ("Janma", "Birth"), ("Sampat", "Wealth"), ("Vipat", "Danger"),
            ("Kshema", "Well-being"), ("Pratyak", "Obstacles"), ("Saadhana", "Achievement"),
            ("Naidhana", "Death"), ("Mitra", "Friend"), ("Parama Mitra", "Good friend")
        ]
        
        data = []
        current_nakshatra = start_nakshatra
        for tara, meaning in taras:
            nak1 = self.get_nakshatras(current_nakshatra, 9)[0]
            nak2_start = self.nakshatras[(self.nakshatras.index(current_nakshatra) + 9) % len(self.nakshatras)]
            nak2 = self.get_nakshatras(nak2_start, 9)[0]
            nak3_start = self.nakshatras[(self.nakshatras.index(current_nakshatra) + 18) % len(self.nakshatras)]
            nak3 = self.get_nakshatras(nak3_start, 9)[0]
            lord = self.ruling_planets.get(nak1, "Unknown")
            data.append({
                "Tara": tara,
                "Meaning": meaning,
                "Lord": lord,
                "Nakshatra1": nak1,
                "Nakshatra2": nak2,
                "Nakshatra3": nak3
            })
            current_nakshatra = self.nakshatras[(self.nakshatras.index(current_nakshatra) + 1) % len(self.nakshatras)]
        
        return data

    def get_nakshatras(self, start_nakshatra, count):
        start_index = self.nakshatras.index(start_nakshatra)
        return [self.nakshatras[(start_index + i) % len(self.nakshatras)] for i in range(count)]

    def calculate(self):
        return {
            "navatara_table": self.get_navatara_table()
        }