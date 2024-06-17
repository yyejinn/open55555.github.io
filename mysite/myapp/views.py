from django.shortcuts import render, redirect
import requests
import pandas as pd
from datetime import datetime, timedelta
import os
from .models import Review
from .forms import ReviewForm, AdminAuthForm
from .utils import authenticate_admin

# CSV 파일을 읽어옵니다.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
csv_path = os.path.join(BASE_DIR, 'mysite/myapp/data/location_file.csv')
xy_df = pd.read_csv(csv_path)
# NaN 값을 0으로 대체합니다.
a_df = xy_df.fillna(0)

# 옷차림 데이터 세분화
clothing_data = {
    'temperature_range': ['매우 추운 날씨', '추운 날씨', '쌀쌀한 날씨', '선선한 날씨', '적당한 날씨', '따뜻한 날씨', '더운 날씨', '매우 더운 날씨'],
    'tops': ['두꺼운 패딩, 기모제품', '패딩, 니트', '자켓, 스웨터', '후드티, 맨투맨', '긴팔 셔츠, 얇은 자켓', '반팔 셔츠, 얇은 상의', '반팔 티셔츠', '민소매, 반팔'],
    'bottoms': ['기모제품, 두꺼운 청바지', '청바지, 두꺼운 슬랙스', '청바지, 슬랙스', '청바지, 면바지', '면바지, 얇은 청바지', '반바지, 치마', '반바지', '반바지, 얇은 바지'],
    'footwear': ['부츠, 방한화', '부츠, 스니커즈', '스니커즈, 구두', '구두, 운동화', '운동화, 로퍼', '샌들, 슬리퍼', '샌들, 슬리퍼', '샌들, 슬리퍼'],
    'accessories': ['목도리, 장갑, 귀마개', '장갑, 히트텍', '모자, 스카프', '얇은 스카프', '모자, 얇은 스카프', '선글라스, 모자', '선글라스, 모자', '선글라스, 모자']
}

temperature_ranges = [
    {'category': '매우 추운 날씨', 'temperature_range': (-30, -10)},
    {'category': '추운 날씨', 'temperature_range': (-10, 0)},
    {'category': '쌀쌀한 날씨', 'temperature_range': (0, 5)},
    {'category': '선선한 날씨', 'temperature_range': (5, 10)},
    {'category': '적당한 날씨', 'temperature_range': (10, 15)},
    {'category': '따뜻한 날씨', 'temperature_range': (15, 20)},
    {'category': '더운 날씨', 'temperature_range': (20, 25)},
    {'category': '매우 더운 날씨', 'temperature_range': (25, 40)}
]

def categorize_temperature(temp):
    for idx, temp_category in enumerate(temperature_ranges):
        if temp_category['temperature_range'][0] <= temp < temp_category['temperature_range'][1]:
            return idx
    return -1

def get_image_by_temperature(temperature):
    if temperature < -10:
        return 'myapp/images/very_cold.jpeg'
    elif -10 <= temperature < 0:
        return 'myapp/images/cold.jpeg'
    elif 0 <= temperature < 5:
        return 'myapp/images/chilly.jpeg'
    elif 5 <= temperature < 10:
        return 'myapp/images/cool.jpeg'
    elif 10 <= temperature < 15:
        return 'myapp/images/mild.jpeg'
    elif 15 <= temperature < 20:
        return 'myapp/images/pleasant.jpeg'
    elif 20 <= temperature < 25:
        return 'myapp/images/warm.jpeg'
    elif 25 <= temperature < 30:
        return 'myapp/images/hot.jpeg'
    else:
        return 'myapp/images/very_hot.jpeg'

def get_weather_and_recommendation(nx, ny, location):
    API_Key = "I8rsN/eXyw28QEDPY4YblMW9rMSLmoQvM6vXBo9FTRfCOALb0bvQs2ggVULQHlwnesuHCzVcu16/PcmI28dIEQ=="
    URL = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
    
    today = datetime.today()
    base_date = today.strftime("%Y%m%d")
    
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    
    # 현재 시각에서 가장 가까운 이전 30분 또는 정시 단위로 설정
    if minute >= 45:
        base_time = f"{hour:02d}30"
    elif minute >= 15:
        base_time = f"{hour:02d}00"
    else:
        base_time = f"{(hour-1):02d}30"
    
    # 디버깅 출력을 추가합니다
    print(f"현재 시각: {now}")
    print(f"설정된 base_time: {base_time}")
    
    params = {
        "serviceKey": API_Key,
        "dataType": "json",
        "base_date": base_date,
        "base_time": base_time,
        "nx": nx,
        "ny": ny,
        "numOfRows": 10,
        "pageNo": 1
    }
    
    print("Request URL:", URL)
    print("Request Params:", params)
    
    res = requests.get(URL, params=params)
    if res.status_code != 200:
        print(f"API request failed with status code {res.status_code}")
        return None
    
    try:
        response_json = res.json()
        print(response_json)
    except ValueError:
        print("Error parsing JSON response")
        return None
    
    items = response_json.get('response', {}).get('body', {}).get('items')
    if items is None:
        print("No weather data found")
        return None
    
    weather_data = {}
    for item in items['item']:
        if item['category'] == 'T1H':
            weather_data['tmp'] = item['obsrValue']
        if item['category'] == 'PTY':
            weather_code = item['obsrValue']
            if weather_code == '1':
                weather_state = '비'
            elif weather_code == '2':
                weather_state = '비/눈'
            elif weather_code == '3':
                weather_state = '눈'
            elif weather_code == '4':
                weather_state = '소나기'
            else:
                weather_state = '없음'
            weather_data['code'] = weather_code
            weather_data['state'] = weather_state
    
    temperature = float(weather_data.get('tmp', 0))
    recommendation = recommend_clothing(temperature, location)
    weather_data['recommendation'] = recommendation
    weather_data['image'] = get_image_by_temperature(temperature)
    
    return weather_data

def recommend_clothing(temperature, location):
    temp_category = categorize_temperature(temperature)
    if temp_category == -1:
        return "온도 범위를 벗어났습니다."
    
    recommendation = {
        'tops': clothing_data['tops'][temp_category],
        'bottoms': clothing_data['bottoms'][temp_category],
        'footwear': clothing_data['footwear'][temp_category],
        'accessories': clothing_data['accessories'][temp_category]
    }
    
    return recommendation

def weather(request):
    if request.method == 'POST':
        address = request.POST['address']
        address_parts = address.split(' ')
        
        if len(address_parts) < 3:
            return render(request, 'myapp/weather.html', {'error': '주소를 올바르게 입력해주세요.'})
        
        input_1단계 = address_parts[0]
        input_2단계 = address_parts[1]
        input_3단계 = address_parts[2]
        
        filters = {'1단계': input_1단계}
        if input_2단계 != '0':
            filters['2단계'] = input_2단계
        if input_3단계 != '0':
            filters['3단계'] = input_3단계
        
        filtered_df = a_df.copy()
        for key, value in filters.items():
            if value != '0':
                filtered_df = filtered_df[filtered_df[key] == value]
        
        if not filtered_df.empty:
            nx = filtered_df.iloc[0]['격자 X']
            ny = filtered_df.iloc[0]['격자 Y']
            weather_data = get_weather_and_recommendation(nx, ny, address)
            if weather_data is None:
                return render(request, 'myapp/weather.html', {'error': '날씨 데이터를 가져오지 못했습니다.'})
            return render(request, 'myapp/output.html', {'weather_data': weather_data})
        else:
            return render(request, 'myapp/weather.html', {'error': '조건에 맞춰 다시 입력해주세요.'})
    return render(request, 'myapp/weather.html')

def trend(request):
    return render(request, 'myapp/trend.html')

def method_of_use(request):
    return render(request, 'myapp/method_of_use.html')

def situation(request):
    return render(request, 'myapp/situation.html')

def season(request):
    return render(request, 'myapp/season.html')

def qna(request):
    reviews = Review.objects.all()
    review_form = ReviewForm()
    admin_auth_form = AdminAuthForm()
    context = {
        'reviews': reviews,
        'review_form': review_form,
        'admin_auth_form': admin_auth_form
    }
    return render(request, 'myapp/qna.html', context)

def post_review(request):
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('qna')
    return redirect('qna')

def delete_review(request, review_id):
    if request.method == 'POST':
        admin_auth_form = AdminAuthForm(request.POST)
        if admin_auth_form.is_valid():
            admin_id = admin_auth_form.cleaned_data['admin_id']
            password = admin_auth_form.cleaned_data['password']
            if authenticate_admin(admin_id, password):
                review = Review.objects.get(id=review_id)
                review.delete()
                return redirect('qna')
            else:
                return redirect('qna')  # 인증 실패 시 처리
    return redirect('qna')
