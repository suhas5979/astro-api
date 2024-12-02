from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import CustomerDetailsSerializer
from .serializers import CustomerDetailsLimitedSerializer
from .models import CustomerDetails
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from decimal import Decimal, ROUND_HALF_UP
from django.core.exceptions import ValidationError
from .navatara_table import NavataraCalculator
from .transit_table import TransitCalculator
from .astrological_subject import AstrologicalSubject
from .report import Report 
from .dasha_calculator import DashaCalculator
from kerykeion import Report as BaseReport
import requests
import pytz
from datetime import datetime
from django.conf import settings
import time
from requests.exceptions import RequestException
from django.db.models import Q
import json
import os
from pathlib import Path
import asyncio
import aiohttp
from django.http import HttpRequest
from rest_framework.request import Request
from django.http import FileResponse



#-----------------------------------------------------Customer Birth Details------------------------------------------------------

class CustomerDetailsAPIView(APIView):
    def get_lat_long(self, place):
        geolocator = Nominatim(user_agent="astrology_app")
        max_attempts = 3
        attempts = 0
        
        while attempts < max_attempts:
            try:
                location = geolocator.geocode(place)
                if location:
                    return location.latitude, location.longitude
                else:
                    return None, None
            except (GeocoderTimedOut, GeocoderUnavailable):
                attempts += 1
        
        return None, None

    def round_decimal(self, value):
        return Decimal(value).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)

    def store_api_response(self, customer_id, api_name, data):
        """Store API response in a JSON file"""
        customer_dir = os.path.join(settings.CUSTOMER_DATA_DIR, str(customer_id))
        os.makedirs(customer_dir, exist_ok=True)
        
        file_path = os.path.join(customer_dir, f"{api_name}.json")
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)

    async def collect_all_data(self, customer_id):
        """Collect data from all APIs asynchronously"""
        # Create a proper request object
        dummy_request = HttpRequest()
        dummy_request.method = 'GET'
        dummy_request.META = {
            'CONTENT_TYPE': 'application/json',
            'HTTP_ACCEPT': 'application/json',
        }
        
        # Define all API views
        api_views = {
            'customer_details':CustomerDetailsGetAPIView(),
            'navatara': NavataraAPIView(),
            'transit': TransitAPIView(),
            'birth_chart': PlanetsAPIView(),
            'dasha': DashaAPIView()
        }
        
        # List of divisional charts
        chart_classes = [
            D2ChartAPIView, D3ChartAPIView, D4ChartAPIView, D7ChartAPIView,
            NavamsaChartAPIView, D10ChartAPIView, D12ChartAPIView, D16ChartAPIView,
            D20ChartAPIView, D24ChartAPIView, D27ChartAPIView, D30ChartAPIView,
            D40ChartAPIView, D45ChartAPIView, D60ChartAPIView
        ]

        async def get_api_data(name, view):
            """Generic function to get data from any API view"""
            try:
                response = await asyncio.to_thread(view.get, 
                                                 Request(dummy_request), 
                                                 customer_id)
                if response.status_code == 200:
                    self.store_api_response(customer_id, name, response.data)
                    return True
                return False
            except Exception as e:
                print(f"Error getting {name} data: {str(e)}")
                return False

        try:
            # Create tasks for all API calls
            tasks = []
            
            # Add tasks for main APIs
            for name, view in api_views.items():
                tasks.append(get_api_data(name, view))
            
            # Add tasks for divisional charts
            for chart_class in chart_classes:
                chart_view = chart_class()
                chart_name = chart_class.__name__.replace('ChartAPIView', '').lower()
                tasks.append(get_api_data(f'{chart_name}', chart_view))

            # Run all tasks concurrently
            await asyncio.gather(*tasks)

        except Exception as e:
            print(f"Error collecting data for customer {customer_id}: {str(e)}")
            raise

    def post(self, request):
        serializer = CustomerDetailsSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Get validated data
                name = serializer.validated_data['name']
                email = serializer.validated_data['email']
                mobile_no = serializer.validated_data['mobile_no']
                birth_place = serializer.validated_data['birth_place']

                # Check for existing records with various combinations
                existing_record = CustomerDetails.objects.filter(
                    Q(mobile_no=mobile_no) |
                    Q(email=email) |
                    Q(name=name, mobile_no=mobile_no) |
                    Q(name=name, email=email)
                ).first()

                # Get latitude and longitude
                latitude, longitude = self.get_lat_long(birth_place)
                if latitude is None or longitude is None:
                    return Response(
                        {"error": "Unable to geocode the birth place"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

                if existing_record:
                    # Update existing record
                    existing_record.name = name
                    existing_record.email = email
                    existing_record.mobile_no = mobile_no
                    existing_record.birth_date = serializer.validated_data['birth_date']
                    existing_record.birth_time = serializer.validated_data['birth_time']
                    existing_record.birth_place = birth_place
                    existing_record.latitude = self.round_decimal(latitude)
                    existing_record.longitude = self.round_decimal(longitude)
                    
                    try:
                        existing_record.save()
                        # Collect data after updating
                        asyncio.run(self.collect_all_data(existing_record.id))
                        return Response(
                            CustomerDetailsSerializer(existing_record).data,
                            status=status.HTTP_200_OK
                        )
                    except ValidationError as e:
                        return Response(
                            {"error": f"Unable to update record: {str(e)}"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                else:
                    # Create new record
                    try:
                        customer = serializer.save(
                            latitude=self.round_decimal(latitude),
                            longitude=self.round_decimal(longitude)
                        )
                        # Collect data after creating
                        asyncio.run(self.collect_all_data(customer.id))
                        return Response(
                            CustomerDetailsSerializer(customer).data,
                            status=status.HTTP_201_CREATED
                        )
                    except ValidationError as e:
                        return Response(
                            {"error": f"Unable to create new record: {str(e)}"},
                            status=status.HTTP_400_BAD_REQUEST
                        )

            except Exception as e:
                return Response(
                    {"error": f"An unexpected error occurred: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#-------------------------------------------Fetch Customer Details Using Customer_id---------------------------------------------------

class CustomerDetailsGetAPIView(APIView):
    def get(self, request, customer_id):
        try:
            customer = CustomerDetails.objects.get(id=customer_id)
            serializer = CustomerDetailsLimitedSerializer(customer)
            
            if not serializer.data:
                return Response({
                    "error": "Serializer produced empty data",
                    "customer_fields": [field.name for field in CustomerDetails._meta.fields],
                    "serializer_fields": serializer.fields.keys()
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
        except CustomerDetails.DoesNotExist:
            return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({"error": "Invalid Customer ID"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "error": str(e),
                "type": str(type(e))
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#----------------------------------------------------Navatara Data---------------------------------------------------------------------

class NavataraAPIView(APIView):
    def get(self, request, customer_id):
        try:
            if not customer_id:
                return Response({"error": "Customer ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            calculator = NavataraCalculator(customer_id)
            result = calculator.calculate()
            return Response(result, status=status.HTTP_200_OK)
        except CustomerDetails.DoesNotExist:
            return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#----------------------------------------------------Transit Data---------------------------------------------------------------------


class TransitAPIView(APIView):
    def get(self, request, customer_id):
        try:
            if not customer_id:
                return Response({"error": "Customer ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            calculator = TransitCalculator(customer_id)
            result = calculator.calculate()
            return Response(result, status=status.HTTP_200_OK)
        except CustomerDetails.DoesNotExist:
            return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#----------------------------------------------------Birth-Chart Data---------------------------------------------------------------------


class PlanetsAPIView(APIView):
    def get(self, request, customer_id):
        try:
            if not customer_id:
                return Response({"error": "Customer ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            customer_details = CustomerDetails.objects.get(id=customer_id)
            
            birth_date = customer_details.birth_date
            birth_time = customer_details.birth_time
            birth_place = customer_details.birth_place
            
            year, month, day = birth_date.year, birth_date.month, birth_date.day
            hour, minute = birth_time.hour, birth_time.minute
            
            place_parts = birth_place.split(',')
            city = place_parts[0].strip()
            country = place_parts[-1].strip() if len(place_parts) > 1 else ""
            
            subject = AstrologicalSubject(
                name=customer_details.name,
                year=year,
                month=month,
                day=day,
                hour=hour,
                minute=minute,
                city=city,
                nation=country,
                lng=customer_details.longitude,
                lat=customer_details.latitude,
                tz_str="Asia/Kolkata",
                zodiac_type="Sidereal",
                sidereal_mode="LAHIRI",
                houses_system_identifier='W',
                online=False
            )
            
            report = Report(subject)
            
            planets_data = report.get_planets_with_aspects()
           
            response_data = {
                "ascendant": {
                    "sign": subject.ascendant_sign,
                    "position": round(subject.ascendant_degree, 2)
                },
                "planets": planets_data
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except CustomerDetails.DoesNotExist:
            return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#----------------------------------------------------Dasha Data---------------------------------------------------------------------


class DashaAPIView(APIView):
    def get(self, request, customer_id):
        try:
            if not customer_id:
                return Response({"error": "Customer ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            calculator = DashaCalculator(customer_id)
            result = calculator.calculate()
            return Response(result, status=status.HTTP_200_OK)
        except CustomerDetails.DoesNotExist:
            return Response({"error": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
#----------------------------------------------Good Bad Times--------------------------------------------------------------------------

class GoodBadTimesAPIView(APIView):
    def get(self, request):
        LATITUDE = 28.6279
        LONGITUDE = 77.3749
        TIMEZONE = 5.5

        # API_KEY = "3Jl00g95af4w4ZDw53Uzy215P8LuRnmCa0jEuDOT"
        API_KEY = settings.APIASTRO_API_KEY

        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist)

        payload = {
            "year": current_time.year,
            "month": current_time.month,
            "date": current_time.day,
            "hours": current_time.hour,
            "minutes": current_time.minute,
            "seconds": current_time.second,
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "timezone": TIMEZONE,
            "config": {
                "observation_point": "geocentric",
                "ayanamsha": "lahiri"
            }
        }

        headers = {
            "x-api-key": API_KEY,
            "Content-Type": "application/json"
        }

        try:
            response = requests.post('https://json.apiastro.com/good-bad-times', json=payload, headers=headers)
            response.raise_for_status() 

            return Response(response.json(), status=status.HTTP_200_OK)

        except requests.RequestException as e:
            return Response({"error": f"API request failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#----------------------------------------------Divisional Charts----------------------------------------------------------------------

class BaseChartAPIView(APIView):
    """Base class for all chart API views"""
    
    def get_chart_data(self, customer, chart_url):
        payload = {
            "year": customer.birth_date.year,
            "month": customer.birth_date.month,
            "date": customer.birth_date.day,
            "hours": customer.birth_time.hour,
            "minutes": customer.birth_time.minute,
            "seconds": customer.birth_time.second,
            "latitude": float(customer.latitude),
            "longitude": float(customer.longitude),
            "timezone": 5.5,
            "settings": {
                "observation_point": "topocentric",
                "ayanamsha": "lahiri"
            }
        }
        headers = {
            "x-api-key": settings.APIASTRO_API_KEY,
            "Content-Type": "application/json"
        }
        def make_request_with_retry(max_retries=3, delay=0.5):
            for attempt in range(max_retries):
                try:
                    response = requests.post(chart_url, json=payload, headers=headers)
                    response.raise_for_status()
                    return response.json()
                except RequestException as e:
                    if response.status_code == 429 and attempt < max_retries - 1:
                        time.sleep(delay * (2 ** attempt))  # Exponential backoff
                    else:
                        return {"error": f"API request failed: {str(e)}"}
            return {"error": "Max retries reached"}

        return make_request_with_retry()

    def get(self, request, customer_id):
        try:
            customer = CustomerDetails.objects.get(id=customer_id)
        except CustomerDetails.DoesNotExist:
            return Response(
                {"error": "Customer not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        chart_data = self.get_chart_data(customer, self.chart_url)
        return Response(chart_data, status=status.HTTP_200_OK)
    
class D2ChartAPIView(BaseChartAPIView):
    chart_url = "https://json.apiastro.com/d2-chart-info"

class D3ChartAPIView(BaseChartAPIView):
    chart_url = "https://json.apiastro.com/d3-chart-info"

class D4ChartAPIView(BaseChartAPIView):
    chart_url = "https://json.apiastro.com/d4-chart-info"

class D7ChartAPIView(BaseChartAPIView):
    chart_url = "https://json.apiastro.com/d7-chart-info"

class NavamsaChartAPIView(BaseChartAPIView):
    chart_url = "https://json.apiastro.com/navamsa-chart-info"

class D10ChartAPIView(BaseChartAPIView):
    chart_url = "https://json.apiastro.com/d10-chart-info"

class D12ChartAPIView(BaseChartAPIView):
    chart_url = "https://json.apiastro.com/d12-chart-info"

class D16ChartAPIView(BaseChartAPIView):
    chart_url = "https://json.apiastro.com/d16-chart-info"

class D20ChartAPIView(BaseChartAPIView):
    chart_url = "https://json.apiastro.com/d20-chart-info"

class D24ChartAPIView(BaseChartAPIView):
    chart_url = "https://json.apiastro.com/d24-chart-info"

class D27ChartAPIView(BaseChartAPIView):
    chart_url = "https://json.apiastro.com/d27-chart-info"

class D30ChartAPIView(BaseChartAPIView):
    chart_url = "https://json.apiastro.com/d30-chart-info"

class D40ChartAPIView(BaseChartAPIView):
    chart_url = "https://json.apiastro.com/d40-chart-info"

class D45ChartAPIView(BaseChartAPIView):
    chart_url = "https://json.apiastro.com/d45-chart-info"

class D60ChartAPIView(BaseChartAPIView):
    chart_url = "https://json.apiastro.com/d60-chart-info"



