# 🔧 프론트엔드 환경변수 설정 가이드

## 📝 환경변수 파일 생성

프로젝트 루트 (`project/` 폴더)에 `.env` 파일을 생성해야 합니다.

### 1️⃣ 로컬 개발용 설정

프로젝트 폴더에서 다음 명령 실행:

```bash
cd project
```

`.env` 파일 생성:

#### Windows (PowerShell):
```powershell
@"
REACT_APP_API_URL=http://192.168.56.1:4000
EXPO_PUBLIC_API_URL=http://192.168.56.1:4000
"@ | Out-File -Encoding UTF8 .env
```

#### Mac/Linux:
```bash
cat > .env << 'EOF'
REACT_APP_API_URL=http://192.168.56.1:4000
EXPO_PUBLIC_API_URL=http://192.168.56.1:4000
EOF
```

#### 또는 수동으로:
1. `project/.env` 파일 생성
2. 다음 내용 입력:
```
REACT_APP_API_URL=http://192.168.56.1:4000
EXPO_PUBLIC_API_URL=http://192.168.56.1:4000
```

---

### 2️⃣ AWS 배포용 설정

`.env.production` 파일 생성:

```bash
# AWS EC2 퍼블릭 IP 사용
REACT_APP_API_URL=http://YOUR-EC2-PUBLIC-IP:4000
EXPO_PUBLIC_API_URL=http://YOUR-EC2-PUBLIC-IP:4000

# 예시:
# REACT_APP_API_URL=http://52.78.123.456:4000
# EXPO_PUBLIC_API_URL=http://52.78.123.456:4000
```

또는 도메인 사용 시:
```bash
REACT_APP_API_URL=https://api.kkokkaot.com
EXPO_PUBLIC_API_URL=https://api.kkokkaot.com
```

---

## 🎯 빠른 설정 스크립트

### Windows (PowerShell):
```powershell
# 로컬 개발용
@"
REACT_APP_API_URL=http://192.168.56.1:4000
EXPO_PUBLIC_API_URL=http://192.168.56.1:4000
"@ | Out-File -Encoding UTF8 .env

Write-Host "✅ .env 파일이 생성되었습니다!"
```

### Mac/Linux/EC2:
```bash
#!/bin/bash

# 로컬 개발용
cat > .env << 'EOF'
REACT_APP_API_URL=http://192.168.56.1:4000
EXPO_PUBLIC_API_URL=http://192.168.56.1:4000
EOF

echo "✅ .env 파일이 생성되었습니다!"
```

### AWS EC2용:
```bash
#!/bin/bash

# EC2 퍼블릭 IP 가져오기
EC2_IP=$(curl -s ifconfig.me)

# .env 파일 생성
cat > .env << EOF
REACT_APP_API_URL=http://${EC2_IP}:4000
EXPO_PUBLIC_API_URL=http://${EC2_IP}:4000
EOF

echo "✅ .env 파일이 생성되었습니다!"
echo "📡 API URL: http://${EC2_IP}:4000"
```

---

## ✅ 설정 확인

### 1. 파일 존재 확인

```bash
# Windows
dir .env

# Mac/Linux
ls -la .env
```

### 2. 내용 확인

```bash
# Windows
type .env

# Mac/Linux
cat .env
```

### 3. 앱 실행 및 로그 확인

```bash
npm start
```

앱 시작 시 콘솔에 다음과 같이 출력되어야 함:
```
🔧 앱 설정:
  API_URL: http://192.168.56.1:4000
```

---

## 🐛 문제 해결

### ❌ 환경변수가 적용되지 않음

**해결 방법:**
1. 앱을 완전히 종료하고 재시작
2. Metro 번들러 캐시 삭제:
```bash
npm start -- --clear
```

### ❌ "Module not found: .env" 오류

**원인:** `.env` 파일이 `project/` 폴더에 없음

**해결:**
```bash
cd project
# 현재 위치 확인
pwd

# .env 파일 생성
echo "REACT_APP_API_URL=http://192.168.56.1:4000" > .env
```

### ❌ API 연결 실패

**확인 사항:**
1. 백엔드 서버가 실행 중인지 확인
2. `.env` 파일의 URL이 정확한지 확인
3. 방화벽 설정 확인

---

## 📱 Expo 앱 빌드 시

### 1. `app.json`에 설정 추가

```json
{
  "expo": {
    "extra": {
      "apiUrl": "https://api.kkokkaot.com"
    }
  }
}
```

### 2. 코드에서 사용

`lib/config.ts` 수정:
```typescript
import Constants from 'expo-constants';

export const API_URL = 
  Constants.expoConfig?.extra?.apiUrl ||
  process.env.REACT_APP_API_URL || 
  process.env.EXPO_PUBLIC_API_URL || 
  'http://192.168.56.1:4000';
```

---

## 📂 .gitignore 확인

`.env` 파일이 Git에 커밋되지 않도록 확인:

```bash
# .gitignore 내용 확인
cat .gitignore | grep .env
```

다음 내용이 있어야 함:
```
.env
.env.local
.env.production
```

없다면 추가:
```bash
echo ".env" >> .gitignore
echo ".env.local" >> .gitignore
echo ".env.production" >> .gitignore
```

---

## 🔄 환경 전환

### 개발 → 프로덕션

```bash
# .env.production 파일을 .env로 복사
cp .env.production .env

# 앱 재시작
npm start
```

### 프로덕션 → 개발

```bash
# 원래 .env 복원
cp .env.development .env

# 또는 직접 수정
echo "REACT_APP_API_URL=http://192.168.56.1:4000" > .env
```

---

## 💡 팁

1. **개발용과 프로덕션용 분리**
   ```bash
   .env.development  # 로컬
   .env.production   # AWS
   .env              # 현재 사용 중
   ```

2. **자동 전환 스크립트**
   ```bash
   # switch-env.sh
   #!/bin/bash
   if [ "$1" = "prod" ]; then
     cp .env.production .env
     echo "✅ 프로덕션 환경으로 전환"
   else
     cp .env.development .env
     echo "✅ 개발 환경으로 전환"
   fi
   ```

3. **환경변수 확인 명령어**
   ```bash
   # 현재 설정 확인
   cat .env

   # API URL 테스트
   curl $(cat .env | grep REACT_APP_API_URL | cut -d'=' -f2)/
   ```

---

**다음 단계**: 
- `.env` 파일 생성 완료 후 → `npm start` 실행
- AWS 배포 시 → `API/AWS_URL_CONFIG_GUIDE.md` 참고

**문의**: 꼬까옷 개발팀

