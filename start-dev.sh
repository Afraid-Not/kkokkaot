#!/bin/bash
# 꼬까옷 개발 환경 시작 스크립트 (Mac/Linux/EC2)

set -e

echo "================================================"
echo "    꼬까옷 개발 환경 시작"
echo "================================================"
echo ""

# Docker 실행 확인
echo "🐳 Docker 상태 확인 중..."
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker가 실행되지 않았습니다!"
    echo "   Docker를 시작한 후 다시 실행해주세요."
    exit 1
fi
echo "✅ Docker 실행 중"

echo ""
echo "🚀 서비스 시작 옵션:"
echo "  1. PostgreSQL만 실행"
echo "  2. PostgreSQL + 백엔드 실행 (전체)"
echo "  3. 기존 컨테이너 중지"
echo "  4. 전체 삭제 및 재시작"
echo ""

read -p "선택 (1-4): " choice

if [ "$choice" = "1" ]; then
    echo ""
    echo "📦 PostgreSQL 시작 중..."
    docker-compose up -d postgres
    
    echo ""
    echo "⏳ PostgreSQL 준비 대기 중..."
    sleep 5
    
    echo ""
    echo "✅ PostgreSQL 시작 완료!"
    echo ""
    echo "📊 접속 정보:"
    echo "   Host: localhost"
    echo "   Port: 5432"
    echo "   Database: kkokkaot_closet"
    echo "   Username: postgres"
    echo "   Password: 000000"
    echo ""
    echo "🔗 접속 명령어:"
    echo "   docker exec -it kkokkaot_postgres psql -U postgres -d kkokkaot_closet"
    
elif [ "$choice" = "2" ]; then
    echo ""
    echo "📦 전체 서비스 시작 중..."
    docker-compose up -d
    
    echo ""
    echo "⏳ 서비스 준비 대기 중..."
    sleep 10
    
    echo ""
    echo "✅ 전체 서비스 시작 완료!"
    echo ""
    echo "📊 실행 중인 서비스:"
    docker-compose ps
    
    echo ""
    echo "🌐 접속 주소:"
    echo "   백엔드 API: http://localhost:4000"
    echo "   프론트엔드: http://localhost:3000"
    echo "   PostgreSQL: localhost:5432"
    
    echo ""
    echo "🧪 백엔드 연결 테스트..."
    sleep 2
    if curl -s http://localhost:4000/ > /dev/null; then
        echo "✅ 백엔드 서버 연결 성공!"
    else
        echo "⚠️  백엔드 서버가 아직 준비 중이거나 오류가 발생했습니다."
        echo "   로그 확인: docker-compose logs app"
    fi
    
elif [ "$choice" = "3" ]; then
    echo ""
    echo "🛑 서비스 중지 중..."
    docker-compose stop
    
    echo ""
    echo "✅ 서비스 중지 완료!"
    
elif [ "$choice" = "4" ]; then
    echo ""
    echo "⚠️  경고: 모든 데이터가 삭제됩니다!"
    read -p "계속하시겠습니까? (yes/no): " confirm
    
    if [ "$confirm" = "yes" ]; then
        echo ""
        echo "🗑️  전체 삭제 중..."
        docker-compose down -v
        
        echo ""
        echo "📦 새로 시작 중..."
        docker-compose up -d
        
        echo ""
        echo "⏳ 서비스 준비 대기 중..."
        sleep 10
        
        echo ""
        echo "✅ 재시작 완료!"
        
        echo ""
        echo "📊 실행 중인 서비스:"
        docker-compose ps
    else
        echo ""
        echo "❌ 취소되었습니다."
    fi
    
else
    echo ""
    echo "❌ 잘못된 선택입니다."
    exit 1
fi

echo ""
echo "📝 유용한 명령어:"
echo "   로그 확인:     docker-compose logs -f"
echo "   상태 확인:     docker-compose ps"
echo "   서비스 중지:   docker-compose stop"
echo "   서비스 재시작: docker-compose restart"
echo "   PostgreSQL 접속: docker exec -it kkokkaot_postgres psql -U postgres -d kkokkaot_closet"
echo ""

