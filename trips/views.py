from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from .models import Trip
from .forms import TripForm

from google import genai
from groq import Groq

import json
from decimal import Decimal
import requests


COUNTRY_CODE_MAP = {
    "India": "in",
    "Nepal": "np",
    "Bhutan": "bt",
    "Thailand": "th",
    "United Arab Emirates": "ae",
    "United States": "us",
    "United Kingdom": "gb",
    "Canada": "ca",
    "Australia": "au",
    "Germany": "de",
    "France": "fr",
    "Italy": "it",
    "Japan": "jp",
    "South Korea": "kr",
    "Singapore": "sg",
    "Malaysia": "my",
    "Indonesia": "id",
    "Sri Lanka": "lk",
    "Maldives": "mv",
    "Saudi Arabia": "sa",
    "Qatar": "qa",
    "Turkey": "tr",
    "Spain": "es",
    "Netherlands": "nl",
    "Switzerland": "ch",
    "Sweden": "se",
    "Norway": "no",
    "Brazil": "br",
    "Argentina": "ar",
    "South Africa": "za",
    "Egypt": "eg",
}


def generate_ai_suggestions(trip):
    suggestions = []

    country = (trip.country or "").lower()
    destinations = (trip.destination or "").lower()

    if "india" in country:
        suggestions.append("Visit famous cultural places and try local street food.")
        suggestions.append("Best time to travel: October to March.")
    elif "canada" in country:
        suggestions.append("Carry warm clothes and explore natural parks.")
    elif "nepal" in country:
        suggestions.append("Great for trekking and mountain views.")
    elif "thailand" in country:
        suggestions.append("Explore beaches, temples, and local night markets.")
    elif "united states" in country:
        suggestions.append("Plan city travel in advance and check local transport options.")

    if "ooty" in destinations:
        suggestions.append("Visit Botanical Garden and Ooty Lake.")
    if "mysore" in destinations:
        suggestions.append("Don't miss Mysore Palace and local sweets.")
    if "manali" in destinations:
        suggestions.append("Enjoy snow activities and Solang Valley.")
    if "coorg" in destinations:
        suggestions.append("Explore coffee plantations and waterfalls.")
    if "delhi" in destinations:
        suggestions.append("Visit India Gate, Red Fort, and Chandni Chowk.")
    if "jaipur" in destinations:
        suggestions.append("Visit Amber Fort, Hawa Mahal, and local bazaars.")
    if "goa" in destinations:
        suggestions.append("Enjoy beaches, water sports, and local seafood.")
    if "kerala" in destinations:
        suggestions.append("Try backwater boating and explore hill stations.")
    if "haridwar" in destinations:
        suggestions.append("Attend Ganga Aarti and explore nearby temples.")
    if "puri" in destinations:
        suggestions.append("Visit Jagannath Temple and enjoy the beach.")

    if trip.budget:
        if trip.budget < 10000:
            suggestions.append("Plan budget hotels and use public transport.")
        elif trip.budget > 50000:
            suggestions.append("You can enjoy luxury stays and guided tours.")

    if not suggestions:
        suggestions.append("Explore famous local attractions in your selected destinations.")
        suggestions.append("Check weather and transport availability before starting the trip.")

    return suggestions


@login_required
def ai_trip_plan(request):
    prompt = request.GET.get("prompt", "").strip()

    if not prompt:
        return JsonResponse({"error": "Prompt is required."}, status=400)

    full_prompt = f"""
You are a smart travel assistant.

User request:
{prompt}

Your job:
- Suggest actual tourist places only
- Keep destination list practical and usable for map routing
- Each place must be on a separate bullet line
- For each place include a short reason and entry fee
- Then give a separate trip cost summary
- Do not mix places and cost summary together
- Keep response short, clean, and structured

Place count rules:
- If trip is 1 to 2 days: suggest 3 to 5 main places
- If trip is 3 to 4 days: suggest 5 to 7 places
- If trip is 5 to 7 days: suggest 7 to 10 places
- If trip is more than 7 days: include main places plus nearby places or day-trip places

Budget rules:
- Low budget: suggest fewer main places and cheaper attractions
- Medium budget: suggest balanced famous places
- High budget: include more famous places, premium attractions, and nearby trips

Important:
- Do not give too few places for longer trips
- For 5 days or more, do not stop at only 3 or 4 places unless the destination is very small
- Prefer famous places first
- Make sure the number of places matches the trip duration

Output format exactly like this:

## Recommended Destinations
- Place Name | Short reason | Entry Fee: ₹XXX
- Place Name | Short reason | Entry Fee: ₹XXX
- Place Name | Short reason | Entry Fee: ₹XXX

## Trip Cost Summary
- Hotel Cost: ₹XXXX
- Food Cost: ₹XXXX
- Travel Cost: ₹XXXX
- Total Entry Fee: ₹XXXX
- Final Estimated Total: ₹XXXX
"""

    if getattr(settings, "GEMINI_API_KEY", None):
        try:
            gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)

            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=full_prompt,
            )

            result_text = getattr(response, "text", None)
            if result_text and result_text.strip():
                return JsonResponse({
                    "result": result_text,
                    "provider": "gemini"
                })
        except Exception:
            pass

    if getattr(settings, "GROQ_API_KEY", None):
        try:
            groq_client = Groq(api_key=settings.GROQ_API_KEY)

            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a smart travel assistant. Return clean destination bullets and trip cost summary."
                    },
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ],
                temperature=0.7,
            )

            result_text = response.choices[0].message.content
            if result_text and result_text.strip():
                return JsonResponse({
                    "result": result_text,
                    "provider": "groq"
                })
        except Exception as e:
            return JsonResponse({
                "error": f"Both Gemini and Groq failed. Last error: {str(e)}"
            }, status=500)

    return JsonResponse({
        "error": "No AI provider is configured. Add GEMINI_API_KEY or GROQ_API_KEY."
    }, status=500)


@login_required
def trip_list(request):
    trips = Trip.objects.filter(user=request.user)
    return render(request, "trips/trips_list.html", {"trips": trips})


@login_required
def ai_chat(request):
    return render(request, "trips/ai_chat.html")


@login_required
def create_trip(request):
    if request.method == "POST":
        form = TripForm(request.POST)

        destinations = request.POST.getlist("destinations")

        cleaned_destinations = []
        for d in destinations:
            d = d.strip()
            if not d:
                continue

            d = d.split("|")[0].strip()
            d = d.split(":")[0].strip()

            if d and d not in cleaned_destinations:
                cleaned_destinations.append(d)

        destinations = cleaned_destinations

        if not destinations:
            form.add_error(None, "Please add at least one destination.")

        if form.is_valid():
            trip = form.save(commit=False)
            trip.user = request.user
            trip.country = form.cleaned_data["country"]
            trip.country_code = COUNTRY_CODE_MAP.get(trip.country, "in")
            trip.destination = " || ".join(destinations)
            trip.save()
            return redirect("trip_list")
    else:
        form = TripForm()

    return render(request, "trips/create_trip.html", {"form": form})


@login_required
def edit_trip(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)

    if request.method == "POST":
        form = TripForm(request.POST, instance=trip)

        destinations = request.POST.getlist("destinations")

        cleaned_destinations = []
        for d in destinations:
            d = d.strip()
            if not d:
                continue

            d = d.split("|")[0].strip()
            d = d.split(":")[0].strip()

            if d and d not in cleaned_destinations:
                cleaned_destinations.append(d)

        destinations = cleaned_destinations

        if not destinations:
            form.add_error(None, "Please add at least one destination.")

        if form.is_valid():
            trip = form.save(commit=False)
            trip.country = form.cleaned_data["country"]
            trip.country_code = COUNTRY_CODE_MAP.get(trip.country, "in")
            trip.destination = " || ".join(destinations)
            trip.save()
            return redirect("trip_list")
    else:
        form = TripForm(instance=trip)

    destination_list = [d.strip() for d in trip.destination.split("||") if d.strip()]

    return render(
        request,
        "trips/edit_trip.html",
        {
            "form": form,
            "trip": trip,
            "destination_list": destination_list,
        },
    )


@login_required
def delete_trip(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)

    if request.method == "POST":
        trip.delete()
        return redirect("trip_list")

    return render(request, "trips/delete_trip.html", {"trip": trip})


@login_required
def trip_detail(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)

    suggestions = generate_ai_suggestions(trip)
    destination_list = [d.strip() for d in trip.destination.split("||") if d.strip()]

    return render(
        request,
        "trips/trip_detail.html",
        {
            "trip": trip,
            "suggestions": suggestions,
            "destination_list": destination_list,
        },
    )


@csrf_exempt
@login_required
def save_ai_trip(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method is allowed."}, status=405)

    try:
        data = json.loads(request.body)

        destination = data.get("destination", "AI Generated Trip")
        plan = data.get("plan", "")
        country = data.get("country", "India")
        country_code = COUNTRY_CODE_MAP.get(country, "in")

        try:
            budget = Decimal(str(data.get("budget", 0)))
        except Exception:
            budget = Decimal("0")

        try:
            entry_fee = Decimal(str(data.get("entry_fee", 0)))
        except Exception:
            entry_fee = Decimal("0")

        trip = Trip.objects.create(
            user=request.user,
            destination=destination,
            country=country,
            country_code=country_code,
            start_location=data.get("start_location", ""),
            start_date=data.get("start_date", "2026-03-29"),
            end_date=data.get("end_date", "2026-03-31"),
            budget=budget,
            entry_fee=entry_fee,
            notes=data.get("notes", "Saved from AI planner"),
            ai_plan=plan,
        )

        return JsonResponse({"success": True, "trip_id": trip.id})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def start_planning(request):
    return render(request, "trips/start_planning.html")


@login_required
def map_view(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)

    destination_list = []
    for d in trip.destination.split(" || "):
        d = d.strip()
        if not d:
            continue

        d = d.split("|")[0].strip()

        bad_words = [
            "street food",
            "shopping",
            "nightlife",
            "water activities",
            "personal expenses",
            "activities extra",
        ]

        if any(word in d.lower() for word in bad_words):
            continue

        destination_list.append(d)

    places = []
    if trip.start_location:
        places.append(trip.start_location.strip())

    places.extend(destination_list)

    return render(
        request,
        "trips/map.html",
        {
            "trip": trip,
            "places": places,
            "destination_list": destination_list,
        },
    )


@login_required
def get_route_data(request):
    places = request.GET.getlist("places[]")

    if not places:
        places = request.GET.getlist("places")

    places = [p.strip() for p in places if p.strip()]

    print("PLACES FROM FRONTEND:", places)

    if not places or len(places) < 2:
        return JsonResponse({"error": "At least 2 places required"}, status=400)

    coords = []
    countries = []

    for place in places:
        place = place.split("|")[0].strip()

        bad_words = [
            "free",
            "entry",
            "atmosphere",
            "famous",
            "experience",
            "visit",
            "explore",
            "shopping",
            "nightlife",
            "street food",
            "water activities",
            "personal expenses",
            "activities extra",
        ]

        if any(word in place.lower() for word in bad_words):
            print("SKIPPED INVALID PLACE:", place)
            continue

        geo_url = "https://api.olakrutrim.com/geocoding/search"

        try:
            res = requests.get(
                geo_url,
                params={"query": place},
                headers={
                    "Authorization": f"Bearer {settings.OLA_API_KEY}"
                },
                timeout=20,
            )
            data = res.json()
            print("GEOCODE RESPONSE FOR", place, ":", data)
        except Exception as e:
            return JsonResponse({"error": f"Geocoding failed: {str(e)}"}, status=500)

        results = data.get("results", [])
        if not results:
            print("NO GEOCODE RESULT:", place)
            continue

        first_result = results[0]

        loc = first_result.get("location", {})
        lat = loc.get("lat")
        lng = loc.get("lng")

        if lat is None or lng is None:
            print("INVALID COORDS:", place)
            continue

        coords.append({
            "lat": lat,
            "lng": lng,
            "name": place
        })

        country = first_result.get("country", "")
        countries.append(country)

    print("VALID COORDS:", coords)

    if len(coords) < 2:
        return JsonResponse({"error": "Valid locations not found"}, status=400)

    clean_countries = [c.strip().lower() for c in countries if c]

    if len(set(clean_countries)) > 1:
        return JsonResponse({
            "coords": coords,
            "international": True
        })

    route_url = "https://api.olakrutrim.com/routing/directions"

    payload = {
        "waypoints": [{"lat": p["lat"], "lng": p["lng"]} for p in coords],
        "profile": "car"
    }

    print("ROUTE PAYLOAD:", payload)

    try:
        res = requests.post(
            route_url,
            json=payload,
            headers={
                "Authorization": f"Bearer {settings.OLA_API_KEY}",
                "Content-Type": "application/json"
            },
            timeout=25,
        )
        route_data = res.json()
        print("ROUTE RESPONSE:", route_data)
    except Exception as e:
        return JsonResponse({"error": f"Route API failed: {str(e)}"}, status=500)

    return JsonResponse({
        "coords": coords,
        "route": route_data,
        "international": False
    })