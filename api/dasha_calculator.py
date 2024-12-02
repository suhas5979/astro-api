from datetime import datetime, timedelta
from .models import CustomerDetails
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .astrological_subject import AstrologicalSubject
from .report import Report

class DashaCalculator:
    DASHA_YEARS = 120
    NAKSHATRA_SPAN = 13 + 20/60
    DASHA_PERIODS = {
        "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
        "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17
    }
    PLANET_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
    NAKSHATRA_TO_PLANET = [
        "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
        "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
        "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"
    ]
    NAKSHATRAS = [
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha",
        "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
        "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
    ]
    ZODIAC_SIGNS = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]

    def __init__(self, customer_id):
        self.customer = CustomerDetails.objects.get(id=customer_id)
        self.subject = self.create_astrological_subject()
        self.report = Report(self.subject)

    def calculate_dasha_balance(self, moon_sign, moon_degree):
        adjusted_moon_degree = (self.ZODIAC_SIGNS.index(moon_sign) * 30) + moon_degree
        nakshatra_index = int(adjusted_moon_degree // self.NAKSHATRA_SPAN) % 27
        nakshatra_progress = (adjusted_moon_degree % self.NAKSHATRA_SPAN) / self.NAKSHATRA_SPAN
        
        current_nakshatra = self.NAKSHATRAS[nakshatra_index]
        current_dasha_lord = self.NAKSHATRA_TO_PLANET[nakshatra_index]
        dasha_length = self.DASHA_PERIODS[current_dasha_lord]
        
        elapsed_years = nakshatra_progress * dasha_length
        balance_years = dasha_length - elapsed_years
        
        return current_dasha_lord, balance_years, current_nakshatra, elapsed_years

    def generate_dasha_periods(self, start_dasha, start_date, balance_years):
        dasha_list = []
        current_date = start_date - timedelta(days=(self.DASHA_PERIODS[start_dasha] - balance_years)*365)
        
        start_index = self.PLANET_ORDER.index(start_dasha)
        for i in range(9):
            planet = self.PLANET_ORDER[(start_index + i) % 9]
            period = self.DASHA_PERIODS[planet]
            
            end_date = current_date + timedelta(days=period*365)
            
            dasha_list.append((planet, current_date, end_date))
            current_date = end_date 
        
        return dasha_list
    
    def calculate_antardasha(self, mahadasha_list):
        antardasha_list = []
        for maha_planet, maha_start, maha_end in mahadasha_list:
            maha_duration = (maha_end - maha_start).days / 365
            current_date = maha_start
            
            start_index = self.PLANET_ORDER.index(maha_planet)
            for i in range(9):
                antar_planet = self.PLANET_ORDER[(start_index + i) % 9]
                antar_duration = (self.DASHA_PERIODS[antar_planet] / self.DASHA_YEARS) * maha_duration
                antar_end = current_date + timedelta(days=antar_duration*365)
                
                antardasha_list.append((maha_planet, antar_planet, current_date, antar_end))
                current_date = antar_end
        
        return antardasha_list

    def find_current_dasha(self, dasha_list, current_date):
        for dasha in dasha_list:
            if len(dasha) == 4:  
                maha, antar, start, end = dasha
                if start <= current_date <= end:
                    return maha, antar, start, end
        return None, None, None, None

    def create_astrological_subject(self):
        return AstrologicalSubject(
            name=self.customer.name,
            year=self.customer.birth_date.year,
            month=self.customer.birth_date.month,
            day=self.customer.birth_date.day,
            hour=self.customer.birth_time.hour,
            minute=self.customer.birth_time.minute,
            lng=float(self.customer.longitude),
            lat=float(self.customer.latitude),
            tz_str="Asia/Kolkata",  
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
            houses_system_identifier='W'
        )

    def get_moon_sign_and_degree(self):
        for planet in self.report.planets_data:
            if planet['name'] == 'Moon':
                return planet['sign'], planet['position']
        raise ValueError("Moon data not found in the report")

    def calculate(self):
        moon_sign, moon_degree = self.get_moon_sign_and_degree()
        
        start_dasha, balance_years, current_nakshatra, elapsed_years = self.calculate_dasha_balance(moon_sign, moon_degree)
        
        birth_date = datetime.combine(self.customer.birth_date, self.customer.birth_time)
        mahadasha_list = self.generate_dasha_periods(start_dasha, birth_date, balance_years)
        antardasha_list = self.calculate_antardasha(mahadasha_list)
        
        current_date = datetime.now()
        current_maha, current_antar, start, end = self.find_current_dasha(antardasha_list, current_date)
        
        return {
            "current_dasha": {
                "mahadasha": current_maha,
                "antardasha": current_antar,
                "start_date": start.strftime('%Y-%m-%d'),
                "end_date": end.strftime('%Y-%m-%d'),
            },
            "mahadasha_list": [
                {
                    "planet": maha,
                    "start_date": start.strftime('%Y-%m-%d'),
                    "end_date": end.strftime('%Y-%m-%d'),
                } for maha, start, end in mahadasha_list
            ],
            "antardasha_list": [
                {
                    "mahadasha": maha,
                    "antardasha": antar,
                    "start_date": start.strftime('%Y-%m-%d'),
                    "end_date": end.strftime('%Y-%m-%d'),
                } for maha, antar, start, end in antardasha_list
            ],
        }
    
    