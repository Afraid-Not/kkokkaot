import React, { useMemo, useState } from 'react';
import {
  Image,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { ArrowLeft } from 'lucide-react-native';
import AsyncStorage from '@react-native-async-storage/async-storage'; // ✅ 추가

export type SignupScreenProps = {
  onSignupSuccess: (data: { name: string }) => void;
  onBackToLogin: () => void;
};

// API URL 설정 (환경에 따라 변경)
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://192.168.56.1:4000';

const STYLE_PREFERENCES = [
  { name: '기타', image: `${API_BASE_URL}/api/represent-images/etc.jpg` },
  { name: '레트로', image: `${API_BASE_URL}/api/represent-images/retro.jpg` },
  { name: '로맨틱', image: `${API_BASE_URL}/api/represent-images/romantic.jpg` },
  { name: '리조트', image: `${API_BASE_URL}/api/represent-images/resort.jpg` },
  { name: '매니시', image: `${API_BASE_URL}/api/represent-images/manish.jpg` },
  { name: '모던', image: `${API_BASE_URL}/api/represent-images/modern.jpg` },
  { name: '밀리터리', image: `${API_BASE_URL}/api/represent-images/military.jpg` },
  { name: '섹시', image: `${API_BASE_URL}/api/represent-images/sexy.jpg` },
  { name: '소피스트케이티드', image: `${API_BASE_URL}/api/represent-images/sophisticated.jpg` },
  { name: '스트리트', image: `${API_BASE_URL}/api/represent-images/street.jpg` },
  { name: '스포티', image: `${API_BASE_URL}/api/represent-images/sporty.jpg` },
  { name: '아방가르드', image: `${API_BASE_URL}/api/represent-images/avangard.jpg` },
  { name: '오리엔탈', image: `${API_BASE_URL}/api/represent-images/oriental.jpg` },
  { name: '웨스턴', image: `${API_BASE_URL}/api/represent-images/western.jpg` },
  { name: '젠더리스', image: `${API_BASE_URL}/api/represent-images/genderless.jpg` },
  { name: '컨트리', image: `${API_BASE_URL}/api/represent-images/country.jpg` },
  { name: '클래식', image: `${API_BASE_URL}/api/represent-images/classic.jpg` },
  { name: '키치', image: `${API_BASE_URL}/api/represent-images/kitsch.jpg` },
  { name: '톰보이', image: `${API_BASE_URL}/api/represent-images/tomboy.jpg` },
  { name: '펑크', image: `${API_BASE_URL}/api/represent-images/funk.jpg` },
  { name: '페미닌', image: `${API_BASE_URL}/api/represent-images/feminin.jpg` },
  { name: '프레피', image: `${API_BASE_URL}/api/represent-images/preppy.jpg` },
  { name: '히피', image: `${API_BASE_URL}/api/represent-images/hippy.jpg` },
  { name: '힙합', image: `${API_BASE_URL}/api/represent-images/hiphop.jpg` },
];

// 회원가입 API URL
const API_URL = `${API_BASE_URL}/api/signup`;

export default function SignupScreen({ onSignupSuccess, onBackToLogin }: SignupScreenProps) {
  const [step, setStep] = useState(1);
  const totalSteps = 3;

  const [form, setForm] = useState({ 
    name: '', 
    email: '', 
    pw: '', 
    ageGroup: null as number | null, 
    stylePreferences: [] as string[] 
  });
  const [loading, setLoading] = useState(false);

  const progress = useMemo(() => (step / totalSteps) * 100, [step]);

  const next = () => (step < totalSteps) ? setStep(s => s + 1) : handleSubmit();
  const back = () => step > 1 && setStep(s => s - 1);

  const toggleStyle = (name: string) => setForm(p => ({ 
    ...p, 
    stylePreferences: p.stylePreferences.includes(name) 
      ? p.stylePreferences.filter(v => v !== name) 
      : [...p.stylePreferences, name] 
  }));

  const handleSubmit = async () => {
    console.log('\n========================================');
    console.log('📝 회원가입 시작');
    console.log('========================================');
    
    setLoading(true);
    
    try {
      console.log('📤 전송 데이터:', {
        name: form.name,
        email: form.email,
        password: '***',
        ageGroup: form.ageGroup,
        stylePreferences: form.stylePreferences,
      });

      // FormData로 전송 (백엔드와 일치)
      const formData = new FormData();
      formData.append('name', form.name);
      formData.append('email', form.email);
      formData.append('password', form.pw);
      formData.append('ageGroup', form.ageGroup?.toString() || '20');
      formData.append('stylePreferences', JSON.stringify(form.stylePreferences));

      const response = await fetch(API_URL, {
        method: 'POST',
        body: formData,  // FormData 전송 (Content-Type 자동 설정)
      });

      console.log('📥 응답 상태:', response.status, response.statusText);

      const result = await response.json();
      console.log('📦 응답 데이터:', result);

      // ✅ 성공 여부 확인
      if (result.success && result.user) {
        console.log('✅ 회원가입 성공!');
        console.log('👤 사용자 정보:', result.user);

        // ✅ AsyncStorage에 사용자 정보 저장
        try {
          await AsyncStorage.setItem('user', JSON.stringify(result.user));
          console.log('✅ AsyncStorage 저장 완료');
          
          const saved = await AsyncStorage.getItem('user');
          console.log('✅ 저장 확인:', saved);
        } catch (storageError) {
          console.error('❌ AsyncStorage 저장 실패:', storageError);
        }

        console.log('========================================\n');

        // ✅ Alert 없이 바로 화면 전환 (선택사항)
        console.log('🎉 onSignupSuccess 호출');
        onSignupSuccess({ name: result.user.name });
      } else {
        // ❌ 실패
        console.error('❌ 회원가입 실패:', result.message);
        console.log('========================================\n');
        
        Alert.alert('회원가입 실패', result.message || '다시 시도해주세요.');
      }
    } catch (error) {
      console.error('❌ 네트워크 오류:', error);
      console.log('========================================\n');
      
      Alert.alert(
        '네트워크 연결 실패',
        `회원가입 중 문제가 발생했습니다.\n\n[확인 사항]\n1. 백엔드 서버(4000 포트)가 켜져 있습니까?\n2. ngrok 주소가 유효한가요?\n\n현재 주소: ${API_URL}`
      );
    } finally {
      setLoading(false);
    }
  };

  const canProceed = useMemo(() => {
    if (step === 1) return form.name.trim().length > 0 && /@/.test(form.email) && form.pw.length > 0;
    if (step === 2) return form.ageGroup !== null;
    if (step === 3) return form.stylePreferences.length > 0;
    return false;
  }, [step, form]);

  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
        <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
          <View style={{ alignItems: 'center' }}>
            <Pressable onPress={onBackToLogin} style={styles.backBtn}>
              <ArrowLeft size={20} color="#111" />
            </Pressable>
            <Text style={styles.title}>회원가입</Text>
          </View>

          <View style={styles.progressBar}>
            <View style={[styles.progressFill, { width: `${progress}%` }]} />
          </View>
          <Text style={styles.progressText}>{step} / {totalSteps}</Text>

          <View style={styles.card}>
            {step === 1 && (
              <View style={{ gap: 12 }}>
                <Text style={styles.sectionTitle}>기본 정보를 입력해주세요</Text>
                <TextInput 
                  value={form.name} 
                  onChangeText={t => setForm(p => ({ ...p, name: t}))} 
                  placeholder="이름 (닉네임)" 
                  placeholderTextColor="#6B7280" 
                  style={styles.input} 
                />
                <TextInput 
                  value={form.email} 
                  onChangeText={t => setForm(p => ({ ...p, email: t}))} 
                  placeholder="이메일" 
                  placeholderTextColor="#6B7280" 
                  style={styles.input} 
                  keyboardType="email-address" 
                  autoCapitalize="none" 
                />
                <TextInput 
                  value={form.pw} 
                  onChangeText={t => setForm(p => ({ ...p, pw: t}))} 
                  placeholder="비밀번호 (6자 이상)" 
                  placeholderTextColor="#6B7280" 
                  style={styles.input} 
                  secureTextEntry 
                />
              </View>
            )}

            {step === 2 && (
              <View style={{ gap: 12 }}>
                <Text style={styles.sectionTitle}>나이대를 선택해주세요</Text>
                {['10대', '20대', '30대', '40대', '50대 이상'].map(age => (
                  <Pressable
                    key={age}
                    onPress={() => setForm(p => ({ ...p, ageGroup: parseInt(age) }))}
                    style={[styles.selectRow, form.ageGroup === parseInt(age) && styles.selectRowActive]}
                  >
                    <Text style={styles.selectLabel}>{age}</Text>
                    <View style={[styles.circle, form.ageGroup === parseInt(age) ? styles.circleOn : styles.circleOff]} />
                  </Pressable>
                ))}
              </View>
            )}

            {step === 3 && (
              <View style={{ gap: 16 }}>
                <Text style={styles.sectionTitle}>선호하는 스타일을 선택해주세요</Text>
                <Text style={styles.sectionSub}>
                  여러 개 선택할 수 있습니다. ({form.stylePreferences.length}개 선택)
                </Text>
                <View style={styles.grid2}>
                  {STYLE_PREFERENCES.map(s => (
                    <Pressable 
                      key={s.name} 
                      onPress={() => toggleStyle(s.name)} 
                      style={[styles.styleCard, form.stylePreferences.includes(s.name) && styles.styleCardActive]}
                    >
                      <Image source={{ uri: s.image }} style={styles.styleThumb} />
                      <View style={styles.styleOverlay} />
                      <Text style={styles.styleName}>{s.name}</Text>
                    </Pressable>
                  ))}
                </View>
              </View>
            )}

            <View style={{ flexDirection: 'row', gap: 12, marginTop: 24 }}>
              {step > 1 && (
                <Pressable onPress={back} style={styles.secondaryBtn}>
                  <Text style={styles.secondaryBtnText}>이전</Text>
                </Pressable>
              )}
              <Pressable 
                onPress={next} 
                disabled={!canProceed || loading} 
                style={[styles.primaryBtn, (!canProceed || loading) && { opacity: 0.5 }]}
              >
                {loading ? (
                  <ActivityIndicator color="#FFF" />
                ) : (
                  <Text style={styles.primaryBtnText}>
                    {step === totalSteps ? '완료' : '다음'}
                  </Text>
                )}
              </Pressable>
            </View>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F9FAFB' },
  container: { padding: 16, paddingBottom: 32, flexGrow: 1, justifyContent: 'center' },
  backBtn: { position: 'absolute', left: 0, top: 0, padding: 8 },
  title: { fontSize: 22, fontWeight: 'bold', textAlign: 'center', marginBottom: 8 },
  progressBar: { height: 4, borderRadius: 2, backgroundColor: '#E5E7EB', overflow: 'hidden', marginVertical: 8 },
  progressFill: { height: '100%', backgroundColor: '#111111' },
  progressText: { textAlign: 'center', fontSize: 11, color: '#6B7280', marginBottom: 16 },
  card: { backgroundColor: '#FFFFFF', borderRadius: 12, padding: 20, shadowColor: '#000', shadowOpacity: 0.08, shadowRadius: 16, elevation: 3 },
  sectionTitle: { fontSize: 18, fontWeight: '600', marginBottom: 4 },
  sectionSub: { fontSize: 13, color: '#6B7280', marginBottom: 12 },
  input: { backgroundColor: '#F9FAFB', borderWidth: 1, borderColor: '#E5E7EB', borderRadius: 8, padding: 12, fontSize: 14, color: '#111' },
  selectRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 12, borderWidth: 1, borderColor: '#E5E7EB', borderRadius: 8 },
  selectRowActive: { backgroundColor: '#F3F4F6', borderColor: '#111' },
  selectLabel: { fontSize: 14, color: '#111' },
  circle: { width: 20, height: 20, borderRadius: 10, borderWidth: 2, borderColor: '#D1D5DB' },
  circleOn: { backgroundColor: '#111', borderColor: '#111' },
  circleOff: {},
  grid2: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', rowGap: 12 },
  styleCard: { width: '48.5%', aspectRatio: 1, borderRadius: 8, overflow: 'hidden', justifyContent: 'flex-end', padding: 8 },
  styleCardActive: { borderWidth: 2, borderColor: '#111' },
  styleThumb: { ...StyleSheet.absoluteFillObject },
  styleOverlay: { ...StyleSheet.absoluteFillObject, backgroundColor: 'rgba(0,0,0,0.3)' },
  styleName: { color: '#FFF', fontWeight: 'bold', fontSize: 14, textShadowColor: 'rgba(0,0,0,0.5)', textShadowOffset: {width: 0, height: 1}, textShadowRadius: 2 },
  primaryBtn: { flex: 1, backgroundColor: '#111', padding: 12, borderRadius: 8, alignItems: 'center' },
  primaryBtnText: { color: '#FFF', fontWeight: '600' },
  secondaryBtn: { flex: 1, backgroundColor: '#F3F4F6', padding: 12, borderRadius: 8, alignItems: 'center' },
  secondaryBtnText: { color: '#111', fontWeight: '600' },
});