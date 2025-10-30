// 에러 핸들링 유틸리티
import { Alert, Platform } from 'react-native';
import { AxiosError } from 'axios';

export interface ApiError {
  message: string;
  code?: string;
  statusCode?: number;
  details?: any;
}

/**
 * API 에러를 사용자 친화적인 메시지로 변환
 */
export const handleApiError = (error: any): ApiError => {
  // Axios 에러인 경우
  if (error.response) {
    // 서버가 응답했지만 에러 코드 반환
    const status = error.response.status;
    const data = error.response.data;

    switch (status) {
      case 400:
        return {
          message: data.message || '잘못된 요청입니다.',
          code: 'BAD_REQUEST',
          statusCode: 400,
          details: data,
        };
      
      case 401:
        return {
          message: '인증이 필요합니다. 다시 로그인해주세요.',
          code: 'UNAUTHORIZED',
          statusCode: 401,
          details: data,
        };
      
      case 403:
        return {
          message: '접근 권한이 없습니다.',
          code: 'FORBIDDEN',
          statusCode: 403,
          details: data,
        };
      
      case 404:
        return {
          message: '요청하신 데이터를 찾을 수 없습니다.',
          code: 'NOT_FOUND',
          statusCode: 404,
          details: data,
        };
      
      case 500:
        return {
          message: '서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
          code: 'SERVER_ERROR',
          statusCode: 500,
          details: data,
        };
      
      case 503:
        return {
          message: '서버가 일시적으로 사용 불가능합니다.',
          code: 'SERVICE_UNAVAILABLE',
          statusCode: 503,
          details: data,
        };
      
      default:
        return {
          message: data.message || `오류가 발생했습니다 (${status})`,
          code: 'UNKNOWN_ERROR',
          statusCode: status,
          details: data,
        };
    }
  } else if (error.request) {
    // 요청은 보냈지만 응답 없음 (네트워크 오류)
    return {
      message: '서버에 연결할 수 없습니다. 네트워크를 확인해주세요.',
      code: 'NETWORK_ERROR',
      details: error.message,
    };
  } else {
    // 요청 설정 중 에러
    return {
      message: error.message || '알 수 없는 오류가 발생했습니다.',
      code: 'UNKNOWN_ERROR',
      details: error,
    };
  }
};

/**
 * 에러를 Alert로 표시
 */
export const showErrorAlert = (error: any, title: string = '오류') => {
  const apiError = handleApiError(error);
  
  if (Platform.OS === 'web') {
    alert(`${title}\n\n${apiError.message}`);
  } else {
    Alert.alert(title, apiError.message, [{ text: '확인' }]);
  }
};

/**
 * 성공 메시지를 Alert로 표시
 */
export const showSuccessAlert = (message: string, title: string = '성공') => {
  if (Platform.OS === 'web') {
    alert(`${title}\n\n${message}`);
  } else {
    Alert.alert(title, message, [{ text: '확인' }]);
  }
};

/**
 * 확인 다이얼로그 표시
 */
export const showConfirmDialog = (
  message: string,
  onConfirm: () => void,
  title: string = '확인',
  confirmText: string = '확인',
  cancelText: string = '취소'
): Promise<boolean> => {
  return new Promise((resolve) => {
    if (Platform.OS === 'web') {
      const confirmed = confirm(`${title}\n\n${message}`);
      if (confirmed) {
        onConfirm();
      }
      resolve(confirmed);
    } else {
      Alert.alert(
        title,
        message,
        [
          {
            text: cancelText,
            style: 'cancel',
            onPress: () => resolve(false),
          },
          {
            text: confirmText,
            onPress: () => {
              onConfirm();
              resolve(true);
            },
          },
        ],
        { cancelable: false }
      );
    }
  });
};

/**
 * 로딩 상태 관리를 위한 래퍼 함수
 */
export const withLoading = async <T>(
  asyncFn: () => Promise<T>,
  setLoading: (loading: boolean) => void,
  onError?: (error: ApiError) => void
): Promise<T | null> => {
  setLoading(true);
  
  try {
    const result = await asyncFn();
    return result;
  } catch (error) {
    const apiError = handleApiError(error);
    
    if (onError) {
      onError(apiError);
    } else {
      showErrorAlert(error);
    }
    
    return null;
  } finally {
    setLoading(false);
  }
};

/**
 * 재시도 로직이 포함된 API 호출
 */
export const retryApiCall = async <T>(
  apiCall: () => Promise<T>,
  maxRetries: number = 3,
  delayMs: number = 1000
): Promise<T> => {
  let lastError: any;
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await apiCall();
    } catch (error) {
      lastError = error;
      
      // 네트워크 오류가 아니면 재시도하지 않음
      if (error.response && error.response.status !== 503) {
        throw error;
      }
      
      // 마지막 시도가 아니면 대기 후 재시도
      if (i < maxRetries - 1) {
        console.log(`재시도 ${i + 1}/${maxRetries}...`);
        await new Promise((resolve) => setTimeout(resolve, delayMs));
      }
    }
  }
  
  throw lastError;
};

/**
 * 네트워크 연결 상태 확인
 */
export const checkNetworkConnection = async (apiUrl: string): Promise<boolean> => {
  try {
    const response = await fetch(apiUrl, {
      method: 'HEAD',
      cache: 'no-cache',
    });
    return response.ok;
  } catch (error) {
    console.error('네트워크 연결 확인 실패:', error);
    return false;
  }
};

export default {
  handleApiError,
  showErrorAlert,
  showSuccessAlert,
  showConfirmDialog,
  withLoading,
  retryApiCall,
  checkNetworkConnection,
};

