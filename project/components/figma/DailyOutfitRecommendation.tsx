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
  TextInput,        // 👈 추가
  KeyboardAvoidingView,  // 👈 추가
  Platform,         // 👈 이미 있으면 생략
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  Cloud,
  Thermometer,
  Calendar,
  MapPin,
  RefreshCw,
  Zap,
  MessageCircle,  // 👈 추가
  Send,           // 👈 추가
  X,              // 👈 추가
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
  top_image?: string;
  bottom_image?: string;
  has_top?: boolean;
  has_bottom?: boolean;
};

// ✅ 코드 변경 강제 트리거 - v2.0
export default function DailyOutfitRecommendation({
  onBack,
  onNavigate,
}: {
  onBack: () => void;
  onNavigate: (step: NavigationStep) => void;
}) {
  const [selectedOccasion, setSelectedOccasion] = useState<
    'daily' | 'work' | 'date' | 'party' | 'casual' | 'formal'
  >('daily');
  const [loading, setLoading] = useState(true);
  const [recommending, setRecommending] = useState(false);
  const [userId, setUserId] = useState<number | null>(null);
  const [wardrobeItems, setWardrobeItems] = useState<WardrobeItem[]>([]);
  const [recommendations, setRecommendations] = useState<Rec[]>([]);
  const [baseItemId, setBaseItemId] = useState<number | null>(null); 
  const [selectedPart, setSelectedPart] = useState<'full' | 'top' | 'bottom'>('full');
  const [showChat, setShowChat] = useState(false);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [chatRecommendations, setChatRecommendations] = useState<WardrobeItem[]>([]);

  
  const baseItem = useMemo(() => {
      if (baseItemId === null && wardrobeItems.length > 0) {
          setBaseItemId(wardrobeItems[0].id);
          return wardrobeItems[0];
      }
      return wardrobeItems.find(item => item.id === baseItemId) || null;
  }, [wardrobeItems, baseItemId]);
  

  const occasions = [
    { id: 'daily', name: '데일리', icon: '☀️' },
    { id: 'work', name: '업무', icon: '💼' },
    { id: 'date', name: '데이트', icon: '💕' },
    { id: 'party', name: '파티', icon: '🎉' },
    { id: 'casual', name: '캐주얼', icon: '👕' },
    { id: 'formal', name: '포멀', icon: '👔' },
  ] as const;

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

  // 옷장 데이터 불러오기
  const fetchWardrobe = useCallback(async (id: number) => {
    try {
      const url = `${API_BASE_URL}/api/wardrobe/${id}`;
      const response = await fetch(url);
      
      const contentType = response.headers.get('content-type');
      if (response.status !== 200 || !contentType || !contentType.includes('application/json')) {
        console.error(`❌ 옷장 조회 실패: 상태 코드 ${response.status}`);
        const errorText = await response.text();
        console.error('서버 응답:', errorText.substring(0, 500));
        Alert.alert('서버 오류', `옷장 목록을 불러올 수 없습니다 (Status: ${response.status})`);
        setWardrobeItems([]);
        return;
      }

      const data = await response.json();

      if (data.success && data.items.length > 0) {
        const loadedItems: WardrobeItem[] = data.items.map((item: any) => {
            let name = item.has_top ? `${item.top_color || ''} ${item.top_category}`.trim() : 
                      item.has_bottom ? `${item.bottom_color || ''} ${item.bottom_category}`.trim() : '새 아이템';
            
            const category = item.has_top ? '상의' : item.has_bottom ? '하의' : '';
            
            // ✅ 카테고리별 이미지 URL 생성 (수정!)
            let imageUrl = '';
            
            console.log(`🖼️ Daily - 이미지 URL 생성 중 - item ${item.id}:`);
            console.log(`  - image_path: ${item.image_path}`);
            console.log(`  - image_category: ${item.image_category}`);
            
            if (item.image_category === 'original') {
              imageUrl = `${API_BASE_URL}/api/images/${item.image_path}`;
            } else if (item.image_category) {
              // full, top, bottom, outer
              imageUrl = `${API_BASE_URL}/api/processed-images/${item.image_category}/${item.image_path}`;
            } else {
              // 카테고리 정보가 없으면 원본 경로 사용
              imageUrl = `${API_BASE_URL}/api/images/${item.image_path}`;
            }
            
            console.log(`  ✅ 생성된 URL: ${imageUrl}`);

            return {
              id: item.id,
              name: name || '새 아이템',
              brand: 'My Wardrobe',
              image: imageUrl,
              category: category,
              loved: false,
              top_category: item.top_category,
              bottom_category: item.bottom_category,
              top_image: item.top_image ? `${API_BASE_URL}${item.top_image}` : undefined,
              bottom_image: item.bottom_image ? `${API_BASE_URL}${item.bottom_image}` : undefined,
              has_top: item.has_top,
              has_bottom: item.has_bottom,
            };
        });
        setWardrobeItems(loadedItems);
        
        if (loadedItems.length > 0 && baseItemId === null) {
            setBaseItemId(loadedItems[0].id);
        }
      } else {
        setWardrobeItems([]);
      }
    } catch (error) {
      console.error('❌ 옷장 데이터 로드 실패:', error);
      Alert.alert('네트워크 오류', `서버 연결에 실패했습니다. ngrok 주소를 확인하세요.`);
    }
  }, [baseItemId]); 

  
  // ✨ AI 추천 요청 (수정: 상의/하의 분리 추천 지원)
  const fetchRecommendation = async () => {
    if (!baseItem) {
      Alert.alert('알림', '추천 기준이 될 아이템을 먼저 선택해주세요.');
      return;
    }
    
    setRecommending(true);

    try {
      // ✅ selectedPart에 따라 다른 엔드포인트 호출
      let url = '';
      
      if (selectedPart === 'full') {
        // 전체 코디 유사 추천 (기존 로직)
        url = `${API_BASE_URL}/api/recommendations/similar/${baseItem.id}?n_results=3&user_id=${userId}`;
      } else if (selectedPart === 'top') {
        // 이 상의와 어울리는 하의 추천
        url = `${API_BASE_URL}/api/recommendations/match-bottom/${baseItem.id}?n_results=3&user_id=${userId}`;
      } else if (selectedPart === 'bottom') {
        // 이 하의와 어울리는 상의 추천
        url = `${API_BASE_URL}/api/recommendations/match-top/${baseItem.id}?n_results=3&user_id=${userId}`;
      }
      
      console.log(`\n✨ 추천 요청 URL: ${url}`);
      
      const response = await fetch(url);
      
      const contentType = response.headers.get('content-type');
      if (response.status !== 200 || !contentType || !contentType.includes('application/json')) {
        console.error(`❌ 추천 요청 실패: 상태 코드 ${response.status}`);
        const errorText = await response.text();
        console.error('서버 응답:', errorText.substring(0, 500));
        Alert.alert('서버 오류', `추천을 받을 수 없습니다 (Status: ${response.status})`);
        setRecommendations([]);
        return;
      }

      const data = await response.json();

      if (data.success && data.recommendations) {
        // ✅ 이미지 URL 생성 + 디버깅
        const recs: Rec[] = data.recommendations.map((rec: any, index: number) => {
          const imageUrl = `${API_BASE_URL}/api/images/${rec.image_path}`;
          
          console.log(`\n📸 추천 아이템 ${index + 1}:`);
          console.log(`  - ID: ${rec.id}`);
          console.log(`  - image_path (from server): ${rec.image_path}`);
          console.log(`  - imageUrl (generated): ${imageUrl}`);
          console.log(`  - name: ${rec.name}`);
          console.log(`  - category: ${rec.category}`);
          
          return {
            id: rec.id,
            image: imageUrl,
            title: selectedPart === 'full' 
              ? `${baseItem.name} 아이템과 유사`
              : selectedPart === 'top'
              ? `${baseItem.name}와 어울리는 하의`
              : `${baseItem.name}와 어울리는 상의`,
            items: [rec.name, rec.category],
            score: Math.round((1.0 - rec.distance) * 100), 
            reason: `유사도 점수: ${(1.0 - rec.distance).toFixed(2)}`,
            is_default: rec.is_default || false,
          };
        });
        
        setRecommendations(recs);
        
        const hasDefaultItems = recs.some(r => r.is_default);
        const recommendType = selectedPart === 'full' ? '유사한' : '어울리는';
        
        if (hasDefaultItems) {
          Alert.alert(
            '추천 완료',
            `${baseItem.name}와 ${recommendType} 아이템 ${recs.length}개를 찾았습니다.\n\n일부 기본 추천 아이템이 포함되었습니다.`
          );
        } else {
          Alert.alert('추천 완료', `${baseItem.name}와 ${recommendType} 아이템 ${recs.length}개를 찾았습니다.`);
        }
      } else {
        Alert.alert('추천 실패', data.detail || '추천 목록을 가져오지 못했습니다.');
        setRecommendations([]);
      }
    } catch (error) {
      console.error('❌ 추천 네트워크 오류:', error);
      Alert.alert('네트워크 오류', '추천 서버와 연결할 수 없습니다.');
    } finally {
      setRecommending(false);
    }
  };

  // 💬 LLM 채팅 메시지 전송
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
              : `${rec.bottom_color || ''} ${rec.bottom_category || ''}`.trim(),
            brand: 'AI 추천',
            image: `${API_BASE_URL}${rec.image}`,
            category: rec.has_top ? '상의' : '하의',
            loved: false,
          }));
          
          setChatRecommendations(items);
          
          // 추천이 완료되면 알림
          if (!data.need_more_info) {
            Alert.alert(
              '추천 완료! 🎉',
              `${items.length}개의 아이템을 추천해드렸습니다. 아래에서 확인하세요!`
            );
          }
        }
        
        console.log('✅ 채팅 응답:', data.response);
        console.log('📦 컨텍스트:', data.context);
        console.log('👕 추천 아이템:', data.recommendations?.length || 0);
      } else {
        Alert.alert('오류', data.message || '메시지 전송에 실패했습니다.');
      }
    } catch (error) {
      console.error('❌ 채팅 오류:', error);
      Alert.alert('네트워크 오류', '서버와 연결할 수 없습니다.');
    } finally {
      setChatLoading(false);
    }
  };

  // 💬 채팅 초기화
  const resetChat = async () => {
    if (!userId) return;
    
    try {
      const formData = new FormData();
      formData.append('user_id', String(userId));
      
      const response = await fetch(`${API_BASE_URL}/api/chat/reset`, {
        method: 'POST',
        body: formData,
      });
      
      const data = await response.json();
      
      if (data.success) {
        setChatMessages([]);
        setChatRecommendations([]);
        Alert.alert('초기화 완료', '새로운 대화를 시작하세요!');
      }
    } catch (error) {
      console.error('❌ 초기화 오류:', error);
    }
  };


  useEffect(() => {
    const loadUser = async () => {
      try {
        const userStr = await AsyncStorage.getItem('user');
        if (userStr) {
          const user = JSON.parse(userStr);
          setUserId(user.user_id);
          fetchWardrobe(user.user_id);
        } else {
          Alert.alert('로그인 필요', '로그인이 필요합니다.');
        }
      } catch (error) {
        console.error('❌ 사용자 정보 로드 실패:', error);
      } finally {
        setLoading(false); 
      }
    };
    loadUser();
  }, [fetchWardrobe]);
  
  async function onRefresh() {
    await fetchRecommendation();
  }

  const handleNavigation = (screen: string) => {
    console.log('========================================');
    console.log('📢 네비게이션 클릭!');
    console.log('전달받은 screen 값:', screen);
    console.log('screen 타입:', typeof screen);
    console.log('========================================');
    
    onNavigate(screen as NavigationStep);
  };

// ✅ HeaderRightAction 수정 (line ~260 근처)
  const HeaderRightAction = (
    <View style={{ flexDirection: 'row', gap: 8 }}>
      {/* 👇 채팅 버튼 추가 */}
      <Pressable 
        onPress={() => setShowChat(!showChat)} 
        style={[styles.chatToggleBtn, showChat && styles.chatToggleBtnActive]}
      >
        {showChat ? <X size={16} color="#FFF" /> : <MessageCircle size={16} color="#FFF" />}
      </Pressable>
      
      {/* 기존 AI 추천 버튼 */}
      <Pressable 
        onPress={onRefresh} 
        style={[styles.refreshBtn, (loading || recommending || !baseItem) && styles.refreshBtnDisabled]} 
        disabled={loading || recommending || !baseItem}
      >
        {(loading || recommending) ? <ActivityIndicator color="#FFF" size="small" /> : <Zap size={16} color="#FFF" />}
        <Text style={styles.refreshText}>{(loading || recommending) ? '처리중...' : 'AI 추천'}</Text>
      </Pressable>
    </View>
  );

  return (
    <SafeAreaView style={styles.safe}>
      <AppHeader
        title="AI 코디 분석"
        subtitle="옷장 기반 유사 아이템 추천"
        onBack={onBack}
        rightAction={HeaderRightAction}
      />

      {(loading || recommending) && (
        <View style={styles.overlay}>
          <ActivityIndicator size="large" color="#FFF" />
          <Text style={styles.overlayText}>
            {loading ? '데이터 로딩 중...' : 'AI가 추천을 생성하는 중...'}
          </Text>
        </View>
      )}

      {/* 👇 채팅 모달 추가 */}
      {showChat && (
        <KeyboardAvoidingView 
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.chatModal}
        >
          <View style={styles.chatContainer}>
            {/* 채팅 헤더 */}
            <View style={styles.chatHeader}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                <MessageCircle size={20} color="#111" />
                <Text style={styles.chatHeaderTitle}>AI 스타일리스트와 대화</Text>
              </View>
              <Pressable onPress={resetChat}>
                <Text style={styles.chatResetBtn}>초기화</Text>
              </Pressable>
            </View>

            {/* 채팅 메시지 */}
            <ScrollView 
              style={styles.chatMessages}
              contentContainerStyle={{ padding: 12, gap: 12 }}
            >
              {chatMessages.length === 0 ? (
                <View style={styles.chatEmptyState}>
                  <Text style={styles.chatEmptyText}>
                    안녕하세요! 😊{'\n\n'}
                    오늘 어떤 옷을 입을지 고민이시라면{'\n'}
                    편하게 물어보세요!{'\n\n'}
                    예: "오늘 회사 가는데 좀 추워요"
                  </Text>
                </View>
              ) : (
                chatMessages.map((msg, index) => (
                  <View 
                    key={index}
                    style={[
                      styles.chatBubble,
                      msg.role === 'user' ? styles.chatBubbleUser : styles.chatBubbleAI
                    ]}
                  >
                    <Text style={[
                      styles.chatBubbleText,
                      msg.role === 'user' && styles.chatBubbleTextUser
                    ]}>
                      {msg.content}
                    </Text>
                  </View>
                ))
              )}
              
              {chatLoading && (
                <View style={[styles.chatBubble, styles.chatBubbleAI]}>
                  <ActivityIndicator size="small" color="#666" />
                </View>
              )}
            </ScrollView>

            {/* 채팅 입력창 */}
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
        </KeyboardAvoidingView>
      )}


      <ScrollView contentContainerStyle={styles.screenPad}>
        
        {/* A. 현재 날씨 카드 */}
        <View style={styles.weatherCard}>
          <View style={styles.weatherLeft}>
            <View style={styles.weatherIcon}>
              <Cloud size={24} color="#FFF" />
            </View>
            <View>
              <Text style={styles.weatherTitle}>오늘의 날씨 (임시)</Text>
              <View style={styles.weatherRow}>
                <View style={styles.inlineRow}>
                  <Calendar size={12} color="#374151" />
                  <Text style={styles.weatherMeta}>{todayStr}</Text>
                </View>
                <View style={styles.inlineRow}>
                  <MapPin size={12} color="#374151" />
                  <Text style={styles.weatherMeta}>서울 (임시)</Text>
                </View>
              </View>
            </View>
          </View>
          <View>
            <Text style={styles.weatherMain}>18°C / 23°C</Text>
            <Text style={styles.weatherSub}>약간 흐림, 겉옷 추천</Text>
          </View>
        </View>

        {/* B. 기준 아이템 선택 섹션 */}
        <View>
            <Text style={styles.sectionTitle}>추천 기준 아이템 선택</Text>
            {wardrobeItems.length === 0 ? (
                <View style={[styles.emptyArea, {paddingVertical: 10}]}>
                    <Text style={styles.emptyText}>옷장에 아이템이 없습니다. 등록해주세요.</Text>
                </View>
            ) : (
                <>
                    <View style={styles.baseItemInfo}>
                        <Text style={styles.baseItemText}>
                            현재 기준: <Text style={{fontWeight: 'bold', color: '#111'}}>{baseItem?.name || '선택 필요'}</Text> ({baseItem?.category || '-'})
                        </Text>
                    </View>
                    <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.baseItemScroll}>
                        {wardrobeItems.map((item) => (
                            <Pressable 
                                key={item.id} 
                                onPress={() => { setBaseItemId(item.id); setRecommendations([]); }} 
                                style={[styles.baseItemCard, item.id === baseItemId && styles.baseItemCardActive]}
                                disabled={loading || recommending}
                            >
                                <Image source={{ uri: item.image }} style={styles.baseItemImg} />
                                <View style={styles.baseItemOverlay}>
                                    <Text style={styles.baseItemCardText}>{item.name}</Text>
                                </View>
                            </Pressable>
                        ))}
                    </ScrollView>
                </>
            )}
        </View>

        {/* C. 추천 방식 선택 */}
        {baseItem && (baseItem.has_top || baseItem.has_bottom) && (
          <View>
            <Text style={styles.sectionTitle}>추천 방식 선택</Text>
            <Text style={styles.sectionSubtitle}>
              {selectedPart === 'full' ? '전체 코디 유사 추천' :
              selectedPart === 'top' ? '이 상의와 어울리는 하의 추천' :
              '이 하의와 어울리는 상의 추천'}
            </Text>
            
            <View style={styles.partSelector}>
              <Pressable 
                style={[
                  styles.partCard,
                  selectedPart === 'full' && styles.partCardActive
                ]}
                onPress={() => {
                  setSelectedPart('full');
                  setRecommendations([]);
                }}
                disabled={loading || recommending}
              >
                <Image source={{ uri: baseItem.image }} style={styles.partImage} />
                <Text style={[
                  styles.partText,
                  selectedPart === 'full' && styles.partTextActive
                ]}>
                  전체
                </Text>
              </Pressable>
              
              {baseItem.has_top && baseItem.top_image && (
                <Pressable 
                  style={[
                    styles.partCard,
                    selectedPart === 'top' && styles.partCardActive
                  ]}
                  onPress={() => {
                    setSelectedPart('top');
                    setRecommendations([]);
                  }}
                  disabled={loading || recommending}
                >
                  <Image source={{ uri: baseItem.top_image }} style={styles.partImage} />
                  <Text style={[
                    styles.partText,
                    selectedPart === 'top' && styles.partTextActive
                  ]}>
                    👕 상의
                  </Text>
                </Pressable>
              )}
              
              {baseItem.has_bottom && baseItem.bottom_image && (
                <Pressable 
                  style={[
                    styles.partCard,
                    selectedPart === 'bottom' && styles.partCardActive
                  ]}
                  onPress={() => {
                    setSelectedPart('bottom');
                    setRecommendations([]);
                  }}
                  disabled={loading || recommending}
                >
                  <Image source={{ uri: baseItem.bottom_image }} style={styles.partImage} />
                  <Text style={[
                    styles.partText,
                    selectedPart === 'bottom' && styles.partTextActive
                  ]}>
                    👖 하의
                  </Text>
                </Pressable>
              )}
            </View>
          </View>
        )}
        
        {/* D. 상황별 선택 */}
        <View>
          <Text style={styles.sectionTitle}>추천 상황 선택</Text>
          <View style={[styles.occGrid, { marginTop: 12 }]}>
            {occasions.map((occ) => (
              <Pressable
                key={occ.id}
                onPress={() => setSelectedOccasion(occ.id)}
                disabled={loading || recommending}
                style={[
                  styles.occBtn,
                  selectedOccasion === occ.id ? styles.occActive : styles.occIdle,
                  (loading || recommending) && styles.occBtnDisabled
                ]}
              >
                <Text style={styles.occEmoji}>{occ.icon}</Text>
                <Text
                  style={[
                    styles.occText,
                    selectedOccasion === occ.id && styles.occTextActive,
                  ]}
                >
                  {occ.name}
                </Text>
              </Pressable>
            ))}
          </View>
        </View>

        {/* 👇 채팅 추천 결과 섹션 추가 (E. 추천 결과 목록 위에) */}
        {chatRecommendations.length > 0 && (
          <View>
            <Text style={styles.sectionTitle}>💬 대화 기반 AI 추천</Text>
            <View style={{ gap: 16, marginTop: 16 }}>
              {chatRecommendations.map((item, index) => (
                <View key={item.id} style={styles.cardRow}>
                  <View style={styles.thumbBig}>
                    <Image 
                      source={{ uri: item.image }} 
                      style={[styles.thumbImg, { width: 96, height: 140 }]}
                      resizeMode="cover"
                    />
                    <View style={styles.bestBadge}>
                      <Text style={styles.bestBadgeText}>
                        {index === 0 ? 'BEST' : `No.${index + 1}`}
                      </Text>
                    </View>
                  </View>
                  <View style={{ flex: 1, padding: 12, justifyContent: 'space-between' }}>
                    <View>
                      <Text style={styles.cardTitle}>{item.name}</Text>
                      <Text style={styles.reason}>대화를 통해 추천된 아이템입니다</Text>
                    </View>
                    <Pressable style={[styles.btn, styles.btnPrimary]}>
                      <Text style={styles.btnPrimaryText}>코디 보기</Text>
                    </Pressable>
                  </View>
                </View>
              ))}
            </View>
          </View>
        )}

        {/* E. 추천 결과 목록 */}
        <View>
          <View style={styles.rowBetween}>
            <Text style={styles.sectionTitle}>
                {recommendations.length > 0 ? 'AI 추천 결과' : 'AI 추천을 시작해주세요'}
            </Text>
            {recommendations.length > 0 && (
              <View style={styles.rowCenter}>
                <View style={styles.badgeSoftGreen}>
                  <Text style={styles.badgeSoftGreenText}>평균 점수 {avgScore}</Text>
                </View>
              </View>
            )}
          </View>
          
          {wardrobeItems.length === 0 ? (
            <View style={styles.emptyArea}>
                <Text style={styles.emptyText}>아이템이 없어서 추천을 할 수 없습니다.</Text>
            </View>
          ) : recommendations.length === 0 && !recommending ? (
             <View style={styles.emptyArea}>
                <Text style={styles.emptyText}>기준 아이템을 선택하고 'AI 추천' 버튼을 눌러보세요.</Text>
            </View>
          ) : (
            <View style={{ gap: 16, marginTop: 16 }}>
              {recommendations.map((rec, index) => (
                <View key={rec.id} style={styles.cardRow}>
                  <View style={styles.thumbBig}>
                    <Image 
                      source={{ uri: rec.image }} 
                      style={[styles.thumbImg, { width: 96, height: 140 }]}  // ✅ 명시적 크기 추가
                      resizeMode="cover"
                      onError={(e) => {
                        console.error('❌ 이미지 로드 실패:', rec.image);
                        console.error('에러:', e.nativeEvent.error);
                        console.error('추천 아이템 전체 데이터:', JSON.stringify(rec, null, 2));
                      }}
                      onLoad={() => {
                        console.log('✅ 이미지 로드 성공:', rec.image);
                      }}
                    />
                    {/* 이미지 로드 실패 시 표시할 텍스트 */}
                    <View style={styles.imageLoadingOverlay}>
                      <Text style={styles.imageLoadingText}>📸</Text>
                    </View>
                    <View style={styles.bestBadge}>
                        <Text style={styles.bestBadgeText}>
                            {index === 0 ? 'BEST MATCH' : `No.${index + 1}`}
                        </Text>
                    </View>
                  </View>
                  <View style={{ flex: 1, padding: 12, justifyContent: 'space-between' }}>
                    <View>
                      <Text style={styles.cardTitle}>{rec.title}</Text>
                      <Text style={[styles.scoreText, { marginTop: 4 }]}>
                        {rec.score}점 매칭
                      </Text>
                      <Text style={styles.reason}>{rec.reason}</Text>
                      <View style={{ height: 1, backgroundColor: '#F3F4F6', marginVertical: 8 }} />
                      <View style={styles.tagWrap}>
                        {rec.items.map((item, i) => (
                          <View key={i} style={styles.tag}>
                            <Text style={styles.tagText}>{item}</Text>
                          </View>
                        ))}
                      </View>
                    </View>
                    <View style={{ flexDirection: 'row', gap: 8, marginTop: 12 }}>
                      <Pressable style={[styles.btn, styles.btnPrimary]}>
                        <Text style={styles.btnPrimaryText}>코디 보기</Text>
                      </Pressable>
                      <Pressable style={[styles.btn, styles.btnOutline]}>
                        <Text style={styles.btnOutlineText}>내 옷으로 대체</Text>
                      </Pressable>
                    </View>
                  </View>
                </View>
              ))}
            </View>
          )}
        </View>
      </ScrollView>

      <BottomNavBar 
        activeScreen="style-analysis"
        onNavigate={handleNavigation} 
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#FFFFFF' },
  overlay: {
    ...StyleSheet.absoluteFillObject,
    top: APP_HEADER_HEIGHT,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.4)',
    zIndex: 99, 
    justifyContent: 'center',
    alignItems: 'center',
  },
  overlayText: {
    color: '#FFF',
    marginTop: 10,
    fontWeight: 'bold',
  },
  refreshBtn: {
    paddingHorizontal: 10,
    paddingVertical: 8,
    backgroundColor: '#111111',
    borderRadius: 8,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  refreshBtnDisabled: { opacity: 0.5 },
  refreshText: { color: '#FFFFFF', fontSize: 12, fontWeight: '600' },
  screenPad: { 
    padding: 16, 
    gap: 24, 
    paddingBottom: 80, 
    minHeight: '100%',
    position: 'relative'
  },
  
  baseItemInfo: { 
      backgroundColor: '#F3F4F6', 
      padding: 12, 
      borderRadius: 8, 
      marginBottom: 10 
  },
  baseItemText: { 
      fontSize: 13, 
      color: '#4B5563', 
  },
  baseItemScroll: { 
      flexDirection: 'row',
      marginHorizontal: -16, 
      paddingHorizontal: 16
  },
  baseItemCard: {
      width: 80,
      height: 110,
      borderRadius: 8,
      marginRight: 8,
      overflow: 'hidden',
      borderWidth: 2,
      borderColor: 'transparent',
  },
  baseItemCardActive: {
      borderColor: '#111',
  },
  baseItemImg: {
      ...StyleSheet.absoluteFillObject,
      width: '100%',
      height: '100%',
  },
  baseItemOverlay: {
      ...StyleSheet.absoluteFillObject,
      backgroundColor: 'rgba(0,0,0,0.2)',
      justifyContent: 'flex-end',
      padding: 4,
  },
  baseItemCardText: {
      color: '#FFF',
      fontSize: 10,
      fontWeight: '600',
  },
  
  loadingArea: { paddingVertical: 40, alignItems: 'center' },
  loadingText: { marginTop: 16, color: '#666' },
  emptyArea: { paddingVertical: 20, alignItems: 'center' },
  emptyText: { fontSize: 16, color: '#9CA3AF', marginBottom: 8, textAlign: 'center' },
  
  weatherCard: {
    backgroundColor: '#F9FAFB',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#F3F4F6',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  weatherLeft: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  weatherIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#3B82F6',
    alignItems: 'center',
    justifyContent: 'center',
  },
  weatherTitle: { fontSize: 14, fontWeight: '600', color: '#111827' },
  weatherRow: { flexDirection: 'row', gap: 10, marginTop: 4, flexWrap: 'wrap' },
  inlineRow: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  weatherMeta: { fontSize: 12, color: '#374151' },
  weatherMain: { fontSize: 16, fontWeight: '600', color: '#111827', textAlign: 'right' },
  weatherSub: { fontSize: 12, color: '#6B7280' },
  sectionTitle: { fontSize: 16, fontWeight: '600', color: '#0B0B0B' },
  occGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  occBtn: {
    flex: 1,
    minWidth: '30%',
    paddingVertical: 12,
    alignItems: 'center',
    borderRadius: 8,
    borderWidth: 1,
    gap: 6,
  },
  occBtnDisabled: {
      opacity: 0.5
  },
  occIdle: { backgroundColor: '#FFFFFF', borderColor: '#E5E7EB' },
  occActive: { backgroundColor: '#111111', borderColor: '#111111' },
  occEmoji: { fontSize: 20 },
  occText: { fontSize: 13, color: '#111' },
  occTextActive: { color: '#FFF', fontWeight: '600' },
  rowBetween: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  rowCenter: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  badgeSoftGreen: {
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 999,
  },
  badgeSoftGreenText: { color: '#166534', fontSize: 12, fontWeight: '600' },
  cardRow: {
    backgroundColor: '#FFFFFF',
    borderRadius: 10,
    overflow: 'hidden',
    flexDirection: 'row',
    minHeight: 140,  // ✅ 최소 높이 추가
    elevation: 2,
    shadowColor: '#000',
    shadowOpacity: 0.06,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 4 },
    borderWidth: 1.5,
    borderColor: '#F3F4F6'
  },
  thumbBig: { 
    width: 96, 
    height: 140,  // ✅ 'auto'에서 고정 높이로 변경
    backgroundColor: '#EEE',
    overflow: 'hidden',
  },
  thumbImg: { 
    width: '100%', 
    height: '100%', 
    resizeMode: 'cover' 
  },
  imageLoadingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: '#F3F4F6',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: -1,
  },
  imageLoadingText: {
    fontSize: 32,
    opacity: 0.3,
  },
  bestBadge: {
    position: 'absolute',
    top: 6,
    left: 6,
    backgroundColor: '#111',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  bestBadgeText: { color: '#FFF', fontSize: 10, fontWeight: '700' },
  cardTitle: { fontSize: 14, fontWeight: '600', color: '#111827' },
  dot: { width: 8, height: 8, borderRadius: 4 },
  scoreText: { fontSize: 12, color: '#111827', fontWeight: '600' },
  tagWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  tag: {
    borderWidth: 1,
    borderColor: '#E5E7EB',
    backgroundColor: '#F9FAFB',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
  },
  tagText: { fontSize: 11, color: '#4B5563' },
  reason: { fontSize: 12, color: '#6B7280' },
  btn: {
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    flex: 1,
  },
  btnPrimary: { backgroundColor: '#111' },
  btnPrimaryText: { color: '#FFF', fontSize: 13, fontWeight: '600' },
  btnOutline: { backgroundColor: '#FFF', borderWidth: 1, borderColor: '#E5E7EB' },
  btnOutlineText: { color: '#111', fontSize: 13, fontWeight: '600' },

  sectionSubtitle: {
    fontSize: 13,
    color: '#6B7280',
    marginTop: 4,
    marginBottom: 12,
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
    marginBottom: 8,
  },
  partText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#6B7280',
  },
  partTextActive: {
    color: '#111',
  },
    // 👇 채팅 관련 스타일 추가
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
    shadowColor: '#000',
    shadowOpacity: 0.3,
    shadowRadius: 20,
    elevation: 10,
  },
  chatHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
    backgroundColor: '#F9FAFB',
  },
  chatHeaderTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111',
  },
  chatResetBtn: {
    fontSize: 13,
    fontWeight: '600',
    color: '#EF4444',
  },
  chatMessages: {
    flex: 1,
    backgroundColor: '#FFF',
  },
  chatEmptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 40,
  },
  chatEmptyText: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 22,
  },
  chatBubble: {
    maxWidth: '80%',
    padding: 12,
    borderRadius: 12,
    marginBottom: 8,
  },
  chatBubbleUser: {
    alignSelf: 'flex-end',
    backgroundColor: '#111',
  },
  chatBubbleAI: {
    alignSelf: 'flex-start',
    backgroundColor: '#F3F4F6',
  },
  chatBubbleText: {
    fontSize: 14,
    color: '#111',
    lineHeight: 20,
  },
  chatBubbleTextUser: {
    color: '#FFF',
  },
  chatInputContainer: {
    flexDirection: 'row',
    padding: 12,
    gap: 8,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
    backgroundColor: '#FFF',
  },
  chatInput: {
    flex: 1,
    backgroundColor: '#F9FAFB',
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    fontSize: 14,
  },
  chatSendBtn: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#111',
    justifyContent: 'center',
    alignItems: 'center',
  },
  chatSendBtnDisabled: {
    opacity: 0.5,
  },
});