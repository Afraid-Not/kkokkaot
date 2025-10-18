// components/figma/VirtualFittingScreen.tsx
import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Pressable,
  Image,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  ArrowLeft,
  Camera,
  Upload,
  Sparkles,
  Info,
} from 'lucide-react-native';
import AppHeader from '../common/AppHeader';
import BottomNavBar from '../common/BottomNavBar';

type NavigationStep =
  | 'home'
  | 'today-curation'
  | 'daily-outfit'
  | 'wardrobe-management'
  | 'style-analysis'
  | 'shopping'
  | 'virtual-fitting'
  | 'recent-styling'
  | 'blocked-outfits'
  | 'llm-chat';

export default function VirtualFittingScreen({
  onBack,
  onNavigate,
}: {
  onBack: () => void;
  onNavigate: (step: NavigationStep) => void;
}) {
  const [selectedMode, setSelectedMode] = useState<'body' | 'clothes' | null>(null);

  const handleCameraPress = () => {
    Alert.alert('준비 중', '카메라 촬영 기능은 곧 출시됩니다! 📸');
  };

  const handleUploadPress = () => {
    Alert.alert('준비 중', '이미지 업로드 기능은 곧 출시됩니다! 📤');
  };

  const handleStartFitting = () => {
    if (!selectedMode) {
      Alert.alert('알림', '먼저 가상 피팅 모드를 선택해주세요.');
      return;
    }
    Alert.alert('준비 중', 'AI 가상 피팅 기능은 곧 출시됩니다! ✨');
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <AppHeader title="가상 피팅" onBack={onBack} />

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* 안내 카드 */}
        <View style={styles.infoCard}>
          <Info size={24} color="#3B82F6" />
          <View style={styles.infoTextContainer}>
            <Text style={styles.infoTitle}>AI 가상 피팅이란?</Text>
            <Text style={styles.infoDescription}>
              내 사진에 옷장의 옷을 가상으로 입혀보고, 어울리는지 미리 확인할 수 있는 기능입니다.
            </Text>
          </View>
        </View>

        {/* 모드 선택 */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>피팅 모드 선택</Text>
          <View style={styles.modeContainer}>
            <Pressable
              style={[
                styles.modeCard,
                selectedMode === 'body' && styles.modeCardActive,
              ]}
              onPress={() => setSelectedMode('body')}
            >
              <View style={styles.modeIcon}>
                <Camera size={32} color={selectedMode === 'body' ? '#3B82F6' : '#6B7280'} />
              </View>
              <Text style={[
                styles.modeTitle,
                selectedMode === 'body' && styles.modeTextActive,
              ]}>
                전신 사진
              </Text>
              <Text style={styles.modeDescription}>
                내 전신 사진에 옷장의 옷을 입혀봅니다
              </Text>
            </Pressable>

            <Pressable
              style={[
                styles.modeCard,
                selectedMode === 'clothes' && styles.modeCardActive,
              ]}
              onPress={() => setSelectedMode('clothes')}
            >
              <View style={styles.modeIcon}>
                <Sparkles size={32} color={selectedMode === 'clothes' ? '#3B82F6' : '#6B7280'} />
              </View>
              <Text style={[
                styles.modeTitle,
                selectedMode === 'clothes' && styles.modeTextActive,
              ]}>
                옷 미리보기
              </Text>
              <Text style={styles.modeDescription}>
                옷장의 옷을 3D로 미리 확인합니다
              </Text>
            </Pressable>
          </View>
        </View>

        {/* 사진 업로드 섹션 */}
        {selectedMode && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>
              {selectedMode === 'body' ? '전신 사진 업로드' : '옷 선택'}
            </Text>
            <View style={styles.uploadContainer}>
              <Pressable style={styles.uploadButton} onPress={handleCameraPress}>
                <Camera size={24} color="#3B82F6" />
                <Text style={styles.uploadButtonText}>카메라 촬영</Text>
              </Pressable>

              <Pressable style={styles.uploadButton} onPress={handleUploadPress}>
                <Upload size={24} color="#3B82F6" />
                <Text style={styles.uploadButtonText}>갤러리에서 선택</Text>
              </Pressable>
            </View>
          </View>
        )}

        {/* 미리보기 영역 */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>미리보기</Text>
          <View style={styles.previewContainer}>
            <View style={styles.previewPlaceholder}>
              <Sparkles size={48} color="#D1D5DB" />
              <Text style={styles.previewPlaceholderText}>
                {selectedMode
                  ? '사진을 업로드하면 여기에 미리보기가 표시됩니다'
                  : '먼저 피팅 모드를 선택해주세요'}
              </Text>
            </View>
          </View>
        </View>

        {/* 시작 버튼 */}
        <Pressable
          style={[styles.startButton, !selectedMode && styles.startButtonDisabled]}
          onPress={handleStartFitting}
        >
          <Sparkles size={20} color="#FFFFFF" />
          <Text style={styles.startButtonText}>AI 가상 피팅 시작</Text>
        </Pressable>

        {/* 하단 여백 */}
        <View style={{ height: 100 }} />
      </ScrollView>

      <BottomNavBar activeScreen="virtual-fitting" onNavigate={onNavigate} />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
  },
  infoCard: {
    flexDirection: 'row',
    backgroundColor: '#EFF6FF',
    borderRadius: 12,
    padding: 16,
    marginTop: 20,
    marginBottom: 24,
    gap: 12,
  },
  infoTextContainer: {
    flex: 1,
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1E3A8A',
    marginBottom: 4,
  },
  infoDescription: {
    fontSize: 14,
    color: '#3B82F6',
    lineHeight: 20,
  },
  section: {
    marginBottom: 32,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 16,
  },
  modeContainer: {
    flexDirection: 'row',
    gap: 12,
  },
  modeCard: {
    flex: 1,
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#E5E7EB',
    padding: 16,
    alignItems: 'center',
  },
  modeCardActive: {
    backgroundColor: '#EFF6FF',
    borderColor: '#3B82F6',
  },
  modeIcon: {
    width: 60,
    height: 60,
    backgroundColor: '#FFFFFF',
    borderRadius: 30,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  modeTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 4,
  },
  modeTextActive: {
    color: '#1E40AF',
  },
  modeDescription: {
    fontSize: 12,
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 16,
  },
  uploadContainer: {
    flexDirection: 'row',
    gap: 12,
  },
  uploadButton: {
    flex: 1,
    backgroundColor: '#EFF6FF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#3B82F6',
    borderStyle: 'dashed',
    padding: 20,
    alignItems: 'center',
    gap: 8,
  },
  uploadButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#3B82F6',
  },
  previewContainer: {
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    aspectRatio: 9 / 16,
    overflow: 'hidden',
  },
  previewPlaceholder: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 40,
  },
  previewPlaceholderText: {
    fontSize: 14,
    color: '#9CA3AF',
    textAlign: 'center',
    marginTop: 12,
    lineHeight: 20,
  },
  startButton: {
    flexDirection: 'row',
    backgroundColor: '#3B82F6',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginTop: 8,
  },
  startButtonDisabled: {
    backgroundColor: '#D1D5DB',
  },
  startButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
});

