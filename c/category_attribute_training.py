#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
카테고리별 속성 분류 모델 학습 코드
prepared_data의 분리된 데이터를 사용하여 각 카테고리별 속성 분류 모델을 학습합니다.
"""

import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, models
from PIL import Image
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

# 설정
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

class CategoryAttributeDataset(Dataset):
    """카테고리별 속성 분류 데이터셋"""
    
    def __init__(self, image_paths, labels, transform=None):
        self.image_paths = image_paths
        self.labels = labels
        self.transform = transform
    
    def __len__(self):
        return len(self.image_paths)
    
    def __getitem__(self, idx):
        image_path = self.image_paths[idx]
        
        # 이미지 로드
        try:
            image = Image.open(image_path).convert('RGB')
        except Exception as e:
            print(f"이미지 로드 오류 {image_path}: {e}")
            # 빈 이미지 생성
            image = Image.new('RGB', (224, 224), (128, 128, 128))
        
        if self.transform:
            image = self.transform(image)
        
        label = self.labels[idx]
        return image, label

class CategoryAttributeCNN(nn.Module):
    """카테고리별 속성 분류 CNN 모델"""
    
    def __init__(self, num_classes, pretrained=True):
        super(CategoryAttributeCNN, self).__init__()
        
        # ResNet50 백본 사용
        self.backbone = models.resnet50(pretrained=pretrained)
        num_features = self.backbone.fc.in_features  # ResNet50: 2048
        
        # 기존 fc 레이어 제거
        self.backbone.fc = nn.Identity()
        
        # 분류 헤드
        self.classifier = nn.Sequential(
            nn.Linear(num_features, 512),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes)
        )
    
    def forward(self, x):
        features = self.backbone(x)
        output = self.classifier(features)
        return output

class CategoryAttributeTrainer:
    """카테고리별 속성 학습 클래스"""
    
    def __init__(self, data_dir="D:/converted_data/prepared_data", output_dir="D:/kkokkaot/API/pre_trained_weights/category_attributes"):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 카테고리별 데이터 경로
        self.cnn_labels_dir = self.data_dir / "cnn_labels"
        self.cropped_images_dir = self.data_dir / "cropped_images"
        
        # 모델 저장소
        self.models = {}
        self.label_encoders = {}
        self.training_results = {}
        
        print(f"📁 데이터 디렉토리: {self.data_dir}")
        print(f"📁 출력 디렉토리: {self.output_dir}")
        print(f"📁 CNN 라벨 디렉토리: {self.cnn_labels_dir}")
        print(f"📁 크롭 이미지 디렉토리: {self.cropped_images_dir}")
    
    def load_category_data(self, category):
        """특정 카테고리의 데이터 로드"""
        print(f"\n🔄 {category} 데이터 로딩...")
        
        category_cnn_dir = self.cnn_labels_dir / category
        category_images_dir = self.cropped_images_dir / category
        
        if not category_cnn_dir.exists() or not category_images_dir.exists():
            print(f"❌ {category} 디렉토리가 존재하지 않습니다!")
            return None, None
        
        # CNN 라벨 파일들 로드
        cnn_files = list(category_cnn_dir.glob("*.json"))
        print(f"📊 {category} CNN 라벨 파일: {len(cnn_files)}개")
        
        # 이미지 파일들 확인
        image_files = list(category_images_dir.glob("*.jpg"))
        print(f"📊 {category} 크롭 이미지: {len(image_files)}개")
        
        # 데이터 매칭
        valid_data = []
        for cnn_file in cnn_files:
            try:
                with open(cnn_file, 'r', encoding='utf-8') as f:
                    cnn_data = json.load(f)
                
                image_id = cnn_data['image_id']
                item_data = cnn_data['item_data']
                
                # 해당 이미지 ID로 시작하는 이미지 파일들 찾기
                matching_images = [img for img in image_files if img.stem.startswith(f"{image_id}_")]
                
                for image_path in matching_images:
                    valid_data.append({
                        'image_path': str(image_path),
                        'item_data': item_data
                    })
                    
            except Exception as e:
                print(f"⚠️ CNN 파일 처리 오류 {cnn_file}: {e}")
                continue
        
        print(f"✅ {category} 유효한 데이터: {len(valid_data)}개")
        return valid_data
    
    def prepare_attribute_data(self, category_data, attribute_name):
        """특정 속성에 대한 학습 데이터 준비"""
        print(f"  🎯 {attribute_name} 데이터 준비...")
        
        filtered_data = []
        for item in category_data:
            item_data = item['item_data']
            
            # 속성 매핑 (한글 -> 영어)
            attribute_mapping = {
                '카테고리': 'category',
                '색상': 'color',
                '핏': 'fit',
                '소재': 'material',
                '기장': 'length',
                '소매기장': 'sleeve_length',
                '넥라인': 'neckline',
                '프린트': 'print'
            }
            
            # 해당 속성이 있는지 확인
            if attribute_mapping.get(attribute_name) in item_data:
                attr_value = item_data[attribute_mapping[attribute_name]]
                
                # 리스트인 경우 첫 번째 값만 사용
                if isinstance(attr_value, list):
                    attr_value = attr_value[0] if attr_value else None
                
                # 빈 값이 아닌 경우만 추가
                if attr_value and str(attr_value).strip():
                    filtered_data.append({
                        'image_path': item['image_path'],
                        'label': attr_value
                    })
        
        print(f"    📊 {attribute_name} 데이터: {len(filtered_data)}개")
        
        if len(filtered_data) == 0:
            print(f"    ❌ {attribute_name} 학습할 데이터가 없습니다!")
            return None
        
        return filtered_data
    
    def create_data_loaders(self, filtered_data, batch_size=32, test_size=0.2):
        """데이터 로더 생성"""
        if not filtered_data:
            return None, None, None, None
        
        # 라벨 인코딩
        all_labels = [item['label'] for item in filtered_data]
        label_encoder = LabelEncoder()
        encoded_labels = label_encoder.fit_transform(all_labels)
        
        # 이미지 경로와 라벨 분리
        image_paths = [item['image_path'] for item in filtered_data]
        
        # 데이터 분할
        X_train, X_test, y_train, y_test = train_test_split(
            image_paths, encoded_labels, test_size=test_size, random_state=42, stratify=encoded_labels
        )
        
        # 이미지 전처리
        train_transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(10),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        test_transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        # 데이터셋 생성
        train_dataset = CategoryAttributeDataset(X_train, y_train, transform=train_transform)
        test_dataset = CategoryAttributeDataset(X_test, y_test, transform=test_transform)
        
        # 데이터 로더 생성
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
        test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=0)
        
        print(f"    📈 학습 데이터: {len(X_train)}개")
        print(f"    📈 테스트 데이터: {len(X_test)}개")
        print(f"    📈 클래스 수: {len(label_encoder.classes_)}개")
        
        return train_loader, test_loader, label_encoder, len(label_encoder.classes_)
    
    def train_attribute_model(self, train_loader, test_loader, num_classes, category, attribute, epochs=20, learning_rate=0.001):
        """속성별 모델 학습"""
        print(f"    🚀 {category}_{attribute} 모델 학습 시작 (클래스 수: {num_classes})")
        
        # 모델 초기화
        model = CategoryAttributeCNN(num_classes, pretrained=True).to(DEVICE)
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(model.parameters(), lr=learning_rate)
        
        # 학습률 스케줄러
        scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.1)
        
        # 학습 기록
        train_losses = []
        train_accuracies = []
        val_losses = []
        val_accuracies = []
        best_val_acc = 0.0
        
        # Early stopping 설정
        patience = 3
        patience_counter = 0
        
        for epoch in range(epochs):
            # 학습 단계
            model.train()
            train_loss = 0.0
            train_correct = 0
            train_total = 0
            
            for images, labels in tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs}", leave=False):
                images, labels = images.to(DEVICE), labels.to(DEVICE)
                
                optimizer.zero_grad()
                outputs = model(images)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()
                
                train_loss += loss.item()
                _, predicted = torch.max(outputs.data, 1)
                train_total += labels.size(0)
                train_correct += (predicted == labels).sum().item()
            
            # 검증 단계
            model.eval()
            val_loss = 0.0
            val_correct = 0
            val_total = 0
            
            with torch.no_grad():
                for images, labels in test_loader:
                    images, labels = images.to(DEVICE), labels.to(DEVICE)
                    outputs = model(images)
                    loss = criterion(outputs, labels)
                    
                    val_loss += loss.item()
                    _, predicted = torch.max(outputs.data, 1)
                    val_total += labels.size(0)
                    val_correct += (predicted == labels).sum().item()
            
            # 통계 계산
            train_loss /= len(train_loader)
            train_acc = 100 * train_correct / train_total
            val_loss /= len(test_loader)
            val_acc = 100 * val_correct / val_total
            
            train_losses.append(train_loss)
            train_accuracies.append(train_acc)
            val_losses.append(val_loss)
            val_accuracies.append(val_acc)
            
            # 최고 성능 모델 저장
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                patience_counter = 0
                
                # 모델 저장
                model_filename = f'best_model_{category}_{attribute}.pth'
                torch.save(model.state_dict(), self.output_dir / model_filename)
                
            else:
                patience_counter += 1
            
            scheduler.step()
            
            # 얼리스타핑 체크
            if patience_counter >= patience:
                print(f"    ⚠️ Early stopping triggered!")
                break
        
        print(f"    ✅ {category}_{attribute} 학습 완료! 최고 정확도: {best_val_acc:.2f}%")
        
        return model, best_val_acc, train_losses, train_accuracies, val_losses, val_accuracies
    
    def train_category_models(self, category, sample_ratio=1.0):
        """특정 카테고리의 모든 속성 모델 학습"""
        print(f"\n{'='*60}")
        print(f"🎯 {category} 카테고리 모델 학습 시작")
        print(f"{'='*60}")
        
        # 카테고리 데이터 로드
        category_data = self.load_category_data(category)
        if not category_data:
            return None
        
        # 샘플링 적용
        if sample_ratio < 1.0:
            import random
            random.seed(42)
            sample_size = int(len(category_data) * sample_ratio)
            category_data = random.sample(category_data, sample_size)
            print(f"📊 샘플링 적용: {sample_size}개 데이터 선택 ({sample_ratio*100:.1f}%)")
        
        # 속성별 모델 학습
        attributes = ['카테고리', '색상', '핏', '소재', '기장', '소매기장', '넥라인', '프린트']
        category_results = {}
        
        for attribute in attributes:
            try:
                # 속성 데이터 준비
                filtered_data = self.prepare_attribute_data(category_data, attribute)
                if not filtered_data:
                    continue
                
                # 데이터 로더 생성
                data_loaders = self.create_data_loaders(filtered_data, batch_size=32)
                if data_loaders[0] is None:
                    continue
                
                train_loader, test_loader, label_encoder, num_classes = data_loaders
                
                # 라벨 인코더 저장
                self.label_encoders[f'{category}_{attribute}'] = label_encoder
                
                # 모델 학습
                model, best_acc, train_losses, train_accs, val_losses, val_accs = self.train_attribute_model(
                    train_loader, test_loader, num_classes, category, attribute, epochs=10
                )
                
                category_results[attribute] = best_acc
                
                # 모델 정보 저장
                self.save_model_info(category, attribute, num_classes, best_acc, label_encoder)
                
            except Exception as e:
                print(f"❌ {category}_{attribute} 학습 실패: {e}")
                continue
        
        return category_results
    
    def save_model_info(self, category, attribute, num_classes, best_acc, label_encoder):
        """모델 정보 저장"""
        model_filename = f'best_model_{category}_{attribute}.pth'
        info_filename = f'model_info_{category}_{attribute}.json'
        
        model_info = {
            'category': category,
            'attribute': attribute,
            'num_classes': num_classes,
            'class_names': label_encoder.classes_.tolist(),
            'best_accuracy': best_acc,
            'model_path': str(self.output_dir / model_filename)
        }
        
        with open(self.output_dir / info_filename, 'w', encoding='utf-8') as f:
            json.dump(model_info, f, ensure_ascii=False, indent=2)
    
    def run_training(self, sample_ratio=0.3):
        """전체 학습 실행"""
        print("🚀 카테고리별 속성 분류 모델 학습 시작!")
        print("=" * 60)
        print(f"🚀 사용 중인 디바이스: {DEVICE}")
        print(f"📊 데이터 샘플링: {sample_ratio*100:.1f}%")
        
        categories = ['상의', '하의', '아우터', '원피스']
        
        for category in categories:
            try:
                category_results = self.train_category_models(category, sample_ratio)
                if category_results:
                    self.training_results[category] = category_results
                    print(f"✅ {category} 학습 완료!")
                else:
                    print(f"❌ {category} 학습 실패!")
                    
            except Exception as e:
                print(f"❌ {category} 학습 중 오류: {e}")
                continue
        
        # 결과 요약
        self.print_training_summary()
        
        # 결과 파일 저장
        self.save_training_summary()
    
    def print_training_summary(self):
        """학습 결과 요약 출력"""
        print(f"\n{'='*60}")
        print("📊 전체 학습 결과 요약")
        print(f"{'='*60}")
        
        for category, attributes in self.training_results.items():
            print(f"\n{category}:")
            print("-" * 30)
            for attribute, acc in attributes.items():
                print(f"  {attribute:12s}: {acc:6.2f}%")
    
    def save_training_summary(self):
        """학습 결과 요약 파일 저장"""
        summary_file = self.output_dir / 'training_summary.json'
        
        summary_data = {
            'training_results': self.training_results,
            'output_directory': str(self.output_dir),
            'device': str(DEVICE),
            'categories': ['상의', '하의', '아우터', '원피스'],
            'attributes': ['카테고리', '색상', '핏', '소재', '기장', '소매기장', '넥라인', '프린트']
        }
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 학습 결과 요약 저장: {summary_file}")

def main():
    """메인 실행 함수"""
    print("🎯 카테고리별 속성 분류 모델 학습")
    print("=" * 60)
    
    # 학습기 초기화
    trainer = CategoryAttributeTrainer()
    
    # 학습 실행 (30% 샘플링으로 빠른 실험)
    trainer.run_training(sample_ratio=0.3)

if __name__ == "__main__":
    main()
