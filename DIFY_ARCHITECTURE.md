# Dify 기반 LLM 채팅 인터페이스 아키텍처

## 🎯 개요

기존 GPS 기반 여행지 추천 시스템을 Dify 플랫폼을 활용한 LLM 채팅 인터페이스로 전환하는 설계 문서입니다.

## 🏗️ 아키텍처 개요

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Dify Platform │
│   (Chat UI)     │◄──►│   (Flask API)   │◄──►│   (LLM Engine)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Map Display   │    │   Database      │    │   External APIs │
│   (Folium)      │    │   (SQLite)      │    │   (Places, etc) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 기술 스택

### Frontend
- **React/Vue.js**: 채팅 인터페이스
- **WebSocket**: 실시간 채팅
- **Folium**: 지도 표시
- **Bootstrap**: UI 프레임워크

### Backend
- **Flask**: API 서버
- **Dify SDK**: LLM 연동
- **SQLite**: 대화 히스토리 저장
- **WebSocket**: 실시간 통신

### LLM Platform
- **Dify**: LLM 애플리케이션 플랫폼
- **OpenAI GPT-4/Claude**: 대화 모델
- **Vector Database**: 임베딩 저장

## 📋 핵심 기능

### 1. 대화형 여행지 추천
```
사용자: "서울에서 맛있는 파스타 먹을 수 있는 곳 추천해줘"
AI: "서울에서 맛있는 파스타를 찾고 계시는군요! 현재 위치를 알려주시면 
     주변의 인기 파스타 맛집들을 추천해드릴게요. 
     
     📍 현재 위치를 설정해주세요:
     - GPS 자동 감지
     - 수동 위치 입력
     - 주소 검색"
```

### 2. 컨텍스트 기반 추천
- 대화 히스토리 기반 개인화
- 사용자 선호도 학습
- 계절/날씨 고려 추천

### 3. 자연어 위치 입력
```
사용자: "강남역 근처에서"
AI: "강남역 근처를 검색해드릴게요! 
     📍 위치: 강남역 (위도: 37.498, 경도: 127.027)
     
     어떤 종류의 장소를 찾고 계신가요?"
```

## 🗂️ 데이터 구조

### 대화 히스토리
```sql
CREATE TABLE chat_history (
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    user_message TEXT,
    ai_response TEXT,
    location_data JSON,
    timestamp DATETIME,
    intent TEXT,
    entities JSON
);
```

### 사용자 세션
```sql
CREATE TABLE user_sessions (
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    current_location JSON,
    preferences JSON,
    created_at DATETIME,
    last_activity DATETIME
);
```

## 🔄 워크플로우

### 1. 사용자 입력 처리
```
사용자 메시지 → 의도 파악 → 엔티티 추출 → 컨텍스트 분석
```

### 2. LLM 응답 생성
```
컨텍스트 + 사용자 입력 → Dify API 호출 → 응답 생성 → 포맷팅
```

### 3. 지도 업데이트
```
위치 정보 → Places API 호출 → 지도 마커 업데이트 → 결과 표시
```

## 🎨 UI/UX 설계

### 채팅 인터페이스
```
┌─────────────────────────────────────┐
│  🗺️ 여행지 추천 AI 어시스턴트        │
├─────────────────────────────────────┤
│                                     │
│  🤖 안녕하세요! 여행지 추천을         │
│     도와드릴게요.                   │
│                                     │
│  👤 서울에서 맛있는 파스타           │
│     먹을 수 있는 곳 추천해줘        │
│                                     │
│  🤖 서울에서 맛있는 파스타를         │
│     찾고 계시는군요!                │
│                                     │
│  [📍 위치 설정] [🍝 맛집] [🏨 호텔]  │
│                                     │
├─────────────────────────────────────┤
│  💬 메시지를 입력하세요...          │
│  [📎] [🎤] [📤]                    │
└─────────────────────────────────────┘
```

### 지도 인터페이스
```
┌─────────────────────────────────────┐
│  🗺️ 지도 뷰                        │
│                                     │
│  [현재 위치] [추천 장소들]           │
│                                     │
│  📍 강남역                          │
│  🍝 파스타 맛집 A (4.5★, 0.3km)     │
│  🍝 파스타 맛집 B (4.2★, 0.5km)     │
│                                     │
└─────────────────────────────────────┘
```

## 🔌 API 설계

### Dify API 연동
```python
# Dify API 클라이언트
class DifyClient:
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url
    
    def chat_completion(self, messages, context=None):
        # Dify 채팅 완성 API 호출
        pass
    
    def extract_intent(self, message):
        # 의도 추출
        pass
    
    def extract_entities(self, message):
        # 엔티티 추출 (위치, 장소 유형 등)
        pass
```

### Flask API 엔드포인트
```python
@app.route('/api/chat', methods=['POST'])
def chat():
    # 채팅 메시지 처리
    
@app.route('/api/location', methods=['POST'])
def set_location():
    # 위치 설정
    
@app.route('/api/places', methods=['GET'])
def get_places():
    # 주변 장소 검색
    
@app.route('/api/map', methods=['POST'])
def update_map():
    # 지도 업데이트
```

## 🚀 구현 단계

### Phase 1: 기본 채팅 인터페이스
- [ ] Dify 플랫폼 설정
- [ ] 채팅 UI 구현
- [ ] 기본 대화 기능

### Phase 2: 위치 기반 기능
- [ ] GPS 연동
- [ ] 지도 표시
- [ ] 장소 검색

### Phase 3: 고급 기능
- [ ] 컨텍스트 기반 추천
- [ ] 개인화
- [ ] 음성 입력

### Phase 4: 최적화
- [ ] 성능 최적화
- [ ] 사용자 경험 개선
- [ ] 테스트 및 배포

## 🔧 설정 가이드

### Dify 설정
1. Dify 계정 생성
2. 새로운 애플리케이션 생성
3. API 키 발급
4. 프롬프트 템플릿 설정

### 환경 변수
```bash
DIFY_API_KEY=your_dify_api_key
DIFY_BASE_URL=https://api.dify.ai
OPENAI_API_KEY=your_openai_key
GOOGLE_PLACES_API_KEY=your_places_key
```

## 📊 성능 지표

- 응답 시간: < 2초
- 정확도: > 90%
- 사용자 만족도: > 4.5/5
- 대화 완성률: > 85%

## 🔗 관련 링크

- [Dify 공식 문서](https://docs.dify.ai/)
- [Dify API 문서](https://docs.dify.ai/api-reference)
- [OpenAI API 문서](https://platform.openai.com/docs)
- [Google Places API](https://developers.google.com/maps/documentation/places/web-service) 