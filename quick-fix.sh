#!/bin/bash
# 꼬까옷 AWS URL 설정 스크립트 (Mac/Linux/EC2)
# 사용법: ./quick-fix.sh

set -e

echo "================================================"
echo "    꼬까옷 프론트엔드 환경변수 설정"
echo "================================================"
echo ""

# 현재 위치 확인
ORIGINAL_PATH=$(pwd)
echo "📂 현재 위치: $ORIGINAL_PATH"

# project 폴더로 이동
if [ -d "project" ]; then
    cd project
    echo "✅ project 폴더로 이동"
elif [ -d "../project" ]; then
    cd ../project
    echo "✅ project 폴더로 이동"
else
    echo "❌ project 폴더를 찾을 수 없습니다!"
    echo "   프로젝트 루트 폴더에서 실행해주세요."
    exit 1
fi

echo ""
echo "🔧 환경 선택:"
echo "  1. 로컬 개발 (http://192.168.56.1:4000)"
echo "  2. AWS 배포 (자동으로 EC2 IP 가져오기)"
echo "  3. AWS 배포 (직접 입력)"
echo ""

read -p "선택 (1, 2 또는 3): " choice

if [ "$choice" = "1" ]; then
    # 로컬 개발용
    API_URL="http://192.168.56.1:4000"
    
    cat > .env << EOF
REACT_APP_API_URL=$API_URL
EXPO_PUBLIC_API_URL=$API_URL
EOF
    
    echo ""
    echo "✅ 로컬 개발 환경으로 설정되었습니다!"
    echo "   API URL: $API_URL"
    
elif [ "$choice" = "2" ]; then
    # AWS 배포용 (자동)
    echo ""
    echo "🌐 EC2 퍼블릭 IP 가져오는 중..."
    
    EC2_IP=$(curl -s ifconfig.me)
    
    if [ -z "$EC2_IP" ]; then
        echo "❌ EC2 IP를 가져올 수 없습니다."
        echo "   직접 입력해주세요."
        exit 1
    fi
    
    API_URL="http://${EC2_IP}:4000"
    
    cat > .env << EOF
REACT_APP_API_URL=$API_URL
EXPO_PUBLIC_API_URL=$API_URL
EOF
    
    echo ""
    echo "✅ AWS 배포 환경으로 설정되었습니다!"
    echo "   API URL: $API_URL"
    
elif [ "$choice" = "3" ]; then
    # AWS 배포용 (수동)
    echo ""
    read -p "AWS EC2 퍼블릭 IP 또는 도메인을 입력하세요 (예: 52.78.123.456): " aws_ip
    
    # http:// 또는 https:// 확인
    if [[ ! "$aws_ip" =~ ^https?:// ]]; then
        echo ""
        echo "프로토콜 선택:"
        echo "  1. HTTP (기본)"
        echo "  2. HTTPS (SSL 인증서 있는 경우)"
        read -p "선택 (1 또는 2): " protocol
        
        if [ "$protocol" = "2" ]; then
            API_URL="https://$aws_ip"
        else
            API_URL="http://${aws_ip}:4000"
        fi
    else
        API_URL="$aws_ip"
    fi
    
    cat > .env << EOF
REACT_APP_API_URL=$API_URL
EXPO_PUBLIC_API_URL=$API_URL
EOF
    
    echo ""
    echo "✅ AWS 배포 환경으로 설정되었습니다!"
    echo "   API URL: $API_URL"
    
else
    echo ""
    echo "❌ 잘못된 선택입니다."
    exit 1
fi

# .env 파일 확인
echo ""
echo "📄 생성된 .env 파일 내용:"
echo "-----------------------------------"
cat .env
echo "-----------------------------------"

# 백엔드 연결 테스트
echo ""
echo "🧪 백엔드 연결 테스트 중..."
if curl -s -o /dev/null -w "%{http_code}" "$API_URL/" | grep -q "200"; then
    echo "✅ 백엔드 서버 연결 성공!"
else
    echo "⚠️  백엔드 서버에 연결할 수 없습니다."
    echo "   백엔드 서버가 실행 중인지 확인해주세요."
fi

echo ""
echo "✅ 설정 완료!"
echo ""
echo "다음 단계:"
echo "  1. 터미널에서 'npm start' 실행"
echo "  2. 콘솔에 API URL이 올바르게 출력되는지 확인"
echo "  3. 앱에서 로그인/회원가입 테스트"
echo ""
echo "문제가 있으면 다음 문서를 참고하세요:"
echo "  - ENV_SETUP_GUIDE.md (환경변수 가이드)"
echo "  - ../API/AWS_URL_CONFIG_GUIDE.md (AWS 배포 가이드)"
echo ""

# 원래 위치로 돌아가기
cd "$ORIGINAL_PATH"

