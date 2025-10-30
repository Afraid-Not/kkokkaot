# 꼬까옷 (kkokkaot) 👔

AI 기반 가상 옷장 및 패션 추천 서비스

## 📋 프로젝트 개요

꼬까옷은 사용자의 옷장을 디지털화하고, AI(LLM/YOLO/SAM2/DNN)를 활용하여 스타일 추천 및 코디 제안을 제공하는 가상 옷장 애플리케이션입니다.

---

## 🎯 주요 기능

### 1. **옷 업로드 및 AI 분석**
- 사용자가 옷 사진 촬영/업로드
- YOLO로 객체 탐지 (상의/하의/아우터/원피스 자동 분리)
- CNN으로 속성 예측 (카테고리, 색상, 핏, 소재, 프린트, 스타일 등)
- PostgreSQL 및 ChromaDB에 자동 저장

### 2. **LLM 챗봇 기반 대화형 추천**
```
사용자: "오늘 뭐 입을까?"
AI: "오늘 어디 가? 날씨는 어때? 😊"

사용자: "회사 가는데 좀 추워"
AI: "알겠어! 추운 날 출근 스타일 찾아줄게! 깔끔하고 따뜻한 옷 추천할게 ✨"
```

- 자연어 대화로 날씨, 상황, 건강 상태 등 파악
- 컨텍스트 기반 자동 필터링 및 추천

### 3. **선택 기반 조합 추천**
- 상의 선택 → 어울리는 하의 추천
- 하의 선택 → 어울리는 상의 추천
- 상의+하의 → 어울리는 아우터 추천

### 4. **날씨 연동 스타일 추천**
- OpenWeatherMap API 연동
- 실시간 날씨 기반 옷 추천
- 온도별 스타일 팁 제공

### 5. **기본 아이템 제공**
- 옷장이 비어있어도 기본 아이템으로 추천 가능
- 남성/여성별 기본 의류 세트 제공

---

## 🛠 기술 스택

### **백엔드**
- **FastAPI**: REST API 서버
- **PostgreSQL**: 관계형 DB
- **PyTorch**: 딥러닝 프레임워크
- **Ultralytics YOLO**: 객체 탐지
- **Transformers (Qwen)**: LLM 챗봇
- **ChromaDB**: 벡터 데이터베이스
- **OpenCV**: 이미지 전처리

### **프론트엔드**
- **React Native**: 모바일 앱
- **Expo**: 개발 도구
- **TypeScript**: 타입 안전성
- **AsyncStorage**: 로컬 저장소
- **Axios**: HTTP 클라이언트

### **인프라**
- **Docker**: 컨테이너화
- **ngrok**: 로컬 서버 터널링

---

## 🚀 빠른 시작

### 1. 저장소 클론
```bash
git clone https://github.com/your-username/kkokkaot.git
cd kkokkaot
```

### 2. 백엔드 설정
```bash
cd API

# 환경 변수 파일 생성
cp .env.example .env

# .env 파일 수정 (날씨 API 키 등)
# OPENWEATHER_API_KEY=여기에_발급받은_키_입력

# Python 패키지 설치
pip install -r requirements.txt

# 서버 실행
python backend_server_new.py
```

### 3. 프론트엔드 설정
```bash
cd project

# 환경 변수 파일 생성
cp .env.example .env

# .env 파일 수정 (PC IP 주소 입력)
# REACT_APP_API_URL=http://192.168.0.10:4000

# Node 패키지 설치
npm install

# 앱 실행
expo start
```

### 4. 데이터베이스 설정
```bash
# PostgreSQL 접속
psql -U postgres

# 데이터베이스 생성
CREATE DATABASE kkokkaot_closet;

# 스키마 생성
\c kkokkaot_closet
\i API/휴지통/postgresql.sql
```

---

## 📚 상세 문서

- **[설정 가이드](./API/SETUP_GUIDE.md)** - 백엔드 환경 설정, 날씨 API 키 발급 등
- **[브랜치 가이드](./BRANCH_GUIDE.md)** - Git 브랜치 전략 및 커밋 규칙
- **[리팩토링 가이드](./API/REFACTORING_GUIDE.md)** - 백엔드 코드 구조 변경 내역

---

## 🔥 주요 변경사항 (최신)

### ✅ **완료된 작업**
1. **라우터 API 완성**
   - `recommendations.py`: 추천 시스템 ✅
   - `chat.py`: LLM 챗봇 ✅
   - `images.py`: 이미지 제공 ✅
   - `weather.py`: 날씨 API ✅
   - `admin.py`: 관리자 기능 ✅

2. **날씨 API 연동**
   - OpenWeatherMap API 통합
   - 실시간 날씨 데이터 제공
   - 온도별 스타일 추천

3. **프론트엔드 API 클라이언트 확장**
   - `lib/api.ts`: 모든 API 엔드포인트 추가
   - `lib/errorHandler.ts`: 에러 핸들링 유틸리티
   - 인터셉터를 통한 로그 및 인증 관리

4. **환경 변수 설정**
   - `.env.example` 파일 생성
   - 설정 가이드 문서 작성
   - 서버 HOST를 0.0.0.0으로 변경 (모든 네트워크 접근 가능)

5. **에러 핸들링 개선**
   - 사용자 친화적인 에러 메시지
   - 재시도 로직 구현
   - 네트워크 연결 체크

---

## 🧪 테스트

### 백엔드 API 테스트
```bash
cd API
python test_api.py
```

### 수동 테스트
```bash
# 1. 서버 상태 확인
curl http://localhost:4000/

# 2. 날씨 API 테스트
curl http://localhost:4000/api/weather?city=Seoul

# 3. API 문서 확인
# 브라우저에서 http://localhost:4000/docs 접속
```

---

## 📊 프로젝트 구조

```
kkokkaot/
├── API/                          # 백엔드
│   ├── backend_server_new.py    # 메인 서버 (리팩토링 버전)
│   ├── config/                  # 설정
│   ├── routers/                 # API 엔드포인트
│   ├── pipeline/                # AI 파이프라인
│   ├── models/                  # Pydantic 스키마
│   ├── pre_trained_weights/     # AI 모델 (.pth, .pt)
│   ├── uploaded_images/         # 원본 업로드 이미지
│   ├── processed_images/        # 크롭된 이미지
│   ├── default_items/           # 기본 제공 아이템
│   ├── _llm_recommender.py      # LLM 챗봇 시스템
│   ├── _advanced_recommender.py # 고급 추천 시스템
│   ├── requirements.txt         # Python 패키지
│   ├── .env.example             # 환경 변수 예시
│   ├── SETUP_GUIDE.md           # 설정 가이드
│   └── test_api.py              # API 테스트
│
├── project/                      # 프론트엔드
│   ├── App.tsx                  # 메인 앱
│   ├── components/figma/        # UI 컴포넌트
│   ├── lib/                     # 유틸리티
│   │   ├── api.ts               # API 클라이언트
│   │   └── errorHandler.ts     # 에러 핸들링
│   ├── screens/                 # 화면들
│   ├── package.json             # Node 패키지
│   └── .env.example             # 환경 변수 예시
│
├── docker-compose.yml            # Docker 설정
├── BRANCH_GUIDE.md              # 브랜치 가이드
└── README.md                    # 프로젝트 문서
```

---

## 🔧 트러블슈팅

### 서버 연결 실패
- PC 방화벽 확인 (4000번 포트 허용)
- IP 주소 확인 (`ipconfig` 또는 `ifconfig`)
- `.env` 파일의 `REACT_APP_API_URL` 수정

### 날씨 API 오류
- OpenWeatherMap API 키 발급 (https://openweathermap.org/api)
- `.env` 파일에 `OPENWEATHER_API_KEY` 추가
- API 키 활성화 대기 (10분~2시간)

### 데이터베이스 연결 오류
- PostgreSQL 서비스 실행 확인
- `.env` 파일의 DB 설정 확인
- 데이터베이스 생성 확인

---

## 👨‍💻 팀원

- **이문용** (1석사)
- **김재현** (2석사)
- **김현진** (아이1)
- **어지유** (아이2)

---

## 📞 문의

프로젝트 관련 문의사항이나 버그 리포트는 이슈를 등록해주세요.

---

⭐ Made with 💙 by 삼석사와아이들

