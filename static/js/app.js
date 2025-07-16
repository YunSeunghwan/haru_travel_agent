// 전역 변수
let currentLocation = null;
let currentPlaces = [];

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // 반경 슬라이더 이벤트 리스너
    const radiusSlider = document.getElementById('radius');
    const radiusValue = document.getElementById('radiusValue');
    
    radiusSlider.addEventListener('input', function() {
        radiusValue.textContent = this.value;
    });
    
    // 기본 지도 초기화
    initializeMap();
}

function initializeMap() {
    // 기본 서울 시청 좌표로 지도 초기화
    const defaultLat = 37.5665;
    const defaultLng = 126.9780;
    
    // 간단한 지도 초기화 (실제 지도는 서버에서 생성됨)
    const mapContainer = document.getElementById('map');
    mapContainer.innerHTML = `
        <div style="width: 100%; height: 100%; background-color: #e9ecef; display: flex; align-items: center; justify-content: center;">
            <div style="text-align: center; color: #6c757d;">
                <i class="fas fa-map" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                <p>위치를 설정하고 여행지를 검색해보세요!</p>
            </div>
        </div>
    `;
}

function getCurrentLocation() {
    showLoading();
    
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function(position) {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                
                // 입력 필드 업데이트
                document.getElementById('latitude').value = lat;
                document.getElementById('longitude').value = lng;
                
                // 서버에 위치 정보 요청
                fetchLocationInfo(lat, lng);
            },
            function(error) {
                hideLoading();
                showAlert('위치를 가져올 수 없습니다. 수동으로 입력해주세요.', 'warning');
                console.error('Geolocation error:', error);
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 60000
            }
        );
    } else {
        hideLoading();
        showAlert('브라우저가 위치 서비스를 지원하지 않습니다.', 'warning');
    }
}

function fetchLocationInfo(lat, lng) {
    fetch('/get_location', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            latitude: lat,
            longitude: lng
        })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            currentLocation = data.location;
            displayLocationInfo(data.location);
            showAlert('현재 위치가 설정되었습니다!', 'success');
        } else {
            showAlert('위치 정보를 가져오는데 실패했습니다.', 'danger');
        }
    })
    .catch(error => {
        hideLoading();
        showAlert('서버 오류가 발생했습니다.', 'danger');
        console.error('Error:', error);
    });
}

function displayLocationInfo(location) {
    const locationInfo = document.getElementById('locationInfo');
    const currentAddress = document.getElementById('currentAddress');
    
    currentAddress.textContent = location.address;
    locationInfo.style.display = 'block';
    locationInfo.classList.add('fade-in');
}

function searchPlaces() {
    const lat = parseFloat(document.getElementById('latitude').value);
    const lng = parseFloat(document.getElementById('longitude').value);
    const radius = parseInt(document.getElementById('radius').value) * 1000; // km를 m로 변환
    const placeType = document.getElementById('placeType').value;
    
    if (isNaN(lat) || isNaN(lng)) {
        showAlert('올바른 위도와 경도를 입력해주세요.', 'warning');
        return;
    }
    
    showLoading();
    
    fetch('/search_places', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            latitude: lat,
            longitude: lng,
            radius: radius,
            place_type: placeType
        })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            currentLocation = data.location;
            currentPlaces = data.places;
            
            displayLocationInfo(data.location);
            displayPlaces(data.places);
            displayMap(data.map_html);
            
            showAlert(`${data.places.length}개의 여행지를 찾았습니다!`, 'success');
        } else {
            showAlert('여행지 검색에 실패했습니다.', 'danger');
        }
    })
    .catch(error => {
        hideLoading();
        showAlert('서버 오류가 발생했습니다.', 'danger');
        console.error('Error:', error);
    });
}

function displayPlaces(places) {
    const resultsCard = document.getElementById('resultsCard');
    const placesList = document.getElementById('placesList');
    
    if (places.length === 0) {
        placesList.innerHTML = '<p class="text-muted">검색 결과가 없습니다.</p>';
    } else {
        let html = '';
        places.forEach((place, index) => {
            const ratingStars = getRatingStars(place.rating);
            const typeBadges = place.types.slice(0, 3).map(type => 
                `<span class="place-type-badge">${getTypeLabel(type)}</span>`
            ).join('');
            
            html += `
                <div class="place-item fade-in" style="animation-delay: ${index * 0.1}s">
                    <div class="place-name">${place.name}</div>
                    <div class="place-address">
                        <i class="fas fa-map-marker-alt"></i> ${place.address}
                    </div>
                    <div class="place-rating">
                        <i class="fas fa-star"></i> ${ratingStars} (${place.rating})
                    </div>
                    <div class="place-distance">
                        <i class="fas fa-route"></i> ${place.distance.toFixed(1)}km
                    </div>
                    <div class="place-types">
                        ${typeBadges}
                    </div>
                </div>
            `;
        });
        placesList.innerHTML = html;
    }
    
    resultsCard.style.display = 'block';
    resultsCard.classList.add('fade-in');
}

function displayMap(mapHtml) {
    const mapContainer = document.getElementById('map');
    mapContainer.innerHTML = mapHtml;
}

function getRatingStars(rating) {
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 >= 0.5;
    const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);
    
    let stars = '';
    for (let i = 0; i < fullStars; i++) {
        stars += '<i class="fas fa-star"></i>';
    }
    if (hasHalfStar) {
        stars += '<i class="fas fa-star-half-alt"></i>';
    }
    for (let i = 0; i < emptyStars; i++) {
        stars += '<i class="far fa-star"></i>';
    }
    
    return stars;
}

function getTypeLabel(type) {
    const typeLabels = {
        'tourist_attraction': '관광지',
        'restaurant': '레스토랑',
        'hotel': '호텔',
        'museum': '박물관',
        'park': '공원',
        'shopping_mall': '쇼핑몰',
        'cafe': '카페',
        'bar': '바',
        'movie_theater': '영화관',
        'amusement_park': '놀이공원',
        'point_of_interest': '관심지점',
        'establishment': '시설',
        'shopping': '쇼핑'
    };
    
    return typeLabels[type] || type;
}

function showLoading() {
    document.getElementById('loading').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

function showAlert(message, type) {
    // Bootstrap 알림 생성
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // 5초 후 자동 제거
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// 키보드 이벤트 처리
document.addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
        if (event.target.id === 'latitude' || event.target.id === 'longitude') {
            searchPlaces();
        }
    }
});

// 반응형 디자인을 위한 리사이즈 이벤트
window.addEventListener('resize', function() {
    // 지도 리사이즈 (필요한 경우)
    const mapContainer = document.getElementById('map');
    if (mapContainer.innerHTML.includes('folium')) {
        // 지도가 로드된 경우 리사이즈 처리
        setTimeout(() => {
            if (window.map && typeof window.map.invalidateSize === 'function') {
                window.map.invalidateSize();
            }
        }, 100);
    }
}); 