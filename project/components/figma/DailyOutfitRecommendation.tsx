// project/components/figma/DailyOutfitRecommendation.tsx
import React, { useMemo, useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Image,
  Pressable,
  ActivityIndicator,
  Alert,
  TextInput,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  Cloud,
  Thermometer,
  Calendar,
  MapPin,
  RefreshCw,
  Zap,
  MessageCircle,
  Send,
  X,
} from 'lucide-react-native';
import AppHeader from '../common/AppHeader';
import BottomNavBar from '../common/BottomNavBar';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL = 'https://loyd-extemporaneous-annalise.ngrok-free.dev';
const APP_HEADER_HEIGHT = 56;
const BOTTOM_NAV_HEIGHT = 80;

type NavigationStep =
  | 'home'
  | 'today-curation'
  | 'daily-outfit'
  | 'wardrobe-management'
  | 'style-analysis'
  | 'shopping'
  | 'virtual-fitting'
  | 'recent-styling'
  | 'blocked-outfits';

type Rec = {
  id: number;
  image: string;
  title: string;
  items: string[];
  score: number;
  reason: string;
  is_default?: boolean;
  detailed_scores?: {
    color_harmony: number;
    material_combination: number;
    fit_combination: number;
    style_combination: number;
    seasonal_suitability: number;
    category_compatibility: number;
  };
  explanation?: string;
};

type ChatMessage = {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
};

type WardrobeItem = { 
  id: number; 
  name: string; 
  brand: string; 
  image: string; 
  category: string; 
  loved: boolean;
  top_category?: string;
  bottom_category?: string;
  outer_category?: string;
  dress_category?: string;
  full_image?: string;
  top_image?: string;
  bottom_image?: string;
  outer_image?: string;
  dress_image?: string;
  has_top?: boolean;
  has_bottom?: boolean;
  has_outer?: boolean;
  has_dress?: boolean;
  is_default?: boolean;
};

export default function DailyOutfitRecommendation({
  onBack,
  onNavigate,
}: {
  onBack: () => void;
  onNavigate: (step: NavigationStep) => void;
}) {
  const [loading, setLoading] = useState(true);
  const [recommending, setRecommending] = useState(false);
  const [userId, setUserId] = useState<number | null>(null);
  const [wardrobeItems, setWardrobeItems] = useState<WardrobeItem[]>([]);
  const [recommendations, setRecommendations] = useState<Rec[]>([]);
  const [baseItemId, setBaseItemId] = useState<number | null>(null); 
  const [selectedPart, setSelectedPart] = useState<'top' | 'bottom' | 'outer' | 'dress'>('top');
  const [defaultRecommendations, setDefaultRecommendations] = useState<WardrobeItem[]>([]);
  const [showChat, setShowChat] = useState(false);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [chatRecommendations, setChatRecommendations] = useState<WardrobeItem[]>([]);
  const [weather, setWeather] = useState({
    temperature: 22,
    description: '맑음',
    icon: '☁️',
    styleTip: '가벼운 레이어드 스타일링 추천',
    date: todayStr
  });

  const baseItem = useMemo(() => {
      if (baseItemId === null && wardrobeItems.length > 0) {
          // 사용자 아이템 중 첫 번째 아이템을 자동 선택
          const userItems = wardrobeItems.filter(item => !item.is_default);
          if (userItems.length > 0) {
              setBaseItemId(userItems[0].id);
              return userItems[0];
          }
      }
      return wardrobeItems.find(item => item.id === baseItemId) || null;
  }, [wardrobeItems, baseItemId]);

  const avgScore =
    recommendations.length > 0
      ? Math.round(
          (recommendations.reduce((acc, r) => acc + r.score, 0) / recommendations.length) * 1
        )
      : 0;

  const todayStr = useMemo(() => {
    const d = new Date();
    return d.toLocaleDateString('ko-KR', { month: 'long', day: 'numeric' });
  }, []);

  // 날씨 데이터 불러오기
  const fetchWeather = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/weather?city=Seoul`);
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setWeather({
            temperature: data.temperature,
            description: data.description,
            icon: data.icon,
            styleTip: data.style_tip,
            date: data.date
          });
        }
      }
    } catch (error) {
      console.error('❌ 날씨 데이터 로드 실패:', error);
    }
  }, []);

  // 옷장 데이터 불러오기
  const fetchWardrobe = useCallback(async () => {
    if (!userId) {
      console.log('❌ userId 없음, 옷장 데이터 로드 건너뜀');
      return;
    }
    
    console.log('🔄 옷장 데이터 로드 시작, userId:', userId);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/wardrobe/${userId}?include_defaults=false`);
      console.log('📡 옷장 API 응답 상태:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('✅ 옷장 데이터 로드 성공:', data.items?.length || 0, '개');
        console.log('📦 원본 데이터:', data);
        
        if (data.items && data.items.length > 0) {
          // 중복 제거 및 이미지 URL 생성
          const uniqueItems = data.items.filter((item: WardrobeItem, index: number, self: WardrobeItem[]) => 
            index === self.findIndex((t: WardrobeItem) => t.id === item.id)
          ).map((item: any) => {
            // 이미지 URL 생성 (image_category가 'original'인 경우 'full'로 변경)
            const imageCategory = item.image_category === 'original' ? 'full' : (item.image_category || 'full');
            let imageUrl = '';
            
            // full_image가 있으면 우선 사용, 없으면 image_path 사용
            if (item.full_image) {
              imageUrl = `${API_BASE_URL}${item.full_image}`;
            } else if (item.image_path) {
              // 기본 아이템인 경우 default-images API 사용
              if (item.is_default) {
                imageUrl = `${API_BASE_URL}/api/default-images/${item.image_path}`;
              } else {
                // 사용자 아이템인 경우 사용자별 processed-images API 사용
                // image_path가 item_xxx_full.jpg 형태인지 확인
                if (item.image_path.startsWith('item_') && item.image_path.includes('_full.jpg')) {
                  imageUrl = `${API_BASE_URL}/api/processed-images/user_${userId}/${imageCategory}/${item.image_path}`;
                } else {
                  // 원본 파일명인 경우 item_xxx_full.jpg 형태로 변환
                  imageUrl = `${API_BASE_URL}/api/processed-images/user_${userId}/${imageCategory}/item_${item.id}_full.jpg`;
                }
              }
            } else {
              // 폴백: images 디렉토리에서 시도
              imageUrl = `${API_BASE_URL}/api/images/item_${item.id}.jpg`;
            }
            
            // 카테고리별 이미지 URL 생성 (기본 아이템인 경우 default-images API 사용)
            const topImageUrl = item.top_image 
              ? (item.is_default 
                  ? `${API_BASE_URL}/api/default-images/${item.top_image.split('/').pop()}`
                  : item.top_image.startsWith('/api/') 
                    ? `${API_BASE_URL}${item.top_image}`
                    : `${API_BASE_URL}/api/processed-images/user_${userId}/top/item_${item.id}_top.jpg`)
              : null;
            const bottomImageUrl = item.bottom_image 
              ? (item.is_default 
                  ? `${API_BASE_URL}/api/default-images/${item.bottom_image.split('/').pop()}`
                  : item.bottom_image.startsWith('/api/') 
                    ? `${API_BASE_URL}${item.bottom_image}`
                    : `${API_BASE_URL}/api/processed-images/user_${userId}/bottom/item_${item.id}_bottom.jpg`)
              : null;
            const outerImageUrl = item.outer_image 
              ? (item.is_default 
                  ? `${API_BASE_URL}/api/default-images/${item.outer_image.split('/').pop()}`
                  : item.outer_image.startsWith('/api/') 
                    ? `${API_BASE_URL}${item.outer_image}`
                    : `${API_BASE_URL}/api/processed-images/user_${userId}/outer/item_${item.id}_outer.jpg`)
              : null;
            const dressImageUrl = item.dress_image 
              ? (item.is_default 
                  ? `${API_BASE_URL}/api/default-images/${item.dress_image.split('/').pop()}`
                  : item.dress_image.startsWith('/api/') 
                    ? `${API_BASE_URL}${item.dress_image}`
                    : `${API_BASE_URL}/api/processed-images/user_${userId}/dress/item_${item.id}_dress.jpg`)
              : null;
            
            // 이름 생성 (카테고리 기반)
            let name = '';
            if (item.has_dress) name = '드레스';
            else if (item.has_outer) name = '아우터';
            else if (item.has_top && item.has_bottom) name = '상의 / 하의';
            else if (item.has_top) name = '상의';
            else if (item.has_bottom) name = '하의';
            else name = `아이템 ${item.id}`;
            
            return {
              ...item,
              image: imageUrl,
              top_image: topImageUrl,
              bottom_image: bottomImageUrl,
              outer_image: outerImageUrl,
              dress_image: dressImageUrl,
              name: name,
              brand: 'My Wardrobe',
              category: item.has_top ? 'top' : item.has_bottom ? 'bottom' : item.has_outer ? 'outer' : item.has_dress ? 'dress' : 'other',
              loved: false,
            };
          });
          
          console.log('🔄 중복 제거 후 아이템 수:', uniqueItems.length);
          console.log('🖼️ 첫 번째 아이템 이미지 URL:', uniqueItems[0]?.image);
          setWardrobeItems(uniqueItems);
        } else {
          console.log('⚠️ 옷장에 아이템이 없음');
          setWardrobeItems([]);
        }
      } else {
        console.error('❌ 옷장 데이터 로드 실패:', response.status);
        setWardrobeItems([]);
      }
    } catch (error) {
      console.error('❌ 옷장 데이터 로드 실패:', error);
      setWardrobeItems([]);
    }
  }, [userId]);

  // 기본 추천 아이템 불러오기
  const fetchDefaultRecommendations = useCallback(async () => {
    if (!userId) return;
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/recommendations/default/${userId}`);
      if (response.ok) {
        const data = await response.json();
        console.log('✅ 기본 추천 아이템 로드 성공:', data.length, '개');
        setDefaultRecommendations(data);
      } else {
        console.error('❌ 기본 추천 아이템 로드 실패:', response.status);
      }
    } catch (error) {
      console.error('❌ 기본 추천 아이템 로드 실패:', error);
    }
  }, [userId]);

  // 사용자 ID 불러오기
  useEffect(() => {
    const loadUserId = async () => {
      try {
        const userData = await AsyncStorage.getItem('@kko/user');
        if (userData) {
          const user = JSON.parse(userData);
          console.log('🔍 사용자 데이터 로드:', user);
          
          // user_id가 숫자인지 확인하고 설정
          if (user.user_id && typeof user.user_id === 'number') {
            setUserId(user.user_id);
          } else if (user.id && typeof user.id === 'number') {
            setUserId(user.id);
          } else if (user.id === 'local-user') {
            // local-user인 경우 기본값으로 1 사용 (개발용)
            console.log('⚠️ local-user 감지, 기본값 1 사용');
            setUserId(1);
          } else {
            console.log('❌ 유효한 user_id 없음:', user);
            setLoading(false);
          }
        } else {
          console.log('❌ 사용자 데이터 없음');
          setLoading(false);
        }
      } catch (error) {
        console.error('사용자 ID 로드 실패:', error);
        setLoading(false);
      }
    };
    loadUserId();
  }, []);

  useEffect(() => {
    if (userId) {
      const loadData = async () => {
        try {
          console.log('🔄 데이터 로드 시작, userId:', userId);
          // 10초 타임아웃 설정
          const timeoutPromise = new Promise((_, reject) => 
            setTimeout(() => reject(new Error('로딩 타임아웃')), 10000)
          );
          
          await Promise.race([
            Promise.all([
              fetchWardrobe(),
              fetchDefaultRecommendations(),
              fetchWeather()
            ]),
            timeoutPromise
          ]);
          console.log('✅ 데이터 로드 완료');
        } catch (error) {
          console.error('데이터 로드 실패:', error);
        } finally {
          console.log('🔄 로딩 상태 해제');
          setLoading(false);
        }
      };
      loadData();
    } else {
      // userId가 null이거나 undefined인 경우
      console.log('❌ userId 없음, 로딩 해제');
      setLoading(false);
    }
  }, [userId, fetchWardrobe, fetchDefaultRecommendations, fetchWeather]);

  // baseItem이 변경될 때 selectedPart 자동 설정
  useEffect(() => {
    if (baseItem) {
      if (baseItem.has_dress) {
        setSelectedPart('dress');
      } else if (baseItem.has_outer) {
        setSelectedPart('outer');
      } else if (baseItem.has_top) {
        setSelectedPart('top');
      } else if (baseItem.has_bottom) {
        setSelectedPart('bottom');
      }
    }
  }, [baseItem]);

  // 고급 추천 시스템 사용
  const fetchRecommendation = async () => {
    if (!baseItem || baseItem.is_default || !userId || recommending) return;

    setRecommending(true);
    setRecommendations([]);

    try {
      const response = await fetch(`${API_BASE_URL}/api/recommendations/advanced/${baseItem.id}?user_id=${userId}&n_results=10`);
      
      if (response.ok) {
        const responseData = await response.json();
        console.log('✅ 고급 추천 데이터 로드 성공:', responseData);
        
        // 백엔드에서 {success: true, recommendations: [...]} 형태로 반환
        const data = responseData.recommendations || [];
        console.log('📦 추천 배열:', data, '길이:', data.length);
        
        if (!data || !Array.isArray(data)) {
          console.log('⚠️ 추천 데이터가 배열이 아님, 빈 배열로 처리');
          setRecommendations([]);
          Alert.alert('추천 완료', '추천할 아이템을 찾을 수 없습니다.');
          return;
        }
        
        const recs = data.map((rec: any) => {
          // 이미지 URL 생성 (기본 아이템과 사용자 아이템 구분)
          let imageUrl = '';
          if (rec.is_default) {
            imageUrl = `${API_BASE_URL}/api/default-images/${rec.image_path}`;
          } else {
            // image_path가 item_xxx_full.jpg 형태인지 확인
            if (rec.image_path && rec.image_path.startsWith('item_') && rec.image_path.includes('_full.jpg')) {
              imageUrl = `${API_BASE_URL}/api/processed-images/user_${userId}/full/${rec.image_path}`;
            } else {
              // 원본 파일명인 경우 item_xxx_full.jpg 형태로 변환
              imageUrl = `${API_BASE_URL}/api/processed-images/user_${userId}/full/item_${rec.id}_full.jpg`;
            }
          }
          
          console.log(`🖼️ 추천 아이템 ${rec.id} 이미지 URL:`, imageUrl, 'is_default:', rec.is_default);
          
          return {
            id: rec.id,
            image: imageUrl,
            title: rec.name || `아이템 ${rec.id}`,
            items: [],
            score: Math.round(rec.score * 100),
            reason: rec.explanation || 'AI 추천',
            is_default: rec.is_default || false,
            detailed_scores: rec.detailed_scores,
            explanation: rec.explanation,
          };
        });
        
        setRecommendations(recs);
        
        // 상세한 추천 결과 메시지 생성
        let detailMessage = '';
        const selectedCategory = selectedPart;
        
        // 카테고리별 개수 계산
        const categoryCounts = {
          top: recs.filter(r => r.title.includes('상의') || r.title.includes('티셔츠') || r.title.includes('셔츠')).length,
          bottom: recs.filter(r => r.title.includes('하의') || r.title.includes('바지') || r.title.includes('스커트')).length,
          outer: recs.filter(r => r.title.includes('아우터') || r.title.includes('재킷') || r.title.includes('코트')).length,
          dress: recs.filter(r => r.title.includes('드레스') || r.title.includes('원피스')).length,
        };
        
        if (selectedCategory === 'top') {
          const parts = [];
          if (categoryCounts.bottom > 0) parts.push(`하의 ${categoryCounts.bottom}개`);
          if (categoryCounts.outer > 0) parts.push(`아우터 ${categoryCounts.outer}개`);
          if (categoryCounts.bottom > 0 && categoryCounts.outer > 0) parts.push(`하의+아우터 조합 ${Math.min(categoryCounts.bottom, categoryCounts.outer)}개`);
          
          if (parts.length > 0) {
            detailMessage = `상의와 어울리는 ${parts.join(', ')} 발견`;
          } else {
            detailMessage = `상의와 어울리는 아이템을 찾을 수 없습니다`;
          }
        } else if (selectedCategory === 'bottom') {
          const parts = [];
          if (categoryCounts.top > 0) parts.push(`상의 ${categoryCounts.top}개`);
          if (categoryCounts.outer > 0) parts.push(`아우터 ${categoryCounts.outer}개`);
          if (categoryCounts.top > 0 && categoryCounts.outer > 0) parts.push(`상의+아우터 조합 ${Math.min(categoryCounts.top, categoryCounts.outer)}개`);
          
          if (parts.length > 0) {
            detailMessage = `하의와 어울리는 ${parts.join(', ')} 발견`;
          } else {
            detailMessage = `하의와 어울리는 아이템을 찾을 수 없습니다`;
          }
        } else if (selectedCategory === 'outer') {
          const parts = [];
          if (categoryCounts.top > 0) parts.push(`상의 ${categoryCounts.top}개`);
          if (categoryCounts.bottom > 0) parts.push(`하의 ${categoryCounts.bottom}개`);
          if (categoryCounts.top > 0 && categoryCounts.bottom > 0) parts.push(`상의+하의 조합 ${Math.min(categoryCounts.top, categoryCounts.bottom)}개`);
          
          if (parts.length > 0) {
            detailMessage = `아우터와 어울리는 ${parts.join(', ')} 발견`;
          } else {
            detailMessage = `아우터와 어울리는 아이템을 찾을 수 없습니다`;
          }
        } else if (selectedCategory === 'dress') {
          const parts = [];
          if (categoryCounts.bottom > 0) parts.push(`하의 ${categoryCounts.bottom}개`);
          if (categoryCounts.outer > 0) parts.push(`아우터 ${categoryCounts.outer}개`);
          
          if (parts.length > 0) {
            detailMessage = `드레스와 어울리는 ${parts.join(', ')} 발견`;
          } else {
            detailMessage = `드레스와 어울리는 아이템을 찾을 수 없습니다`;
          }
        }
        
        Alert.alert('추천 완료', detailMessage);
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      console.error('❌ 추천 요청 실패:', error);
      Alert.alert('네트워크 오류', '추천 서버와 연결할 수 없습니다.');
    } finally {
      setRecommending(false);
    }
  };

  // LLM 채팅 메시지 전송
  const sendChatMessage = async () => {
    if (!chatInput.trim() || !userId) return;
    
    const userMessage = chatInput.trim();
    setChatInput('');
    
    // 사용자 메시지 추가
    const newUserMsg: ChatMessage = {
      role: 'user',
      content: userMessage,
      timestamp: new Date()
    };
    setChatMessages(prev => [...prev, newUserMsg]);
    
    setChatLoading(true);
    
    try {
      const formData = new FormData();
      formData.append('user_id', String(userId));
      formData.append('message', userMessage);
      
      const response = await fetch(`${API_BASE_URL}/api/chat/recommend`, {
        method: 'POST',
        body: formData,
      });
      
      const data = await response.json();
      
      if (data.success) {
        // AI 응답 추가
        const aiMsg: ChatMessage = {
          role: 'assistant',
          content: data.response,
          timestamp: new Date()
        };
        setChatMessages(prev => [...prev, aiMsg]);
        
        // 추천 아이템이 있으면 표시
        if (data.recommendations && data.recommendations.length > 0) {
          const items: WardrobeItem[] = data.recommendations.map((rec: any) => ({
            id: rec.id,
            name: rec.has_top 
              ? `${rec.top_color || ''} ${rec.top_category || ''}`.trim()
              : rec.has_bottom 
              ? `${rec.bottom_color || ''} ${rec.bottom_category || ''}`.trim()
              : rec.has_outer
              ? `${rec.outer_color || ''} ${rec.outer_category || ''}`.trim()
              : rec.has_dress
              ? `${rec.dress_color || ''} ${rec.dress_category || ''}`.trim()
              : `아이템 ${rec.id}`,
            brand: rec.brand || '브랜드 미상',
            category: rec.has_top ? '상의' : rec.has_bottom ? '하의' : rec.has_outer ? '아우터' : rec.has_dress ? '드레스' : '기타',
            color: rec.top_color || rec.bottom_color || rec.outer_color || rec.dress_color || '미상',
            fit: rec.top_fit || rec.bottom_fit || rec.outer_fit || rec.dress_fit || '미상',
            materials: rec.top_materials || rec.bottom_materials || rec.outer_materials || rec.dress_materials || [],
            image: rec.image_path ? 
              (rec.image_path.startsWith('item_') && rec.image_path.includes('_full.jpg') 
                ? `${API_BASE_URL}/api/processed-images/user_${userId}/full/${rec.image_path}`
                : `${API_BASE_URL}/api/processed-images/user_${userId}/full/item_${rec.id}_full.jpg`) 
              : `${API_BASE_URL}/api/images/item_${rec.id}.jpg`,
            top_category: rec.top_category,
            bottom_category: rec.bottom_category,
            outer_category: rec.outer_category,
            dress_category: rec.dress_category,
            top_image: rec.top_image_path,
            bottom_image: rec.bottom_image_path,
            outer_image: rec.outer_image_path,
            dress_image: rec.dress_image_path,
            has_top: rec.has_top,
            has_bottom: rec.has_bottom,
            has_outer: rec.has_outer,
            has_dress: rec.has_dress,
            loved: false,
          }));
          setChatRecommendations(items);
        }
      } else {
        throw new Error(data.error || '알 수 없는 오류');
      }
    } catch (error) {
      console.error('❌ LLM 채팅 실패:', error);
      Alert.alert('오류', 'AI와의 대화 중 오류가 발생했습니다.');
    } finally {
      setChatLoading(false);
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.safe}>
        <AppHeader title="AI 코디 분석" onBack={onBack} />
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#111" />
          <Text style={styles.loadingText}>데이터를 불러오는 중...</Text>
        </View>
        <BottomNavBar activeScreen="style-analysis" onNavigate={onNavigate} />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safe}>
      <AppHeader 
        title="AI 코디 분석" 
        onBack={onBack}
        rightComponent={
          <Pressable 
            onPress={() => setShowChat(!showChat)} 
            style={[styles.chatToggleBtn, showChat && styles.chatToggleBtnActive]}
          >
            {showChat ? <X size={16} color="#FFF" /> : <MessageCircle size={16} color="#FFF" />}
          </Pressable>
        }
      />
      
      <ScrollView 
        style={styles.container}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* 날씨 정보 */}
        <View style={styles.weatherCard}>
          <View style={styles.weatherHeader}>
            <View style={styles.weatherInfo}>
              <Text style={styles.weatherDate}>{weather.date}</Text>
              <Text style={styles.weatherTemp}>{weather.temperature}°C</Text>
            </View>
            <View style={styles.weatherIcon}>
              <Text style={{ fontSize: 24 }}>{weather.icon}</Text>
            </View>
          </View>
          <Text style={styles.weatherDesc}>{weather.styleTip}</Text>
        </View>

        {/* 추천 기준 아이템 선택 */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>추천 기준 아이템 선택</Text>
          {(() => {
            const userItems = wardrobeItems.filter(item => !item.is_default);
            console.log('🔍 디버깅 - 전체 아이템 수:', wardrobeItems.length);
            console.log('🔍 디버깅 - 사용자 아이템 수:', userItems.length);
            console.log('🔍 디버깅 - 전체 아이템:', wardrobeItems.map(item => ({ id: item.id, is_default: item.is_default })));
            return userItems.length === 0;
          })() ? (
            <View style={styles.emptyState}>
              <Text style={styles.emptyText}>옷장에 아이템이 없습니다.</Text>
              <Text style={styles.emptySubtext}>옷장 탭에서 아이템을 추가해보세요.</Text>
            </View>
          ) : (
            <ScrollView 
              horizontal 
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.itemScrollContent}
              style={styles.itemScroll}
            >
              {wardrobeItems.filter(item => !item.is_default).map((item) => (
              <Pressable
                key={item.id}
                onPress={() => {
                  setBaseItemId(item.id);
                  // 아이템의 실제 카테고리에 따라 selectedPart 자동 설정
                  if (item.has_dress) setSelectedPart('dress');
                  else if (item.has_outer) setSelectedPart('outer');
                  else if (item.has_top) setSelectedPart('top');
                  else if (item.has_bottom) setSelectedPart('bottom');
                }}
                style={[
                  styles.itemCard,
                  baseItemId === item.id && styles.itemCardActive
                ]}
              >
                <Image 
                  source={{ uri: item.image }} 
                  style={styles.itemImage}
                  onError={(error) => {
                    console.log('❌ 이미지 로드 실패:', item.image, error.nativeEvent.error);
                  }}
                  onLoad={() => {
                    console.log('✅ 이미지 로드 성공:', item.image);
                  }}
                />
                <Text style={styles.itemName} numberOfLines={2}>
                  {item.name}
                </Text>
              </Pressable>
              ))}
            </ScrollView>
          )}
        </View>

        {/* 추천 방식 선택 */}
        {baseItem && !baseItem.is_default && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>추천 방식 선택</Text>
            <Text style={styles.sectionSubtitle}>
              {baseItem.has_dress 
                ? "이 드레스와 어울리는 하의 or 아우터 추천"
                : baseItem.has_outer
                ? "이 아우터와 어울리는 상의 or 하의 or 상의+하의 추천"
                : baseItem.has_top
                ? "이 상의와 어울리는 하의 or 아우터 추천"
                : baseItem.has_bottom
                ? "이 하의와 어울리는 상의 or 아우터+상의 추천"
                : "추천 방식을 선택해주세요"
              }
            </Text>
            
            <View style={styles.partSelector}>
              {baseItem.has_top && (
                <Pressable
                  onPress={() => setSelectedPart('top')}
                  style={[
                    styles.partCard,
                    selectedPart === 'top' && styles.partCardActive
                  ]}
                >
                  <Text style={[styles.partText, selectedPart === 'top' && styles.partTextActive]}>
                    👕 상의
                  </Text>
                  <Image 
                    source={{ uri: baseItem.top_image || baseItem.image }} 
                    style={styles.partImage}
                    onError={(error) => {
                      console.log('❌ 상의 이미지 로드 실패:', baseItem.top_image || baseItem.image);
                    }}
                    onLoad={() => {
                      console.log('✅ 상의 이미지 로드 성공:', baseItem.top_image || baseItem.image);
                    }}
                  />
                </Pressable>
              )}
              
              {baseItem.has_bottom && (
                <Pressable
                  onPress={() => setSelectedPart('bottom')}
                  style={[
                    styles.partCard,
                    selectedPart === 'bottom' && styles.partCardActive
                  ]}
                >
                  <Text style={[styles.partText, selectedPart === 'bottom' && styles.partTextActive]}>
                    👖 하의
                  </Text>
                  <Image 
                    source={{ uri: baseItem.bottom_image || baseItem.image }} 
                    style={styles.partImage}
                    onError={(error) => {
                      console.log('❌ 하의 이미지 로드 실패:', baseItem.bottom_image || baseItem.image);
                    }}
                    onLoad={() => {
                      console.log('✅ 하의 이미지 로드 성공:', baseItem.bottom_image || baseItem.image);
                    }}
                  />
                </Pressable>
              )}
              
              {baseItem.has_outer && (
                <Pressable
                  onPress={() => setSelectedPart('outer')}
                  style={[
                    styles.partCard,
                    selectedPart === 'outer' && styles.partCardActive
                  ]}
                >
                  <Text style={[styles.partText, selectedPart === 'outer' && styles.partTextActive]}>
                    🧥 아우터
                  </Text>
                  <Image source={{ uri: baseItem.outer_image || baseItem.image }} style={styles.partImage} />
                </Pressable>
              )}
              
              {baseItem.has_dress && (
                <Pressable
                  onPress={() => setSelectedPart('dress')}
                  style={[
                    styles.partCard,
                    selectedPart === 'dress' && styles.partCardActive
                  ]}
                >
                  <Text style={[styles.partText, selectedPart === 'dress' && styles.partTextActive]}>
                    👗{' '}드레스
                  </Text>
                  <Image 
                    source={{ uri: baseItem.dress_image || baseItem.image }} 
                    style={styles.partImage}
                    onError={(error) => {
                      console.log('❌ 드레스 이미지 로드 실패:', baseItem.dress_image || baseItem.image);
                    }}
                    onLoad={() => {
                      console.log('✅ 드레스 이미지 로드 성공:', baseItem.dress_image || baseItem.image);
                    }}
                  />
                </Pressable>
              )}
            </View>
          </View>
        )}

        {/* AI 추천 버튼 */}
        {baseItem && !baseItem.is_default && (
        <View style={styles.section}>
          <Pressable
            onPress={fetchRecommendation}
            disabled={!baseItem || recommending}
            style={[styles.recommendBtn, (!baseItem || recommending) && styles.recommendBtnDisabled]}
          >
            {recommending ? (
              <ActivityIndicator size="small" color="#FFF" />
            ) : (
              <>
                <Zap size={20} color="#FFF" />
                <Text style={styles.recommendBtnText}>AI 추천</Text>
              </>
            )}
          </Pressable>
        </View>
        )}

        {/* 추천 결과 */}
        {recommendations.length > 0 && (
          <View style={styles.section}>
            <View style={styles.resultHeader}>
              <Text style={styles.sectionTitle}>추천 결과</Text>
              <View style={styles.scoreBadge}>
                <Text style={styles.scoreText}>평균 {avgScore}점</Text>
              </View>
            </View>
            
            <View style={styles.recommendationsGrid}>
              {recommendations.map((rec, index) => (
                <Pressable key={`${rec.id}-${index}-${rec.is_default ? 'default' : 'user'}`} style={styles.recommendationCard}>
                  <Image 
                    source={{ uri: rec.image }} 
                    style={styles.recommendationImage}
                    onError={(error) => {
                      console.log('❌ 추천 아이템 이미지 로드 실패:', rec.image, error.nativeEvent.error);
                    }}
                    onLoad={() => {
                      console.log('✅ 추천 아이템 이미지 로드 성공:', rec.image);
                    }}
                  />
                  <View style={styles.recommendationInfo}>
                    <Text style={styles.recommendationTitle} numberOfLines={2}>
                      {rec.title}
                    </Text>
                    <View style={styles.recommendationMeta}>
                      <Text style={styles.recommendationScore}>{rec.score}점</Text>
                      {rec.is_default && (
                        <View style={styles.defaultBadge}>
                          <Text style={styles.defaultBadgeText}>기본 추천</Text>
                        </View>
                      )}
                    </View>
                    {rec.detailed_scores && (
                      <View style={styles.detailedScores}>
                        <Text style={styles.scoreLabel}>색상: {Math.round(rec.detailed_scores.color_harmony * 100)}</Text>
                        <Text style={styles.scoreLabel}>소재: {Math.round(rec.detailed_scores.material_combination * 100)}</Text>
                        <Text style={styles.scoreLabel}>핏: {Math.round(rec.detailed_scores.fit_combination * 100)}</Text>
                        <Text style={styles.scoreLabel}>스타일: {Math.round(rec.detailed_scores.style_combination * 100)}</Text>
                        <Text style={styles.scoreLabel}>계절: {Math.round(rec.detailed_scores.seasonal_suitability * 100)}</Text>
                      </View>
                    )}
                    {rec.explanation && (
                      <Text style={styles.explanationText} numberOfLines={2}>
                        {rec.explanation}
                      </Text>
                    )}
                  </View>
                </Pressable>
              ))}
            </View>
          </View>
        )}
      </ScrollView>

      {/* LLM 채팅 모달 */}
      {showChat && (
        <View style={styles.chatModal}>
          <View style={styles.chatContainer}>
            <View style={styles.chatHeader}>
              <Text style={styles.chatTitle}>AI 스타일리스트</Text>
              <Pressable onPress={() => setShowChat(false)}>
                <X size={24} color="#6B7280" />
              </Pressable>
            </View>
            
            <ScrollView 
              style={styles.chatMessages}
              contentContainerStyle={styles.chatMessagesContent}
            >
              {chatMessages.length === 0 ? (
                <View style={styles.welcomeMessage}>
                  <Text style={styles.welcomeText}>
                    안녕하세요! 저는 당신의 패션 스타일리스트 AI입니다. 
                    어떤 스타일링을 도와드릴까요?
                  </Text>
                </View>
              ) : (
                chatMessages.map((msg, index) => (
                  <View
                    key={index}
                    style={[
                      styles.messageContainer,
                      msg.role === 'user' ? styles.userMessage : styles.assistantMessage,
                    ]}
                  >
                    <Text style={[
                      styles.messageText,
                      msg.role === 'user' ? styles.userMessageText : styles.assistantMessageText,
                    ]}>
                      {msg.content}
                    </Text>
                    <Text style={styles.messageTime}>
                      {msg.timestamp.toLocaleTimeString('ko-KR', { 
                        hour: '2-digit', 
                        minute: '2-digit' 
                      })}
                    </Text>
                  </View>
                ))
              )}
              
              {chatLoading && (
                <View style={[styles.messageContainer, styles.assistantMessage]}>
                  <ActivityIndicator size="small" color="#6B7280" />
                  <Text style={[styles.messageText, styles.assistantMessageText, { marginLeft: 8 }]}>
                    AI가 답변을 준비 중입니다...
                  </Text>
                </View>
              )}
            </ScrollView>

            {/* 채팅 추천 아이템 */}
            {chatRecommendations.length > 0 && (
              <View style={styles.recommendationsContainer}>
                <Text style={styles.recommendationsTitle}>추천 아이템</Text>
                <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                  <View style={styles.recommendationsList}>
                    {chatRecommendations.map((item) => (
                      <Pressable key={item.id} style={styles.recommendationCard}>
                        <Image source={{ uri: item.image }} style={styles.recommendationImage} />
                        <Text style={styles.recommendationName} numberOfLines={2}>
                          {item.name}
                        </Text>
                      </Pressable>
                    ))}
                  </View>
                </ScrollView>
              </View>
            )}

            <View style={styles.chatInputContainer}>
              <TextInput
                style={styles.chatInput}
                placeholder="메시지를 입력하세요..."
                value={chatInput}
                onChangeText={setChatInput}
                onSubmitEditing={sendChatMessage}
                editable={!chatLoading}
              />
              <Pressable 
                onPress={sendChatMessage}
                style={[styles.chatSendBtn, (!chatInput.trim() || chatLoading) && styles.chatSendBtnDisabled]}
                disabled={!chatInput.trim() || chatLoading}
              >
                <Send size={18} color="#FFF" />
              </Pressable>
            </View>
          </View>
        </View>
      )}

      <BottomNavBar activeScreen="style-analysis" onNavigate={onNavigate} />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  container: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 16,
    paddingBottom: 100,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#6B7280',
  },
  weatherCard: {
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 16,
    marginTop: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  weatherHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  weatherInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  weatherDate: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111',
  },
  weatherTemp: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#111',
  },
  weatherIcon: {
    padding: 8,
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
  },
  weatherDesc: {
    fontSize: 14,
    color: '#6B7280',
  },
  section: {
    marginTop: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111',
  },
  sectionSubtitle: {
    fontSize: 13,
    color: '#6B7280',
    marginTop: 4,
    marginBottom: 12,
  },
  itemScroll: {
    marginTop: 12,
  },
  itemScrollContent: {
    paddingRight: 16,
  },
  itemCard: {
    width: 100,
    marginRight: 12,
    backgroundColor: '#FFF',
    borderRadius: 8,
    padding: 8,
    borderWidth: 2,
    borderColor: '#E5E7EB',
  },
  itemCardActive: {
    borderColor: '#111',
    backgroundColor: '#F9FAFB',
  },
  itemImage: {
    width: 84,
    height: 100,
    borderRadius: 6,
    backgroundColor: '#F3F4F6',
  },
  itemName: {
    fontSize: 12,
    color: '#6B7280',
    textAlign: 'center',
    marginTop: 8,
    lineHeight: 16,
  },
  partSelector: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 12,
  },
  partCard: {
    flex: 1,
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 12,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#E5E7EB',
  },
  partCardActive: {
    borderColor: '#111',
    backgroundColor: '#F9FAFB',
  },
  partImage: {
    width: 80,
    height: 100,
    borderRadius: 8,
    marginTop: 8,
  },
  partText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#6B7280',
  },
  partTextActive: {
    color: '#111',
  },
  recommendBtn: {
    backgroundColor: '#111',
    borderRadius: 12,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  recommendBtnDisabled: {
    backgroundColor: '#D1D5DB',
  },
  recommendBtnText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: '600',
  },
  resultHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  scoreBadge: {
    backgroundColor: '#F3F4F6',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  scoreText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#111',
  },
  recommendationsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  recommendationCard: {
    width: '48%',
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  recommendationImage: {
    width: '100%',
    height: 120,
    borderRadius: 8,
    backgroundColor: '#F3F4F6',
  },
  recommendationInfo: {
    marginTop: 12,
  },
  recommendationTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111',
    lineHeight: 20,
  },
  recommendationMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 8,
  },
  recommendationScore: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6B7280',
  },
  defaultBadge: {
    backgroundColor: '#FEF3C7',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 8,
  },
  defaultBadgeText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#D97706',
  },
  detailedScores: {
    marginTop: 8,
    gap: 2,
  },
  scoreLabel: {
    fontSize: 10,
    color: '#6B7280',
  },
  explanationText: {
    fontSize: 11,
    color: '#6B7280',
    marginTop: 8,
    lineHeight: 16,
  },
  chatToggleBtn: {
    paddingHorizontal: 10,
    paddingVertical: 8,
    backgroundColor: '#111111',
    borderRadius: 8,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    width: 36,
    height: 36,
  },
  chatToggleBtnActive: {
    backgroundColor: '#EF4444',
  },
  chatModal: {
    position: 'absolute',
    top: APP_HEADER_HEIGHT,
    left: 0,
    right: 0,
    bottom: BOTTOM_NAV_HEIGHT,
    zIndex: 100,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
  chatContainer: {
    flex: 1,
    backgroundColor: '#FFF',
    margin: 16,
    borderRadius: 16,
    overflow: 'hidden',
  },
  chatHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  chatTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111',
  },
  chatMessages: {
    flex: 1,
  },
  chatMessagesContent: {
    padding: 16,
  },
  welcomeMessage: {
    alignItems: 'center',
    paddingVertical: 32,
  },
  welcomeText: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 20,
  },
  messageContainer: {
    marginVertical: 4,
    maxWidth: '80%',
  },
  userMessage: {
    alignSelf: 'flex-end',
    backgroundColor: '#111',
    borderRadius: 18,
    borderBottomRightRadius: 4,
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  assistantMessage: {
    alignSelf: 'flex-start',
    backgroundColor: '#F3F4F6',
    borderRadius: 18,
    borderBottomLeftRadius: 4,
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  messageText: {
    fontSize: 14,
    lineHeight: 20,
  },
  userMessageText: {
    color: '#FFF',
  },
  assistantMessageText: {
    color: '#111',
  },
  messageTime: {
    fontSize: 11,
    color: '#9CA3AF',
    marginTop: 4,
    textAlign: 'right',
  },
  recommendationsContainer: {
    backgroundColor: '#F9FAFB',
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  recommendationsTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111',
    marginBottom: 12,
  },
  recommendationsList: {
    flexDirection: 'row',
    gap: 12,
  },
  chatInputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
    gap: 12,
  },
  chatInput: {
    flex: 1,
    backgroundColor: '#F3F4F6',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 14,
    color: '#111',
  },
  chatSendBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#111',
    alignItems: 'center',
    justifyContent: 'center',
  },
  chatSendBtnDisabled: {
    backgroundColor: '#D1D5DB',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 32,
    paddingHorizontal: 16,
  },
  emptyText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#6B7280',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#9CA3AF',
    textAlign: 'center',
  },
});