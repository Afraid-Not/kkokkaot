import React, { useState, useRef } from 'react';
import { 
  View, 
  Text, 
  TextInput, 
  Pressable, 
  StyleSheet, 
  Alert, 
  ActivityIndicator,
  TextInput as RNTextInput 
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

export type LoginScreenProps = {
  onLoginSuccess: (name: string) => void;
  onLoginFail: () => void;
  onNavigateToSignup: () => void;
};

// 정규식 정의
const EMAIL_REGEX = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
const PASSWORD_REGEX = /^(?=.*[a-zA-Z])(?=.*[0-9])(?=.*[!@#$%^&*()_+])[a-zA-Z0-9!@#$%^&*()_+]{8,20}$/;

const API_BASE_URL = 'https://loyd-extemporaneous-annalise.ngrok-free.dev';
// const API_BASE_URL = 'http://10.0.2.2:4000';

export default function LoginScreen({
  onLoginSuccess,
  onLoginFail,
  onNavigateToSignup,
}: LoginScreenProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const passwordInputRef = useRef<RNTextInput>(null);

  // 이메일 입력 처리 - 한글 입력 방지
  const handleEmailChange = (text: string) => {
    const cleanedValue = text.replace(/[ㄱ-ㅎ|가-힣]/g, '');
    setEmail(cleanedValue);
  };

  const handleLogin = async () => {
    console.log('\n========================================');
    console.log('🔑 로그인 시작');
    console.log('========================================');

    // 1. 빈 값 체크
    if (!email || !password) {
      Alert.alert("오류", "이메일과 비밀번호를 모두 입력해주세요.");
      return;
    }

    // 2. 이메일 유효성 검사 (선택사항 - 간단히 하려면 주석 처리)
    /*
    if (!EMAIL_REGEX.test(email)) {
      Alert.alert("유효성 오류", "유효한 이메일 형식으로 입력해주세요.");
      return;
    }
    */

    // 3. 비밀번호 유효성 검사 (선택사항 - 간단히 하려면 주석 처리)
    /*
    if (!PASSWORD_REGEX.test(password)) {
      Alert.alert("유효성 오류", "비밀번호는 8~20자 이내이며, 영문, 숫자, 특수문자를 각각 1개 이상 포함해야 합니다.");
      return;
    }
    */
    
    setLoading(true);

    try {
      console.log('📤 로그인 요청:', email);

      // ✅ FormData로 전송 (백엔드 요구사항)
      const formData = new FormData();
      formData.append('email', email);
      formData.append('password', password);

      const response = await fetch(`${API_BASE_URL}/api/login`, {
        method: 'POST',
        body: formData,
      });

      console.log('📥 응답 상태:', response.status, response.statusText);

      const result = await response.json();
      console.log('📦 로그인 응답:', result);

      if (result.success) {
        // ✅ AsyncStorage에 사용자 정보 저장
        await AsyncStorage.setItem('user', JSON.stringify(result.user));
        console.log('✅ 사용자 정보 저장 완료:', result.user);
        console.log('========================================\n');

        // 로그인 성공
        onLoginSuccess(result.user.name);
      } else {
        console.error('❌ 로그인 실패:', result.message);
        console.log('========================================\n');

        Alert.alert("로그인 실패", result.message || "로그인에 실패했습니다.");
        
        // 회원가입 유도
        if (result.message.includes('찾을 수 없습니다')) {
          onLoginFail();
        }
      }
    } catch (error) {
      console.error('❌ 로그인 오류:', error);
      console.log('========================================\n');

      Alert.alert(
        "네트워크 오류", 
        `서버와 연결할 수 없습니다.\n\n[확인 사항]\n1. 백엔드 서버가 실행 중인가요?\n2. ngrok 주소: ${API_BASE_URL}`
      );
      onLoginFail();
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={[styles.container, { backgroundColor: '#000' }]}> 
      <Text style={styles.title}>로그인</Text>
      
      <TextInput
        style={styles.input}
        placeholder="이메일"
        placeholderTextColor="#6B7280"
        value={email}
        onChangeText={handleEmailChange}
        keyboardType="email-address"
        autoCapitalize="none"
        autoCorrect={false}
        returnKeyType="next"
        onSubmitEditing={() => passwordInputRef.current?.focus()}
      />
      
      <TextInput
        ref={passwordInputRef}
        style={styles.input}
        placeholder="비밀번호"
        placeholderTextColor="#6B7280"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
        returnKeyType="done"
        onSubmitEditing={handleLogin}
      />
      
      <Pressable 
        style={[styles.button, loading && { opacity: 0.6 }]} 
        onPress={handleLogin} 
        disabled={loading}
      >
        {loading ? (
          <ActivityIndicator color="#FFF" />
        ) : (
          <Text style={styles.buttonText}>로그인</Text>
        )}
      </Pressable>
      
      <Pressable style={styles.linkButton} onPress={onNavigateToSignup}>
        <Text style={styles.linkButtonText}>계정이 없으신가요? 회원가입</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', padding: 20 }, 
  title: { 
    fontSize: 28, 
    fontWeight: 'bold', 
    textAlign: 'center', 
    marginBottom: 24, 
    color: '#FFF' 
  }, 
  input: { 
    backgroundColor: '#F3F4F6', 
    padding: 12, 
    borderRadius: 8, 
    fontSize: 16, 
    marginBottom: 16,
    color: '#111'
  },
  button: { 
    backgroundColor: '#111', 
    padding: 16, 
    borderRadius: 8, 
    alignItems: 'center' 
  },
  buttonText: { color: '#FFF', fontWeight: 'bold', fontSize: 16 },
  linkButton: { marginTop: 20, alignItems: 'center' },
  linkButtonText: { color: '#D1D5DB', fontSize: 14 },
});