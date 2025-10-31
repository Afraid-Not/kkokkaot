# 꼬까옷 개발 환경 시작 스크립트 (Windows)

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "    꼬까옷 개발 환경 시작" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Docker 실행 확인
Write-Host "🐳 Docker 상태 확인 중..." -ForegroundColor Yellow
docker info > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker가 실행되지 않았습니다!" -ForegroundColor Red
    Write-Host "   Docker Desktop을 시작한 후 다시 실행해주세요." -ForegroundColor Red
    exit 1
}
Write-Host "✅ Docker 실행 중" -ForegroundColor Green

Write-Host ""
Write-Host "🚀 서비스 시작 옵션:" -ForegroundColor Cyan
Write-Host "  1. PostgreSQL만 실행"
Write-Host "  2. PostgreSQL + 백엔드 실행 (전체)"
Write-Host "  3. 기존 컨테이너 중지"
Write-Host "  4. 전체 삭제 및 재시작"
Write-Host ""

$choice = Read-Host "선택 (1-4)"

if ($choice -eq "1") {
    Write-Host ""
    Write-Host "📦 PostgreSQL 시작 중..." -ForegroundColor Yellow
    docker-compose up -d postgres
    
    Write-Host ""
    Write-Host "⏳ PostgreSQL 준비 대기 중..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    Write-Host ""
    Write-Host "✅ PostgreSQL 시작 완료!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 접속 정보:" -ForegroundColor Cyan
    Write-Host "   Host: localhost"
    Write-Host "   Port: 5432"
    Write-Host "   Database: kkokkaot_closet"
    Write-Host "   Username: postgres"
    Write-Host "   Password: 000000"
    Write-Host ""
    Write-Host "🔗 접속 명령어:" -ForegroundColor Cyan
    Write-Host "   docker exec -it kkokkaot_postgres psql -U postgres -d kkokkaot_closet"
    
} elseif ($choice -eq "2") {
    Write-Host ""
    Write-Host "📦 전체 서비스 시작 중..." -ForegroundColor Yellow
    docker-compose up -d
    
    Write-Host ""
    Write-Host "⏳ 서비스 준비 대기 중..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    Write-Host ""
    Write-Host "✅ 전체 서비스 시작 완료!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 실행 중인 서비스:" -ForegroundColor Cyan
    docker-compose ps
    
    Write-Host ""
    Write-Host "🌐 접속 주소:" -ForegroundColor Cyan
    Write-Host "   백엔드 API: http://localhost:4000"
    Write-Host "   프론트엔드: http://localhost:3000"
    Write-Host "   PostgreSQL: localhost:5432"
    
} elseif ($choice -eq "3") {
    Write-Host ""
    Write-Host "🛑 서비스 중지 중..." -ForegroundColor Yellow
    docker-compose stop
    
    Write-Host ""
    Write-Host "✅ 서비스 중지 완료!" -ForegroundColor Green
    
} elseif ($choice -eq "4") {
    Write-Host ""
    Write-Host "⚠️  경고: 모든 데이터가 삭제됩니다!" -ForegroundColor Red
    $confirm = Read-Host "계속하시겠습니까? (yes/no)"
    
    if ($confirm -eq "yes") {
        Write-Host ""
        Write-Host "🗑️  전체 삭제 중..." -ForegroundColor Yellow
        docker-compose down -v
        
        Write-Host ""
        Write-Host "📦 새로 시작 중..." -ForegroundColor Yellow
        docker-compose up -d
        
        Write-Host ""
        Write-Host "⏳ 서비스 준비 대기 중..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
        
        Write-Host ""
        Write-Host "✅ 재시작 완료!" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "❌ 취소되었습니다." -ForegroundColor Yellow
    }
    
} else {
    Write-Host ""
    Write-Host "❌ 잘못된 선택입니다." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "📝 유용한 명령어:" -ForegroundColor Cyan
Write-Host "   로그 확인:     docker-compose logs -f"
Write-Host "   상태 확인:     docker-compose ps"
Write-Host "   서비스 중지:   docker-compose stop"
Write-Host "   서비스 재시작: docker-compose restart"
Write-Host ""

