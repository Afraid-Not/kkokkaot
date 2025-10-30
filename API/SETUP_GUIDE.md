# 🚀 꼬까옷 백엔드 설정 가이드

## 📋 목차
1. [환경 변수 설정](#환경-변수-설정)
2. [날씨 API 키 발급](#날씨-api-키-발급)
3. [데이터베이스 설정](#데이터베이스-설정)
4. [서버 실행](#서버-실행)

---

## 환경 변수 설정

### 1. `.env` 파일 생성

```bash
cd API
cp .env.example .env
```

### 2. `.env` 파일 수정

```bash
# 데이터베이스 설정 (PostgreSQL)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=kkokkaot_closet
DB_USER=postgres
DB_PASSWORD=000000

# 날씨 API (필수!)
OPENWEATHER_API_KEY=여기에_발급받은_API_키_입력

# 서버 설정
SERVER_HOST=0.0.0.0  # 모든 네트워크 인터페이스에서 접근 가능
SERVER_PORT=4000
```

---

## 날씨 API 키 발급

### 1. OpenWeatherMap 가입

1. [OpenWeatherMap](https://openweathermap.org/api) 접속
2. **Sign Up** 클릭하여 무료 계정 생성
3. 이메일 인증 완료

### 2. API 키 발급

1. 로그인 후 **API keys** 메뉴 클릭
2. **Create key** 버튼 클릭
3. Key Name 입력 (예: `kkokkaot`)
4. 생성된 API 키 복사

**예시:**
```
OPENWEATHER_API_KEY=abc123def456ghi789jkl012mno345pq
```

### 3. `.env` 파일에 API 키 추가

```bash
# API/.env 파일 열기
OPENWEATHER_API_KEY=abc123def456ghi789jkl012mno345pq
```

### 4. API 키 활성화 대기

- API 키는 발급 후 **약 10분~2시간** 후에 활성화됩니다.
- 활성화 전에는 `401 Unauthorized` 에러가 발생할 수 있습니다.

---

## 데이터베이스 설정

### 1. PostgreSQL 설치

#### Windows
```bash
# PostgreSQL 다운로드 및 설치
# https://www.postgresql.org/download/windows/
```

#### macOS
```bash
brew install postgresql
brew services start postgresql
```

#### Linux (Ubuntu)
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### 2. 데이터베이스 생성

```bash
# PostgreSQL 접속
psql -U postgres

# 데이터베이스 생성
CREATE DATABASE kkokkaot_closet;

# 스키마 생성 (SQL 파일 실행)
\c kkokkaot_closet
\i /path/to/kkokkaot/API/휴지통/postgresql.sql
```

### 3. 연결 테스트

```bash
# Python에서 연결 테스트
python -c "import psycopg2; conn = psycopg2.connect('dbname=kkokkaot_closet user=postgres password=000000'); print('✅ 연결 성공!')"
```

---

## 서버 실행

### 1. Python 패키지 설치

```bash
cd API
pip install -r requirements.txt
```

### 2. 서버 실행

```bash
python backend_server_new.py
```

### 3. 서버 확인

브라우저에서 아래 주소 접속:
- **서버 상태**: http://localhost:4000/
- **API 문서**: http://localhost:4000/docs
- **날씨 API 테스트**: http://localhost:4000/api/weather?city=Seoul

**정상 응답 예시:**
```json
{
  "success": true,
  "temperature": 22,
  "weather": "Clear",
  "description": "맑음",
  "icon": "☀️",
  "style_tip": "맑음 · 가벼운 레이어드 스타일링 추천",
  "city": "Seoul",
  "date": "10월 30일"
}
```

---

## 🔥 트러블슈팅

### 날씨 API 오류

#### 오류 1: `401 Unauthorized`
- **원인**: API 키가 아직 활성화되지 않았거나 잘못된 키
- **해결**:
  1. API 키 발급 후 **10분~2시간** 대기
  2. `.env` 파일의 API 키 확인
  3. API 키에 공백이나 특수문자가 없는지 확인

#### 오류 2: API 키 없음
- **증상**: 기본 날씨 데이터만 반환됨 (항상 22도, 흐림)
- **해결**: `.env` 파일에 `OPENWEATHER_API_KEY` 추가

### 데이터베이스 연결 오류

#### 오류: `connection refused`
- **원인**: PostgreSQL이 실행되지 않음
- **해결**:
  ```bash
  # Windows
  services.msc 에서 PostgreSQL 서비스 시작
  
  # macOS
  brew services start postgresql
  
  # Linux
  sudo systemctl start postgresql
  ```

#### 오류: `authentication failed`
- **원인**: 비밀번호 불일치
- **해결**: `.env` 파일의 `DB_PASSWORD` 확인

### 서버 포트 충돌

#### 오류: `Address already in use`
- **원인**: 4000번 포트가 이미 사용 중
- **해결**:
  ```bash
  # 포트 사용 중인 프로세스 확인
  # Windows
  netstat -ano | findstr :4000
  
  # macOS/Linux
  lsof -i :4000
  
  # 또는 다른 포트 사용 (.env 파일 수정)
  SERVER_PORT=5000
  ```

---

## 📱 프론트엔드 연동

### 1. 프론트엔드 환경 변수 설정

```bash
cd project
cp .env.example .env
```

### 2. IP 주소 확인

#### Windows
```bash
ipconfig
# "IPv4 Address" 확인
```

#### macOS/Linux
```bash
ifconfig
# "inet" 확인
```

### 3. `.env` 파일 수정

```bash
# project/.env
REACT_APP_API_URL=http://192.168.0.10:4000
```

**⚠️ 주의**: `192.168.0.10`을 본인의 PC IP 주소로 변경하세요!

### 4. 프론트엔드 실행

```bash
cd project
npm install
expo start
```

---

## ✅ 설정 완료 체크리스트

- [ ] PostgreSQL 설치 및 실행
- [ ] 데이터베이스 생성 (`kkokkaot_closet`)
- [ ] API 키 발급 (OpenWeatherMap)
- [ ] `.env` 파일 생성 및 설정
- [ ] Python 패키지 설치
- [ ] 백엔드 서버 실행 성공
- [ ] http://localhost:4000/docs 접속 확인
- [ ] 날씨 API 테스트 성공
- [ ] 프론트엔드 `.env` 파일 설정
- [ ] 프론트엔드 실행 성공

---

## 🎉 완료!

모든 설정이 완료되었습니다. 이제 꼬까옷 서비스를 사용할 수 있습니다!

문제가 발생하면 위의 트러블슈팅 섹션을 참고하거나 팀원에게 문의하세요.

