import React, { useState, useRef } from 'react';
import { 
  View, 
  Text, 
  TextInput, 
  Pressable, 
  StyleSheet, 
  Alert, 
  ActivityIndicator,
  TextInput as RNTextInput,
  ImageBackground 
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_URL as API_BASE_URL } from '../../lib/config';

export type LoginScreenProps = {
  onLoginSuccess: (name: string) => void;
  onLoginFail: () => void;
  onNavigateToSignup: () => void;
};

// 정규식 정의
const EMAIL_REGEX = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
const PASSWORD_REGEX = /^(?=.*[a-zA-Z])(?=.*[0-9])(?=.*[!@#$%^&*()_+])[a-zA-Z0-9!@#$%^&*()_+]{8,20}$/;

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
        await AsyncStorage.setItem('@kko/user', JSON.stringify(result.user));
        console.log('✅ 사용자 정보 저장 완료:', result.user);
        console.log('🔍 저장된 user_id 타입:', typeof result.user.user_id);
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
    <ImageBackground 
      source={require('../../assets/login_logo.png')}
      style={styles.container}
      resizeMode="cover"
      imageStyle={styles.backgroundImage}
    >
      <View style={styles.overlay} />
      <View style={styles.formContainer}>
        <TextInput
          style={styles.input}
          placeholder="이메일"
          placeholderTextColor="#999"
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
          placeholderTextColor="#999"
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
      
      <Text style={styles.creditText}>Curated by the 3M2C</Text>
    </ImageBackground>
  );
}

const styles = StyleSheet.create({
  container: { 
    flex: 1, 
    justifyContent: 'center',
  },
  backgroundImage: {
    transform: [{ translateX: -10 }, { scale: 1.1 }],
  },
  overlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
  },
  formContainer: {
    padding: 24,
    marginTop: 200,
  },
  input: { 
    backgroundColor: 'rgba(255, 255, 255, 0.95)', 
    padding: 16, 
    borderRadius: 12, 
    fontSize: 16, 
    marginBottom: 12,
    color: '#111',
    borderWidth: 1,
    borderColor: 'rgba(139, 115, 85, 0.3)',
  },
  button: { 
    backgroundColor: 'rgba(139, 115, 85, 0.95)', 
    padding: 18, 
    borderRadius: 12, 
    alignItems: 'center',
    marginTop: 8,
  },
  buttonText: { 
    color: '#FFF', 
    fontWeight: 'bold', 
    fontSize: 17,
    letterSpacing: 0.5,
  },
  linkButton: { 
    marginTop: 20, 
    alignItems: 'center',
    padding: 8,
  },
  linkButtonText: { 
    color: '#FFF', 
    fontSize: 15,
    fontWeight: '500',
    textShadowColor: 'rgba(0, 0, 0, 0.5)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 3,
  },
  creditText: {
    position: 'absolute',
    bottom: 20,
    left: 0,
    right: 0,
    color: 'rgba(255, 255, 255, 0.7)',
    fontSize: 12,
    textAlign: 'center',
    letterSpacing: 0.5,
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
  },
});