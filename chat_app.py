from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
import requests
import json
import sqlite3
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv
import folium
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

class DifyClient:
    def __init__(self):
        self.api_key = os.getenv('DIFY_API_KEY')
        self.base_url = os.getenv('DIFY_BASE_URL', 'https://api.dify.ai')
        
    def chat_completion(self, messages, context=None):
        """Dify 채팅 완성 API 호출"""
        if not self.api_key:
            return self.get_fallback_response(messages[-1]['content'])
        
        url = f"{self.base_url}/v1/chat-messages"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'inputs': {},
            'query': messages[-1]['content'],
            'response_mode': 'streaming',
            'conversation_id': context.get('conversation_id') if context else None,
            'user': context.get('user_id') if context else 'anonymous'
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                return response.json()
            else:
                return self.get_fallback_response(messages[-1]['content'])
        except Exception as e:
            print(f"Dify API 오류: {e}")
            return self.get_fallback_response(messages[-1]['content'])
    
    def get_fallback_response(self, user_message):
        """API 키가 없을 때의 기본 응답"""
        # 간단한 의도 파악
        if any(word in user_message for word in ['맛집', '음식', '식당', '레스토랑', '카페']):
            return {
                'answer': '맛집을 찾고 계시는군요! 현재 위치를 알려주시면 주변의 인기 맛집들을 추천해드릴게요. 📍 위치를 설정해주세요.',
                'conversation_id': str(uuid.uuid4())
            }
        elif any(word in user_message for word in ['관광', '여행', '명소', '볼거리']):
            return {
                'answer': '관광지를 찾고 계시는군요! 현재 위치를 알려주시면 주변의 인기 관광지를 추천해드릴게요. 📍 위치를 설정해주세요.',
                'conversation_id': str(uuid.uuid4())
            }
        elif any(word in user_message for word in ['호텔', '숙박', '잔다']):
            return {
                'answer': '숙박 시설을 찾고 계시는군요! 현재 위치를 알려주시면 주변의 호텔과 게스트하우스를 추천해드릴게요. 📍 위치를 설정해주세요.',
                'conversation_id': str(uuid.uuid4())
            }
        else:
            return {
                'answer': '안녕하세요! 여행지 추천을 도와드릴게요. 어떤 종류의 장소를 찾고 계신가요? (맛집, 관광지, 호텔 등)',
                'conversation_id': str(uuid.uuid4())
            }

class DatabaseManager:
    def __init__(self):
        self.db_path = 'chat_history.db'
        self.init_database()
    
    def init_database(self):
        """데이터베이스 초기화"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 대화 히스토리 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                user_message TEXT,
                ai_response TEXT,
                location_data TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                intent TEXT,
                entities TEXT
            )
        ''')
        
        # 사용자 세션 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE,
                current_location TEXT,
                preferences TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_activity DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_chat(self, session_id, user_message, ai_response, location_data=None, intent=None, entities=None):
        """대화 저장"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO chat_history (session_id, user_message, ai_response, location_data, intent, entities)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session_id, user_message, ai_response, 
              json.dumps(location_data) if location_data else None,
              intent, json.dumps(entities) if entities else None))
        
        conn.commit()
        conn.close()
    
    def get_chat_history(self, session_id, limit=10):
        """대화 히스토리 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_message, ai_response, timestamp 
            FROM chat_history 
            WHERE session_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (session_id, limit))
        
        history = cursor.fetchall()
        conn.close()
        
        return [{'user': msg, 'ai': response, 'timestamp': ts} for msg, response, ts in history]
    
    def update_session_location(self, session_id, location_data):
        """세션 위치 정보 업데이트"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_sessions (session_id, current_location, last_activity)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (session_id, json.dumps(location_data)))
        
        conn.commit()
        conn.close()

class TravelRecommender:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="travel_chat_bot")
        self.api_key = os.getenv('GOOGLE_PLACES_API_KEY', 'AIzaSyBUM2enIXi8HZgaahsCuEYfFflCfn5gdUQ')
    
    def search_nearby_places(self, lat, lng, radius=5000, place_type='restaurant'):
        """주변 장소 검색"""
        if not self.api_key:
            return self.get_sample_places(lat, lng, place_type)
        
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
                    geometry = place.get('geometry', {}).get('location', {})
                    lat_ = geometry.get('lat')
                    lng_ = geometry.get('lng')
                    if lat_ is None or lng_ is None:
                        continue  # 위치 정보 없는 장소 제외
                    place_info = {
                        'name': place.get('name', ''),
                        'address': place.get('vicinity', ''),
                        'rating': place.get('rating', 0),
                        'types': place.get('types', []),
                        'latitude': lat_,
                        'longitude': lng_,
                        'distance': geodesic((lat, lng), (lat_, lng_)).kilometers
                    }
                    places.append(place_info)
                places.sort(key=lambda x: x['distance'])
                if not places:
                    return self.get_sample_places(lat, lng, place_type)
                return places[:5]
            else:
                return self.get_sample_places(lat, lng, place_type)
        except Exception as e:
            print(f"Places API 오류: {e}")
            return self.get_sample_places(lat, lng, place_type)
    
    def get_sample_places(self, lat, lng, place_type):
        """샘플 장소 데이터"""
        sample_data = {
            'restaurant': [
                {'name': '맛있는 파스타', 'address': '강남구 테헤란로', 'rating': 4.5, 'distance': 0.3},
                {'name': '이탈리안 레스토랑', 'address': '강남구 역삼동', 'rating': 4.2, 'distance': 0.5},
                {'name': '고급 스테이크하우스', 'address': '강남구 삼성동', 'rating': 4.7, 'distance': 0.8}
            ],
            'tourist_attraction': [
                {'name': '남산타워', 'address': '용산구 남산공원길', 'rating': 4.3, 'distance': 2.1},
                {'name': '경복궁', 'address': '종로구 사직로', 'rating': 4.7, 'distance': 3.5},
                {'name': '한강공원', 'address': '영등포구 여의도동', 'rating': 4.5, 'distance': 1.2}
            ],
            'hotel': [
                {'name': '그랜드 호텔', 'address': '강남구 테헤란로', 'rating': 4.6, 'distance': 0.4},
                {'name': '비즈니스 호텔', 'address': '강남구 역삼동', 'rating': 4.1, 'distance': 0.6},
                {'name': '리조트 호텔', 'address': '강남구 삼성동', 'rating': 4.8, 'distance': 1.0}
            ]
        }
        
        return sample_data.get(place_type, sample_data['restaurant'])
    
    def create_map(self, current_location, places):
        """지도 생성"""
        map_obj = folium.Map(
            location=[current_location['latitude'], current_location['longitude']],
            zoom_start=14
        )
        
        # 현재 위치 마커
        folium.Marker(
            [current_location['latitude'], current_location['longitude']],
            popup=f"현재 위치<br>{current_location['address']}",
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(map_obj)
        
        # 추천 장소 마커
        for place in places:
            lat = place.get('latitude')
            lng = place.get('longitude')
            if lat is None or lng is None:
                continue  # 위치 정보가 없으면 마커 추가하지 않음
            folium.Marker(
                [lat, lng],
                popup=f"<b>{place.get('name','')}</b><br>주소: {place.get('address','')}<br>평점: {place.get('rating','')}<br>거리: {place.get('distance',0):.1f}km",
                icon=folium.Icon(color='blue', icon='star')
            ).add_to(map_obj)
        
        return map_obj

# 전역 객체들
dify_client = DifyClient()
db_manager = DatabaseManager()
travel_recommender = TravelRecommender()

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('chat.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """채팅 API"""
    data = request.get_json()
    user_message = data.get('message', '')
    session_id = data.get('session_id', str(uuid.uuid4()))
    
    # Dify API 호출
    messages = [{'role': 'user', 'content': user_message}]
    context = {'conversation_id': session_id, 'user_id': session_id}
    
    response = dify_client.chat_completion(messages, context)
    ai_response = response.get('answer', '죄송합니다. 응답을 생성할 수 없습니다.')
    
    # 대화 저장
    db_manager.save_chat(session_id, user_message, ai_response)
    
    return jsonify({
        'success': True,
        'response': ai_response,
        'session_id': session_id
    })

@app.route('/api/location', methods=['POST'])
def set_location():
    """위치 설정 API"""
    data = request.get_json()
    lat = float(data.get('latitude', 37.5665))
    lng = float(data.get('longitude', 126.9780))
    session_id = data.get('session_id', str(uuid.uuid4()))
    
    try:
        location = travel_recommender.geolocator.reverse(f"{lat}, {lng}")
        location_data = {
            'address': location.address,
            'latitude': lat,
            'longitude': lng
        }
    except:
        location_data = {
            'address': f"위치: {lat}, {lng}",
            'latitude': lat,
            'longitude': lng
        }
    
    # 세션 위치 업데이트
    db_manager.update_session_location(session_id, location_data)
    
    return jsonify({
        'success': True,
        'location': location_data,
        'session_id': session_id
    })

@app.route('/api/places', methods=['POST'])
def search_places():
    """장소 검색 API"""
    data = request.get_json()
    lat = float(data.get('latitude', 37.5665))
    lng = float(data.get('longitude', 126.9780))
    place_type = data.get('place_type', 'restaurant')
    session_id = data.get('session_id', str(uuid.uuid4()))
    
    # 주변 장소 검색
    places = travel_recommender.search_nearby_places(lat, lng, 5000, place_type)
    
    # 지도 생성
    current_location = {'latitude': lat, 'longitude': lng, 'address': f"위치: {lat}, {lng}"}
    map_obj = travel_recommender.create_map(current_location, places)
    map_html = map_obj._repr_html_()
    
    return jsonify({
        'success': True,
        'places': places,
        'map_html': map_html,
        'session_id': session_id
    })

@app.route('/api/history/<session_id>')
def get_history(session_id):
    """대화 히스토리 조회"""
    history = db_manager.get_chat_history(session_id)
    return jsonify({
        'success': True,
        'history': history
    })

@socketio.on('connect')
def handle_connect():
    """WebSocket 연결"""
    session_id = str(uuid.uuid4())
    emit('session_id', {'session_id': session_id})

@socketio.on('message')
def handle_message(data):
    """WebSocket 메시지 처리"""
    user_message = data.get('message', '')
    session_id = data.get('session_id', str(uuid.uuid4()))
    
    # Dify API 호출
    messages = [{'role': 'user', 'content': user_message}]
    context = {'conversation_id': session_id, 'user_id': session_id}
    
    response = dify_client.chat_completion(messages, context)
    ai_response = response.get('answer', '죄송합니다. 응답을 생성할 수 없습니다.')
    
    # 대화 저장
    db_manager.save_chat(session_id, user_message, ai_response)
    
    emit('response', {
        'response': ai_response,
        'session_id': session_id
    })

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5002, allow_unsafe_werkzeug=True) 