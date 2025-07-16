from flask import Flask, render_template, request, jsonify
import requests
import folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import os
from dotenv import load_dotenv
import json

load_dotenv()

app = Flask(__name__)

class TravelRecommender:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="travel_recommender")
        
        self.api_key = os.getenv('GOOGLE_PLACES_API_KEY')
        
    def get_current_location(self, lat, lng):
        """현재 위치 정보를 가져옵니다."""
        try:
            location = self.geolocator.reverse(f"{lat}, {lng}")
            return {
                'address': location.address,
                'latitude': lat,
                'longitude': lng
            }
        except Exception as e:
            return {
                'address': f"위치: {lat}, {lng}",
                'latitude': lat,
                'longitude': lng
            }
    
    def search_nearby_places(self, lat, lng, radius=5000, place_type='tourist_attraction'):
        """주변 여행지를 검색합니다."""
        if not self.api_key:
            # API 키가 없을 경우 샘플 데이터 반환
            return self.get_sample_places(lat, lng)
        
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        params = {
            'location': f"{lat},{lng}",
            'radius': radius,
            'type': place_type,
            'key': self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if data['status'] == 'OK':
                places = []
                for place in data['results']:
                    place_info = {
                        'name': place.get('name', ''),
                        'address': place.get('vicinity', ''),
                        'rating': place.get('rating', 0),
                        'types': place.get('types', []),
                        'latitude': place['geometry']['location']['lat'],
                        'longitude': place['geometry']['location']['lng'],
                        'distance': geodesic((lat, lng), 
                                           (place['geometry']['location']['lat'], 
                                            place['geometry']['location']['lng'])).kilometers
                    }
                    places.append(place_info)
                
                # 거리순으로 정렬
                places.sort(key=lambda x: x['distance'])
                return places[:10]  # 상위 10개만 반환
            else:
                return self.get_sample_places(lat, lng)
                
        except Exception as e:
            print(f"API 호출 오류: {e}")
            return self.get_sample_places(lat, lng)
    
    def get_sample_places(self, lat, lng):
        """샘플 여행지 데이터를 반환합니다."""
        sample_places = [
            {
                'name': '한강공원',
                'address': '서울특별시 영등포구 여의도동',
                'rating': 4.5,
                'types': ['park', 'tourist_attraction'],
                'latitude': lat + 0.01,
                'longitude': lng + 0.01,
                'distance': 1.2
            },
            {
                'name': '남산타워',
                'address': '서울특별시 용산구 남산공원길',
                'rating': 4.3,
                'types': ['tourist_attraction', 'point_of_interest'],
                'latitude': lat - 0.008,
                'longitude': lng + 0.005,
                'distance': 2.1
            },
            {
                'name': '경복궁',
                'address': '서울특별시 종로구 사직로',
                'rating': 4.7,
                'types': ['tourist_attraction', 'museum'],
                'latitude': lat + 0.015,
                'longitude': lng - 0.003,
                'distance': 3.5
            },
            {
                'name': '홍대거리',
                'address': '서울특별시 마포구 홍대로',
                'rating': 4.2,
                'types': ['tourist_attraction', 'shopping'],
                'latitude': lat - 0.012,
                'longitude': lng - 0.008,
                'distance': 4.2
            },
            {
                'name': '동대문디자인플라자',
                'address': '서울특별시 중구 을지로',
                'rating': 4.0,
                'types': ['tourist_attraction', 'shopping'],
                'latitude': lat + 0.018,
                'longitude': lng + 0.002,
                'distance': 5.1
            }
        ]
        return sample_places
    
    def create_map(self, current_location, places):
        """지도를 생성합니다."""
        # 현재 위치를 중심으로 지도 생성
        map_obj = folium.Map(
            location=[current_location['latitude'], current_location['longitude']],
            zoom_start=13
        )
        
        # 현재 위치 마커 추가
        folium.Marker(
            [current_location['latitude'], current_location['longitude']],
            popup=f"현재 위치<br>{current_location['address']}",
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(map_obj)
        
        # 여행지 마커 추가
        for place in places:
            folium.Marker(
                [place['latitude'], place['longitude']],
                popup=f"<b>{place['name']}</b><br>"
                      f"주소: {place['address']}<br>"
                      f"평점: {place['rating']}<br>"
                      f"거리: {place['distance']:.1f}km",
                icon=folium.Icon(color='blue', icon='star')
            ).add_to(map_obj)
        
        return map_obj

recommender = TravelRecommender()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_location', methods=['POST'])
def get_location():
    """현재 위치를 가져옵니다."""
    data = request.get_json()
    lat = float(data.get('latitude', 37.5665))
    lng = float(data.get('longitude', 126.9780))
    
    current_location = recommender.get_current_location(lat, lng)
    
    return jsonify({
        'success': True,
        'location': current_location
    })

@app.route('/search_places', methods=['POST'])
def search_places():
    """주변 여행지를 검색합니다."""
    data = request.get_json()
    lat = float(data.get('latitude', 37.5665))
    lng = float(data.get('longitude', 126.9780))
    radius = int(data.get('radius', 5000))
    place_type = data.get('place_type', 'tourist_attraction')
    
    current_location = recommender.get_current_location(lat, lng)
    places = recommender.search_nearby_places(lat, lng, radius, place_type)
    
    # 지도 생성
    map_obj = recommender.create_map(current_location, places)
    map_html = map_obj._repr_html_()
    
    return jsonify({
        'success': True,
        'location': current_location,
        'places': places,
        'map_html': map_html
    })

@app.route('/get_place_types')
def get_place_types():
    """사용 가능한 장소 타입을 반환합니다."""
    place_types = [
        {'value': 'tourist_attraction', 'label': '관광지'},
        {'value': 'restaurant', 'label': '레스토랑'},
        {'value': 'hotel', 'label': '호텔'},
        {'value': 'museum', 'label': '박물관'},
        {'value': 'park', 'label': '공원'},
        {'value': 'shopping_mall', 'label': '쇼핑몰'},
        {'value': 'cafe', 'label': '카페'},
        {'value': 'bar', 'label': '바'},
        {'value': 'movie_theater', 'label': '영화관'},
        {'value': 'amusement_park', 'label': '놀이공원'}
    ]
    return jsonify(place_types)

if __name__ == '__main__':
    import sys
    port = 5001
    if len(sys.argv) > 1 and sys.argv[1] == '--port':
        port = int(sys.argv[2])
    app.run(debug=True, host='0.0.0.0', port=port) 