# GPS 기반 여행지 추천 시스템

현재 위치 GPS 데이터를 기반으로 주변 여행지를 추천해주는 웹 애플리케이션입니다.

## 주요 기능

- 🌍 **현재 위치 자동 감지**: 브라우저 GPS를 통한 현재 위치 자동 설정
- 📍 **수동 위치 입력**: 위도/경도 수동 입력 지원
- 🔍 **다양한 장소 유형**: 관광지, 레스토랑, 호텔, 박물관, 공원 등
- 🗺️ **인터랙티브 지도**: Folium을 사용한 지도 시각화
- 📏 **검색 반경 조절**: 1km~50km 범위에서 검색 반경 설정
- ⭐ **평점 및 거리 정보**: 각 장소의 평점과 현재 위치로부터의 거리 표시
- 📱 **반응형 디자인**: 모바일과 데스크톱 모두 지원

## 기술 스택

### Backend
- **Flask**: Python 웹 프레임워크
- **Folium**: Python 지도 라이브러리
- **Geopy**: 지리 정보 처리 라이브러리
- **Requests**: HTTP 요청 라이브러리

### Frontend
- **HTML5/CSS3**: 마크업 및 스타일링
- **JavaScript (ES6+)**: 클라이언트 사이드 로직
- **Bootstrap 5**: 반응형 UI 프레임워크
- **Font Awesome**: 아이콘 라이브러리

### API
- **Google Places API**: 주변 장소 검색 (선택사항)
- **Nominatim**: 주소 역지오코딩

## 설치 및 실행

### 1. 저장소 클론
```bash
git clone <repository-url>
cd haru_20250709
```

### 2. Python 가상환경 생성 및 활성화
```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정 (선택사항)
Google Places API를 사용하려면:

1. `env_example.txt`를 `.env`로 복사
```bash
cp env_example.txt .env
```

2. `.env` 파일에서 Google Places API 키 설정
```bash
GOOGLE_PLACES_API_KEY=your_actual_api_key_here
```

### 5. 애플리케이션 실행
```bash
python app.py
```

### 6. 브라우저에서 접속
```
http://localhost:5000
```

## 사용법

### 1. 현재 위치 설정
- **자동 설정**: "현재 위치 가져오기" 버튼 클릭
- **수동 설정**: 위도/경도 입력 필드에 좌표 입력

### 2. 검색 옵션 설정
- **장소 유형**: 드롭다운에서 원하는 장소 유형 선택
- **검색 반경**: 슬라이더로 1km~50km 범위에서 설정

### 3. 여행지 검색
- "여행지 검색" 버튼 클릭
- 검색 결과가 사이드바에 표시되고 지도에 마커로 표시

### 4. 결과 확인
- **사이드바**: 장소 목록, 평점, 거리, 주소 정보
- **지도**: 현재 위치(빨간 마커)와 여행지(파란 마커) 표시

## API 키 설정 (선택사항)

Google Places API를 사용하면 실제 주변 장소 데이터를 가져올 수 있습니다:

1. [Google Cloud Console](https://console.cloud.google.com/)에서 프로젝트 생성
2. Places API 활성화
3. API 키 생성
4. `.env` 파일에 API 키 설정

API 키가 설정되지 않은 경우, 샘플 데이터가 표시됩니다.

## 프로젝트 구조

```
haru_20250709/
├── app.py                 # Flask 메인 애플리케이션
├── requirements.txt       # Python 의존성
├── env_example.txt       # 환경 변수 예시
├── README.md             # 프로젝트 문서
├── templates/
│   └── index.html        # 메인 HTML 템플릿
└── static/
    ├── css/
    │   └── style.css     # CSS 스타일
    └── js/
        └── app.js        # JavaScript 로직
```

## 주요 클래스 및 함수

### TravelRecommender 클래스
- `get_current_location()`: 현재 위치 정보 반환
- `search_nearby_places()`: 주변 장소 검색
- `create_map()`: 지도 생성
- `get_sample_places()`: 샘플 데이터 반환

### 주요 API 엔드포인트
- `GET /`: 메인 페이지
- `POST /get_location`: 위치 정보 가져오기
- `POST /search_places`: 주변 장소 검색
- `GET /get_place_types`: 사용 가능한 장소 유형

## 커스터마이징

### 새로운 장소 유형 추가
`app.py`의 `get_place_types()` 함수에서 장소 유형을 추가할 수 있습니다.

### 샘플 데이터 수정
`get_sample_places()` 메서드에서 샘플 데이터를 수정할 수 있습니다.

### UI 스타일 변경
`static/css/style.css`에서 스타일을 수정할 수 있습니다.

## 문제 해결

### GPS 권한 오류
- 브라우저에서 위치 권한을 허용해주세요
- HTTPS 환경에서 실행하는 것을 권장합니다

### API 키 오류
- Google Places API 키가 올바르게 설정되었는지 확인
- API 할당량을 초과하지 않았는지 확인

### 지도가 표시되지 않는 경우
- 인터넷 연결을 확인해주세요
- 브라우저 콘솔에서 오류 메시지를 확인해주세요

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 연락처

프로젝트에 대한 문의사항이 있으시면 이슈를 생성해주세요. 