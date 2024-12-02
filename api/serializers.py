
from rest_framework import serializers
from .models import CustomerDetails

class CustomerDetailsSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=100, required=True)
    email = serializers.CharField(required=True)
    mobile_no = serializers.CharField(max_length=15, required=True)
    birth_time = serializers.TimeField(format='%H:%M', required=True)
    birth_date = serializers.DateField(required=True)
    birth_place = serializers.CharField(max_length=100, required=True) 
    latitude = serializers.DecimalField(max_digits=7, decimal_places=4, required=False, read_only=True)
    longitude = serializers.DecimalField(max_digits=7, decimal_places=4, required=False, read_only=True)

    class Meta:
        model = CustomerDetails
        fields = ['id', 'name', 'email', 'mobile_no', 'birth_date', 'birth_time', 'birth_place', 'latitude', 'longitude']
        read_only_fields = ['id']


class CustomerDetailsLimitedSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerDetails
        fields = ['name', 'birth_date', 'birth_time', 'birth_place', 'latitude', 'longitude']

class PlanetSerializer(serializers.ModelSerializer):
    symbol = serializers.CharField()  

    class Meta:
        model = CustomerDetails
        fields = ['symbol', 'name', 'sign', 'position', 'house', 'nakshatra']

