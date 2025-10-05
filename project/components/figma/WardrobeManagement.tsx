// components/figma/WardrobeManagement.tsx

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Image,
  TextInput,
  Pressable,
  Alert,
  ActivityIndicator,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Camera, Grid3X3, List, Search, Filter, Heart, MoreVertical } from 'lucide-react-native';
import * as ImagePicker from 'expo-image-picker';
import AsyncStorage from '@react-native-async-storage/async-storage';
import AppHeader from '../common/AppHeader';
import BottomNavBar from '../common/BottomNavBar';
import { MainScreen } from '../../App';

type ViewMode = 'grid' | 'list';
type Item = { 
  id: number; 
  name: string; 
  brand: string; 
  image: string; 
  category: string; 
  loved: boolean;
};

// 🌐 API 주소 (ngrok 주소로 변경하세요)
const API_BASE_URL = 'https://loyd-extemporaneous-annalise.ngrok-free.dev';
// const API_BASE_URL = 'http://10.0.2.2:4000';
export default function WardrobeManagement({
  onBack,
  onNavigate,
}: {
  onBack: () => void;
  onNavigate: (step: MainScreen) => void;
}) {
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [uploading, setUploading] = useState(false);
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(true);
  const [userId, setUserId] = useState<number | null>(null); // 👈 실제 user_id

  // ✅ 상세 정보 모달 state 추가
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedItemDetail, setSelectedItemDetail] = useState<any>(null);

  const total = items.length;

  // 📥 옷장 데이터 가져오기 (useCallback을 사용하여 최적화)
  const fetchWardrobe = useCallback(async () => {
    if (!userId) {
      console.log('⚠️ userId가 없습니다!');
      return;
    }

    setLoading(true);
    try {
      const url = `${API_BASE_URL}/api/wardrobe/${userId}`;
      console.log('\n========================================');
      console.log('🔍 옷장 조회 시작');
      console.log('👤 user_id:', userId);
      console.log('🌐 요청 URL:', url);
      console.log('========================================\n');
      
      const response = await fetch(url);
      
      // 응답 본문 처리 로직
      const text = await response.text();
      console.log('📝 응답 본문 (text):', text.substring(0, 200));

      const data = JSON.parse(text);
      console.log('📦 서버 응답 (JSON):', data);

      if (data.success) {
        console.log('✅ 성공! 아이템 개수:', data.items.length);
        
        const wardrobeItems: Item[] = data.items.map((item: any, index: number) => {
          
          let name = '';
          let category = '';
          
          if (item.has_top && item.top_category) {
            name = `${item.top_color || ''} ${item.top_category}`.trim();
            category = '상의';
          } else if (item.has_bottom && item.bottom_category) {
            name = `${item.bottom_color || ''} ${item.bottom_category}`.trim();
            category = '하의';
          }
          
          // 파일명 추출 시 슬래시/역슬래시 모두 처리
          const filename = item.image_path.split(/\\|\//).pop();
          const imageUrl = `${API_BASE_URL}/api/images/${filename}`;
          
          return {
            id: item.id,
            name: name || '새 아이템',
            brand: 'My Wardrobe',
            image: imageUrl,
            category: category,
            loved: false,
          };
        });
        
        console.log('\n✅ 최종 변환 완료!');
        console.log('📦 wardrobeItems:', wardrobeItems);
        console.log('========================================\n');
        
        setItems(wardrobeItems);
      } else {
        console.error('❌ 서버 응답 실패:', data.message);
      }
    } catch (error) {
      console.error('\n❌❌❌ 옷장 조회 실패 ❌❌❌');
      console.error('에러:', error);
      console.error('========================================\n');
      
      Alert.alert(
        '옷장 조회 실패', 
        `서버: ${API_BASE_URL}\n\n에러: ${error}`
      );
    } finally {
      setLoading(false);
    }
  }, [userId]); // userId가 변경될 때만 fetchWardrobe 재생성

  // ✅ 1. 로그인한 사용자 정보 불러오기
  useEffect(() => {
    const loadUser = async () => {
      try {
        const userStr = await AsyncStorage.getItem('user');
        if (userStr) {
          const user = JSON.parse(userStr);
          setUserId(user.user_id);
        } else {
          Alert.alert('로그인 필요', '로그인이 필요합니다.');
        }
      } catch (error) {
        console.error('❌ 사용자 정보 로드 실패:', error);
      }
    };
    
    loadUser();
  }, []);

  // ✅ 2. userId가 있으면 옷장 데이터 가져오기
  useEffect(() => {
    if (userId) {
      fetchWardrobe();
    }
  }, [userId, fetchWardrobe]);
  
  // 🗑️ 옷장 아이템 삭제 로직 (추가)
  const deleteItem = async (itemId: number, itemName: string) => {
    Alert.alert(
      '아이템 삭제 확인',
      `정말로 "${itemName}"을(를) 옷장에서 삭제하시겠습니까?`,
      [
        { text: '취소', style: 'cancel' },
        { 
          text: '삭제', 
          style: 'destructive',
          onPress: async () => {
            setLoading(true); // 삭제 요청 동안 로딩 표시
            try {
              const url = `${API_BASE_URL}/api/wardrobe/${itemId}`;
              console.log(`\n🗑️ 삭제 요청: ${url}`);
              
              const response = await fetch(url, {
                method: 'DELETE',
              });

              if (response.ok) {
                Alert.alert('삭제 성공', `${itemName}이(가) 옷장에서 삭제되었습니다.`);
                fetchWardrobe(); // 목록 새로고침
              } else {
                const errorData = await response.json();
                Alert.alert('삭제 실패', errorData.detail || '삭제에 실패했습니다. 서버 로그를 확인하세요.');
              }
            } catch (error) {
              console.error('❌ 삭제 네트워크 오류:', error);
              Alert.alert('네트워크 오류', '삭제 중 서버와 연결할 수 없습니다.');
            } finally {
              setLoading(false);
            }
          }
        },
      ]
    );
  };

  // 아이템 상세 정보 표시 함수 (수정)
  const showItemDetail = async (itemId: number) => {
    setLoading(true);
    try {
      const url = `${API_BASE_URL}/api/wardrobe/item/${itemId}`;
      console.log(`\n🔍 상세 정보 요청: ${url}`);
      
      const response = await fetch(url);
      const data = await response.json();
      
      if (data.success && data.item) {
        setSelectedItemDetail(data.item);
        setShowDetailModal(true);
      } else {
        Alert.alert('오류', data.message || '상세 정보를 불러올 수 없습니다.');
      }
    } catch (error) {
      console.error('❌ 상세 정보 조회 실패:', error);
      Alert.alert('네트워크 오류', '서버와 연결할 수 없습니다.');
    } finally {
      setLoading(false);
    }
  };

  // 옷장 아이템 옵션 메뉴 표시 (수정)
  const showItemOptions = (item: Item) => {
    Alert.alert(
      item.name,
      '원하는 작업을 선택해주세요.',
      [
        { text: '정보 보기', onPress: () => showItemDetail(item.id) },  // 👈 수정!
        { text: '편집', onPress: () => Alert.alert('알림', '편집 기능은 곧 추가될 예정입니다.') },
        { text: '삭제', style: 'destructive', onPress: () => deleteItem(item.id, item.name) },
        { text: '취소', style: 'cancel' },
      ]
    );
  };
  
  // 📤 이미지 업로드
  const uploadImage = async (imageUri: string) => {
    if (userId === null || userId === undefined) {
      Alert.alert('오류', '사용자 정보를 불러올 수 없습니다. 다시 로그인해주세요.');
      return; // 👈 함수 실행 중단
    }

    setUploading(true);

    try {
      const formData = new FormData();
      
      if (Platform.OS === 'web') {
        const response = await fetch(imageUri);
        const blob = await response.blob();
        const file = new File([blob], 'photo.jpg', { type: 'image/jpeg' });
        formData.append('image', file);
        console.log('📤 웹에서 업로드 시작...');
      } else {
        const filename = imageUri.split(/\\|\//).pop() || 'photo.jpg';
        const match = /\.(\w+)$/.exec(filename);
        const type = match ? `image/${match[1]}` : 'image/jpeg';

        formData.append('image', {
          uri: imageUri,
          name: filename,
          type: type,
        } as any);
        
        console.log('📤 모바일에서 업로드 시작...');
      }
      
      formData.append('user_id', String(userId)); // 👈 실제 user_id 사용

      console.log(`🌐 업로드 요청 (user_id: ${userId})`);
      
      const uploadResponse = await fetch(`${API_BASE_URL}/api/upload-wardrobe`, {
        method: 'POST',
        body: formData,
        headers: {
          'Accept': 'application/json',
        },
      });

      const data = await uploadResponse.json();
      console.log('📦 업로드 응답:', data);

      if (data.success) {
        let message = `✅ AI 분석 완료!\n\n`;
        
        if (data.top_attributes) {
          message += `👕 상의\n`;
          message += `• ${data.top_attributes.category}\n`;
          message += `• ${data.top_attributes.color}\n`;
          message += `• ${data.top_attributes.fit}핏\n\n`;
        }
        
        if (data.bottom_attributes) {
          message += `👖 하의\n`;
          message += `• ${data.bottom_attributes.category}\n`;
          message += `• ${data.bottom_attributes.color}\n`;
          message += `• ${data.bottom_attributes.fit}핏\n`;
        }
        
        Alert.alert('업로드 성공!', message, [
          { 
            text: '확인', 
            onPress: () => {
              console.log('🔄 옷장 새로고침...');
              fetchWardrobe();
            }
          }
        ]);
      } else {
        Alert.alert('업로드 실패', data.message || '다시 시도해주세요.');
      }
    } catch (error) {
      console.error('❌ 업로드 에러:', error);
      Alert.alert('에러', `업로드 중 오류가 발생했습니다.\n\n${error}`);
    } finally {
      setUploading(false);
    }
  };

  // 카메라 권한 요청
  const requestPermissions = async () => {
    if (Platform.OS !== 'web') {
      const cameraPermission = await ImagePicker.requestCameraPermissionsAsync();
      const galleryPermission = await ImagePicker.requestMediaLibraryPermissionsAsync();
      
      if (cameraPermission.status !== 'granted' || galleryPermission.status !== 'granted') {
        Alert.alert('권한 필요', '카메라와 갤러리 접근 권한이 필요합니다.');
        return false;
      }
    }
    return true;
  };

  // 카메라로 촬영
  const takePhoto = async () => {
    const hasPermission = await requestPermissions();
    if (!hasPermission) return;

    const result = await ImagePicker.launchCameraAsync({
      allowsEditing: true,
      aspect: [3, 4],
      quality: 0.8,
    });

    if (!result.canceled) {
      uploadImage(result.assets[0].uri);
    }
  };

  // 갤러리에서 선택
  const pickImage = async () => {
    const hasPermission = await requestPermissions();
    if (!hasPermission) return;

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [3, 4],
      quality: 0.8,
    });

    if (!result.canceled) {
      uploadImage(result.assets[0].uri);
    }
  };

  // 옵션 선택
  const showImageOptions = () => {
    if (uploading) return;

    if (Platform.OS === 'web') {
      pickImage();
    } else {
      Alert.alert(
        '사진 선택',
        '어떻게 추가하시겠어요?',
        [
          { text: '📸 카메라로 촬영', onPress: takePhoto },
          { text: '🖼️ 갤러리에서 선택', onPress: pickImage },
          { text: '취소', style: 'cancel' },
        ]
      );
    }
  };

  // 헤더 우측 버튼
  const HeaderRightAction = (
    <View style={{ flexDirection: 'row', alignItems: 'center' }}>
      <Pressable onPress={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')} style={styles.iconBtn}>
        {viewMode === 'grid' ? <List size={20} color="#111" /> : <Grid3X3 size={20} color="#111" />}
      </Pressable>
      <Pressable 
        onPress={showImageOptions} 
        style={[styles.addBtn, uploading && styles.addBtnDisabled]}
        disabled={uploading}
      >
        {uploading ? (
          <>
            <ActivityIndicator size="small" color="#FFF" />
            <Text style={styles.addBtnText}>분석중...</Text>
          </>
        ) : (
          <>
            <Camera size={16} color="#FFF" />
            <Text style={styles.addBtnText}>추가</Text>
          </>
        )}
      </Pressable>
    </View>
  );

  // 로딩 화면
  if (loading && items.length === 0) {
    return (
      <SafeAreaView style={styles.safe}>
        <AppHeader title="내 옷장" subtitle="로딩 중..." onBack={onBack} />
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
          <ActivityIndicator size="large" color="#111" />
          <Text style={{ marginTop: 16, color: '#666' }}>옷장을 불러오는 중...</Text>
        </View>
        <BottomNavBar activeScreen="wardrobe-management" onNavigate={onNavigate} />
      </SafeAreaView>
    );
  }

  // ✅ 상세 정보 모달 렌더링 함수
  const renderDetailModal = () => {
    if (!showDetailModal || !selectedItemDetail) return null;

    const item = selectedItemDetail;
    
    return (
      <View style={styles.modalOverlay}>
        <Pressable 
          style={styles.modalBackdrop} 
          onPress={() => setShowDetailModal(false)}
        />
        <View style={styles.modalContent}>
          <ScrollView showsVerticalScrollIndicator={false}>
            {/* 모달 헤더 */}
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>AI 분석 결과</Text>
              <Pressable onPress={() => setShowDetailModal(false)}>
                <Text style={styles.modalClose}>✕</Text>
              </Pressable>
            </View>

            {/* 원본 이미지 */}
            <View style={styles.modalSection}>
              <Text style={styles.modalSectionTitle}>📸 원본 이미지</Text>
              <Image 
                source={{ uri: `${API_BASE_URL}/api/images/${item.original_image_path.split(/\\|\//).pop()}` }} 
                style={styles.modalOriginalImage}
                resizeMode="contain"
              />
            </View>

            {/* 상의 정보 */}
            {item.has_top && item.top_attributes && (
              <View style={styles.modalSection}>
                <Text style={styles.modalSectionTitle}>👕 상의</Text>
                
                {/* 상의 이미지 */}
                {item.top_image_path && (
                  <Image 
                    source={{ uri: `${API_BASE_URL}/api/processed-images/item_${item.item_id}_top.jpg` }} 
                    style={styles.modalSeparatedImage}
                    resizeMode="contain"
                  />
                )}
                
                <View style={styles.modalInfoBox}>
                  <View style={styles.modalInfoRow}>
                    <Text style={styles.modalLabel}>카테고리</Text>
                    <Text style={styles.modalValue}>
                      {item.top_attributes.category} ({(item.top_attributes.category_confidence * 100).toFixed(0)}%)
                    </Text>
                  </View>
                  <View style={styles.modalInfoRow}>
                    <Text style={styles.modalLabel}>색상</Text>
                    <Text style={styles.modalValue}>
                      {item.top_attributes.color} ({(item.top_attributes.color_confidence * 100).toFixed(0)}%)
                    </Text>
                  </View>
                  <View style={styles.modalInfoRow}>
                    <Text style={styles.modalLabel}>핏</Text>
                    <Text style={styles.modalValue}>
                      {item.top_attributes.fit} ({(item.top_attributes.fit_confidence * 100).toFixed(0)}%)
                    </Text>
                  </View>
                  <View style={styles.modalInfoRow}>
                    <Text style={styles.modalLabel}>소재</Text>
                    <Text style={styles.modalValue}>
                      {Array.isArray(item.top_attributes.materials) 
                        ? item.top_attributes.materials.join(', ') 
                        : item.top_attributes.materials}
                    </Text>
                  </View>
                </View>
              </View>
            )}

            {/* 하의 정보 */}
            {item.has_bottom && item.bottom_attributes && (
              <View style={styles.modalSection}>
                <Text style={styles.modalSectionTitle}>👖 하의</Text>
                
                {/* 하의 이미지 */}
                {item.bottom_image_path && (
                  <Image 
                    source={{ uri: `${API_BASE_URL}/api/processed-images/item_${item.item_id}_bottom.jpg` }} 
                    style={styles.modalSeparatedImage}
                    resizeMode="contain"
                  />
                )}
                
                <View style={styles.modalInfoBox}>
                  <View style={styles.modalInfoRow}>
                    <Text style={styles.modalLabel}>카테고리</Text>
                    <Text style={styles.modalValue}>
                      {item.bottom_attributes.category} ({(item.bottom_attributes.category_confidence * 100).toFixed(0)}%)
                    </Text>
                  </View>
                  <View style={styles.modalInfoRow}>
                    <Text style={styles.modalLabel}>색상</Text>
                    <Text style={styles.modalValue}>
                      {item.bottom_attributes.color} ({(item.bottom_attributes.color_confidence * 100).toFixed(0)}%)
                    </Text>
                  </View>
                  <View style={styles.modalInfoRow}>
                    <Text style={styles.modalLabel}>핏</Text>
                    <Text style={styles.modalValue}>
                      {item.bottom_attributes.fit} ({(item.bottom_attributes.fit_confidence * 100).toFixed(0)}%)
                    </Text>
                  </View>
                  <View style={styles.modalInfoRow}>
                    <Text style={styles.modalLabel}>소재</Text>
                    <Text style={styles.modalValue}>
                      {Array.isArray(item.bottom_attributes.materials) 
                        ? item.bottom_attributes.materials.join(', ') 
                        : item.bottom_attributes.materials}
                    </Text>
                  </View>
                </View>
              </View>
            )}

            {/* 닫기 버튼 */}
            <Pressable 
              style={styles.modalCloseButton} 
              onPress={() => setShowDetailModal(false)}
            >
              <Text style={styles.modalCloseButtonText}>닫기</Text>
            </Pressable>
          </ScrollView>
        </View>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.safe}>
      <AppHeader title="내 옷장" subtitle={`${total}개 아이템`} onBack={onBack} rightAction={HeaderRightAction} />

      <ScrollView contentContainerStyle={styles.screenPad}>
        <View style={{ position: 'relative', marginBottom: 16 }}>
          <View style={{position: 'absolute', left: 12, top: 14, zIndex: 1}}>
            <Search size={16} color="#9CA3AF" />
          </View>
          <TextInput placeholder="아이템 검색..." style={styles.searchInput} />
          <Pressable style={styles.filterBtn}><Filter size={16} color="#111" /></Pressable>
        </View>

        {items.length === 0 ? (
          <View style={{ paddingVertical: 60, alignItems: 'center' }}>
            <Text style={{ fontSize: 16, color: '#9CA3AF', marginBottom: 8 }}>아직 옷이 없어요</Text>
            <Text style={{ fontSize: 14, color: '#D1D5DB' }}>우측 상단 "추가" 버튼을 눌러 옷을 등록해보세요!</Text>
          </View>
        ) : viewMode === 'grid' ? (
          <View style={styles.gridWrap}>
            {items.map((item) => (
              <Pressable key={item.id} style={styles.card}>
                <Image 
                  source={{ uri: item.image }} 
                  style={styles.cardImg}
                  onError={(e) => console.error('❌ 이미지 로드 실패:', item.image, e.nativeEvent.error)}
                  onLoad={() => console.log('✅ 이미지 로드 성공:', item.image)}
                />
                <View style={styles.cardTopRight}>
                  {item.loved && <View style={styles.roundBtnWhite}><Heart size={14} color="#EF4444" fill="#EF4444" /></View>}
                  {/* ... 버튼에 showItemOptions 연결 */}
                  <Pressable style={styles.roundBtnWhite} onPress={() => showItemOptions(item)}>
                    <MoreVertical size={14} color="#111" />
                  </Pressable>
                </View>
                <View style={styles.cardBottomOverlay}>
                  <Text style={styles.cardName}>{item.name}</Text>
                  <Text style={styles.cardBrand}>{item.category}</Text>
                </View>
              </Pressable>
            ))}
          </View>
        ) : (
          <View style={{ gap: 8 }}>
            <Text style={{textAlign: 'center', paddingVertical: 40, color: '#6B7280'}}>리스트 뷰가 여기에 표시됩니다.</Text>
          </View>
        )}
      </ScrollView>
      
      <BottomNavBar activeScreen="wardrobe-management" onNavigate={onNavigate} />
      
      {/* ✅ 상세 정보 모달 추가 */}
      {renderDetailModal()}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#FFFFFF' },
  iconBtn: { padding: 8 },
  addBtn: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    gap: 6, 
    backgroundColor: '#111', 
    paddingHorizontal: 12, 
    paddingVertical: 8, 
    borderRadius: 8 
  },
  addBtnDisabled: {
    opacity: 0.6,
  },
  addBtnText: { color: '#FFF', fontSize: 13, fontWeight: '600' },
  screenPad: { padding: 16, paddingBottom: 24 },
  searchInput: { 
    backgroundColor: '#F9FAFB', 
    borderWidth: 1, 
    borderColor: '#E5E7EB', 
    borderRadius: 8, 
    paddingLeft: 40, 
    paddingRight: 50, 
    paddingVertical: 10, 
    fontSize: 14 
  },
  filterBtn: { 
    position: 'absolute', 
    right: 6, 
    top: 6, 
    padding: 8, 
    backgroundColor: '#FFF', 
    borderWidth: 1, 
    borderColor: '#E5E7EB', 
    borderRadius: 6 
  },
  gridWrap: { 
    flexDirection: 'row', 
    flexWrap: 'wrap', 
    justifyContent: 'space-between', 
    rowGap: 12 
  },
  card: { 
    width: '48.5%', 
    aspectRatio: 3 / 4, 
    borderRadius: 8, 
    overflow: 'hidden', 
    backgroundColor: '#EEE', 
    elevation: 2, 
    shadowColor: '#000', 
    shadowOpacity: 0.1, 
    shadowRadius: 5
  },
  cardImg: { width: '100%', height: '100%' },
  cardTopRight: { 
    position: 'absolute', 
    top: 8, 
    right: 8, 
    flexDirection: 'row', 
    gap: 6 
  },
  roundBtnWhite: { 
    width: 28, 
    height: 28, 
    borderRadius: 14, 
    backgroundColor: 'rgba(255,255,255,0.9)', 
    justifyContent: 'center', 
    alignItems: 'center' 
  },
  cardBottomOverlay: { 
    position: 'absolute', 
    bottom: 0, 
    left: 0, 
    right: 0, 
    padding: 8, 
    backgroundColor: 'rgba(0,0,0,0.45)' 
  },
  cardName: { color: '#FFF', fontWeight: '600' },
  cardBrand: { color: '#FFF', fontSize: 11, opacity: 0.9 },
  modalOverlay: {
    ...StyleSheet.absoluteFillObject,
    zIndex: 1000,
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalBackdrop: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
  modalContent: {
    width: '90%',
    maxHeight: '80%',
    backgroundColor: '#FFF',
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOpacity: 0.3,
    shadowRadius: 20,
    elevation: 10,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111',
  },
  modalClose: {
    fontSize: 24,
    color: '#6B7280',
    fontWeight: '300',
  },
  modalSection: {
    marginBottom: 20,
  },
  modalSectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111',
    marginBottom: 12,
  },
  modalOriginalImage: {
    width: '100%',
    height: 200,
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
  },
  modalSeparatedImage: {
    width: '100%',
    height: 150,
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
    marginBottom: 12,
  },
  modalInfoBox: {
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
    padding: 12,
    gap: 8,
  },
  modalInfoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  modalLabel: {
    fontSize: 13,
    color: '#6B7280',
    fontWeight: '500',
  },
  modalValue: {
    fontSize: 13,
    color: '#111',
    fontWeight: '600',
  },
  modalCloseButton: {
    backgroundColor: '#111',
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 8,
  },
  modalCloseButtonText: {
    color: '#FFF',
    fontSize: 14,
    fontWeight: '600',
  },
});
