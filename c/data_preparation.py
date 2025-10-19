#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터 준비 스크립트
1. CNN 라벨을 카테고리별로 분리하여 저장
2. YOLO 바운딩 박스 정보를 사용하여 이미지를 잘라서 저장
"""

import os
import json
import shutil
from pathlib import Path
from PIL import Image
import numpy as np
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

class DataPreparation:
    """데이터 준비 클래스"""
    
    def __init__(self, data_dir="D:/converted_data", output_dir="D:/converted_data/prepared_data"):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        
        # 입력 경로
        self.cnn_dir = self.data_dir / "cnn"
        self.yolo_dir = self.data_dir / "yolo"
        self.images_dir = self.data_dir / "all_images"
        
        # 출력 경로
        self.output_dir.mkdir(exist_ok=True)
        
        print(f"📁 입력 데이터 디렉토리: {self.data_dir}")
        print(f"📁 출력 데이터 디렉토리: {self.output_dir}")
        print(f"📁 CNN 라벨 디렉토리: {self.cnn_dir}")
        print(f"📁 YOLO 라벨 디렉토리: {self.yolo_dir}")
        print(f"📁 이미지 디렉토리: {self.images_dir}")
    
    def prepare_cnn_labels(self):
        """CNN 라벨을 카테고리별로 분리하여 저장"""
        print("\n🔄 CNN 라벨 분리 시작...")
        
        # 카테고리별 출력 디렉토리 생성
        categories = ['상의', '하의', '아우터', '원피스']
        for category in categories:
            category_dir = self.output_dir / "cnn_labels" / category
            category_dir.mkdir(parents=True, exist_ok=True)
        
        # CNN JSON 파일들 처리
        cnn_files = list(self.cnn_dir.glob("*.json"))
        print(f"📊 처리할 CNN 파일: {len(cnn_files)}개")
        
        category_counts = {cat: 0 for cat in categories}
        
        for cnn_file in tqdm(cnn_files, desc="CNN 라벨 분리 중"):
            try:
                # JSON 파일 로드
                with open(cnn_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 각 카테고리별로 처리
                items = data.get('items', {})
                
                for category in categories:
                    if category in items and items[category]:
                        # 해당 카테고리에 데이터가 있으면 저장
                        category_data = {
                            'image_id': data['image_id'],
                            'file_name': data['file_name'],
                            'category': category,
                            'item_data': items[category],
                            'style': data.get('style', {})
                        }
                        
                        # 파일명 생성 (이미지ID_카테고리.json)
                        output_filename = f"{data['image_id']}_{category}.json"
                        output_path = self.output_dir / "cnn_labels" / category / output_filename
                        
                        # JSON 파일 저장
                        with open(output_path, 'w', encoding='utf-8') as f:
                            json.dump(category_data, f, ensure_ascii=False, indent=2)
                        
                        category_counts[category] += 1
                        
            except Exception as e:
                print(f"⚠️ CNN 파일 처리 오류 {cnn_file}: {e}")
                continue
        
        print("\n✅ CNN 라벨 분리 완료!")
        for category, count in category_counts.items():
            print(f"  {category}: {count}개 파일")
        
        return category_counts
    
    def prepare_cropped_images(self):
        """YOLO 바운딩 박스 정보를 사용하여 이미지를 잘라서 저장"""
        print("\n🔄 이미지 크롭 시작...")
        
        # 카테고리별 출력 디렉토리 생성
        categories = ['상의', '하의', '아우터', '원피스']
        category_mapping = {
            'top': '상의',
            'bottom': '하의', 
            'outer': '아우터',
            'dress': '원피스'
        }
        
        for category in categories:
            category_dir = self.output_dir / "cropped_images" / category
            category_dir.mkdir(parents=True, exist_ok=True)
        
        # YOLO JSON 파일들 처리
        yolo_files = list(self.yolo_dir.glob("*.json"))
        print(f"📊 처리할 YOLO 파일: {len(yolo_files)}개")
        
        category_counts = {cat: 0 for cat in categories}
        processed_images = 0
        
        for yolo_file in tqdm(yolo_files, desc="이미지 크롭 중"):
            try:
                # YOLO JSON 파일 로드
                with open(yolo_file, 'r', encoding='utf-8') as f:
                    yolo_data = json.load(f)
                
                # 이미지 정보 추출
                if not yolo_data.get('images') or not yolo_data.get('annotations'):
                    continue
                
                image_info = yolo_data['images'][0]
                image_id = image_info['id']
                image_width = image_info['width']
                image_height = image_info['height']
                
                # 원본 이미지 파일 경로
                image_path = self.images_dir / f"{image_id}.jpg"
                if not image_path.exists():
                    continue
                
                # 원본 이미지 로드
                original_image = Image.open(image_path).convert('RGB')
                
                # 각 어노테이션(바운딩 박스) 처리
                for annotation in yolo_data['annotations']:
                    category_id = annotation['category_id']
                    bbox = annotation['bbox']  # [x, y, width, height]
                    
                    # 카테고리 매핑
                    category_name = None
                    for cat_id, cat_name in enumerate(['outer', 'top', 'bottom', 'dress']):
                        if category_id == cat_id:
                            category_name = category_mapping[cat_name]
                            break
                    
                    if category_name is None:
                        continue
                    
                    # 바운딩 박스 좌표 계산
                    x, y, w, h = bbox
                    
                    # 좌표가 이미지 범위를 벗어나지 않도록 조정
                    x = max(0, min(x, image_width - 1))
                    y = max(0, min(y, image_height - 1))
                    w = max(1, min(w, image_width - x))
                    h = max(1, min(h, image_height - y))
                    
                    # 이미지 크롭
                    cropped_image = original_image.crop((x, y, x + w, y + h))
                    
                    # 크롭된 이미지가 너무 작으면 스킵 (최소 32x32 픽셀)
                    if cropped_image.width < 32 or cropped_image.height < 32:
                        continue
                    
                    # 파일명 생성 (이미지ID_카테고리_순번.jpg)
                    category_count = category_counts[category_name]
                    output_filename = f"{image_id}_{category_name}_{category_count:04d}.jpg"
                    output_path = self.output_dir / "cropped_images" / category_name / output_filename
                    
                    # 크롭된 이미지 저장
                    cropped_image.save(output_path, 'JPEG', quality=95)
                    
                    category_counts[category_name] += 1
                
                processed_images += 1
                
            except Exception as e:
                print(f"⚠️ YOLO 파일 처리 오류 {yolo_file}: {e}")
                continue
        
        print(f"\n✅ 이미지 크롭 완료! 처리된 이미지: {processed_images}개")
        for category, count in category_counts.items():
            print(f"  {category}: {count}개 크롭 이미지")
        
        return category_counts, processed_images
    
    def create_mapping_file(self, cnn_counts, image_counts, processed_images):
        """매핑 정보 파일 생성"""
        print("\n📄 매핑 정보 파일 생성 중...")
        
        mapping_info = {
            'summary': {
                'total_processed_images': processed_images,
                'cnn_label_counts': cnn_counts,
                'cropped_image_counts': image_counts,
                'categories': ['상의', '하의', '아우터', '원피스']
            },
            'directory_structure': {
                'cnn_labels': {
                    'description': '카테고리별로 분리된 CNN 라벨 파일들',
                    'format': 'imageID_category.json'
                },
                'cropped_images': {
                    'description': 'YOLO 바운딩 박스로 크롭된 이미지들',
                    'format': 'imageID_category_sequence.jpg'
                }
            },
            'usage_notes': [
                '각 카테고리별로 CNN 라벨과 크롭된 이미지가 분리되어 저장됨',
                '하나의 원본 이미지에서 여러 카테고리가 감지되면 각각 저장됨',
                'CNN 라벨 파일과 크롭된 이미지는 imageID로 매칭 가능'
            ]
        }
        
        # JSON 매핑 파일 저장
        mapping_file = self.output_dir / 'data_mapping.json'
        with open(mapping_file, 'w', encoding='utf-8') as f:
            json.dump(mapping_info, f, ensure_ascii=False, indent=2)
        
        print(f"💾 매핑 정보 파일 저장: {mapping_file}")
        
        return mapping_file
    
    def run_preparation(self):
        """전체 데이터 준비 프로세스 실행"""
        print("🚀 데이터 준비 시작!")
        print("=" * 60)
        
        try:
            # 1. CNN 라벨 분리
            cnn_counts = self.prepare_cnn_labels()
            
            # 2. 이미지 크롭
            image_counts, processed_images = self.prepare_cropped_images()
            
            # 3. 매핑 파일 생성
            mapping_file = self.create_mapping_file(cnn_counts, image_counts, processed_images)
            
            # 4. 결과 요약
            print(f"\n{'='*60}")
            print("📊 데이터 준비 완료!")
            print(f"{'='*60}")
            
            print(f"📁 출력 디렉토리: {self.output_dir}")
            print(f"📄 매핑 파일: {mapping_file}")
            print(f"🖼️ 처리된 이미지: {processed_images}개")
            
            print("\n📊 카테고리별 결과:")
            print("-" * 40)
            for category in ['상의', '하의', '아우터', '원피스']:
                cnn_count = cnn_counts.get(category, 0)
                img_count = image_counts.get(category, 0)
                print(f"{category:8s}: CNN 라벨 {cnn_count:4d}개, 크롭 이미지 {img_count:4d}개")
            
            print(f"\n🎉 모든 작업이 완료되었습니다!")
            
        except Exception as e:
            print(f"❌ 데이터 준비 중 오류 발생: {e}")
            raise

def main():
    """메인 실행 함수"""
    print("🎯 데이터 준비 스크립트")
    print("CNN 라벨 분리 및 이미지 크롭")
    print("=" * 60)
    
    # 데이터 준비기 초기화
    preparer = DataPreparation()
    
    # 데이터 준비 실행
    preparer.run_preparation()

if __name__ == "__main__":
    main()
