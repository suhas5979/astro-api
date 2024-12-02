from django.urls import path
from .views import CustomerDetailsAPIView, CustomerDetailsGetAPIView
from .views import NavataraAPIView
from .views import TransitAPIView
from .views import PlanetsAPIView
from .views import DashaAPIView
from .views import GoodBadTimesAPIView

from .views import (
    D2ChartAPIView, D3ChartAPIView, D4ChartAPIView,
    D7ChartAPIView, NavamsaChartAPIView,
    D10ChartAPIView,D12ChartAPIView, D16ChartAPIView, D20ChartAPIView,
    D24ChartAPIView, D27ChartAPIView, D30ChartAPIView, D40ChartAPIView, D45ChartAPIView, D60ChartAPIView
)

urlpatterns = [
    path('customer-details/', CustomerDetailsAPIView.as_view(), name='customer-details'),
    path('navatara-data/<int:customer_id>/', NavataraAPIView.as_view(), name='navatara-data'),
    path('transit-data/<int:customer_id>/', TransitAPIView.as_view(), name='transit-data'),
    path('birth-chart-data/<int:customer_id>/', PlanetsAPIView.as_view(), name='birth-chart-data'),
    path('dasha-data/<int:customer_id>/', DashaAPIView.as_view(), name='dasha-data'),
    path('fetch-customer-details/<int:customer_id>/', CustomerDetailsGetAPIView.as_view(), name='fetch-customer-details'),
    path('good-bad-times/', GoodBadTimesAPIView.as_view(), name='good-bad-times'), 
    path('charts/d2/<int:customer_id>/', D2ChartAPIView.as_view(), name='d2-chart'),
    path('charts/d3/<int:customer_id>/', D3ChartAPIView.as_view(), name='d3-chart'),
    path('charts/d4/<int:customer_id>/', D4ChartAPIView.as_view(), name='d4-chart'),
    path('charts/d7/<int:customer_id>/', D7ChartAPIView.as_view(), name='d7-chart'),
    path('charts/navamsa/<int:customer_id>/', NavamsaChartAPIView.as_view(), name='navamsa-chart'),
    path('charts/d10/<int:customer_id>/', D10ChartAPIView.as_view(), name='d10-chart'),
    path('charts/d12/<int:customer_id>/', D12ChartAPIView.as_view(), name='d12-chart'),
    path('charts/d16/<int:customer_id>/', D16ChartAPIView.as_view(), name='d16-chart'),
    path('charts/d20/<int:customer_id>/', D20ChartAPIView.as_view(), name='d20-chart'),
    path('charts/d24/<int:customer_id>/', D24ChartAPIView.as_view(), name='d24-chart'),
    path('charts/d27/<int:customer_id>/', D27ChartAPIView.as_view(), name='d27-chart'),
    path('charts/d30/<int:customer_id>/', D30ChartAPIView.as_view(), name='d30-chart'),
    path('charts/d40/<int:customer_id>/', D40ChartAPIView.as_view(), name='d40-chart'),
    path('charts/d45/<int:customer_id>/', D45ChartAPIView.as_view(), name='d45-chart'),
    path('charts/d60/<int:customer_id>/', D60ChartAPIView.as_view(), name='d60-chart'),
    ]
