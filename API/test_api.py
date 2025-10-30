"""
API 통합 테스트 스크립트
- 서버 연결 테스트
- 각 엔드포인트 동작 확인
"""
import requests
import json
from pathlib import Path

# 서버 URL
BASE_URL = "http://localhost:4000"

def print_result(test_name, success, message=""):
    """테스트 결과 출력"""
    status = "✅" if success else "❌"
    print(f"{status} {test_name}")
    if message:
        print(f"   {message}")
    print()

def test_server_health():
    """서버 상태 확인"""
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            data = response.json()
            print_result(
                "서버 상태 확인",
                True,
                f"버전: {data.get('version')}, AI 파이프라인: {data.get('ai_pipeline')}"
            )
            return True
        else:
            print_result("서버 상태 확인", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_result("서버 상태 확인", False, f"연결 실패: {str(e)}")
        return False

def test_weather_api():
    """날씨 API 테스트"""
    try:
        response = requests.get(f"{BASE_URL}/api/weather", params={"city": "Seoul"})
        if response.status_code == 200:
            data = response.json()
            print_result(
                "날씨 API",
                True,
                f"온도: {data.get('temperature')}°C, 날씨: {data.get('description')}"
            )
            return True
        else:
            print_result("날씨 API", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_result("날씨 API", False, f"오류: {str(e)}")
        return False

def test_signup():
    """회원가입 테스트"""
    try:
        payload = {
            "name": "테스트유저",
            "email": f"test_{Path(__file__).stat().st_mtime}@test.com",
            "password": "test1234",
            "ageGroup": 20,
            "stylePreferences": ["캐주얼", "스트리트"]
        }
        
        response = requests.post(f"{BASE_URL}/api/signup", json=payload)
        data = response.json()
        
        if data.get('success'):
            user = data.get('user', {})
            print_result(
                "회원가입",
                True,
                f"사용자 ID: {user.get('user_id')}, 이름: {user.get('name')}"
            )
            return user.get('user_id')
        else:
            print_result("회원가입", False, data.get('message'))
            return None
    except Exception as e:
        print_result("회원가입", False, f"오류: {str(e)}")
        return None

def test_login():
    """로그인 테스트"""
    try:
        payload = {
            "email": "test@example.com",
            "password": "test1234"
        }
        
        response = requests.post(f"{BASE_URL}/api/login", json=payload)
        data = response.json()
        
        if data.get('success'):
            user = data.get('user', {})
            print_result(
                "로그인",
                True,
                f"사용자 ID: {user.get('user_id')}, 이름: {user.get('name')}"
            )
            return user.get('user_id')
        else:
            print_result("로그인", False, data.get('message'))
            return None
    except Exception as e:
        print_result("로그인", False, f"오류: {str(e)}")
        return None

def test_get_wardrobe(user_id):
    """옷장 조회 테스트"""
    try:
        response = requests.get(f"{BASE_URL}/api/wardrobe/{user_id}")
        data = response.json()
        
        if data.get('success'):
            items = data.get('items', [])
            print_result(
                "옷장 조회",
                True,
                f"총 {len(items)}개 아이템"
            )
            return True
        else:
            print_result("옷장 조회", False, data.get('message'))
            return False
    except Exception as e:
        print_result("옷장 조회", False, f"오류: {str(e)}")
        return False

def test_admin_stats():
    """관리자 통계 테스트"""
    try:
        response = requests.get(f"{BASE_URL}/api/admin/stats")
        data = response.json()
        
        if data.get('success'):
            stats = data.get('stats', {})
            print_result(
                "관리자 통계",
                True,
                f"총 사용자: {stats.get('total_users')}명, 총 아이템: {stats.get('total_items')}개"
            )
            return True
        else:
            print_result("관리자 통계", False, data.get('message', ''))
            return False
    except Exception as e:
        print_result("관리자 통계", False, f"오류: {str(e)}")
        return False

def test_health_check():
    """헬스 체크 테스트"""
    try:
        response = requests.get(f"{BASE_URL}/api/admin/health")
        data = response.json()
        
        status = data.get('status', {})
        all_ok = all(
            status.get(key) in ['running', 'active', 'connected'] 
            for key in ['server', 'pipeline', 'database']
        )
        
        print_result(
            "헬스 체크",
            all_ok,
            f"서버: {status.get('server')}, 파이프라인: {status.get('pipeline')}, DB: {status.get('database')}"
        )
        return all_ok
    except Exception as e:
        print_result("헬스 체크", False, f"오류: {str(e)}")
        return False

def main():
    """메인 테스트 실행"""
    print("\n" + "="*60)
    print("🧪 꼬까옷 API 통합 테스트")
    print("="*60 + "\n")
    
    results = {}
    
    # 1. 서버 상태 확인
    results['server'] = test_server_health()
    if not results['server']:
        print("❌ 서버가 실행되지 않았습니다. 먼저 서버를 시작해주세요:")
        print("   python backend_server_new.py")
        return
    
    # 2. 헬스 체크
    results['health'] = test_health_check()
    
    # 3. 날씨 API
    results['weather'] = test_weather_api()
    
    # 4. 회원가입
    user_id = test_signup()
    results['signup'] = user_id is not None
    
    # 5. 로그인 (기존 사용자)
    # results['login'] = test_login()
    
    # 6. 옷장 조회
    if user_id:
        results['wardrobe'] = test_get_wardrobe(user_id)
    
    # 7. 관리자 통계
    results['admin'] = test_admin_stats()
    
    # 결과 요약
    print("\n" + "="*60)
    print("📊 테스트 결과 요약")
    print("="*60 + "\n")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print(f"총 테스트: {total}개")
    print(f"성공: {passed}개")
    print(f"실패: {total - passed}개")
    print(f"성공률: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n✅ 모든 테스트 통과!")
    else:
        print(f"\n⚠️ {total - passed}개 테스트 실패")
    
    print()

if __name__ == "__main__":
    main()

