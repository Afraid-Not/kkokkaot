// components/figma/LLMChatScreen.tsx
import React, { useState, useEffect, useCallback } from 'react';
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
  MessageCircle,
  Send,
  X,
  ArrowLeft,
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

type ChatMessage = {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
};

type WardrobeItem = {
  id: number;
  name: string;
  brand: string;
  category: string;
  color: string;
  fit: string;
  materials: string[];
  image: string;
  top_category?: string;
  bottom_category?: string;
  outer_category?: string;
  dress_category?: string;
  top_image?: string;
  bottom_image?: string;
  outer_image?: string;
  dress_image?: string;
  has_top?: boolean;
  has_bottom?: boolean;
  has_outer?: boolean;
  has_dress?: boolean;
};

export default function LLMChatScreen({
  onBack,
  onNavigate,
}: {
  onBack: () => void;
  onNavigate: (step: NavigationStep) => void;
}) {
  const [userId, setUserId] = useState<number | null>(null);
  const [wardrobeItems, setWardrobeItems] = useState<WardrobeItem[]>([]);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [chatRecommendations, setChatRecommendations] = useState<WardrobeItem[]>([]);

  // 사용자 ID 불러오기
  useEffect(() => {
    const loadUserId = async () => {
      try {
        const userData = await AsyncStorage.getItem('@kko/user');
        if (userData) {
          const user = JSON.parse(userData);
          setUserId(user.id);
        }
      } catch (error) {
        console.error('사용자 ID 로드 실패:', error);
      }
    };
    loadUserId();
  }, []);

  // 옷장 데이터 불러오기
  const fetchWardrobe = useCallback(async () => {
    if (!userId) return;
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/wardrobe/${userId}?include_defaults=false`);
      if (response.ok) {
        const data = await response.json();
        console.log('✅ 옷장 데이터 로드 성공:', data.items.length, '개');
        
        // 중복 제거
        const uniqueItems = data.items.filter((item: WardrobeItem, index: number, self: WardrobeItem[]) => 
          index === self.findIndex((t: WardrobeItem) => t.id === item.id)
        );
        
        setWardrobeItems(uniqueItems);
      } else {
        console.error('❌ 옷장 데이터 로드 실패:', response.status);
      }
    } catch (error) {
      console.error('❌ 옷장 데이터 로드 실패:', error);
    }
  }, [userId]);

  useEffect(() => {
    if (userId) {
      fetchWardrobe();
    }
  }, [userId, fetchWardrobe]);

  // LLM 채팅 요청
  const sendChatMessage = async () => {
    if (!chatInput.trim() || !userId || chatLoading) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: chatInput.trim(),
      timestamp: new Date(),
    };

    setChatMessages(prev => [...prev, userMessage]);
    setChatInput('');
    setChatLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/llm-chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          message: userMessage.content,
          wardrobe_items: wardrobeItems,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        
        const assistantMessage: ChatMessage = {
          role: 'assistant',
          content: data.response,
          timestamp: new Date(),
        };

        setChatMessages(prev => [...prev, assistantMessage]);
        
        if (data.recommendations && data.recommendations.length > 0) {
          setChatRecommendations(data.recommendations);
        }
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      console.error('❌ LLM 채팅 실패:', error);
      Alert.alert('오류', 'AI와의 대화 중 오류가 발생했습니다.');
      
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: '죄송합니다. 일시적인 오류가 발생했습니다. 다시 시도해주세요.',
        timestamp: new Date(),
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setChatLoading(false);
    }
  };

  // 초기 인사 메시지
  useEffect(() => {
    if (wardrobeItems.length > 0 && chatMessages.length === 0) {
      const welcomeMessage: ChatMessage = {
        role: 'assistant',
        content: `안녕하세요! 저는 당신의 패션 스타일리스트 AI입니다. 옷장에 ${wardrobeItems.length}개의 아이템이 있네요. 어떤 스타일링을 도와드릴까요?`,
        timestamp: new Date(),
      };
      setChatMessages([welcomeMessage]);
    }
  }, [wardrobeItems, chatMessages.length]);

  return (
    <SafeAreaView style={styles.safe}>
      <AppHeader
        title="AI 스타일리스트"
        onBack={onBack}
        rightComponent={
          <Pressable style={styles.headerBtn}>
            <MessageCircle size={20} color="#111" />
          </Pressable>
        }
      />
      
      <KeyboardAvoidingView 
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 20}
      >
        {/* 채팅 메시지 영역 */}
        <ScrollView 
          style={styles.chatArea}
          contentContainerStyle={styles.chatContent}
          showsVerticalScrollIndicator={false}
        >
          {chatMessages.map((message, index) => (
            <View
              key={index}
              style={[
                styles.messageContainer,
                message.role === 'user' ? styles.userMessage : styles.assistantMessage,
              ]}
            >
              <Text style={[
                styles.messageText,
                message.role === 'user' ? styles.userMessageText : styles.assistantMessageText,
              ]}>
                {message.content}
              </Text>
              <Text style={styles.messageTime}>
                {message.timestamp.toLocaleTimeString('ko-KR', { 
                  hour: '2-digit', 
                  minute: '2-digit' 
                })}
              </Text>
            </View>
          ))}
          
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

        {/* 입력 영역 */}
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.textInput}
            placeholder="AI에게 패션 조언을 요청해보세요..."
            value={chatInput}
            onChangeText={setChatInput}
            multiline
            maxLength={500}
            placeholderTextColor="#9CA3AF"
          />
          <Pressable
            style={[styles.sendButton, (!chatInput.trim() || chatLoading) && styles.sendButtonDisabled]}
            onPress={sendChatMessage}
            disabled={!chatInput.trim() || chatLoading}
          >
            {chatLoading ? (
              <ActivityIndicator size="small" color="#FFF" />
            ) : (
              <Send size={20} color="#FFF" />
            )}
          </Pressable>
        </View>
      </KeyboardAvoidingView>

      <BottomNavBar activeScreen="llm-chat" onNavigate={onNavigate} />
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
    paddingHorizontal: 16,
  },
  headerBtn: {
    padding: 8,
  },
  chatArea: {
    flex: 1,
    marginTop: 16,
  },
  chatContent: {
    paddingBottom: 16,
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
    backgroundColor: '#FFF',
    borderRadius: 18,
    borderBottomLeftRadius: 4,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
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
    backgroundColor: '#FFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  recommendationsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111',
    marginBottom: 12,
  },
  recommendationsList: {
    flexDirection: 'row',
    gap: 12,
  },
  recommendationCard: {
    width: 80,
    alignItems: 'center',
  },
  recommendationImage: {
    width: 80,
    height: 100,
    borderRadius: 8,
    backgroundColor: '#F3F4F6',
  },
  recommendationName: {
    fontSize: 12,
    color: '#6B7280',
    textAlign: 'center',
    marginTop: 8,
    lineHeight: 16,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    backgroundColor: '#FFF',
    borderRadius: 24,
    paddingHorizontal: 16,
    paddingVertical: 12,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    gap: 12,
  },
  textInput: {
    flex: 1,
    fontSize: 14,
    color: '#111',
    maxHeight: 100,
    minHeight: 20,
  },
  sendButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#111',
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: '#D1D5DB',
  },
});
