/**
 * 꼬까옷 앱 설정
 * API URL을 여기서 중앙 관리합니다
 */

// 환경변수에서 읽거나 기본값 사용
export const API_URL = 
  process.env.REACT_APP_API_URL || 
  process.env.EXPO_PUBLIC_API_URL || 
  'http://15.165.88.97:4000';  // AWS 서버

// 이미지 URL 생성 헬퍼
export const getImageUrl = (path: string) => {
  if (!path) return '';
  
  // 이미 전체 URL이면 그대로 반환
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }
  
  // API 경로가 아니면 그대로 반환
  if (!path.startsWith('/api/')) {
    return path;
  }
  
  // API 경로를 전체 URL로 변환
  return `${API_URL}${path}`;
};

// 설정 로깅 (개발 시에만)
if (__DEV__) {
  console.log('🔧 앱 설정:');
  console.log('  API_URL:', API_URL);
}

export default {
  API_URL,
  getImageUrl,
};

