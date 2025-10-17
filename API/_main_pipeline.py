import cv2
import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from pathlib import Path
from ultralytics import YOLO
from transformers import CLIPProcessor, CLIPModel
from torchvision import models, transforms
import chromadb
import psycopg2
from psycopg2.extras import Json
import json
from typing import Dict, Tuple, Optional

# Background Remover 관련 import
try:
    from rembg import remove, new_session
    REMBG_AVAILABLE = True
except ImportError:
    print("⚠️ rembg가 설치되지 않았습니다. Background Remover 기능을 사용할 수 없습니다.")
    REMBG_AVAILABLE = False

# GPU 설정
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"사용 디바이스: {DEVICE}")


class FashionPipeline:
    """가상옷장 전체 파이프라인"""
    
    def __init__(self, 
                yolo_pose_path: str = "./API/pre_trained_weights/yolo11n-pose.pt",
                yolo_detection_path: str = "./API/pre_trained_weights/yolo_best.pt",
                # top_model_path: str = "./API/pre_trained_weights/fashion_top_model.pth",
                top_model_path: str = "./API/pre_trained_weights/fashion_top_model_1017.pth",
                # bottom_model_path: str = "./API/pre_trained_weights/fashion_bottom_model.pth",
                bottom_model_path: str = "./API/pre_trained_weights/fashion_bottom_model_1017.pth",
                chroma_path: str = "./chroma_db",
                db_config: dict = None):
        """초기화"""
        
        print("\n=== 모델 로딩 중 ===")
        
        # 1. YOLO Pose 모델 (선택적)
        if yolo_pose_path:
            print("1. YOLO Pose 로드...")
            self.yolo_model = YOLO(yolo_pose_path)
        else:
            print("1. YOLO Pose 건너뛰기...")
            self.yolo_model = None
        
        # 1-1. YOLO Detection 모델 (상의/하의/아우터/드레스 분류)
        print("1-1. YOLO Detection 로드...")
        self.yolo_detection_model = YOLO(yolo_detection_path)
        
        # 1-2. Background Remover (누끼따기)
        if REMBG_AVAILABLE:
            print("1-2. Background Remover 초기화...")
            try:
                # Background Remover 세션 초기화 (u2net 모델 사용)
                self.rembg_session = new_session('u2net')
                self.rembg_available = True
                print("✅ Background Remover 초기화 완료!")
            except Exception as e:
                print(f"⚠️ Background Remover 초기화 실패: {e}")
                self.rembg_session = None
                self.rembg_available = False
        else:
            print("1-2. Background Remover 건너뛰기...")
            self.rembg_session = None
            self.rembg_available = False
        
        # 2. 상의 모델 로드
        print("2. 상의 모델 로드...")
        top_checkpoint = torch.load(top_model_path, map_location=DEVICE, weights_only=False)
        self.top_encoders = top_checkpoint['encoders']
        
        top_num_categories = len(self.top_encoders['category'].classes_)
        top_num_colors = len(self.top_encoders['color'].classes_)
        top_num_fits = len(self.top_encoders['fit'].classes_)
        top_num_materials = len(self.top_encoders['material_classes'])
        
        self.top_model = MultiTaskFashionModel(
            top_num_categories, top_num_colors, top_num_fits, top_num_materials
        ).to(DEVICE)
        self.top_model.load_state_dict(top_checkpoint['model_state_dict'])
        self.top_model.eval()
        
        # 3. 하의 모델 로드
        print("3. 하의 모델 로드...")
        bottom_checkpoint = torch.load(bottom_model_path, map_location=DEVICE, weights_only=False)
        self.bottom_encoders = bottom_checkpoint['encoders']
        
        bottom_num_categories = len(self.bottom_encoders['category'].classes_)
        bottom_num_colors = len(self.bottom_encoders['color'].classes_)
        bottom_num_fits = len(self.bottom_encoders['fit'].classes_)
        bottom_num_materials = len(self.bottom_encoders['material_classes'])
        
        self.bottom_model = MultiTaskFashionModel(
            bottom_num_categories, bottom_num_colors, bottom_num_fits, bottom_num_materials
        ).to(DEVICE)
        self.bottom_model.load_state_dict(bottom_checkpoint['model_state_dict'])
        self.bottom_model.eval()
        
        # 이미지 전처리
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
        
        # 4. CLIP 모델 (임베딩용)
        print("4. CLIP 모델 로드...")
        try:
            self.clip_model = CLIPModel.from_pretrained("patrickjohncyh/fashion-clip").to(DEVICE)
            self.clip_processor = CLIPProcessor.from_pretrained("patrickjohncyh/fashion-clip")
        except:
            self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-large-patch14").to(DEVICE)
            self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-large-patch14")
        self.clip_model.eval()
        
        # 5. ChromaDB
        print("5. ChromaDB 연결...")
        self.chroma_client = chromadb.PersistentClient(path=chroma_path)
        self.chroma_collection = self.chroma_client.get_collection(name="fashion_collection")
        
        # 6. PostgreSQL
        print("6. PostgreSQL 연결...")
        if db_config is None:
            db_config = {
                'host': 'localhost',
                'port': 5432,
                'database': 'kkokkaot_closet',
                'user': 'postgres',
                'password': '000000'
            }
        self.db_config = db_config  # 연결 정보 저장
        self.db_conn = psycopg2.connect(**db_config)
        
        print("\n✓ 모든 모델 로드 완료\n")
    
    def reconnect_db(self):
        """데이터베이스 연결 재시도"""
        try:
            if hasattr(self, 'db_conn') and self.db_conn:
                self.db_conn.close()
        except:
            pass
        
        try:
            self.db_conn = psycopg2.connect(**self.db_config)
            print("✅ 데이터베이스 재연결 성공")
        except Exception as e:
            print(f"❌ 데이터베이스 재연결 실패: {e}")
            raise
    
    def detect_fashion_categories(self, image_path: str) -> Dict:
        """YOLO Detection으로 상의/하의/아우터/드레스 4개 카테고리 분류"""
        
        print(f"[1/6] YOLO Detection으로 카테고리 분류 중: {image_path}")
        
        # 이미지 로드
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"이미지를 열 수 없습니다: {image_path}")
        
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # YOLO Detection 추론
        results = self.yolo_detection_model(image_path, verbose=False)
        
        detected_items = {
            'top': [],
            'bottom': [],
            'outer': [],
            'dress': []
        }
        
        # 🔍 디버깅: YOLO 원본 결과 출력
        print(f"  🔍 YOLO 원본 결과: {len(results[0].boxes)}개 객체 감지")
        if len(results[0].boxes) > 0:
            for i, box in enumerate(results[0].boxes):
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                print(f"    - 객체 {i}: class_id={class_id}, confidence={confidence:.3f}")
        
        if len(results[0].boxes) > 0:
            boxes = results[0].boxes
            for i, box in enumerate(boxes):
                # 클래스 ID와 신뢰도
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                
                # 클래스 이름 매핑 (yolo_best.pt 모델의 클래스 순서에 따라)
                # 실제 모델 클래스 순서: ['outer', 'top', 'bottom', 'dress'] (로그 기반 추정)
                class_names = ['outer', 'top', 'bottom', 'dress']
                
                if class_id < len(class_names) and confidence > 0.3:  # 신뢰도 임계값 낮춤
                    class_name = class_names[class_id]
                    
                    # 바운딩 박스 좌표
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    
                    # 이미지 크롭
                    cropped_image = image_rgb[y1:y2, x1:x2]
                    
                    detected_items[class_name].append({
                        'bbox': (x1, y1, x2, y2),
                        'confidence': confidence,
                        'cropped_image': cropped_image
                    })
                    
                    print(f"  - class_id={class_id}, {class_name}: confidence={confidence:.2f}, bbox=({x1},{y1},{x2},{y2})")
        
        # 모든 감지된 의류를 포함 (다중 의류 감지 지원)
        final_items = {}
        for category, items in detected_items.items():
            if items:
                # 신뢰도 기준으로 정렬하여 가장 높은 것 선택
                best_item = max(items, key=lambda x: x['confidence'])
                final_items[category] = best_item
                print(f"  ✅ {category} 선택: confidence={best_item['confidence']:.2f}")
        
        # 🔍 디버깅: 감지된 모든 아이템 출력
        print(f"  📊 총 감지된 카테고리: {list(final_items.keys())}")
        for category, item in final_items.items():
            bbox = item['bbox']
            print(f"    - {category}: bbox=({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]})")
        
        # 🔍 디버깅: 최종 결과 확인
        has_top = 'top' in final_items
        has_bottom = 'bottom' in final_items
        has_outer = 'outer' in final_items
        has_dress = 'dress' in final_items
        
        print(f"  🔍 최종 Detection 결과:")
        print(f"    - has_top: {has_top}")
        print(f"    - has_bottom: {has_bottom}")
        print(f"    - has_outer: {has_outer}")
        print(f"    - has_dress: {has_dress}")
        
        # ✅ 의류 감지 검증: 아무것도 감지되지 않았으면 오류 발생
        if not any([has_top, has_bottom, has_outer, has_dress]):
            print(f"  ❌ 의류 감지 실패: 신뢰도 0.3 이상인 의류가 감지되지 않았습니다.")
            
            # 더 상세한 오류 메시지 생성
            total_detections = len(results[0].boxes) if results[0].boxes is not None else 0
            error_details = f"총 {total_detections}개의 객체가 감지되었지만, 신뢰도 0.3 이상인 의류(top, bottom, outer, dress)가 없습니다."
            
            if total_detections == 0:
                error_details = "이미지에서 의류를 전혀 감지할 수 없습니다. 의류가 명확하게 보이는 사진인지 확인해주세요."
            elif total_detections > 0:
                error_details += f" 감지된 객체들의 신뢰도가 너무 낮아 의류로 인식되지 않았습니다."
            
            raise ValueError(error_details)
        
        return {
            'original': image_rgb,
            'detected_items': final_items,
            'has_top': has_top,
            'has_bottom': has_bottom,
            'has_outer': has_outer,
            'has_dress': has_dress
        }

    def separate_top_bottom(self, image_path: str) -> Dict:
        """1단계: YOLO Pose로 상/하의 분리"""
        
        print(f"[1/6] 이미지 분리 중: {image_path}")
        
        # YOLO Pose 모델이 없으면 전체 이미지만 반환
        if self.yolo_model is None:
            print("  ⚠️ YOLO Pose 모델이 없어서 전체 이미지만 사용합니다.")
            return {
                'original': image_path,
                'top': None,
                'bottom': None,
                'has_top': False,
                'has_bottom': False
            }
        
        # 이미지 로드
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"이미지를 열 수 없습니다: {image_path}")
        
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # YOLO 추론
        results = self.yolo_model(image_path, verbose=False)
        
        if len(results[0].boxes) == 0:
            raise ValueError("사람이 감지되지 않았습니다")
        
        # 키포인트 추출
        keypoints = results[0].keypoints.data[0].cpu().numpy()
        
        # 허리 위치 계산
        left_shoulder = keypoints[5]
        right_shoulder = keypoints[6]
        left_hip = keypoints[11]
        right_hip = keypoints[12]
        
        shoulder_y = np.mean([left_shoulder[1], right_shoulder[1]])
        hip_y = np.mean([left_hip[1], right_hip[1]])
        waist_y = int(shoulder_y + (hip_y - shoulder_y) * 0.6)
        
        # 상의/하의 분리
        height = image_rgb.shape[0]
        top_image = image_rgb[0:waist_y, :]
        bottom_image = image_rgb[waist_y:height, :]
        
        print(f"  - 허리선: Y={waist_y}")
        print(f"  - 상의 크기: {top_image.shape}")
        print(f"  - 하의 크기: {bottom_image.shape}")
        
        return {
            'original': image_rgb,
            'top': top_image,
            'bottom': bottom_image,
            'waist_y': waist_y,
            'has_top': top_image.shape[0] > 50,
            'has_bottom': bottom_image.shape[0] > 50
        }
    
    
    def predict_attributes(self, image: np.ndarray, is_top: bool = True) -> Dict:
        """2단계: 속성 예측"""
        
        item_type = "상의" if is_top else "하의"
        print(f"[2/6] {item_type} 속성 예측 중...")
        
        # PIL 이미지로 변환
        pil_image = Image.fromarray(image)
        image_tensor = self.transform(pil_image).unsqueeze(0).to(DEVICE)
        
        # 상의/하의에 따라 다른 모델과 인코더 사용
        if is_top:
            model = self.top_model
            encoders = self.top_encoders
        else:
            model = self.bottom_model
            encoders = self.bottom_encoders
        
        # 예측
        with torch.no_grad():
            cat_out, color_out, fit_out, mat_out = model(image_tensor)
            
            # 확률값
            cat_probs = torch.softmax(cat_out, dim=1)[0]
            color_probs = torch.softmax(color_out, dim=1)[0]
            fit_probs = torch.softmax(fit_out, dim=1)[0]
            mat_probs = torch.sigmoid(mat_out)[0]
            
            # 최대값 인덱스
            cat_idx = cat_probs.argmax().item()
            color_idx = color_probs.argmax().item()
            fit_idx = fit_probs.argmax().item()
            
            # 라벨 변환
            category = encoders['category'].inverse_transform([cat_idx])[0]
            color = encoders['color'].inverse_transform([color_idx])[0]
            fit = encoders['fit'].inverse_transform([fit_idx])[0]
            
            # 소재 (threshold > 0.5)
            mat_indices = (mat_probs > 0.5).nonzero(as_tuple=True)[0]
            materials = [encoders['material_classes'][i] for i in mat_indices.cpu().numpy()]
            
            # 신뢰도
            cat_conf = cat_probs[cat_idx].item()
            color_conf = color_probs[color_idx].item()
            fit_conf = fit_probs[fit_idx].item()
        
        result = {
            'category': category,
            'color': color,
            'fit': fit,
            'materials': materials,
            'category_confidence': cat_conf,
            'color_confidence': color_conf,
            'fit_confidence': fit_conf
        }
        
        print(f"  - 카테고리: {category} ({cat_conf:.2f})")
        print(f"  - 색상: {color} ({color_conf:.2f})")
        print(f"  - 핏: {fit} ({fit_conf:.2f})")
        print(f"  - 소재: {materials}")
        
        return result
    
    
    def create_embedding(self, image: np.ndarray) -> np.ndarray:
        """3단계: CLIP 임베딩 생성"""
        
        print("[3/6] 이미지 임베딩 생성 중...")
        
        pil_image = Image.fromarray(image)
        
        inputs = self.clip_processor(
            images=pil_image,
            return_tensors="pt",
            padding=True
        ).to(DEVICE)
        
        with torch.no_grad():
            image_features = self.clip_model.get_image_features(**inputs)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        
        embedding = image_features.cpu().numpy()[0]
        print(f"  - 임베딩 차원: {embedding.shape}")
        
        return embedding
    
    
    def save_to_postgresql(self, user_id: int, image_path: str, 
                        detection_result: Dict, 
                        top_attrs: Dict = None, 
                        bottom_attrs: Dict = None,
                        outer_attrs: Dict = None,
                        dress_attrs: Dict = None,
                        chroma_id: str = None) -> int:
        """4단계: PostgreSQL에 저장"""
        
        print("[4/6] PostgreSQL에 저장 중...")
        
        # ✅ 트랜잭션 시작 전 기존 트랜잭션 정리
        try:
            self.db_conn.rollback()
        except:
            pass
        
        try:
            with self.db_conn.cursor() as cur:
                # wardrobe_items 삽입
                cur.execute("""
                    INSERT INTO wardrobe_items (
                        user_id, original_image_path, 
                        has_top, has_bottom, has_outer, has_dress,
                        chroma_embedding_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING item_id
                """, (
                    user_id, 
                    image_path,
                    detection_result['has_top'],
                    detection_result['has_bottom'],
                    detection_result['has_outer'],
                    detection_result['has_dress'],
                    chroma_id
                ))
                
                item_id = cur.fetchone()[0]
                
                # 상의 속성
                if top_attrs and detection_result['has_top']:
                    cur.execute("""
                        INSERT INTO top_attributes (
                            item_id, category, color, fit, materials,
                            category_confidence, color_confidence, fit_confidence
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        item_id,
                        top_attrs['category'],
                        top_attrs['color'],
                        top_attrs['fit'],
                        Json(top_attrs['materials']),
                        top_attrs['category_confidence'],
                        top_attrs['color_confidence'],
                        top_attrs['fit_confidence']
                    ))
                
                # 하의 속성
                if bottom_attrs and detection_result['has_bottom']:
                    cur.execute("""
                        INSERT INTO bottom_attributes (
                            item_id, category, color, fit, materials,
                            category_confidence, color_confidence, fit_confidence
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        item_id,
                        bottom_attrs['category'],
                        bottom_attrs['color'],
                        bottom_attrs['fit'],
                        Json(bottom_attrs['materials']),
                        bottom_attrs['category_confidence'],
                        bottom_attrs['color_confidence'],
                        bottom_attrs['fit_confidence']
                    ))
                
                # 아우터 속성 (outer_attributes 테이블에 저장)
                if outer_attrs and detection_result['has_outer']:
                    cur.execute("""
                        INSERT INTO outer_attributes (
                            item_id, category, color, fit, materials,
                            category_confidence, color_confidence, fit_confidence
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        item_id,
                        outer_attrs['category'],
                        outer_attrs['color'],
                        outer_attrs['fit'],
                        Json(outer_attrs['materials']),
                        outer_attrs['category_confidence'],
                        outer_attrs['color_confidence'],
                        outer_attrs['fit_confidence']
                    ))
                
                # 드레스 속성 (dress_attributes 테이블에 저장)
                if dress_attrs and detection_result['has_dress']:
                    cur.execute("""
                        INSERT INTO dress_attributes (
                            item_id, category, color, fit, materials,
                            category_confidence, color_confidence, fit_confidence
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        item_id,
                        dress_attrs['category'],
                        dress_attrs['color'],
                        dress_attrs['fit'],
                        Json(dress_attrs['materials']),
                        dress_attrs['category_confidence'],
                        dress_attrs['color_confidence'],
                        dress_attrs['fit_confidence']
                    ))
                
                # ✅ 커밋
                self.db_conn.commit()
                
            print(f"  - 아이템 ID: {item_id}")
            return item_id
            
        except Exception as e:
            # ✅ 에러 발생 시 명시적 rollback
            try:
                self.db_conn.rollback()
                print(f"  ❌ PostgreSQL 저장 실패 (rollback 완료): {e}")
            except:
                print(f"  ❌ PostgreSQL 저장 실패: {e}")
            raise e
    
    
    def save_to_chromadb(self, item_id: int, embedding: np.ndarray, 
                        metadata: Dict) -> str:
        """5단계: ChromaDB에 저장"""
        
        print("[5/6] ChromaDB에 저장 중...")
        
        chroma_id = f"item_{item_id}"
        
        # 메타데이터를 문서로 변환
        doc_parts = []
        if metadata.get('top_category'):
            doc_parts.append(f"상의: {metadata['top_category']}")
        if metadata.get('bottom_category'):
            doc_parts.append(f"하의: {metadata['bottom_category']}")
        if metadata.get('top_color'):
            doc_parts.append(f"색상: {metadata['top_color']}")
        
        document = " | ".join(doc_parts)
        
        self.chroma_collection.add(
            ids=[chroma_id],
            embeddings=[embedding.tolist()],
            metadatas=[metadata],
            documents=[document]
        )
        
        print(f"  - Chroma ID: {chroma_id}")
        return chroma_id
    
    
    def search_similar(self, embedding: np.ndarray, n_results: int = 5) -> list:
        """6단계: 유사 아이템 검색"""
        
        print(f"[6/6] 유사 아이템 검색 중 (Top {n_results})...")
        
        results = self.chroma_collection.query(
            query_embeddings=[embedding.tolist()],
            n_results=n_results
        )
        
        print(f"  - 검색 완료: {len(results['ids'][0])}개")
        return results
    
    def remove_background_with_rembg(self, image: np.ndarray) -> np.ndarray:
        """
        Background Remover를 사용하여 배경 제거
        
        Args:
            image: 입력 이미지 (RGB)
        
        Returns:
            transparent_image: 투명 배경 이미지 (RGBA)
        """
        if not self.rembg_available:
            print("⚠️ Background Remover가 사용 불가능합니다.")
            return None
        
        try:
            # PIL Image로 변환
            pil_image = Image.fromarray(image)
            
            # Background Remover로 배경 제거
            transparent_image = remove(pil_image, session=self.rembg_session)
            
            # numpy array로 변환
            transparent_array = np.array(transparent_image)
            
            return transparent_array
            
        except Exception as e:
            print(f"❌ Background Remover 처리 실패: {e}")
            return None
    
    
    
    def process_image(self, image_path: str, user_id: int, 
                    save_separated_images: bool = False) -> Dict:
        """전체 파이프라인 실행"""
        
        print(f"\n{'='*60}")
        print(f"파이프라인 시작: {image_path}")
        print(f"{'='*60}\n")
        
        try:
            # 1. YOLO Detection으로 카테고리 분류
            detection_result = self.detect_fashion_categories(image_path)
            
            # 2. ✅ 속성 예측 - YOLO Detection으로 크롭된 이미지를 각각 모델에 입력!
            print(f"  🔍 Detection 결과 확인:")
            print(f"    - has_top: {detection_result['has_top']}")
            print(f"    - has_bottom: {detection_result['has_bottom']}")
            print(f"    - has_outer: {detection_result['has_outer']}")
            print(f"    - has_dress: {detection_result['has_dress']}")
            
            top_attrs = None
            bottom_attrs = None
            outer_attrs = None
            dress_attrs = None
            
            if detection_result['has_top']:
                # 상의 이미지를 상의 모델에 입력
                print("[2-1/6] 상의 이미지로 상의 속성 예측...")
                top_attrs = self.predict_attributes(
                    detection_result['detected_items']['top']['cropped_image'],
                    is_top=True
                )
            
            if detection_result['has_bottom']:
                # 하의 이미지를 하의 모델에 입력
                print("[2-2/6] 하의 이미지로 하의 속성 예측...")
                bottom_attrs = self.predict_attributes(
                    detection_result['detected_items']['bottom']['cropped_image'],
                    is_top=False
                )
            
            if detection_result['has_outer']:
                # 아우터 이미지를 상의 모델에 입력 (아우터도 상의 계열)
                print("[2-3/6] 아우터 이미지로 아우터 속성 예측...")
                print(f"  🔍 아우터 이미지 크기: {detection_result['detected_items']['outer']['cropped_image'].shape}")
                outer_attrs = self.predict_attributes(
                    detection_result['detected_items']['outer']['cropped_image'],
                    is_top=True
                )
                print(f"  ✅ 아우터 속성 예측 완료: {outer_attrs['category'] if outer_attrs else 'None'}")
            
            if detection_result['has_dress']:
                # 드레스 이미지를 상의 모델에 입력 (드레스는 전체 의류)
                print("[2-4/6] 드레스 이미지로 드레스 속성 예측...")
                dress_attrs = self.predict_attributes(
                    detection_result['detected_items']['dress']['cropped_image'],
                    is_top=True
                )
            
            # 3. 임베딩 생성 (원본 전체 이미지로)
            embedding = self.create_embedding(detection_result['original'])
            
            # 4. 메타데이터 준비
            metadata = {
                'user_id': str(user_id),
                'has_top': str(detection_result['has_top']),
                'has_bottom': str(detection_result['has_bottom']),
                'has_outer': str(detection_result['has_outer']),
                'has_dress': str(detection_result['has_dress'])
            }
            
            if top_attrs:
                metadata['top_category'] = top_attrs['category']
                metadata['top_color'] = top_attrs['color']
                metadata['top_fit'] = top_attrs['fit']
            
            if bottom_attrs:
                metadata['bottom_category'] = bottom_attrs['category']
                metadata['bottom_color'] = bottom_attrs['color']
                metadata['bottom_fit'] = bottom_attrs['fit']
            
            if outer_attrs:
                metadata['outer_category'] = outer_attrs['category']
                metadata['outer_color'] = outer_attrs['color']
                metadata['outer_fit'] = outer_attrs['fit']
            
            if dress_attrs:
                metadata['dress_category'] = dress_attrs['category']
                metadata['dress_color'] = dress_attrs['color']
                metadata['dress_fit'] = dress_attrs['fit']
            
            # 5. PostgreSQL 저장 (chroma_id는 나중에 업데이트)
            item_id = self.save_to_postgresql(
                user_id, image_path, detection_result, 
                top_attrs, bottom_attrs, outer_attrs, dress_attrs,
                chroma_id=None
            )
            
            # 6. ChromaDB 저장
            chroma_id = self.save_to_chromadb(item_id, embedding, metadata)
            
            # 7. PostgreSQL에 chroma_id 업데이트
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    UPDATE wardrobe_items 
                    SET chroma_embedding_id = %s 
                    WHERE item_id = %s
                """, (chroma_id, item_id))
                self.db_conn.commit()
            
            # 8. 유사 아이템 검색
            similar_items = self.search_similar(embedding, n_results=5)
            
            # 9. ✅ 분리된 이미지 저장 (사용자별 폴더 구조)
            if save_separated_images:
                # 📁 사용자별 + 카테고리별 폴더 구조 생성
                base_dir = Path("./processed_images") / f"user_{user_id}"
                folders = {
                    'full': base_dir / 'full',
                    'top': base_dir / 'top',
                    'bottom': base_dir / 'bottom',
                    'outer': base_dir / 'outer',
                    'dress': base_dir / 'dress'
                }
                
                for folder in folders.values():
                    folder.mkdir(parents=True, exist_ok=True)
                
                # 전체 이미지 저장
                full_path = folders['full'] / f"item_{item_id}_full.jpg"
                Image.fromarray(detection_result['original']).save(full_path)
                print(f"  ✅ 전체 이미지 저장: {full_path}")
                
                # YOLO Detection으로 크롭된 각 카테고리별 이미지 저장
                if detection_result['has_top']:
                    top_path = folders['top'] / f"item_{item_id}_top.jpg"
                    Image.fromarray(detection_result['detected_items']['top']['cropped_image']).save(top_path)
                    print(f"  ✅ 상의 저장: {top_path}")
                
                if detection_result['has_bottom']:
                    bottom_path = folders['bottom'] / f"item_{item_id}_bottom.jpg"
                    Image.fromarray(detection_result['detected_items']['bottom']['cropped_image']).save(bottom_path)
                    print(f"  ✅ 하의 저장: {bottom_path}")
                
                if detection_result['has_outer']:
                    outer_path = folders['outer'] / f"item_{item_id}_outer.jpg"
                    Image.fromarray(detection_result['detected_items']['outer']['cropped_image']).save(outer_path)
                    print(f"  ✅ 아우터 저장: {outer_path}")
                
                if detection_result['has_dress']:
                    dress_path = folders['dress'] / f"item_{item_id}_dress.jpg"
                    Image.fromarray(detection_result['detected_items']['dress']['cropped_image']).save(dress_path)
                    print(f"  ✅ 드레스 저장: {dress_path}")
                
                # 🎭 Background Remover로 누끼따기 이미지 저장 (마네킹 합성용)
                if self.rembg_available:
                    sam_folders = {
                        'top_segmented': base_dir / 'top_segmented',
                        'bottom_segmented': base_dir / 'bottom_segmented',
                        'outer_segmented': base_dir / 'outer_segmented',
                        'dress_segmented': base_dir / 'dress_segmented'
                    }
                    
                    for folder in sam_folders.values():
                        folder.mkdir(parents=True, exist_ok=True)
                    
                    # 각 카테고리별로 Background Remover 수행
                    categories = [
                        ('top', 'top_segmented', detection_result['has_top']),
                        ('bottom', 'bottom_segmented', detection_result['has_bottom']),
                        ('outer', 'outer_segmented', detection_result['has_outer']),
                        ('dress', 'dress_segmented', detection_result['has_dress'])
                    ]
                    
                    for category, rembg_folder, has_item in categories:
                        if has_item:
                            try:
                                # bbox 크롭 이미지 가져오기
                                cropped_image = detection_result['detected_items'][category]['cropped_image']
                                
                                # Background Remover로 배경 제거
                                transparent_image = self.remove_background_with_rembg(cropped_image)
                                
                                if transparent_image is not None:
                                    # PNG로 저장
                                    rembg_path = sam_folders[rembg_folder] / f"item_{item_id}_{category}_segmented.png"
                                    Image.fromarray(transparent_image, 'RGBA').save(rembg_path)
                                    print(f"  🎭 {category} 누끼따기 저장: {rembg_path}")
                                else:
                                    print(f"  ⚠️ {category} Background Remover 실패")
                                    
                            except Exception as e:
                                print(f"  ❌ {category} Background Remover 처리 오류: {e}")
                else:
                    print("  ⚠️ Background Remover가 사용 불가능하여 누끼따기 건너뛰기")
                    print("  💡 Background Remover를 설치하려면: pip install rembg")
            
            print(f"\n{'='*60}")
            print(f"✔ 파이프라인 완료!")
            print(f"  - 아이템 ID: {item_id}")
            print(f"  - Chroma ID: {chroma_id}")
            if top_attrs:
                print(f"  - 상의: {top_attrs['category']} ({top_attrs['color']})")
            if bottom_attrs:
                print(f"  - 하의: {bottom_attrs['category']} ({bottom_attrs['color']})")
            if outer_attrs:
                print(f"  - 아우터: {outer_attrs['category']} ({outer_attrs['color']})")
            if dress_attrs:
                print(f"  - 드레스: {dress_attrs['category']} ({dress_attrs['color']})")
            print(f"{'='*60}\n")
            
            return {
                'success': True,
                'item_id': item_id,
                'chroma_id': chroma_id,
                'detection_result': detection_result,
                'top_attributes': top_attrs,
                'bottom_attributes': bottom_attrs,
                'outer_attributes': outer_attrs,
                'dress_attributes': dress_attrs,
                'similar_items': similar_items
            }
            
        except Exception as e:
            print(f"\n✗ 에러 발생: {e}")
            import traceback
            traceback.print_exc()
            
            # ✅ 트랜잭션 rollback (추가)
            try:
                if hasattr(self, 'db_conn') and self.db_conn:
                    self.db_conn.rollback()
            except:
                pass
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_similar_items(self, image_path: str, n_results: int = 5) -> list:
        """주어진 이미지와 유사한 아이템을 검색"""
        try:
            # 1. 이미지 임베딩 생성
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"이미지를 찾을 수 없습니다: {image_path}")
            
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            embedding = self.create_embedding(image_rgb)
            
            # 2. ChromaDB에서 유사 아이템 검색
            search_results = self.search_similar(embedding, n_results)
            
            # 3. 결과 정리
            item_ids = [int(id.replace("item_", "")) for id in search_results['ids'][0]]
            distances = search_results['distances'][0]
            
            results = []
            for i, item_id in enumerate(item_ids):
                results.append({
                    'item_id': item_id,
                    'distance': distances[i]
                })
                
            return results
        
        except Exception as e:
            print(f"❌ 유사 아이템 검색 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def close(self):
        """연결 종료"""
        if self.db_conn:
            self.db_conn.close()
            print("PostgreSQL 연결 종료")


# MultiTaskFashionModel 정의
class MultiTaskFashionModel(nn.Module):
    """Multi-task 패션 속성 예측 모델"""
    
    def __init__(self, num_categories, num_colors, num_fits, num_materials):
        super().__init__()
        
        self.backbone = models.efficientnet_b0(weights='IMAGENET1K_V1')
        num_features = self.backbone.classifier[1].in_features
        self.backbone.classifier = nn.Identity()
        
        self.category_head = nn.Sequential(
            nn.Linear(num_features, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, num_categories)
        )
        
        self.color_head = nn.Sequential(
            nn.Linear(num_features, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_colors)
        )
        
        self.fit_head = nn.Sequential(
            nn.Linear(num_features, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, num_fits)
        )
        
        self.material_head = nn.Sequential(
            nn.Linear(num_features, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_materials)
        )
    
    def forward(self, x):
        features = self.backbone(x)
        
        category_out = self.category_head(features)
        color_out = self.color_head(features)
        fit_out = self.fit_head(features)
        material_out = self.material_head(features)
        
        return category_out, color_out, fit_out, material_out