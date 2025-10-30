// 꼬까옷 API 클라이언트
import axios, { AxiosError } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

// API URL (환경변수 또는 기본값)
const API_URL = process.env.REACT_APP_API_URL || 'http://192.168.56.1:4000';

console.log('🌐 API URL:', API_URL);

// Axios 인스턴스 생성
const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 30000, // 30초 타임아웃
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터 (로그 및 인증 토큰 추가)
apiClient.interceptors.request.use(
  async (config) => {
    console.log(`📤 API 요청: ${config.method?.toUpperCase()} ${config.url}`);
    
    // 인증 토큰이 있으면 헤더에 추가 (나중에 JWT 구현 시)
    try {
      const token = await AsyncStorage.getItem('@kko/token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (error) {
      console.warn('토큰 로드 실패:', error);
    }
    
    return config;
  },
  (error) => {
    console.error('❌ 요청 인터셉터 오류:', error);
    return Promise.reject(error);
  }
);

// 응답 인터셉터 (로그 및 에러 핸들링)
apiClient.interceptors.response.use(
  (response) => {
    console.log(`✅ API 응답: ${response.config.url} - ${response.status}`);
    return response;
  },
  (error: AxiosError) => {
    if (error.response) {
      // 서버가 응답했지만 에러 코드 반환
      console.error(`❌ API 에러 (${error.response.status}):`, error.response.data);
    } else if (error.request) {
      // 요청은 보냈지만 응답 없음
      console.error('❌ 서버 응답 없음:', error.message);
    } else {
      // 요청 설정 중 에러
      console.error('❌ 요청 설정 오류:', error.message);
    }
    return Promise.reject(error);
  }
);

// ===========================
// 인증 API
// ===========================

export interface SignupData {
  name: string;
  email: string;
  password: string;
  ageGroup?: number;
  stylePreferences?: string[];
}

export interface LoginData {
  email: string;
  password: string;
}

export interface UserInfo {
  user_id: number;
  name: string;
  email: string;
}

export const signup = async (data: SignupData) => {
  const response = await apiClient.post('/api/signup', data);
  return response.data;
};

export const login = async (data: LoginData) => {
  const response = await apiClient.post('/api/login', data);
  
  // 로그인 성공 시 사용자 정보 저장
  if (response.data.success && response.data.user) {
    await AsyncStorage.setItem('@kko/user', JSON.stringify(response.data.user));
  }
  
  return response.data;
};

export const logout = async () => {
  await AsyncStorage.removeItem('@kko/user');
  await AsyncStorage.removeItem('@kko/token');
};

export const getCurrentUser = async (): Promise<UserInfo | null> => {
  try {
    const userJson = await AsyncStorage.getItem('@kko/user');
    return userJson ? JSON.parse(userJson) : null;
  } catch (error) {
    console.error('사용자 정보 로드 실패:', error);
    return null;
  }
};

// ===========================
// 옷장 API
// ===========================

export const uploadWardrobeItem = async (userId: number, imageFile: any) => {
  const formData = new FormData();
  formData.append('user_id', userId.toString());
  formData.append('file', imageFile);

  const response = await apiClient.post('/api/wardrobe/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getWardrobe = async (userId: number, includeDefaults: boolean = true) => {
  const response = await apiClient.get(`/api/wardrobe/${userId}`, {
    params: { include_defaults: includeDefaults },
  });
  return response.data;
};

export const getWardrobeSeparated = async (userId: number) => {
  const response = await apiClient.get(`/api/wardrobe/separated/${userId}`);
  return response.data;
};

export const deleteWardrobeItem = async (itemId: number) => {
  const response = await apiClient.delete(`/api/wardrobe/${itemId}`);
  return response.data;
};

export const getWardrobeItemDetail = async (itemId: number) => {
  const response = await apiClient.get(`/api/wardrobe/item/${itemId}`);
  return response.data;
};

// ===========================
// 추천 API
// ===========================

export const getDefaultRecommendations = async (userId: number) => {
  const response = await apiClient.get(`/api/recommendations/default/${userId}`);
  return response.data;
};

export const getAdvancedRecommendations = async (
  itemId: number,
  userId?: number,
  nResults: number = 10
) => {
  const response = await apiClient.get(`/api/recommendations/advanced/${itemId}`, {
    params: { user_id: userId, n_results: nResults },
  });
  return response.data;
};

// ===========================
// LLM 챗봇 API
// ===========================

export interface ChatMessage {
  user_id: number;
  message: string;
  selected_items?: number[];
}

export const chatRecommend = async (data: ChatMessage) => {
  const formData = new FormData();
  formData.append('user_id', data.user_id.toString());
  formData.append('message', data.message);
  
  if (data.selected_items && data.selected_items.length > 0) {
    formData.append('selected_items', JSON.stringify(data.selected_items));
  }

  const response = await apiClient.post('/api/chat/recommend', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const chatUploadImage = async (userId: number, imageFile: any) => {
  const formData = new FormData();
  formData.append('user_id', userId.toString());
  formData.append('image', imageFile);

  const response = await apiClient.post('/api/chat/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const resetChatHistory = async (userId: number) => {
  const formData = new FormData();
  formData.append('user_id', userId.toString());

  const response = await apiClient.post('/api/chat/reset', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// ===========================
// 날씨 API
// ===========================

export interface WeatherData {
  temperature: number;
  feels_like: number;
  weather: string;
  description: string;
  icon: string;
  style_tip: string;
  city: string;
  date: string;
}

export const getWeather = async (
  city: string = 'Seoul',
  lat?: number,
  lon?: number
): Promise<WeatherData> => {
  const params: any = { city };
  if (lat !== undefined && lon !== undefined) {
    params.lat = lat;
    params.lon = lon;
  }

  const response = await apiClient.get('/api/weather', { params });
  return response.data;
};

// ===========================
// 이미지 URL 생성
// ===========================

export const getImageUrl = (path: string) => {
  if (!path) return '';
  
  // 이미 전체 URL이면 그대로 반환
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }
  
  // API 경로가 아니면 그대로 반환 (로컬 파일)
  if (!path.startsWith('/api/')) {
    return path;
  }
  
  // API 경로를 전체 URL로 변환
  return `${API_URL}${path}`;
};

// ===========================
// 유틸리티
// ===========================

export const checkServerHealth = async () => {
  try {
    const response = await apiClient.get('/');
    return response.data;
  } catch (error) {
    console.error('서버 연결 실패:', error);
    return null;
  }
};

export default apiClient;
