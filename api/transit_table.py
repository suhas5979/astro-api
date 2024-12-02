import swisseph as swe
from datetime import datetime, timedelta
import pytz
from timezonefinder import TimezoneFinder
from astropy.time import Time
from django.db import models
from .models import CustomerDetails, Planet

class TransitCalculator:
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
        self.taras = [
            ("Janma", "Birth"), ("Sampat", "Wealth"), ("Vipat", "Danger"),
            ("Kshema", "Well-being"), ("Pratyak", "Obstacles"), ("Saadhana", "Achievement"),
            ("Naidhana", "Death"), ("Mitra", "Friend"), ("Parama Mitra", "Good friend")
        ]
        self.ayanamsha_mode = swe.SIDM_LAHIRI
        swe.set_sid_mode(self.ayanamsha_mode)
        self.zodiac_signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
                             "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        
        self.exalted_signs = {
            "Sun": "Aries",
            "Moon": "Taurus",
            "Mars": "Capricorn",
            "Mercury": "Virgo",
            "Jupiter": "Cancer",
            "Venus": "Pisces",
            "Saturn": "Libra",
            "Rahu": "Taurus",
            "Ketu": "Scorpio"
        }
        
        self.debilitated_signs = {
            "Sun": "Libra",
            "Moon": "Scorpio",
            "Mars": "Cancer",
            "Mercury": "Pisces",
            "Jupiter": "Capricorn",
            "Venus": "Virgo",
            "Saturn": "Aries",
            "Rahu": "Scorpio",
            "Ketu": "Taurus"
        }
        
        self.own_signs = {
            "Sun": ["Leo"],
            "Moon": ["Cancer"],
            "Mars": ["Aries", "Scorpio"],
            "Mercury": ["Gemini", "Virgo"],
            "Jupiter": ["Sagittarius", "Pisces"],
            "Venus": ["Taurus", "Libra"],
            "Saturn": ["Capricorn", "Aquarius"],
            "Rahu": ["Aquarius"],
            "Ketu": ["Scorpio"]
        }

    def get_planetary_dignity(self, planet, zodiac_sign):
        if zodiac_sign == self.exalted_signs.get(planet):
            return "Exalted"
        elif zodiac_sign == self.debilitated_signs.get(planet):
            return "Debilitated"
        elif zodiac_sign in self.own_signs.get(planet, []):
            return "Own Sign"
        else:
            return "Normal"

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
        
        positions = self.get_planet_positions(jd)
        return positions['Moon']['nakshatra']
    
    def get_zodiac_sign(self, longitude):
        signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
                 "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        return signs[int(longitude / 30)]

    def get_nakshatra_progress(self, longitude):
        nakshatra_span = 360 / 27 
        return (longitude % nakshatra_span) 

    def sidereal_longitude(self, jd, longitude):
        ayanamsha = swe.get_ayanamsa(jd)
        return (longitude - ayanamsha) % 360

    def get_nakshatra(self, longitude):
        nakshatra_index = int(longitude * 27 / 360)
        return self.nakshatras[nakshatra_index]

    def get_planet_positions(self, jd):
        positions = {}
        planet_names = {
            swe.SUN: "Sun", swe.MOON: "Moon", swe.MERCURY: "Mercury",
            swe.VENUS: "Venus", swe.MARS: "Mars", swe.JUPITER: "Jupiter",
            swe.SATURN: "Saturn"
        }
        
        for planet_id, planet_name in planet_names.items():
            result = swe.calc_ut(jd, planet_id)
            lon = result[0][0]  
            sid_lon = self.sidereal_longitude(jd, lon)
            nakshatra = self.get_nakshatra(sid_lon)
            positions[planet_name] = {
                'longitude': round(sid_lon, 2),
                'nakshatra': nakshatra,
            }
        
        rahu_ketu = self.calculate_rahu_ketu(jd, positions["Moon"]['longitude'], positions["Sun"]['longitude'])
        positions.update(rahu_ketu)
        
        return positions

    def calculate_rahu_ketu(self, jd, moon_longitude, sun_longitude):
        rahu_tropical = (sun_longitude + 180) % 360
        rahu_sidereal = self.sidereal_longitude(jd, rahu_tropical)
        ketu_sidereal = (rahu_sidereal + 180) % 360
        
        return {
            'Rahu': {
                'longitude': round(rahu_sidereal, 2),
                'nakshatra': self.get_nakshatra(rahu_sidereal),
            },
            'Ketu': {
                'longitude': round(ketu_sidereal, 2),
                'nakshatra': self.get_nakshatra(ketu_sidereal),
            }
        }

    def find_nakshatra_boundaries(self, planet, start_jd, nakshatra):
        local_tz = self.get_local_timezone()
        jd = start_jd
        while self.get_planet_positions(jd)[planet]['nakshatra'] == nakshatra:
            jd -= 1/24 
        start_time = Time(jd + 1/24, format='jd').datetime
        start_time = pytz.utc.localize(start_time).astimezone(local_tz)
        jd = start_jd
        while self.get_planet_positions(jd)[planet]['nakshatra'] == nakshatra:
            jd += 1/24  
        end_time = Time(jd - 1/24, format='jd').datetime
        end_time = pytz.utc.localize(end_time).astimezone(local_tz)
        return start_time, end_time
    
    def get_planet_tara(self, planet_nakshatra, birth_nakshatra):
        start_index = self.nakshatras.index(birth_nakshatra)
        planet_index = self.nakshatras.index(planet_nakshatra)
        tara_index = (planet_index - start_index) % 9
        return self.taras[tara_index]

    def calculate_transit_table(self):
        local_tz = self.get_local_timezone()
        birth_nakshatra = self.get_birth_nakshatra()
        
        current_time = Time.now()
        jd = current_time.jd
        
        date = current_time.datetime
        date = pytz.utc.localize(date).astimezone(local_tz)
        
        positions = self.get_planet_positions(jd)
        
        transit_data = []
        
        for planet, data in positions.items():
            tara, meaning = self.get_planet_tara(data['nakshatra'], birth_nakshatra)
            planet_tara = f"{tara} ({meaning})" if tara else "Couldn't determine"
            
            start_time, end_time = self.find_nakshatra_boundaries(planet, jd, data['nakshatra'])
            zodiac_sign = self.get_zodiac_sign(data['longitude'])
            nakshatra_progress = self.get_nakshatra_progress(data['longitude'])
            dignity = self.get_planetary_dignity(planet, zodiac_sign)
            
            transit_data.append({
                "Planet": planet,  
                "Longitude": f"{data['longitude']:.2f}",
                "Nakshatra": data['nakshatra'],
                "Planet's Tara": planet_tara,
                "Nakshatra Start": start_time.strftime('%Y-%m-%d %H:%M'),
                "Nakshatra End": end_time.strftime('%Y-%m-%d %H:%M'),
                "Zodiac Sign": zodiac_sign,
                "Nakshatra Degree": f"{nakshatra_progress:.2f}"   
            })
        
        return transit_data
 
#----------------------------------------------------------Planetary Interpretations----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    
    def get_planet_significance(self, planet):
        try:
            planet_obj = Planet.objects.get(planet=planet)
            return planet_obj.significance
        except Planet.DoesNotExist:
            return "Unknown"

    def interpret_planetary_position(self, planet, tara, meaning):
        significance = self.get_planet_significance(planet)

        interpretations = {
        "Janma": f"The {planet} is in its Janma (birth) phase. This is a good time for new beginnings related to {planet}'s significations. Which signifies {significance} Focus on starting fresh projects and initiatives. Good time for introspection and understanding one's inner needs. Avoid impulsiveness, risky new ventures, and over-exerting yourself. Be cautious of ego-driven actions.",
        
        "Sampat": f"The {planet} is in its Sampat (wealth) phase. This is a favorable time for financial matters and resource accumulation related to {planet}'s domains. Which signifies {significance} Utilize this time to make financial decisions, expand your resources, and build stable foundations. Ideal for investments or career advancements. Avoid greed or overindulgence. Don’t take unnecessary financial risks or spend lavishly.",
        
        "Vipat": f"The {planet} is in its Vipat (danger) phase. Exercise caution in matters related to {planet}'s significations. Which signifies {significance} Avoid taking unnecessary risks and be mindful of potential challenges, prepare for potential setbacks. Use this time for problem-solving and learning from difficulties. Avoid taking risks, starting new ventures, or making critical decisions. Delay major actions until a more favorable period.",
        
        "Kshema": f"The {planet} is in its Kshema (well-being) phase. This is a good time for stability and security in areas governed by {planet}. Which signifies {significance} Focus on maintaining balance and nurturing existing projects, relationships, and ensuring your emotional well-being. This is a good time to consolidate and secure what you’ve built. Avoid complacency or neglecting health and safety. Don't overlook small issues, as they could escalate later.",
        
        "Pratyak": f"The {planet} is in its Pratyak (obstacle) phase. Be prepared for potential setbacks or delays in matters related to {planet}. Which signifies {significance} Practice patience and look for alternative solutions to challenges. Tread carefully and focus on diplomacy. Use this time for resolution or rethinking strategies. Avoid direct confrontations, aggressive actions, or starting new endeavors. Be wary of making enemies or taking extreme stances.",
        
        "Saadhana": f"The {planet} is in its Saadhana (achievement) phase. This is an excellent time for accomplishing goals related to {planet}'s significations. Which signifies {significance} Put extra effort into your endeavors for significant progress. It's a time for self-improvement and seeking deeper knowledge or meaning. Avoid distractions, laziness, and material pursuits. Don’t let go of discipline or stray from your higher goals.",
        
        "Naidhana": f"The {planet} is in its Naidhana (death) phase. This might be a challenging time for matters related to {planet}. Which signifies {significance} Focus on reflection, mindfulness, and careful planning. Use this time to let go of old patterns and make room for transformation. Avoid major decisions, financial risks, and emotional overreactions. Refrain from starting new projects or making commitments.",
        
        "Mitra": f"The {planet} is in its Mitra (friendly) phase. This is a good time for cooperation and building relationships in areas governed by {planet}. Which signifies {significance} Seek support and collaborate with others. Avoid conflicts or being overly independent. Don’t push people away or try to go it alone.",
        
        "Parama Mitra": f"The {planet} is in its Parama Mitra (great friend) phase. This is an excellent time for strong alliances and beneficial partnerships related to {planet}'s domains. Which signifies {significance} Maximize on supportive energies. Avoid isolation, ego conflicts, or ignoring the value of teamwork. Don’t distance yourself from supportive people."
        }
    
        return interpretations.get(tara, f"The {planet} is in an unknown phase. Which signifies {significance}. Proceed with caution and seek further guidance.")

    def generate_planetary_interpretations(self, transit_data):
        planetary_interpretations = {}
        for row in transit_data:
            planet = row['Planet']
            tara_info = row["Planet's Tara"]
            if '(' in tara_info and ')' in tara_info:
                tara, meaning = tara_info.split("(")
                tara = tara.strip()
                meaning = meaning.rstrip(")").strip()
            else:
                tara = tara_info
                meaning = "Unknown"
        
            interpretation = self.interpret_planetary_position(planet, tara, meaning)
            planetary_interpretations[planet] = f"{interpretation}"
        return planetary_interpretations

    def calculate(self):
        transit_table = self.calculate_transit_table()
        planetary_interpretations = self.generate_planetary_interpretations(transit_table)
        return {
            "transit_table": transit_table,
            "planetary_interpretations": planetary_interpretations
        }
