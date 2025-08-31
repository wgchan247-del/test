import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import vision_analyzer 

# --- 설정 ---
app = Flask(__name__)
# ❌ 기존 CORS 라이브러리 설정 대신 수동으로 헤더를 추가하는 방식으로 변경합니다.
# CORS(app, resources={r"/api/*": {"origins": "*"}})

@app.after_request
def after_request(response):
    """모든 응답에 CORS 헤더를 추가하여 브라우저의 접근을 허용합니다."""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- API 엔드포인트 정의 ---

# 1. 이미지로부터 음식 이름을 추천하는 API
@app.route('/api/suggest-foods-from-photo', methods=['POST'])
def suggest_foods_proxy():
    if not GEMINI_API_KEY:
        return jsonify({'status': 'error', 'message': '서버에 Gemini API 키가 설정되지 않았습니다.'}), 500

    if 'image' not in request.files:
        return jsonify({'status': 'error', 'message': '이미지 파일이 전송되지 않았습니다.'}), 400

    file = request.files['image']
    image_bytes = file.read()
    file_type = file.mimetype

    result = vision_analyzer.suggest_foods_from_photo_bytes(image_bytes, file_type, GEMINI_API_KEY)

    if result['status'] == 'success':
        return jsonify(result)
    else:
        return jsonify(result), 500

# 2. 텍스트로부터 영양 정보를 분석하는 API
@app.route('/api/analyze-text', methods=['POST'])
def analyze_text_proxy():
    if not GEMINI_API_KEY:
        return jsonify({'status': 'error', 'message': '서버에 Gemini API 키가 설정되지 않았습니다.'}), 500
        
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'status': 'error', 'message': '분석할 텍스트가 전송되지 않았습니다.'}), 400

    text_to_analyze = data['text']
    result = vision_analyzer.analyze_nutrition_from_text(text_to_analyze, GEMINI_API_KEY)
    
    if result['status'] == 'success':
        return jsonify(result)
    else:
        return jsonify(result), 500

# --- 서버 실행 ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

