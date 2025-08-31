import os
import base64
import requests
import json
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- Flask 앱 설정 ---
app = Flask(__name__)
# 다른 도메인(HTML 파일)에서 오는 요청을 허용하기 위해 CORS 설정
CORS(app) 

# --- Gemini API 키 환경 변수에서 가져오기 ---
# ❗️ 매우 중요: 이 코드를 실행하기 전에 터미널/CMD에서 API 키를 환경 변수로 설정해야 합니다.
# (Windows) set GEMINI_API_KEY=여러분의_API_키
# (macOS/Linux) export GEMINI_API_KEY=여러분의_API_키
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- Gemini API 엔드포인트 ---
GEMINI_PRO_VISION_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-vision:generateContent?key={GEMINI_API_KEY}"
GEMINI_PRO_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"

# --- API 라우트 정의 ---

@app.route("/api/suggest-foods-from-photo", methods=['POST'])
def suggest_foods_from_photo():
    """사진을 받아 Gemini Vision API로 음식 목록을 요청하는 엔드포인트"""
    print("--- [AI] 이미지 분석 요청 시작 ---")
    if not GEMINI_API_KEY:
        print("!!! 오류: GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")
        return jsonify({"status": "error", "message": "서버에 API 키가 설정되지 않았습니다."}), 500

    if 'image' not in request.files:
        return jsonify({"status": "error", "message": "이미지 파일이 없습니다."}), 400

    image_file = request.files['image']
    
    try:
        # 1. 이미지를 Base64로 인코딩
        print("1. 이미지를 Base64로 인코딩 중...")
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

        # 2. Gemini API에 보낼 데이터 구성
        payload = {
            "contents": [{
                "parts": [
                    {"text": "사진에 있는 음식들의 이름을 쉼표로만 구분해서 알려줘. 다른 설명은 절대 붙이지 마. 예시: 김치찌개,계란후라이,쌀밥"},
                    {"inline_data": {"mime_type": image_file.mimetype, "data": encoded_image}}
                ]
            }]
        }
        
        # 3. Gemini API에 POST 요청 전송
        print("2. Gemini API에 POST 요청 전송...")
        headers = {"Content-Type": "application/json"}
        response = requests.post(GEMINI_PRO_VISION_URL, headers=headers, json=payload)
        response.raise_for_status() # 200번대 응답이 아니면 예외 발생

        print(f"3. Gemini API로부터 응답 받음. 상태 코드: {response.status_code}")
        result = response.json()
        
        # 4. 응답에서 텍스트 추출 및 파싱
        food_text = result['candidates'][0]['content']['parts'][0]['text']
        food_names = [name.strip() for name in food_text.split(',')]
        
        print(f"4. 분석된 음식 목록: {food_names}")
        return jsonify({"status": "success", "foodNames": food_names})

    except requests.exceptions.RequestException as e:
        print(f"!!! HTTP 오류 발생: {e.response.status_code}. 응답 내용: {e.response.text}")
        return jsonify({"status": "error", "message": "AI 서버와 통신 중 오류가 발생했습니다."}), 500
    except (KeyError, IndexError) as e:
        print(f"!!! AI 응답 파싱 오류: {e}. 받은 데이터: {result}")
        return jsonify({"status": "error", "message": "AI의 응답 형식이 올바르지 않습니다."}), 500
    except Exception as e:
        print(f"!!! 알 수 없는 오류 발생: {e}")
        return jsonify({"status": "error", "message": "서버 내부 오류가 발생했습니다."}), 500


@app.route("/api/analyze-text", methods=['POST'])
def analyze_text():
    """텍스트(음식 목록)를 받아 Gemini API로 영양 정보를 요청하는 엔드포인트"""
    print("--- [AI] 텍스트 분석 요청 시작 ---")
    if not GEMINI_API_KEY:
        print("!!! 오류: GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")
        return jsonify({"status": "error", "message": "서버에 API 키가 설정되지 않았습니다."}), 500

    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"status": "error", "message": "분석할 텍스트가 없습니다."}), 400
    
    food_text = data['text']
    
    try:
        # 1. Gemini API에 보낼 데이터 구성
        prompt = f"""
        다음 음식 목록의 각 항목에 대한 영양 정보를 분석해줘.
        응답은 반드시 아래의 JSON 형식과 동일한 구조의 배열로만 제공해줘. 다른 설명이나 코멘트는 절대 추가하지 마.
        각 음식의 양은 일반적인 1인분 기준으로 계산해줘. 칼로리, 탄수화물, 단백질, 지방은 모두 숫자로만 표시해줘.
        
        음식 목록: "{food_text}"

        JSON 형식:
        [
          {{
            "name": "음식 이름",
            "calories": 숫자,
            "carbs": 숫자,
            "protein": 숫자,
            "fat": 숫자
          }}
        ]
        """
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }

        # 2. Gemini API에 POST 요청
        print(f"1. 다음 텍스트 분석 요청: {food_text}")
        headers = {"Content-Type": "application/json"}
        response = requests.post(GEMINI_PRO_URL, headers=headers, json=payload)
        response.raise_for_status()

        print(f"2. Gemini API로부터 응답 받음. 상태 코드: {response.status_code}")
        result = response.json()
        
        # 3. 응답에서 JSON 텍스트 추출 및 파싱
        json_text = result['candidates'][0]['content']['parts'][0]['text']
        # Gemini가 응답에 ```json ... ``` 같은 마크다운을 포함할 수 있으므로 제거
        if '```json' in json_text:
            json_text = json_text.split('```json')[1].split('```')[0].strip()
            
        nutrition_info = json.loads(json_text)
        
        print(f"3. 분석된 영양 정보: {nutrition_info}")
        return jsonify({"status": "success", "nutritionInfo": nutrition_info})

    except requests.exceptions.RequestException as e:
        print(f"!!! HTTP 오류 발생: {e.response.status_code}. 응답 내용: {e.response.text}")
        return jsonify({"status": "error", "message": "AI 서버와 통신 중 오류가 발생했습니다."}), 500
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"!!! AI 응답 파싱 오류: {e}. 받은 데이터: {result}")
        return jsonify({"status": "error", "message": "AI의 응답 형식이 올바르지 않습니다."}), 500
    except Exception as e:
        print(f"!!! 알 수 없는 오류 발생: {e}")
        return jsonify({"status": "error", "message": "서버 내부 오류가 발생했습니다."}), 500

# --- 서버 실행 ---
if __name__ == "__main__":
    app.run(debug=True, port=5000)
