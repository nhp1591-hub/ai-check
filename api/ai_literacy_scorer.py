from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import sys
from urllib.parse import urlparse, parse_qs
import io

# 상위 디렉토리의 모듈들을 import할 수 있도록 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 기존 모듈들 import
from openai_scoring_logic import OpenAIScoringLogic
from scoring_logic import ScoringLogic
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re

class AILiteracyRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.scoring_logic = ScoringLogic()
        self.openai_scoring = OpenAIScoringLogic()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html_content = self.get_html_content()
            self.wfile.write(html_content.encode('utf-8'))
        elif self.path == '/styles.css':
            self.send_response(200)
            self.send_header('Content-type', 'text/css')
            self.end_headers()
            
            css_content = self.get_css_content()
            self.wfile.write(css_content.encode('utf-8'))
        elif self.path == '/script.js':
            self.send_response(200)
            self.send_header('Content-type', 'application/javascript')
            self.end_headers()
            
            js_content = self.get_js_content()
            self.wfile.write(js_content.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == '/api/score':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                # 파일 데이터 파싱
                files = self.parse_multipart_data(post_data)
                
                if 'file' not in files:
                    self.send_error_response('파일이 업로드되지 않았습니다.')
                    return
                
                excel_file = files['file']
                results = self.process_excel_file(excel_file)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                
                response_data = {
                    'success': True,
                    'results': results
                }
                self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
                
            except Exception as e:
                self.send_error_response(f'처리 중 오류가 발생했습니다: {str(e)}')
        else:
            self.send_response(404)
            self.end_headers()
    
    def parse_multipart_data(self, data):
        # 간단한 multipart 파싱
        files = {}
        lines = data.split(b'\r\n')
        
        for i, line in enumerate(lines):
            if b'Content-Disposition: form-data' in line and b'filename=' in line:
                # 파일 데이터 시작
                filename_match = re.search(b'filename="([^"]+)"', line)
                if filename_match:
                    filename = filename_match.group(1).decode('utf-8')
                    
                    # 파일 내용 찾기
                    content_start = i + 3  # 헤더 건너뛰기
                    content = b''
                    for j in range(content_start, len(lines)):
                        if lines[j] == b'--' + data.split(b'--')[1].split(b'\r\n')[0]:
                            break
                        if j > content_start:
                            content += lines[j] + b'\r\n'
                    
                    files['file'] = content
        
        return files
    
    def process_excel_file(self, excel_data):
        try:
            # Excel 파일을 DataFrame으로 읽기
            df = pd.read_excel(io.BytesIO(excel_data))
            
            # 컬럼명 매핑
            column_mapping = {
                '부서': 'department',
                '성명': 'name', 
                '사번': 'employee_id',
                '과제명': 'task_name',
                '과제소개': 'task_description',
                '과제링크 제출': 'task_link'
            }
            
            # 컬럼명 변경
            df = df.rename(columns=column_mapping)
            
            results = []
            
            for index, row in df.iterrows():
                try:
                    name = row['name']
                    task_name = row['task_name']
                    task_link = row['task_link']
                    
                    print(f"=== {index+1}번째 엔트리 채점 중 ===")
                    print(f"성명: {name}")
                    print(f"과제명: {task_name}")
                    
                    # ChatGPT 링크에서 메시지 추출
                    messages = self.extract_chatgpt_messages(task_link)
                    
                    if messages:
                        # OpenAI API를 사용한 채점 시도
                        try:
                            score, feedback = self.openai_scoring.score_task(task_name, messages)
                            print(f"채점 완료: {score}")
                        except Exception as e:
                            print(f"OpenAI API 오류: {e}")
                            # 기본 채점 로직 사용
                            score, feedback = self.scoring_logic.score_task(task_name, messages)
                            print(f"기본 로직 채점 완료: {score}")
                    else:
                        score, feedback = "F", "메시지를 추출할 수 없습니다."
                        print("메시지 추출 실패")
                    
                    results.append({
                        'name': name,
                        'task_name': task_name,
                        'score': score,
                        'feedback': feedback
                    })
                    
                except Exception as e:
                    print(f"엔트리 처리 오류: {e}")
                    results.append({
                        'name': row.get('name', 'Unknown'),
                        'task_name': row.get('task_name', 'Unknown'),
                        'score': 'F',
                        'feedback': f'처리 오류: {str(e)}'
                    })
            
            return results
            
        except Exception as e:
            raise Exception(f"Excel 파일 처리 오류: {str(e)}")
    
    def extract_chatgpt_messages(self, url):
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            driver = webdriver.Chrome(options=chrome_options)
            
            try:
                print(f"페이지 로딩 중: {url}")
                driver.get(url)
                time.sleep(3)
                
                messages = []
                
                # ChatGPT 공유 링크에서 메시지 추출
                if '/s/' in url:  # 공유 링크
                    message_containers = driver.find_elements(By.CSS_SELECTOR, '[data-message-author-role]')
                    print(f"선택자 \"[data-message-author-role]\"로 {len(message_containers)}개 컨테이너 발견")
                    
                    for i, container in enumerate(message_containers):
                        try:
                            role = container.get_attribute('data-message-author-role')
                            content = container.text.strip()
                            if content:
                                messages.append(f"{role}: {content}")
                                print(f"메시지 {i}: {role} - {content[:100]}...")
                        except Exception as e:
                            print(f"메시지 {i} 추출 오류: {e}")
                
                elif '/g/' in url:  # GPT 링크
                    message_containers = driver.find_elements(By.CSS_SELECTOR, '.flex.flex-col.items-center')
                    print(f"선택자 \".flex.flex-col.items-center\"로 {len(message_containers)}개 컨테이너 발견")
                    
                    for i, container in enumerate(message_containers):
                        try:
                            content = container.text.strip()
                            if content:
                                # GPT 링크에서는 role을 추정
                                role = "assistant" if "assistant" in content.lower() else "user"
                                messages.append(f"{role}: {content}")
                                print(f"메시지 {i}: {role} - {content[:100]}...")
                        except Exception as e:
                            print(f"메시지 {i} 추출 오류: {e}")
                
                print(f"총 {len(messages)}개 메시지 추출 완료")
                return messages
                
            finally:
                driver.quit()
                
        except Exception as e:
            print(f"메시지 추출 오류: {e}")
            return []
    
    def send_error_response(self, message):
        self.send_response(400)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        
        response_data = {
            'success': False,
            'error': message
        }
        self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
    
    def get_html_content(self):
        return '''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 리터러시 채점 시스템</title>
    <link rel="stylesheet" href="/styles.css">
</head>
<body>
    <div class="container">
        <h1>🤖 AI 리터러시 채점 시스템</h1>
        <p class="description">Excel 파일을 업로드하여 AI 리터러시 과제를 자동으로 채점하세요.</p>
        
        <div class="upload-section">
            <form id="uploadForm" enctype="multipart/form-data">
                <div class="file-input-wrapper">
                    <input type="file" id="excelFile" name="file" accept=".xlsx,.xls" required>
                    <label for="excelFile" class="file-label">
                        <span class="file-icon">📁</span>
                        <span class="file-text">Excel 파일 선택</span>
                    </label>
                </div>
                <button type="submit" class="submit-btn">채점 시작</button>
            </form>
        </div>
        
        <div id="loading" class="loading hidden">
            <div class="spinner"></div>
            <p>채점 중입니다... 잠시만 기다려주세요.</p>
        </div>
        
        <div id="results" class="results hidden">
            <h2>📊 채점 결과</h2>
            <div id="resultsTable"></div>
        </div>
        
        <div id="error" class="error hidden">
            <h2>❌ 오류 발생</h2>
            <p id="errorMessage"></p>
        </div>
    </div>
    
    <script src="/script.js"></script>
</body>
</html>
        '''
    
    def get_css_content(self):
        return '''
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
}

.container {
    background: white;
    border-radius: 20px;
    padding: 40px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
    max-width: 800px;
    width: 100%;
    text-align: center;
}

h1 {
    color: #333;
    margin-bottom: 10px;
    font-size: 2.5em;
}

.description {
    color: #666;
    margin-bottom: 30px;
    font-size: 1.1em;
}

.upload-section {
    margin-bottom: 30px;
}

.file-input-wrapper {
    position: relative;
    margin-bottom: 20px;
}

#excelFile {
    position: absolute;
    opacity: 0;
    width: 100%;
    height: 100%;
    cursor: pointer;
}

.file-label {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
    border: 3px dashed #ddd;
    border-radius: 15px;
    cursor: pointer;
    transition: all 0.3s ease;
    background: #f8f9fa;
}

.file-label:hover {
    border-color: #667eea;
    background: #f0f2ff;
}

.file-icon {
    font-size: 2em;
    margin-right: 10px;
}

.file-text {
    font-size: 1.1em;
    color: #666;
}

.submit-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 15px 30px;
    border-radius: 10px;
    font-size: 1.1em;
    cursor: pointer;
    transition: all 0.3s ease;
    width: 100%;
}

.submit-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
}

.submit-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
}

.loading {
    text-align: center;
    padding: 40px;
}

.spinner {
    width: 50px;
    height: 50px;
    border: 5px solid #f3f3f3;
    border-top: 5px solid #667eea;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 20px;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.results {
    text-align: left;
}

.results h2 {
    color: #333;
    margin-bottom: 20px;
    text-align: center;
}

.results-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 20px;
    background: white;
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.results-table th,
.results-table td {
    padding: 15px;
    text-align: left;
    border-bottom: 1px solid #eee;
}

.results-table th {
    background: #f8f9fa;
    font-weight: 600;
    color: #333;
}

.results-table tr:hover {
    background: #f8f9fa;
}

.score {
    font-weight: bold;
    padding: 5px 10px;
    border-radius: 5px;
    text-align: center;
}

.score-A {
    background: #d4edda;
    color: #155724;
}

.score-B {
    background: #d1ecf1;
    color: #0c5460;
}

.score-C {
    background: #fff3cd;
    color: #856404;
}

.score-F {
    background: #f8d7da;
    color: #721c24;
}

.error {
    color: #721c24;
    background: #f8d7da;
    border: 1px solid #f5c6cb;
    border-radius: 10px;
    padding: 20px;
    margin-top: 20px;
}

.error h2 {
    color: #721c24;
    margin-bottom: 10px;
}

.hidden {
    display: none;
}

@media (max-width: 768px) {
    .container {
        padding: 20px;
        margin: 10px;
    }
    
    h1 {
        font-size: 2em;
    }
    
    .results-table {
        font-size: 0.9em;
    }
    
    .results-table th,
    .results-table td {
        padding: 10px 5px;
    }
}
        '''
    
    def get_js_content(self):
        return '''
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('uploadForm');
    const fileInput = document.getElementById('excelFile');
    const submitBtn = document.querySelector('.submit-btn');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const error = document.getElementById('error');
    const resultsTable = document.getElementById('resultsTable');
    const errorMessage = document.getElementById('errorMessage');
    
    // 파일 선택 시 라벨 업데이트
    fileInput.addEventListener('change', function() {
        const file = this.files[0];
        if (file) {
            const label = document.querySelector('.file-text');
            label.textContent = file.name;
            label.style.color = '#333';
        }
    });
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const file = fileInput.files[0];
        if (!file) {
            showError('파일을 선택해주세요.');
            return;
        }
        
        // UI 상태 변경
        showLoading();
        
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch('/api/score', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                showResults(data.results);
            } else {
                showError(data.error || '채점 중 오류가 발생했습니다.');
            }
            
        } catch (err) {
            showError('서버 연결 오류: ' + err.message);
        }
    });
    
    function showLoading() {
        loading.classList.remove('hidden');
        results.classList.add('hidden');
        error.classList.add('hidden');
        submitBtn.disabled = true;
    }
    
    function showResults(resultsData) {
        loading.classList.add('hidden');
        error.classList.add('hidden');
        results.classList.remove('hidden');
        
        let tableHTML = `
            <table class="results-table">
                <thead>
                    <tr>
                        <th>성명</th>
                        <th>과제명</th>
                        <th>점수</th>
                        <th>피드백</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        resultsData.forEach(result => {
            const scoreClass = result.score.startsWith('A') ? 'A' : 
                             result.score.startsWith('B') ? 'B' : 
                             result.score.startsWith('C') ? 'C' : 'F';
            
            tableHTML += `
                <tr>
                    <td>${result.name}</td>
                    <td>${result.task_name}</td>
                    <td><span class="score score-${scoreClass}">${result.score}</span></td>
                    <td>${result.feedback}</td>
                </tr>
            `;
        });
        
        tableHTML += '</tbody></table>';
        resultsTable.innerHTML = tableHTML;
        
        submitBtn.disabled = false;
    }
    
    function showError(message) {
        loading.classList.add('hidden');
        results.classList.add('hidden');
        error.classList.remove('hidden');
        errorMessage.textContent = message;
        submitBtn.disabled = false;
    }
});
        '''

# Vercel 서버리스 함수 핸들러
def handler(request, context):
    """Vercel 서버리스 함수 핸들러"""
    # 요청 정보 파싱
    method = request.get('method', 'GET')
    path = request.get('path', '/')
    headers = request.get('headers', {})
    body = request.get('body', '')
    
    # HTTP 서버 시뮬레이션
    class MockRequest:
        def __init__(self, method, path, headers, body):
            self.method = method
            self.path = path
            self.headers = headers
            self.body = body
    
    class MockResponse:
        def __init__(self):
            self.status_code = 200
            self.headers = {}
            self.body = ''
        
        def set_status(self, code):
            self.status_code = code
        
        def set_header(self, key, value):
            self.headers[key] = value
        
        def set_body(self, body):
            self.body = body
    
    # 핸들러 실행
    handler = AILiteracyRequestHandler(MockRequest(method, path, headers, body), ('localhost', 8001), None)
    response = MockResponse()
    
    if method == 'GET':
        handler.do_GET()
    elif method == 'POST':
        handler.do_POST()
    
    return {
        'statusCode': response.status_code,
        'headers': response.headers,
        'body': response.body
    } 