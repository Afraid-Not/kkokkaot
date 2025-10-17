// App.tsx
import React, { useState } from 'react';
import { Alert, StatusBar, Platform } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import BodyPhotoSetup from './components/figma/BodyPhotoSetup';
import DailyOutfitRecommendation from './components/figma/DailyOutfitRecommendation';
import HomeScreen from './components/figma/homescreen';
import ShoppingRecommendations from './components/figma/ShoppingRecommendations';
import SplashScreen from './components/figma/SplashScreen';
import StyleAnalysisDetail from './components/figma/StyleAnalysisDetail';
import TodayCurationDetail from './components/figma/TodayCurationDetail';
import WardrobeManagement from './components/figma/WardrobeManagement';
import SignupScreen from './components/figma/SignupScreen';
import LoginScreen from './components/figma/LoginScreen';
import MyInfoScreen from './components/figma/MyInfoScreen';
import SettingsScreen from './components/figma/SettingsScreen';
import NotificationsScreen from './components/figma/NotificationsScreen';
import SupportScreen from './components/figma/SupportScreen';
import LLMChatScreen from './components/figma/LLMChatScreen';
import AsyncStorage from '@react-native-async-storage/async-storage';

export type MainScreen =
  | 'home'
  | 'wardrobe-management'
  | 'style-analysis'
  | 'virtual-fitting'
  | 'shopping'
  | 'today-curation'
  | 'daily-outfit'
  | 'recent-styling'
  | 'blocked-outfits'
  | 'myinfo'
  | 'settings'
  | 'notifications'
  | 'support'
  | 'llm-chat';

type Screen =
  | 'splash'
  | 'login'
  | 'signup'
  | 'body-photo-setup'
  | 'main';

export default function App() {
  const [screen, setScreen] = useState<Screen>('splash');
  const [mainScreen, setMainScreen] = useState<MainScreen>('home');
  const [userName, setUserName] = useState('');

  const navigate = (target: MainScreen) => {
    // 'daily-outfit'은 이제 분석 화면으로 사용됩니다.
    // BottomNavBar에서 'Analysis'를 누르면 'daily-outfit'으로 이동합니다.
    if (Platform.OS === 'web' && (target === 'virtual-fitting' || target === 'recent-styling' || target === 'blocked-outfits')) {
        Alert.alert("준비중", "해당 기능은 현재 준비중입니다.");
        return;
    }
    setMainScreen(target);
  };

  const handleLoginSuccess = async (name: string) => {
    setUserName(name);
    // 서버에서 받은 실제 사용자 정보를 사용 (LoginScreen에서 이미 저장됨)
    setScreen('main');
    setMainScreen('home');
  };

  const handleLoginFail = () => {
    Alert.alert(
      "로그인 실패",
      "회원가입 하시겠어요?",
      [
        { text: "나중에", style: "cancel" },
        { text: "회원가입", onPress: () => setScreen('signup') }
      ]
    );
  };

  const handleSignupSuccess = async (data: { name: string }) => {
    console.log('🎉 App.tsx - handleSignupSuccess 호출됨:', data);
    setUserName(data.name);
    // 회원가입 시에는 임시 ID 사용 (실제 서버 응답이 없으므로)
    await AsyncStorage.setItem(
      '@kko/user',
      JSON.stringify({ id: 'local-user', name: data.name, email: `${data.name}@local` })
    );
    setScreen('main');
    setMainScreen('home');
    console.log('✅ 화면 전환 완료: main/home');
  };
  
  const handleLogout = () => {
    setUserName('');
    setScreen('login');
    setMainScreen('home');
  };

  const renderScreen = () => {
  switch (screen) {
    case 'splash':
      return <SplashScreen onGetStarted={() => setScreen('login')} />;
    case 'login':
      return (
        <LoginScreen
          onLoginSuccess={handleLoginSuccess}
          onLoginFail={handleLoginFail}
          onNavigateToSignup={() => setScreen('signup')}
        />
      );
    case 'signup':
      return (
        <SignupScreen
          onSignupSuccess={handleSignupSuccess}
          onBackToLogin={() => setScreen('login')}
        />
      );
    case 'body-photo-setup':
      return (
        <BodyPhotoSetup
          onBack={() => setScreen('signup')}
          onComplete={() => setScreen('main')}
        />
      );

    case 'main':
      switch (mainScreen) {
        case 'home':
          return <HomeScreen userName={userName} onNavigate={navigate} onLogout={handleLogout} />;
        case 'wardrobe-management':
          return <WardrobeManagement onBack={() => navigate('home')} onNavigate={navigate} />;

        case 'style-analysis':
          return <DailyOutfitRecommendation onBack={() => navigate('home')} onNavigate={navigate} />;

        case 'shopping':
          return <ShoppingRecommendations onBack={() => navigate('home')} onNavigate={navigate} />;

        case 'today-curation':
          return <TodayCurationDetail onBack={() => navigate('home')} onNavigate={navigate} />;

        case 'daily-outfit':
          return <DailyOutfitRecommendation onBack={() => navigate('home')} onNavigate={navigate} />;

        // ✅ 여기 네 개를 'default' 위에 추가
        case 'myinfo':
          return <MyInfoScreen onBack={() => navigate('home')} />;
        case 'settings':
          return <SettingsScreen onBack={() => navigate('home')} />;
        case 'notifications':
          return <NotificationsScreen onBack={() => navigate('home')} />;
        case 'support':
          return <SupportScreen onBack={() => navigate('home')} />;
        case 'llm-chat':
          return <LLMChatScreen onBack={() => navigate('home')} onNavigate={navigate} />;
        default:
          return <HomeScreen userName={userName} onNavigate={navigate} onLogout={handleLogout} />;
      }

    default:
      return null;
  }
};


  return (
    <SafeAreaProvider>
      <StatusBar barStyle="dark-content" backgroundColor="#FFFFFF" />
      {renderScreen()}
    </SafeAreaProvider>
  );
}
