# 꼬까옷 AWS URL 설정 스크립트 (Windows PowerShell)
# 사용법: .\quick-fix.ps1

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "    꼬까옷 프론트엔드 환경변수 설정" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# 현재 위치 확인
$currentPath = Get-Location
Write-Host "📂 현재 위치: $currentPath" -ForegroundColor Yellow

# project 폴더로 이동
if (Test-Path "project") {
    Set-Location "project"
    Write-Host "✅ project 폴더로 이동" -ForegroundColor Green
} elseif (Test-Path "../project") {
    Set-Location "../project"
    Write-Host "✅ project 폴더로 이동" -ForegroundColor Green
} else {
    Write-Host "❌ project 폴더를 찾을 수 없습니다!" -ForegroundColor Red
    Write-Host "   프로젝트 루트 폴더에서 실행해주세요." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🔧 환경 선택:" -ForegroundColor Cyan
Write-Host "  1. 로컬 개발 (http://192.168.56.1:4000)"
Write-Host "  2. AWS 배포 (직접 입력)"
Write-Host ""

$choice = Read-Host "선택 (1 또는 2)"

if ($choice -eq "1") {
    # 로컬 개발용
    $apiUrl = "http://192.168.56.1:4000"
    
    @"
REACT_APP_API_URL=$apiUrl
EXPO_PUBLIC_API_URL=$apiUrl
"@ | Out-File -Encoding UTF8 .env
    
    Write-Host ""
    Write-Host "✅ 로컬 개발 환경으로 설정되었습니다!" -ForegroundColor Green
    Write-Host "   API URL: $apiUrl" -ForegroundColor Yellow
    
} elseif ($choice -eq "2") {
    # AWS 배포용
    Write-Host ""
    $awsIp = Read-Host "AWS EC2 퍼블릭 IP 또는 도메인을 입력하세요 (예: 52.78.123.456)"
    
    # http:// 또는 https:// 확인
    if ($awsIp -notmatch "^https?://") {
        Write-Host ""
        Write-Host "프로토콜 선택:" -ForegroundColor Cyan
        Write-Host "  1. HTTP (기본)"
        Write-Host "  2. HTTPS (SSL 인증서 있는 경우)"
        $protocol = Read-Host "선택 (1 또는 2)"
        
        if ($protocol -eq "2") {
            $apiUrl = "https://$awsIp"
        } else {
            $apiUrl = "http://${awsIp}:4000"
        }
    } else {
        $apiUrl = $awsIp
    }
    
    @"
REACT_APP_API_URL=$apiUrl
EXPO_PUBLIC_API_URL=$apiUrl
"@ | Out-File -Encoding UTF8 .env
    
    Write-Host ""
    Write-Host "✅ AWS 배포 환경으로 설정되었습니다!" -ForegroundColor Green
    Write-Host "   API URL: $apiUrl" -ForegroundColor Yellow
    
} else {
    Write-Host ""
    Write-Host "❌ 잘못된 선택입니다." -ForegroundColor Red
    exit 1
}

# .env 파일 확인
Write-Host ""
Write-Host "📄 생성된 .env 파일 내용:" -ForegroundColor Cyan
Write-Host "-----------------------------------"
Get-Content .env
Write-Host "-----------------------------------"

Write-Host ""
Write-Host "✅ 설정 완료!" -ForegroundColor Green
Write-Host ""
Write-Host "다음 단계:" -ForegroundColor Cyan
Write-Host "  1. 터미널에서 'npm start' 실행"
Write-Host "  2. 콘솔에 API URL이 올바르게 출력되는지 확인"
Write-Host "  3. 앱에서 로그인/회원가입 테스트"
Write-Host ""
Write-Host "문제가 있으면 다음 문서를 참고하세요:" -ForegroundColor Yellow
Write-Host "  - ENV_SETUP_GUIDE.md (환경변수 가이드)"
Write-Host "  - ../API/AWS_URL_CONFIG_GUIDE.md (AWS 배포 가이드)"
Write-Host ""

# 원래 위치로 돌아가기
Set-Location $currentPath

