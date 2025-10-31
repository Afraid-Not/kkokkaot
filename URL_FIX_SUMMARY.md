# 🎯 AWS 통신 문제 해결 완료

## 📌 발견된 문제

AWS에 배포 후 프론트엔드와 백엔드가 통신 안 됨 → **로컬 IP 주소가 하드코딩**되어 있었음

### 하드코딩된 위치 (총 9개 파일)
- ❌ `project/lib/api.ts`: `http://192.168.56.1:4000`
- ❌ `project/components/figma/LoginScreen.tsx`
- ❌ `project/components/figma/SignupScreen.tsx`
- ❌ `project/components/figma/homescreen.tsx`
- ❌ `project/components/figma/UserProfileSetup.tsx`
- ❌ `project/components/figma/MyInfoScreen.tsx`
- ❌ `project/components/figma/WardrobeManagement.tsx`
- ❌ `project/components/figma/LLMChatScreen.tsx`
- ❌ `project/components/figma/DailyOutfitRecommendation.tsx`
- ❌ `docker-compose.yml`: `localhost`

---

## ✅ 적용된 해결책

### 1️⃣ **API URL 중앙화**
새로 생성된 파일: `project/lib/config.ts`
- 모든 API URL을 한 곳에서 관리
- 환경변수로 쉽게 변경 가능

### 2️⃣ **모든 컴포넌트 수정 완료**
- 9개 파일의 중복된 `API_BASE_URL` 선언 제거
- `import { API_URL } from '../../lib/config'` 로 통일

### 3️⃣ **Docker Compose 환경변수 지원**
- `docker-compose.yml`에 환경변수 추가
- `.env` 파일로 URL 설정 가능

---

## 🚀 지금 바로 적용하기

### Step 1: 프론트엔드 환경변수 설정

#### 로컬 개발 시:
```bash
cd project
```

**Windows (PowerShell):**
```powershell
@"
REACT_APP_API_URL=http://192.168.56.1:4000
EXPO_PUBLIC_API_URL=http://192.168.56.1:4000
"@ | Out-File -Encoding UTF8 .env
```

**Mac/Linux:**
```bash
cat > .env << 'EOF'
REACT_APP_API_URL=http://192.168.56.1:4000
EXPO_PUBLIC_API_URL=http://192.168.56.1:4000
EOF
```

#### AWS 배포 시:
```bash
# EC2에서 실행
cd /home/ubuntu/kkokkaot/project

# 자동으로 EC2 IP 가져와서 설정
EC2_IP=$(curl -s ifconfig.me)
cat > .env << EOF
REACT_APP_API_URL=http://${EC2_IP}:4000
EXPO_PUBLIC_API_URL=http://${EC2_IP}:4000
EOF

echo "✅ API URL: http://${EC2_IP}:4000"
```

### Step 2: 백엔드 서버 확인

```bash
# 서버가 0.0.0.0으로 리스닝하는지 확인
sudo lsof -i :4000

# 로컬 테스트
curl http://localhost:4000/

# 외부 접속 테스트 (로컬 PC에서)
curl http://YOUR-EC2-PUBLIC-IP:4000/
```

### Step 3: EC2 보안 그룹 확인

AWS 콘솔 → EC2 → 보안 그룹에서 다음 포트가 열려있는지 확인:

| 포트 | 설명 | 소스 |
|------|------|------|
| 22 | SSH | 본인 IP |
| 80 | HTTP | 0.0.0.0/0 |
| 443 | HTTPS | 0.0.0.0/0 |
| 4000 | API 서버 | 0.0.0.0/0 |

### Step 4: 앱 실행

```bash
cd project
npm install
npm start
```

콘솔에서 다음과 같이 출력되는지 확인:
```
🔧 앱 설정:
  API_URL: http://YOUR-EC2-IP:4000
```

---

## 📂 변경된 파일 목록

### 새로 생성된 파일:
1. ✨ `project/lib/config.ts` - API URL 중앙 관리
2. 📄 `API/AWS_URL_CONFIG_GUIDE.md` - AWS 배포 가이드
3. 📄 `project/ENV_SETUP_GUIDE.md` - 환경변수 설정 가이드

### 수정된 파일 (총 10개):
1. ✏️ `project/lib/api.ts`
2. ✏️ `project/components/figma/LoginScreen.tsx`
3. ✏️ `project/components/figma/SignupScreen.tsx`
4. ✏️ `project/components/figma/homescreen.tsx`
5. ✏️ `project/components/figma/UserProfileSetup.tsx`
6. ✏️ `project/components/figma/MyInfoScreen.tsx`
7. ✏️ `project/components/figma/WardrobeManagement.tsx`
8. ✏️ `project/components/figma/LLMChatScreen.tsx`
9. ✏️ `project/components/figma/DailyOutfitRecommendation.tsx`
10. ✏️ `docker-compose.yml`

---

## 🔍 테스트 방법

### 1. 백엔드 연결 테스트

```bash
# EC2 서버에서
curl http://localhost:4000/

# 예상 응답:
{
  "service": "꼬까옷 API",
  "version": "2.0.0",
  "status": "running"
}
```

### 2. 외부 접속 테스트

```bash
# 로컬 PC에서
curl http://YOUR-EC2-PUBLIC-IP:4000/
```

### 3. 프론트엔드 API 호출 테스트

브라우저 개발자 도구 → Network 탭에서 API 요청 확인:
- ✅ URL이 AWS EC2 IP로 시작하는지 확인
- ✅ Status Code 200 응답 확인

---

## 🐛 문제 해결

### ❌ "Network Error" 발생

**원인:** EC2 보안 그룹에서 4000번 포트가 닫혀있음

**해결:**
1. AWS 콘솔 → EC2 → 보안 그룹
2. 인바운드 규칙에 `TCP 4000 0.0.0.0/0` 추가

### ❌ "CORS Error" 발생

**원인:** 백엔드 CORS 설정 문제 (이미 해결되어 있음)

**확인:** `backend_server_new.py` 37-45번째 줄 확인

### ❌ 환경변수가 적용 안 됨

**해결:**
```bash
# Metro 캐시 삭제 후 재시작
cd project
npm start -- --clear
```

### ❌ "Connection Timeout" 발생

**원인:** AI 모델 처리 시간이 길어서 타임아웃

**해결:** `project/lib/api.ts` 타임아웃 증가
```typescript
timeout: 60000, // 30초 → 60초
```

---

## 🎯 다음 단계

### 1. 환경변수 파일 생성 (필수)
```bash
cd project
# .env 파일 생성 (위의 Step 1 참고)
```

### 2. 앱 실행 및 테스트
```bash
npm start
```

### 3. AWS 배포 (선택)
상세 가이드: `API/AWS_URL_CONFIG_GUIDE.md` 참고

---

## 📚 참고 문서

- **환경변수 설정**: `project/ENV_SETUP_GUIDE.md`
- **AWS 배포 가이드**: `API/AWS_URL_CONFIG_GUIDE.md`
- **API 설정 파일**: `project/lib/config.ts`

---

## ✅ 적용 전/후 비교

### Before (❌):
```typescript
// 각 파일마다 중복 선언
const API_BASE_URL = 'http://192.168.56.1:4000';  // 하드코딩!
```

### After (✅):
```typescript
// 중앙 관리 (config.ts)
import { API_URL } from './lib/config';

// 환경변수로 쉽게 변경
REACT_APP_API_URL=http://YOUR-AWS-IP:4000
```

---

## 💡 권장 사항

### 프로덕션 배포 시:

1. **Nginx 리버스 프록시 사용** (보안 강화)
   - 4000번 포트 직접 노출하지 않음
   - SSL 인증서 적용 가능

2. **도메인 연결**
   - Route 53 또는 외부 DNS 사용
   - `api.kkokkaot.com` 형태로 접속

3. **HTTPS 적용**
   - Let's Encrypt 무료 인증서
   - 모바일 앱에서 필수

상세 내용: `API/AWS_URL_CONFIG_GUIDE.md` 참고

---

**작성일**: 2025-10-31  
**해결 완료**: ✅ URL 문제 해결  
**적용 상태**: 코드 수정 완료, 환경변수 설정 필요

**도움이 필요하면**: 위 가이드 문서 참고 또는 팀원에게 문의

