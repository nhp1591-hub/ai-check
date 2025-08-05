#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
import pandas as pd
import numpy as np
from urllib.parse import urlparse
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import cgi
import urllib.parse
import base64
import io
from datetime import datetime
from scoring_logic import AIScoringLogic
from openai_scoring_logic import OpenAIScoringLogic

class AILiteracyScorer:
    def __init__(self):
        self.driver = None
        self.driver_initialized = False
        # OpenAI 채점 로직 초기화
        self.openai_scorer = OpenAIScoringLogic()
        
    def setup_driver(self):
        """Chrome 드라이버 설정 - 최적화된 버전"""
        if self.driver_initialized and self.driver:
            return True
            
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')
        chrome_options.add_argument('--disable-javascript')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(10)  # 10초 타임아웃
            self.driver_initialized = True
            return True
        except Exception as e:
            print(f"드라이버 설정 오류: {e}")
            return False
    
    def parse_gpt_share_link(self, url):
        """GPT 공유 링크 파싱 - 최적화된 버전"""
        if not self.setup_driver():
            return {
                'success': False,
                'error': 'Chrome 드라이버를 초기화할 수 없습니다.',
                'url': url
            }
        
        try:
            print(f'페이지 로딩 중: {url}')
            self.driver.get(url)
            
            # 페이지 로딩 대기 (단축)
            time.sleep(1.5)
            
            # 대화 내용 추출
            messages = self.extract_messages()
            
            # 제목 추출
            title = self.extract_title()
            
            return {
                'success': True,
                'title': title,
                'messages': messages,
                'url': url
            }
            
        except Exception as e:
            print(f'파싱 오류: {e}')
            return {
                'success': False,
                'error': str(e),
                'url': url
            }
    
    def extract_messages(self):
        """메시지 추출"""
        messages = []
        
        try:
            # 다양한 선택자로 메시지 컨테이너 찾기
            selectors = [
                '[data-message-author-role]',
                '[data-testid="conversation-turn"]',
                '.group',
                '.flex.flex-col.items-center',
                '.w-full.text-token-text-primary'
            ]
            
            message_containers = []
            for selector in selectors:
                containers = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if containers:
                    message_containers = containers
                    print(f'선택자 "{selector}"로 {len(containers)}개 컨테이너 발견')
                    break
            
            if not message_containers:
                print("메시지 컨테이너를 찾을 수 없습니다.")
                return messages
            
            for index, container in enumerate(message_containers):
                try:
                    # 역할 정보 추출 (여러 방법 시도)
                    role = None
                    
                    # 방법 1: data-message-author-role 속성
                    try:
                        role = container.get_attribute('data-message-author-role')
                    except:
                        pass
                    
                    # 방법 2: 부모 요소에서 역할 찾기
                    if not role:
                        try:
                            parent = container.find_element(By.XPATH, './..')
                            role = parent.get_attribute('data-message-author-role')
                        except:
                            pass
                    
                    # 방법 3: 클래스명으로 역할 추정
                    if not role:
                        try:
                            class_name = container.get_attribute('class')
                            if 'user' in class_name.lower():
                                role = 'user'
                            elif 'assistant' in class_name.lower():
                                role = 'assistant'
                        except:
                            pass
                    
                    # 방법 4: 인덱스 기반 추정 (짝수=사용자, 홀수=어시스턴트)
                    if not role:
                        role = 'user' if index % 2 == 0 else 'assistant'
                    
                    # 내용 추출 (여러 선택자 시도)
                    content = None
                    content_selectors = [
                        '.markdown',
                        '.prose',
                        '.text-token-text-primary',
                        'p',
                        'div[class*="text"]',
                        '.whitespace-pre-wrap'
                    ]
                    
                    for content_selector in content_selectors:
                        try:
                            content_elements = container.find_elements(By.CSS_SELECTOR, content_selector)
                            if content_elements:
                                content = content_elements[0].text.strip()
                                if content:
                                    break
                        except:
                            continue
                    
                    # 컨테이너 자체의 텍스트도 시도
                    if not content:
                        content = container.text.strip()
                    
                    if content and len(content) > 5:  # 의미있는 내용만 추가
                        messages.append({
                            'id': index,
                            'role': role,
                            'content': content
                        })
                        print(f'메시지 {index}: {role} - {content[:50]}...')
                        
                except Exception as e:
                    print(f'메시지 {index} 추출 실패: {e}')
                    continue
            
            # 메시지가 없으면 대안 방법 시도
            if not messages:
                print("대안 파싱 방법 시도...")
                all_text_elements = self.driver.find_elements(By.CSS_SELECTOR, 'p, div, span')
                for index, element in enumerate(all_text_elements):
                    try:
                        content = element.text.strip()
                        if len(content) > 10 and not any(skip in content.lower() for skip in ['chatgpt', 'log in', 'sign up', 'terms', 'privacy']):
                            role = 'user' if index % 2 == 0 else 'assistant'
                            messages.append({
                                'id': index,
                                'role': role,
                                'content': content
                            })
                    except:
                        continue
                        
        except Exception as e:
            print(f'메시지 추출 오류: {e}')
        
        print(f'총 {len(messages)}개 메시지 추출 완료')
        return messages
    
    def extract_title(self):
        """제목 추출"""
        try:
            title_selectors = ['h1', '.title', '[data-testid="conversation-title"]']
            for selector in title_selectors:
                try:
                    title_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    return title_element.text.strip()
                except:
                    continue
        except:
            pass
        
        return 'GPT 대화'
    
    def cleanup_driver(self):
        """드라이버 정리"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
            self.driver_initialized = False

class AILiteracyRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.scorer = AILiteracyScorer()
        # OpenAI 채점 로직 초기화
        self.openai_scorer = OpenAIScoringLogic()
        super().__init__(*args, **kwargs)
    
    def __del__(self):
        """소멸자에서 드라이버 정리"""
        if hasattr(self, 'scorer'):
            self.scorer.cleanup_driver()
        if hasattr(self, 'openai_scorer'):
            # OpenAI API 클라이언트 정리 (필요한 경우)
            pass
    
    def do_GET(self):
        """GET 요청 처리 - 메인 페이지 제공"""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            html_content = self.get_html_content()
            self.wfile.write(html_content.encode('utf-8'))
        elif self.path == '/styles.css':
            self.send_response(200)
            self.send_header('Content-type', 'text/css; charset=utf-8')
            self.end_headers()
            
            with open('styles.css', 'r', encoding='utf-8') as f:
                css_content = f.read()
            self.wfile.write(css_content.encode('utf-8'))
        elif self.path == '/script.js':
            self.send_response(200)
            self.send_header('Content-type', 'application/javascript; charset=utf-8')
            self.end_headers()
            
            with open('script.js', 'r', encoding='utf-8') as f:
                js_content = f.read()
            self.wfile.write(js_content.encode('utf-8'))
        elif self.path == '/favicon.ico':
            # favicon.ico 요청 처리 - 빈 응답으로 404 오류 방지
            self.send_response(204)  # No Content
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """POST 요청 처리 - API 엔드포인트"""
        if self.path == '/api/score':
            self.handle_score_request()
        else:
            self.send_response(404)
            self.end_headers()
    
    def handle_score_request(self):
        """채점 요청 처리"""
        try:
            # 요청 본문 읽기
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # JSON 파싱
            data = json.loads(post_data.decode('utf-8'))
            excel_data = data.get('file_data', '')  # Changed from 'excel_data' to 'file_data'
            
            if not excel_data:
                self.send_error_response('엑셀 데이터가 필요합니다.')
                return
            
            # Base64 디코딩
            try:
                # Base64 데이터에서 실제 데이터 부분만 추출
                if ',' in excel_data:
                    # data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,UEsDBBQAAAAI... 형태
                    excel_bytes = base64.b64decode(excel_data.split(',')[1])
                else:
                    # 순수 Base64 데이터
                    excel_bytes = base64.b64decode(excel_data)
                
                df = pd.read_excel(io.BytesIO(excel_bytes))
            except Exception as e:
                self.send_error_response(f'엑셀 파일 파싱 오류: {str(e)}')
                return
            
            # 채점 실행
            results = self.score_all_entries(df)
            
            # 응답 전송
            self.send_json_response(results)
            
        except json.JSONDecodeError:
            self.send_error_response('잘못된 JSON 형식입니다.')
        except Exception as e:
            self.send_error_response(f'서버 오류: {str(e)}')
    
    def score_all_entries(self, df):
        """모든 엔트리 채점"""
        results = []
        
        # 디버깅: 실제 컬럼명 출력
        print(f"\n=== 엑셀 파일 분석 ===")
        print(f"실제 컬럼명: {list(df.columns)}")
        print(f"총 행 수: {len(df)}")
        print(f"첫 번째 행 데이터:")
        if len(df) > 0:
            for col in df.columns:
                print(f"  {col}: {df.iloc[0][col]}")
        print("=" * 50)
        
        # 컬럼명 매핑
        column_mapping = {
            '부서': 'department',
            '성명': 'name', 
            '사번': 'employee_id',
            '과제명': 'task_name',
            '과제 소개': 'task_description',
            '과제소개': 'task_description',
            '과제 링크 제출': 'task_link',
            '과제링크 제출': 'task_link'
        }
        
        # 컬럼명 정규화
        df.columns = [column_mapping.get(col, col) for col in df.columns]
        
        # 디버깅: 매핑 후 컬럼명 출력
        print(f"매핑 후 컬럼명: {list(df.columns)}")
        
        # 최적화된 채점 처리
        for index, row in df.iterrows():
            try:
                print(f"\n=== {index+1}번째 엔트리 채점 중 ===")
                print(f"성명: {row.get('name', 'N/A')}")
                print(f"과제명: {row.get('task_name', 'N/A')}")
                
                task_link = row.get('task_link', '')
                task_description = row.get('task_description', '')
                
                if not task_link or pd.isna(task_link):
                    result = {
                        'index': index + 1,
                        'name': row.get('name', 'N/A'),
                        'department': row.get('department', 'N/A'),
                        'employee_id': row.get('employee_id', 'N/A'),
                        'task_name': row.get('task_name', 'N/A'),
                        'task_description': task_description,
                        'task_link': task_link,
                        'success': False,
                        'error': '과제 링크가 없습니다.',
                        'score': {
                            'total_score': 0,
                            'grade': 'C',
                            'details': {},
                            'feedback': '과제 링크가 없어 채점이 불가능합니다.'
                        }
                    }
                else:
                    # GPT 링크 파싱 (최적화된 버전)
                    parse_result = self.scorer.parse_gpt_share_link(task_link)
                    
                    if parse_result['success']:
                        # OpenAI API를 활용한 채점 실행
                        score_result = self.openai_scorer.score_with_openai(
                            parse_result['messages'], 
                            task_description,
                            row.get('task_name', 'N/A')
                        )
                        
                        result = {
                            'index': index + 1,
                            'name': row.get('name', 'N/A'),
                            'department': row.get('department', 'N/A'),
                            'employee_id': row.get('employee_id', 'N/A'),
                            'task_name': row.get('task_name', 'N/A'),
                            'task_description': task_description,
                            'task_link': task_link,
                            'success': True,
                            'parsed_title': parse_result.get('title', 'N/A'),
                            'message_count': len(parse_result.get('messages', [])),
                            'score': score_result
                        }
                    else:
                        result = {
                            'index': index + 1,
                            'name': row.get('name', 'N/A'),
                            'department': row.get('department', 'N/A'),
                            'employee_id': row.get('employee_id', 'N/A'),
                            'task_name': row.get('task_name', 'N/A'),
                            'task_description': task_description,
                            'task_link': task_link,
                            'success': False,
                            'error': parse_result.get('error', '파싱 실패'),
                            'score': {
                                'total_score': 0,
                                'grade': 'C',
                                'details': {},
                                'feedback': 'GPT 링크 파싱에 실패했습니다.'
                            }
                        }
                
                results.append(result)
                print(f"채점 완료: {result['score']['grade']} ({result['score']['total_score']}점)")
                
            except Exception as e:
                print(f"채점 오류: {e}")
                result = {
                    'index': index + 1,
                    'name': row.get('name', 'N/A'),
                    'department': row.get('department', 'N/A'),
                    'employee_id': row.get('employee_id', 'N/A'),
                    'task_name': row.get('task_name', 'N/A'),
                    'task_description': row.get('task_description', 'N/A'),
                    'task_link': row.get('task_link', 'N/A'),
                    'success': False,
                    'error': str(e),
                    'score': {
                        'total_score': 0,
                        'grade': 'C',
                        'details': {},
                        'feedback': f'채점 중 오류가 발생했습니다: {str(e)}'
                    }
                }
                results.append(result)
        
        # 통계 계산
        total_entries = len(results)
        successful_entries = len([r for r in results if r['success']])
        grades = [r['score']['grade'] for r in results if r['success']]
        scores = [r['score']['total_score'] for r in results if r['success']]
        
        # A/B/C 3등급 체계에 맞는 분포 계산
        grade_distribution = {}
        for grade in ['A', 'B', 'C']:
            grade_distribution[grade] = grades.count(grade)
        
        statistics = {
            'total_entries': total_entries,
            'successful_entries': successful_entries,
            'success_rate': (successful_entries / total_entries * 100) if total_entries > 0 else 0,
            'grade_distribution': grade_distribution,
            'average_score': np.mean(scores) if scores else 0,
            'max_score': max(scores) if scores else 0,
            'min_score': min(scores) if scores else 0
        }
        
        return {
            'success': True,
            'results': results,
            'statistics': statistics,
            'timestamp': datetime.now().isoformat()
        }
    
    def send_json_response(self, data):
        """JSON 응답 전송"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        response = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(response.encode('utf-8'))
    
    def send_error_response(self, message):
        """오류 응답 전송"""
        error_data = {
            'success': False,
            'error': message
        }
        self.send_json_response(error_data)
    
    def do_OPTIONS(self):
        """CORS preflight 요청 처리"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def get_html_content(self):
        """HTML 콘텐츠 반환"""
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
        <header class="header">
            <h1>🤖 AI 리터러시 챌린지 심사 시스템</h1>
            <p>서비스를 AI를 통해 자동으로 채점하세요!</p>
        </header>
        
        <div class="guide-section">
            <div class="guide-header">
                <span style="font-size: 2rem;">📋</span>
                <h2>사용 가이드</h2>
            </div>
            <div class="guide-content">
                <div class="guide-step">
                    <h3>1단계: 엑셀 파일 준비</h3>
                    <p>부서, 성명, 사번, 과제명, 과제소개, 과제링크 제출 컬럼이 포함된 엑셀 파일을 준비하세요.</p>
                </div>
                <div class="guide-step">
                    <h3>2단계: 파일 업로드</h3>
                    <p>파일 선택 버튼을 클릭하여 준비한 엑셀 파일을 업로드하세요.</p>
                </div>
                <div class="guide-step">
                    <h3>3단계: 채점 시작</h3>
                    <p>채점 시작 버튼을 클릭하면 AI가 자동으로 분석하고 평가합니다.</p>
                </div>
                <div class="guide-step">
                    <h3>4단계: 결과 확인</h3>
                    <p>채점 결과를 확인하고 필요시 CSV 또는 Excel 파일로 다운로드하세요.</p>
                </div>
            </div>
            <div style="text-align: center;">
                <button onclick="downloadSample()" class="download-btn">📥 샘플 파일 다운로드</button>
            </div>
        </div>

        <div class="guide-section">
            <div class="guide-header">
                <span style="font-size: 2rem;">🎯</span>
                <h2>채점 기준</h2>
            </div>
            <div class="guide-content">
                <div class="guide-step">
                    <h3>📊 평가 항목</h3>
                    <p><strong>과제 설명 분석 (30점)</strong><br>
                    • 과제의 명확성과 구체성<br>
                    • AI 활용 방안의 적절성<br>
                    • 업무 개선 효과의 실현 가능성</p>
                </div>
                <div class="guide-step">
                    <h3>🤖 GPT 대화 분석 (40점)</h3>
                    <p><strong>AI 활용 능력 평가</strong><br>
                    • 프롬프트 작성의 정확성<br>
                    • AI 응답의 품질과 활용도<br>
                    • 대화의 논리적 흐름과 완성도</p>
                </div>
                <div class="guide-step">
                    <h3>💡 창의성 및 혁신성 (20점)</h3>
                    <p><strong>혁신적 접근 방식</strong><br>
                    • 기존 방식 대비 개선점<br>
                    • AI 기술의 창의적 활용<br>
                    • 업무 효율성 증대 효과</p>
                </div>
                <div class="guide-step">
                    <h3>📈 실용성 (10점)</h3>
                    <p><strong>실제 적용 가능성</strong><br>
                    • 즉시 적용 가능한 수준<br>
                    • 조직 내 확산 가능성<br>
                    • 비용 대비 효과성</p>
                </div>
            </div>
            <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e3f2fd 100%); padding: 25px; border-radius: 16px; margin-top: 20px;">
                <h3 style="color: #1e3c72; margin-bottom: 15px; text-align: center;">🏆 등급 기준</h3>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; text-align: center;">
                    <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 20px; border-radius: 12px;">
                        <h4 style="margin-bottom: 10px;">A등급 (80-100점)</h4>
                        <p style="font-size: 0.9rem;">우수한 AI 활용 능력과 혁신적인 접근 방식으로 업무 개선 효과가 뛰어남</p>
                    </div>
                    <div style="background: linear-gradient(135deg, #ffc107 0%, #fd7e14 100%); color: white; padding: 20px; border-radius: 12px;">
                        <h4 style="margin-bottom: 10px;">B등급 (60-79점)</h4>
                        <p style="font-size: 0.9rem;">적절한 AI 활용으로 일정한 업무 개선 효과를 보이며 발전 가능성이 있음</p>
                    </div>
                    <div style="background: linear-gradient(135deg, #dc3545 0%, #e83e8c 100%); color: white; padding: 20px; border-radius: 12px;">
                        <h4 style="margin-bottom: 10px;">C등급 (0-59점)</h4>
                        <p style="font-size: 0.9rem;">AI 활용이 부족하거나 개선 효과가 미미하여 추가 학습이 필요함</p>
                    </div>
                </div>
            </div>
        </div>
        
        <main class="main">
            <div class="upload-section">
                <label for="fileInput" class="file-upload">
                    📁 엑셀 파일 선택
                    <input type="file" id="fileInput" accept=".xlsx,.xls">
                </label>
                <div class="upload-info">지원 형식: .xlsx, .xls</div>
                <button id="scoreButton" class="score-button" disabled>엑셀 파일을 선택하세요</button>
            </div>
            
            <div id="loading" class="loading">
                <div class="spinner"></div>
                <p>AI 서비스 과제를 분석하고 채점 중입니다...</p>
            </div>
            
            <div id="errorMessage" class="error-message" style="display: none;"></div>
            <div id="successMessage" class="success-message" style="display: none;"></div>
            
            <div id="resultsSection" class="results-section">
                <div class="statistics">
                    <div class="stat-card">
                        <div class="stat-number" id="totalEntries">0</div>
                        <div class="stat-label">총 과제 수</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="successfulEntries">0</div>
                        <div class="stat-label">성공한 과제</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="successRate">0%</div>
                        <div class="stat-label">성공률</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="averageScore">0</div>
                        <div class="stat-label">평균 점수</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="maxScore">0</div>
                        <div class="stat-label">최고 점수</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="minScore">0</div>
                        <div class="stat-label">최저 점수</div>
                    </div>
                </div>
                
                <div class="grade-distribution">
                    <div class="grade-badge grade-a">
                        <div class="grade-count" id="gradeACount">0</div>
                        <div class="grade-label">A</div>
                    </div>
                    <div class="grade-badge grade-b">
                        <div class="grade-count" id="gradeBCount">0</div>
                        <div class="grade-label">B</div>
                    </div>
                    <div class="grade-badge grade-c">
                        <div class="grade-count" id="gradeCCount">0</div>
                        <div class="grade-label">C</div>
                    </div>
                </div>
                
                <div class="table-container">
                    <table class="results-table">
                        <thead>
                            <tr>
                                <th>번호</th>
                                <th>부서</th>
                                <th>성명</th>
                                <th>과제명</th>
                                <th>점수/등급</th>
                                <th>상태</th>
                                <th>피드백</th>
                            </tr>
                        </thead>
                        <tbody id="resultsTableBody">
                        </tbody>
                    </table>
                    <div id="expandedFeedbackContainer"></div>
                </div>
                
                <div class="download-section">
                    <button class="download-btn" onclick="downloadResults('csv')">CSV 다운로드</button>
                    <button class="download-btn" onclick="downloadResults('excel')">Excel 다운로드</button>
                </div>
            </div>
        </main>
    </div>
    
    <script src="/script.js"></script>
</body>
</html>
        '''

def main():
    """메인 함수"""
    port = int(os.environ.get('PORT', 8001))
    
    print(f"AI 리터러시 채점 시스템이 포트 {port}에서 실행 중입니다.")
    print(f"http://localhost:{port}에서 접속하세요.")
    print("종료하려면 Ctrl+C를 누르세요.")
    
    try:
        server = HTTPServer(('localhost', port), AILiteracyRequestHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\\n서버를 종료합니다.")
    except Exception as e:
        print(f"서버 오류: {e}")

if __name__ == '__main__':
    main() 