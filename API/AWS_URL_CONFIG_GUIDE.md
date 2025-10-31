# 🌐 AWS 배포 시 URL 설정 가이드

## 📋 문제 요약

AWS에 배포 후 프론트엔드와 백엔드가 통신이 안 되는 이유:
- **로컬 IP 주소가 하드코딩**되어 있었음 (`http://192.168.56.1:4000`)
- AWS EC2의 실제 퍼블릭 IP/도메인으로 변경 필요

## ✅ 해결 방법

### 1️⃣ 백엔드 설정 (이미 완료됨)

`API/config/settings.py`에서:
```python
SERVER_HOST = os.getenv('SERVER_HOST', '0.0.0.0')  # ✅ 모든 네트워크에서 접근 가능
SERVER_PORT = int(os.getenv('SERVER_PORT', 4000))
```

### 2️⃣ 프론트엔드 환경변수 설정

#### **방법 A: `.env` 파일 생성 (권장)**

`project/.env` 파일을 생성하고 AWS 서버 주소 입력:

```bash
# 로컬 개발용
REACT_APP_API_URL=http://192.168.56.1:4000
EXPO_PUBLIC_API_URL=http://192.168.56.1:4000
```

**AWS 배포용 (`.env.production`):**
```bash
# AWS EC2 퍼블릭 IP 사용 예시
REACT_APP_API_URL=http://52.78.123.456:4000
EXPO_PUBLIC_API_URL=http://52.78.123.456:4000

# 또는 도메인 사용 시
REACT_APP_API_URL=https://api.kkokkaot.com
EXPO_PUBLIC_API_URL=https://api.kkokkaot.com
```

#### **방법 B: 시스템 환경변수 설정**

```bash
# EC2에서 실행 전 설정
export REACT_APP_API_URL=http://YOUR-EC2-PUBLIC-IP:4000
export EXPO_PUBLIC_API_URL=http://YOUR-EC2-PUBLIC-IP:4000
```

### 3️⃣ AWS EC2 보안 그룹 설정 확인

EC2 인스턴스의 보안 그룹에서 다음 포트를 **반드시 열어야 함**:

| 타입 | 프로토콜 | 포트 | 소스 | 설명 |
|------|----------|------|------|------|
| HTTP | TCP | 80 | 0.0.0.0/0 | HTTP 접속 |
| HTTPS | TCP | 443 | 0.0.0.0/0 | HTTPS 접속 |
| Custom TCP | TCP | 4000 | 0.0.0.0/0 | 백엔드 API 서버 |

⚠️ **주의**: 프로덕션 환경에서는 4000번 포트를 직접 여는 대신 **Nginx 리버스 프록시**를 사용하는 것이 보안상 안전합니다.

---

## 🚀 AWS 배포 단계별 체크리스트

### Step 1: EC2 인스턴스 확인

```bash
# EC2에 SSH 접속
ssh -i your-key.pem ubuntu@YOUR-EC2-PUBLIC-IP

# 퍼블릭 IP 확인
curl ifconfig.me
```

### Step 2: 백엔드 서버 실행 확인

```bash
# 서버가 실행 중인지 확인
ps aux | grep python

# 4000번 포트 리스닝 확인
sudo lsof -i :4000

# 로컬에서 접속 테스트
curl http://localhost:4000/
```

**정상 응답 예시:**
```json
{
  "service": "꼬까옷 API",
  "version": "2.0.0",
  "status": "running",
  "ai_pipeline": "active"
}
```

### Step 3: 외부에서 접속 테스트

로컬 PC에서 테스트:
```bash
# Windows PowerShell
curl http://YOUR-EC2-PUBLIC-IP:4000/

# Mac/Linux
curl http://YOUR-EC2-PUBLIC-IP:4000/
```

❌ **연결 실패 시:**
- EC2 보안 그룹에서 4000번 포트가 열려있는지 확인
- 백엔드 서버가 `0.0.0.0:4000`으로 리스닝하는지 확인
- 방화벽(UFW) 설정 확인: `sudo ufw status`

### Step 4: 프론트엔드 환경변수 설정

```bash
# project/.env 파일 생성
cd /home/ubuntu/kkokkaot/project
nano .env
```

파일 내용:
```bash
REACT_APP_API_URL=http://YOUR-EC2-PUBLIC-IP:4000
EXPO_PUBLIC_API_URL=http://YOUR-EC2-PUBLIC-IP:4000
```

### Step 5: 프론트엔드 빌드 및 실행

```bash
cd /home/ubuntu/kkokkaot/project

# 패키지 설치
npm install

# 빌드 (React Native Web용)
npm run build

# 또는 Expo 앱 실행
npx expo start
```

---

## 🔧 Nginx 리버스 프록시 설정 (권장)

보안을 위해 4000번 포트를 직접 노출하지 않고 Nginx를 통해 연결:

### 1. Nginx 설치

```bash
sudo apt update
sudo apt install -y nginx
```

### 2. 설정 파일 생성

```bash
sudo nano /etc/nginx/sites-available/kkokkaot
```

설정 내용:
```nginx
server {
    listen 80;
    server_name YOUR-DOMAIN-OR-IP;

    # 최대 업로드 크기 (이미지 업로드용)
    client_max_body_size 50M;

    location / {
        proxy_pass http://localhost:4000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 타임아웃 설정 (AI 모델 처리 시간 고려)
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
    }
}
```

### 3. 설정 활성화

```bash
# 심볼릭 링크 생성
sudo ln -s /etc/nginx/sites-available/kkokkaot /etc/nginx/sites-enabled/

# 기본 사이트 비활성화 (선택)
sudo rm /etc/nginx/sites-enabled/default

# 설정 테스트
sudo nginx -t

# Nginx 재시작
sudo systemctl restart nginx
```

### 4. 프론트엔드 환경변수 업데이트

이제 4000번 포트 없이 접속 가능:
```bash
# .env 파일 수정
REACT_APP_API_URL=http://YOUR-EC2-PUBLIC-IP
EXPO_PUBLIC_API_URL=http://YOUR-EC2-PUBLIC-IP
```

### 5. EC2 보안 그룹 수정

이제 4000번 포트 규칙을 제거하고 80, 443번만 열어두면 됩니다.

---

## 🔒 SSL 인증서 설정 (HTTPS)

### 1. 도메인 연결

먼저 도메인을 EC2 퍼블릭 IP에 연결:
- Route 53 또는 외부 도메인 등록 업체에서 A 레코드 추가
- `api.kkokkaot.com` → `YOUR-EC2-PUBLIC-IP`

### 2. Let's Encrypt 인증서 발급

```bash
# Certbot 설치
sudo apt install -y certbot python3-certbot-nginx

# 인증서 발급 (자동으로 Nginx 설정 수정)
sudo certbot --nginx -d api.kkokkaot.com

# 이메일 입력 및 약관 동의
```

### 3. 자동 갱신 확인

```bash
# 갱신 테스트
sudo certbot renew --dry-run

# Cron 작업 확인 (자동으로 설정됨)
sudo systemctl status certbot.timer
```

### 4. 프론트엔드 HTTPS 적용

```bash
# .env 파일을 HTTPS로 변경
REACT_APP_API_URL=https://api.kkokkaot.com
EXPO_PUBLIC_API_URL=https://api.kkokkaot.com
```

---

## 📱 모바일 앱 배포 시 주의사항

### Expo 앱 빌드 시

`app.json`에 API URL 추가:
```json
{
  "expo": {
    "extra": {
      "apiUrl": "https://api.kkokkaot.com"
    }
  }
}
```

코드에서 사용:
```typescript
import Constants from 'expo-constants';

const API_URL = Constants.expoConfig?.extra?.apiUrl || 'http://localhost:4000';
```

---

## 🐛 문제 해결 (Troubleshooting)

### ❌ 문제: "Network Error" 또는 "Connection Refused"

**원인:**
1. EC2 보안 그룹에서 4000번 포트가 닫혀있음
2. 백엔드 서버가 실행되지 않음
3. 방화벽(UFW)에서 포트 차단

**해결:**
```bash
# 1. 보안 그룹 확인 (AWS 콘솔)
# 2. 서버 실행 확인
sudo systemctl status kkokkaot

# 3. 방화벽 확인
sudo ufw status
sudo ufw allow 4000/tcp
```

### ❌ 문제: "CORS Error"

**원인:** 백엔드에서 CORS 설정 누락

**해결:** `backend_server_new.py`에 이미 설정되어 있음:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ✅ 모든 도메인 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

프로덕션 환경에서는 `allow_origins`를 특정 도메인만 허용하도록 변경 권장:
```python
allow_origins=["https://your-frontend-domain.com"]
```

### ❌ 문제: 이미지가 로드되지 않음

**원인:** 이미지 URL이 상대 경로로 되어있음

**확인:**
- `project/lib/config.ts`의 `getImageUrl` 함수가 올바르게 동작하는지 확인
- 백엔드에서 반환하는 이미지 경로 확인

### ❌ 문제: "Timeout" 오류

**원인:** AI 모델 처리 시간이 길어서 타임아웃 발생

**해결:**
```typescript
// project/lib/api.ts 에서 타임아웃 증가
const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 60000, // 30초 → 60초로 증가
});
```

Nginx 사용 시:
```nginx
proxy_read_timeout 300s;  # 5분
proxy_connect_timeout 300s;
```

---

## 📊 최종 확인 사항

✅ **백엔드 체크리스트:**
- [ ] EC2 인스턴스 실행 중
- [ ] 백엔드 서버가 `0.0.0.0:4000`으로 리스닝
- [ ] EC2 보안 그룹에서 4000번 포트 오픈 (또는 80/443 with Nginx)
- [ ] 외부에서 `http://YOUR-IP:4000/` 접속 가능
- [ ] PostgreSQL 연결 정상

✅ **프론트엔드 체크리스트:**
- [ ] `.env` 파일에 AWS 서버 URL 설정
- [ ] 모든 컴포넌트에서 `config.ts` 사용 (하드코딩 제거)
- [ ] 앱 재시작 후 API 연결 테스트

✅ **네트워크 체크리스트:**
- [ ] EC2 퍼블릭 IP 확인
- [ ] 보안 그룹 인바운드 규칙 확인
- [ ] 방화벽(UFW) 규칙 확인
- [ ] CORS 설정 확인

---

## 🎯 빠른 테스트 스크립트

백엔드 연결 테스트:
```bash
#!/bin/bash
API_URL="http://YOUR-EC2-PUBLIC-IP:4000"

echo "🔍 서버 상태 확인..."
curl -s $API_URL/ | jq

echo "\n🧪 로그인 테스트..."
curl -X POST $API_URL/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Test1234!"}' | jq

echo "\n✅ 테스트 완료"
```

---

## 💡 추가 권장 사항

### 1. 환경별 설정 분리
```bash
# .env.development (로컬)
REACT_APP_API_URL=http://localhost:4000

# .env.production (AWS)
REACT_APP_API_URL=https://api.kkokkaot.com
```

### 2. 로깅 및 모니터링
```bash
# 백엔드 로그 확인
sudo journalctl -u kkokkaot -f

# Nginx 로그 확인
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 3. 백업 스크립트
```bash
# 데이터베이스 백업
pg_dump -U postgres kkokkaot_closet > backup_$(date +%Y%m%d).sql

# S3에 업로드
aws s3 cp backup_$(date +%Y%m%d).sql s3://your-backup-bucket/
```

---

## 📞 도움이 필요하면

1. **서버 로그 확인**: `sudo journalctl -u kkokkaot -f`
2. **보안 그룹 확인**: AWS 콘솔 → EC2 → 보안 그룹
3. **네트워크 테스트**: `curl http://YOUR-IP:4000/`
4. **프론트엔드 콘솔**: 브라우저 개발자 도구에서 네트워크 탭 확인

---

**작성일**: 2025-10-31  
**버전**: 1.0  
**문의**: 꼬까옷 개발팀

