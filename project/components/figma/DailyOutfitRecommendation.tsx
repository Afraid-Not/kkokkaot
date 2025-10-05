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
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  Cloud,
  Thermometer,
  Calendar,
  MapPin,
  RefreshCw,
  Zap,
} from 'lucide-react-native';
import AppHeader from '../common/AppHeader';
import BottomNavBar from '../common/BottomNavBar';
import AsyncStorage from '@react-native-async-storage/async-storage';

// 🌐 API 주소는 WardrobeManagement와 동일하게 사용
const API_BASE_URL = 'https://loyd-extemporaneous-annalise.ngrok-free.dev';
const APP_HEADER_HEIGHT = 56; // AppHeader의 예상 높이 (Safe Area 미포함)
const BOTTOM_NAV_HEIGHT = 80; // BottomNavBar의 예상 높이

// 네비게이션 타입을 정의합니다. (App.tsx의 MainScreen 타입과 일치해야 함)
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
};

// 옷장 아이템 타입 (WardrobeManagement.tsx에서 복사)
type WardrobeItem = { 
  id: number; 
  name: string; 
  brand: string; 
  image: string; 
  category: string; 
  loved: boolean;
  top_category?: string;
  bottom_category?: string;
  // ✅ 이 3줄만 추가!
  top_image?: string;
  bottom_image?: string;
  has_top?: boolean;
  has_bottom?: boolean;
};

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
  // ✅ [추가] 추천의 기준이 될 아이템 ID
  const [baseItemId, setBaseItemId] = useState<number | null>(null); 
  const [selectedPart, setSelectedPart] = useState<'full' | 'top' | 'bottom'>('full');
  
  // 현재 선택된 기준 아이템 정보를 찾습니다.
  const baseItem = useMemo(() => {
      // baseItemId가 null이고 옷장 아이템이 로드되면, 첫 번째 아이템을 자동으로 설정
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

  // 📥 옷장 데이터 불러오기
  const fetchWardrobe = useCallback(async (id: number) => {
    try {
      const url = `${API_BASE_URL}/api/wardrobe/${id}`;
      const response = await fetch(url);
      
      // ✅ [방어 로직 1] 200이 아니거나 JSON이 아니면 오류 처리
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
            const filename = item.image_path.split(/\\|\//).pop();
            const imageUrl = `${API_BASE_URL}/api/images/${filename}`;

            return {
              id: item.id,
              name: name || '새 아이템',
              brand: 'My Wardrobe',
              image: imageUrl,
              category: category,
              loved: false,
              top_category: item.top_category,
              bottom_category: item.bottom_category,
              // ✅ 이 4줄만 추가!
              top_image: item.top_image ? `${API_BASE_URL}${item.top_image}` : undefined,
              bottom_image: item.bottom_image ? `${API_BASE_URL}${item.bottom_image}` : undefined,
              has_top: item.has_top,
              has_bottom: item.has_bottom,
            };
        });
        setWardrobeItems(loadedItems);
        
        // 아이템 로드 후 baseItemId가 설정되지 않았다면 첫 번째 아이템으로 설정
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

  
  // ✨ AI 추천 요청
  const fetchRecommendation = async () => {
    if (!baseItem) {
        Alert.alert('알림', '추천 기준이 될 아이템을 먼저 선택해주세요.');
        return;
    }
    
    setRecommending(true);
    const itemToRecommend = baseItem;

    try {
        const url = `${API_BASE_URL}/api/recommendations/similar/${itemToRecommend.id}?n_results=3`;
        console.log(`\n✨ 추천 요청 URL: ${url}`);
        
        const response = await fetch(url);
        
        // ✅ [방어 로직 2] 200이 아니거나 JSON이 아니면 오류 처리
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
            const recs: Rec[] = data.recommendations.map((rec: any, index: number) => ({
                id: rec.id,
                image: `${API_BASE_URL}/api/images/${rec.image_path.split(/\\|\//).pop()}`, 
                title: `${itemToRecommend.name} 아이템과 유사`,
                items: [rec.name, rec.category],
                score: Math.round((1.0 - rec.distance) * 100), 
                reason: `유사도 점수: ${(1.0 - rec.distance).toFixed(2)}`,
            }));
            
            setRecommendations(recs);
            Alert.alert('추천 완료', `${itemToRecommend.name}와 유사한 아이템 ${recs.length}개를 찾았습니다.`);
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


  // 🔑 사용자 정보 로드 및 초기 데이터 fetch
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
  
  // 새로 추천 버튼 클릭 시
  async function onRefresh() {
    await fetchRecommendation();
  }

  // BottomNavBar의 screen 이름을 NavigationStep으로 매핑하는 함수를 추가합니다.
  const handleNavigation = (screen: string) => {
    console.log('========================================');
    console.log('🔔 네비게이션 클릭!');
    console.log('전달받은 screen 값:', screen);
    console.log('screen 타입:', typeof screen);
    console.log('========================================');
    
    onNavigate(screen as NavigationStep);
  };

  const HeaderRightAction = (
    <Pressable onPress={onRefresh} style={[styles.refreshBtn, (loading || recommending || !baseItem) && styles.refreshBtnDisabled]} disabled={loading || recommending || !baseItem}>
      {(loading || recommending) ? <ActivityIndicator color="#FFF" size="small" /> : <Zap size={16} color="#FFF" />}
      <Text style={styles.refreshText}>{(loading || recommending) ? '처리중...' : 'AI 추천'}</Text>
    </Pressable>
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

      <ScrollView contentContainerStyle={styles.screenPad}>
        
        {/* A. 현재 날씨 카드 (임시 데이터) */}
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
                                // ✅ 아이템 선택 시 baseItemId 변경 및 추천 목록 초기화
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
              {/* 전체 */}
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
              
              {/* 상의 */}
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
              
              {/* 하의 */}
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
        
        {/* C. 상황별 선택 그리드 */}
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

        {/* D. 추천 결과 목록 */}
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
            // 아이템이 아예 없을 때
            <View style={styles.emptyArea}>
                <Text style={styles.emptyText}>아이템이 없어서 추천을 할 수 없습니다.</Text>
            </View>
          ) : recommendations.length === 0 && !recommending ? (
             // 아이템은 있으나 추천 전일 때
             <View style={styles.emptyArea}>
                <Text style={styles.emptyText}>기준 아이템을 선택하고 'AI 추천' 버튼을 눌러보세요.</Text>
            </View>
          ) : (
            // 추천 결과가 있을 때
            <View style={{ gap: 16, marginTop: 16 }}>
              {recommendations.map((rec, index) => (
                <View key={rec.id} style={styles.cardRow}>
                  <View style={styles.thumbBig}>
                    <Image source={{ uri: rec.image }} style={styles.thumbImg} />
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

      {/* BottomNavBar는 SafeAreaView 직계 자식으로 그대로 둡니다. */}
      <BottomNavBar 
        activeScreen="style-analysis"  // ✅ 수정!
        onNavigate={handleNavigation} 
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#FFFFFF' },
  // ✅ [수정] 오버레이 스타일: 네비게이션 바를 막지 않도록 bottom 조정
  overlay: {
    ...StyleSheet.absoluteFillObject,
    top: APP_HEADER_HEIGHT, // AppHeader 아래부터 시작
    bottom: 0, // 네비게이션 바를 덮도록 전체를 덮음 (zIndex로 해결)
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
  
  // ✅ [추가] 기준 아이템 목록 스타일
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
      borderColor: '#111', // 선택 시 진하게 표시
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
  
  // 로딩/빈 영역 스타일
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
  // ✅ [추가] 로딩 중 버튼 스타일
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
    elevation: 2,
    shadowColor: '#000',
    shadowOpacity: 0.06,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 4 },
    borderWidth: 1.5,
    borderColor: '#F3F4F6'
  },
  thumbBig: { width: 96, height: 'auto', backgroundColor: '#EEE' },
  thumbImg: { width: '100%', height: '100%', resizeMode: 'cover' },
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
});