# AI 리터러시 챌린지 심사 시스템

AI를 통해 서비스를 자동으로 채점하는 웹 애플리케이션입니다.

## 🚀 주요 기능

### 📊 AI 기반 자동 채점
- **OpenAI GPT-3.5-turbo** API를 활용한 지능형 평가
- **과제 설명 분석** (30점): 명확성, AI 활용 방안, 실현 가능성
- **GPT 대화 분석** (40점): 프롬프트 작성, AI 응답 품질, 대화 완성도
- **창의성 및 혁신성** (20점): 기존 방식 대비 개선점, 새로운 아이디어
- **실용성** (10점): 즉시 적용 가능성, 조직 내 확산 가능성

### 📈 등급 시스템
- **A등급** (80-100점): 우수한 AI 활용 능력과 혁신적 접근
- **B등급** (60-79점): 적절한 AI 활용으로 일정한 개선 효과
- **C등급** (0-59점): AI 활용 부족, 추가 학습 필요

### 🔗 GPT 공유 링크 분석
- **Selenium WebDriver**를 활용한 자동 웹 스크래핑
- **ChatGPT 공유 링크** 자동 파싱 및 대화 내용 추출
- **사용자/어시스턴트 대화** 모두 분석

### 📁 엑셀 파일 처리
- **Excel 파일 업로드** (.xlsx, .xls 지원)
- **필수 컬럼**: 부서, 성명, 과제명, 과제소개, 과제링크
- **대량 처리**: 여러 과제 동시 채점

### 🎨 직관적인 UI/UX
- **반응형 디자인**: 모든 디바이스에서 최적화
- **실시간 피드백**: 토글 버튼으로 상세 피드백 확인
- **통계 대시보드**: 전체 성과 및 등급 분포 시각화
- **결과 다운로드**: CSV/Excel 형식으로 결과 저장

## 🛠️ 기술 스택

### Backend
- **Python 3.9+**
- **HTTP Server**: Python built-in `http.server`
- **Web Scraping**: Selenium WebDriver
- **Data Processing**: Pandas, NumPy
- **AI Integration**: OpenAI API (gpt-3.5-turbo)

### Frontend
- **HTML5/CSS3**: 반응형 웹 디자인
- **Vanilla JavaScript**: ES6+ 모던 자바스크립트
- **CSS Grid/Flexbox**: 레이아웃 시스템

### Deployment
- **Vercel**: 서버리스 배포 플랫폼
- **GitHub**: 버전 관리 및 소스 코드 저장

## 📦 설치 및 실행

### 로컬 개발 환경

1. **저장소 클론**
```bash
git clone https://github.com/your-username/ai-literacy-check.git
cd ai-literacy-check
```

2. **Python 가상환경 생성**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. **의존성 설치**
```bash
pip install -r requirements.txt
```

4. **Chrome WebDriver 설치**
```bash
# Windows
# ChromeDriver를 다운로드하여 PATH에 추가

# macOS
brew install chromedriver

# Linux
sudo apt-get install chromium-chromedriver
```

5. **서버 실행**
```bash
python ai_literacy_scorer.py
```

6. **브라우저에서 접속**
```
http://localhost:8001
```

### 환경 변수 설정

`.env` 파일을 생성하고 OpenAI API 키를 설정하세요:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

## 🚀 배포

### Vercel 배포

1. **GitHub에 푸시**
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

2. **Vercel 연결**
- [Vercel](https://vercel.com)에 로그인
- GitHub 저장소 연결
- 자동 배포 설정

3. **환경 변수 설정**
- Vercel 대시보드에서 `OPENAI_API_KEY` 환경 변수 설정

### 배포 URL
```
https://your-project-name.vercel.app
```

## 📋 사용 방법

### 1. 엑셀 파일 준비
다음 컬럼을 포함한 Excel 파일을 준비하세요:
- **부서**: 소속 부서명
- **성명**: 평가 대상자 이름
- **과제명**: 수행한 과제 제목
- **과제소개**: 과제에 대한 간단한 설명
- **과제링크**: ChatGPT 공유 링크

### 2. 파일 업로드
- 웹페이지에서 "엑셀 파일 선택" 버튼 클릭
- 준비한 Excel 파일 선택

### 3. 채점 실행
- "채점 시작" 버튼 클릭
- 자동으로 GPT 링크 분석 및 AI 평가 진행

### 4. 결과 확인
- **통계 대시보드**: 전체 성과 및 등급 분포
- **상세 결과**: 각 과제별 점수 및 피드백
- **피드백 토글**: 상세한 평가 내용 확인

### 5. 결과 다운로드
- **CSV 다운로드**: 간단한 결과 파일
- **Excel 다운로드**: 상세한 분석 결과

## 🔧 프로젝트 구조

```
ai-literacy-check/
├── ai_literacy_scorer.py      # 메인 서버 파일
├── openai_scoring_logic.py    # OpenAI API 채점 로직
├── scoring_logic.py          # 기본 채점 로직 (fallback)
├── requirements.txt          # Python 의존성
├── styles.css               # CSS 스타일시트
├── script.js                # JavaScript 기능
├── vercel.json              # Vercel 배포 설정
├── runtime.txt              # Python 런타임 버전
├── .gitignore               # Git 제외 파일
└── README.md                # 프로젝트 문서
```

## 🎯 주요 특징

### 🤖 AI 기반 평가
- **GPT-3.5-turbo** 모델을 활용한 지능형 채점
- **과제 설명과 대화 내용**을 종합적으로 분석
- **객관적이고 일관된** 평가 기준 적용

### ⚡ 고성능 처리
- **Selenium WebDriver** 최적화로 빠른 웹 스크래핑
- **병렬 처리** 지원으로 대량 데이터 처리
- **메모리 효율적** 설계

### 🎨 사용자 친화적 UI
- **직관적인 인터페이스**: 누구나 쉽게 사용 가능
- **실시간 피드백**: 토글 버튼으로 상세 내용 확인
- **반응형 디자인**: 모바일/태블릿/데스크톱 지원

### 📊 상세한 분석
- **다차원 평가**: 4개 영역별 세부 분석
- **통계 대시보드**: 전체 성과 시각화
- **결과 내보내기**: 다양한 형식으로 결과 저장

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 문의

프로젝트에 대한 문의사항이나 버그 리포트는 GitHub Issues를 통해 제출해 주세요.

---

**AI 리터러시 챌린지 심사 시스템** - AI를 통해 더 스마트한 평가를 경험하세요! 🚀 # Vercel 배포 트리거
