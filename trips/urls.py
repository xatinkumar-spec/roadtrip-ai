from django.urls import path
from .views import (
    trip_list, create_trip, edit_trip, delete_trip, trip_detail,
    ai_trip_plan, ai_chat, start_planning, save_ai_trip,
    map_view, get_route_data
)

urlpatterns = [
    path("", trip_list, name="trip_list"),
    path("create/", create_trip, name="create_trip"),
    path("edit/<int:trip_id>/", edit_trip, name="edit_trip"),
    path("delete/<int:trip_id>/", delete_trip, name="delete_trip"),
    path("detail/<int:trip_id>/", trip_detail, name="trip_detail"),
    path("ai-trip/", ai_trip_plan, name="ai_trip_plan"),
    path("ai-chat/", ai_chat, name="ai_chat"),
    path("start-planning/", start_planning, name="start_planning"),
    path("save-ai-trip/", save_ai_trip, name="save_ai_trip"),
    path("map/<int:trip_id>/", map_view, name="map_view"),
    path("api/route/", get_route_data, name="get_route_data"),
]