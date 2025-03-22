from fastapi import APIRouter, Query
import httpx

geocode_router = APIRouter(
    prefix="/geocode",
    tags=["geocode"],
)

url = f"https://nominatim.openstreetmap.org/reverse"

@geocode_router.get("/reverse")
async def reverse_geocode(
        lat: float = Query(...),
        lng: float = Query(...),
):
    params = {
        "format": "json",
        "lat": lat,
        "lon": lng,
        "zoom": 18,
        "addressdetails": 1,
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers={"User-Agent": "PockeTourBot/1.0"})
        data = response.json()

    address = data.get("address", {})
    house_number = address.get("house_number")
    street = address.get("road") or address.get("pedestrian") or address.get("footway")
    city = address.get("city") or address.get("town") or address.get("village")
    country = address.get("country")

    return {
        "house_number": house_number,
        "street": street,
        "city": city,
        "country": country
    }