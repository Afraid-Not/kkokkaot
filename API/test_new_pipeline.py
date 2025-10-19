#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
새로운 파이프라인 테스트 스크립트
"""

import sys
from pathlib import Path

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent))

from _main_pipeline import FashionPipeline

def test_pipeline():
    """파이프라인 테스트"""
    print("🧪 새로운 패션 파이프라인 테스트 시작")
    
    try:
        # 파이프라인 초기화
        print("1. 파이프라인 초기화 중...")
        pipeline = FashionPipeline()
        print("✅ 파이프라인 초기화 성공!")
        
        # 테스트 이미지 경로 (실제 이미지 경로로 변경 필요)
        test_image_path = "test_image.jpg"
        
        if Path(test_image_path).exists():
            print(f"2. 테스트 이미지 처리: {test_image_path}")
            result = pipeline.process_image(test_image_path, user_id=1)
            
            if result['success']:
                print("✅ 이미지 처리 성공!")
                print(f"   - 아이템 ID: {result['item_id']}")
                print(f"   - 스타일: {result['style_result']['style']}")
                print(f"   - 감지된 의류: {list(result['detection_result']['detected_items'].keys())}")
            else:
                print(f"❌ 이미지 처리 실패: {result['error']}")
        else:
            print(f"⚠️ 테스트 이미지가 없습니다: {test_image_path}")
            print("   파이프라인 초기화만 테스트합니다.")
        
        # 연결 종료
        pipeline.close()
        print("✅ 파이프라인 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 파이프라인 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pipeline()
