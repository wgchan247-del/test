import os
import json
import base64
import requests
import traceback

# Gemini API를 사용하여 이미지 바이트 데이터에서 음식 이름을 추천받습니다.
def suggest_foods_from_photo_bytes(image_bytes, file_type, api_key):
    """Gemini API를 사용하여 이미지 바이트 데이터에서 음식 이름을 추천받습니다."""
    print("\n--- [AI] 이미지 분석 요청 시작 ---")
    try:
        API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={api_key}"
        prompt = "이 사진에 보이는 음식들의 이름을 한국어로, JSON 문자열 배열 형식으로 간단히 나열해줘. 예: `[\"쌀밥\", \"김치찌개\", \"계란말이\"]`"
        
        print("1. 이미지를 Base64로 인코딩 중...")
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        request_body = { "contents": [{ "parts": [{ "text": prompt }, { "inlineData": { "mimeType": file_type, "data": base64_image } }] }] }
        
        print("2. Gemini API에 POST 요청 전송...")
        response = requests.post(API_URL, json=request_body, timeout=60)
        print(f"3. Gemini API로부터 응답 받음. 상태 코드: {response.status_code}")

        response.raise_for_status()

        print("4. API 응답을 JSON으로 파싱 중...")
        data = response.json()
        print("5. JSON 파싱 완료.")

        json_string = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '[]')
        print("6. 응답에서 텍스트 추출 완료.")
        
        json_string_cleaned = json_string.replace("```json", "").replace("```", "").strip()
        results = json.loads(json_string_cleaned)
        print("7. 텍스트를 JSON 객체로 변환 완료.")
        
        if isinstance(results, list) and all(isinstance(item, str) for item in results):
             print("8. 데이터 유효성 검사 통과. 성공!")
             return {'status': 'success', 'foodNames': results}
        else:
             print("8. 데이터 유효성 검사 실패.")
             raise ValueError("AI가 반환한 데이터가 유효한 JSON 배열 형식이 아닙니다.")

    except requests.exceptions.HTTPError as e:
        error_text = e.response.text
        print(f"!!! HTTP 오류 발생: {e.response.status_code}. 응답 내용: {error_text}")
        return {'status': 'error', 'message': f"Gemini API 오류: {e.response.status_code} - {error_text}"}
    except Exception as e:
        print(f"!!! 예상치 못한 오류 발생: {str(e)}")
        traceback.print_exc() # 터미널에 상세한 오류 내역 출력
        return {'status': 'error', 'message': f"서버 내부 처리 중 예상치 못한 오류 발생: {str(e)}"}

# Gemini API를 사용하여 텍스트에서 영양 정보를 분석합니다.
def analyze_nutrition_from_text(text, api_key):
    """Gemini API를 사용하여 텍스트에서 영양 정보를 분석합니다."""
    print("\n--- [AI] 텍스트 분석 요청 시작 ---")
    try:
        API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={api_key}"
        prompt = f"""당신은 한국 음식 데이터에 특화된 매우 정밀한 영양 분석 AI입니다. 다음 텍스트에 나열된 각 음식의 영양 정보를 분석하여 JSON 배열 형식으로 반환해 주세요.

        **[엄격히 준수해야 할 규칙]**
        1.  **JSON 형식:** 응답은 오직 유효한 JSON 배열이어야 합니다. 다른 설명이나 텍스트는 절대 포함하지 마세요. 각 객체는 `{{ "name": "음식 (양)", "calories": 숫자, "carbs": 숫자, "protein": 숫자, "fat": 숫자 }}` 형식을 따라야 합니다.
        2.  **이름과 양:** 'name' 필드에는 반드시 음식 이름과 일반적인 1인분 기준의 양(예: "쌀밥 (210g)")을 명시해야 합니다.
        3.  **영양소 현실성:**
            * **칼로리 계산:** 칼로리는 `(탄수화물 * 4) + (단백질 * 4) + (지방 * 9)` 공식에 거의 근접해야 합니다. 약간의 오차는 허용됩니다.
            * **탄수화물 수치:** '쌀밥', '라면'과 같은 탄수화물 위주 음식이라도 1인분(약 200-300g)의 탄수화물 함량은 60-90g 범위를 넘지 않도록 현실적으로 계산해야 합니다.
            * **총량 검사:** 'carbs', 'protein', 'fat'의 그램(g) 총합이 'name'에 명시된 총량(g)을 초과해서는 안 됩니다.
        4.  **0 값 금지:** 물을 제외한 모든 음식의 'calories'는 0이 될 수 없습니다. 모든 영양소 값은 0 이상이어야 합니다.

        **[입력 텍스트]**
        "{text}"

        **[출력 예시]**
        [
            {{ "name": "쌀밥 (210g)", "calories": 310, "carbs": 68, "protein": 6, "fat": 1 }},
            {{ "name": "김치찌개 (400g)", "calories": 250, "carbs": 15, "protein": 20, "fat": 12 }}
        ]"""
        
        request_body = { "contents": [{ "parts": [{ "text": prompt }] }] }
        response = requests.post(API_URL, json=request_body, timeout=60)
        response.raise_for_status()

        data = response.json()
        json_string = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '[]')
        json_string_cleaned = json_string.replace("```json", "").replace("```", "").strip()
        results = json.loads(json_string_cleaned)

        validated_results = [
            item for item in results 
            if isinstance(item, dict) and item.get('name') and isinstance(item.get('calories', 0), (int, float)) and item['calories'] > 0
        ]
        
        return {'status': 'success', 'nutritionInfo': validated_results}

    except requests.exceptions.HTTPError as e:
        error_text = e.response.text
        print(f"!!! HTTP 오류 발생: {e.response.status_code}. 응답 내용: {error_text}")
        return {'status': 'error', 'message': f"Gemini API 오류: {e.response.status_code} - {error_text}"}
    except Exception as e:
        print(f"!!! 예상치 못한 오류 발생: {str(e)}")
        traceback.print_exc()
        return {'status': 'error', 'message': f"서버 내부 처리 중 예상치 못한 오류 발생: {str(e)}"}

