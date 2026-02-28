/**
 * Structured error information for display
 */
export interface ApiErrorInfo {
  /** Short summary (e.g., "Failed to load data") */
  summary: string;
  /** Detailed description (e.g., status code, response body) */
  details: string;
}

/**
 * Format API error into user-friendly message with summary and details
 */
export function formatApiError(
  error: unknown,
  defaultSummary: string = 'An error occurred'
): ApiErrorInfo {
  // Axios error with response
  if (error && typeof error === 'object' && 'response' in error) {
    const axiosError = error as {
      response?: {
        status?: number;
        data?: {
          detail?: string;
          message?: string;
          error?: string;
          [key: string]: unknown;
        };
      };
      message?: string;
      code?: string;
    };

    const status = axiosError.response?.status;
    const data = axiosError.response?.data;

    // Get detail from response
    const detail =
      data?.detail ??
      data?.message ??
      data?.error ??
      (typeof data === 'string' ? data : null);

    // Build summary based on status code
    let summary = defaultSummary;
    if (status) {
      summary = getStatusCodeSummary(status);
    } else if (axiosError.code === 'ECONNREFUSED') {
      summary = 'Server unavailable';
    } else if (axiosError.code === 'NETWORK_ERROR') {
      summary = 'Network error';
    }

    // Build details
    let details = '';
    if (status) {
      details = `HTTP ${status}`;
    }
    if (detail) {
      details = details ? `${details}: ${detail}` : String(detail);
    }
    if (!details && axiosError.message) {
      details = axiosError.message;
    }
    if (!details) {
      details = 'Unknown error';
    }

    return { summary, details };
  }

  // Network or other error without response
  if (error instanceof Error) {
    return {
      summary: getNetworkErrorSummary(error.message),
      details: error.message,
    };
  }

  // Fallback
  return {
    summary: defaultSummary,
    details: String(error ?? 'Unknown error'),
  };
}

/**
 * Get user-friendly summary based on HTTP status code
 */
function getStatusCodeSummary(status: number): string {
  switch (status) {
    case 400:
      return 'Invalid request';
    case 401:
      return 'Authentication required';
    case 403:
      return 'Access denied';
    case 404:
      return 'Not found';
    case 409:
      return 'Conflict';
    case 422:
      return 'Validation error';
    case 500:
      return 'Server error';
    case 502:
      return 'Bad gateway';
    case 503:
      return 'Service unavailable';
    default:
      if (status >= 400 && status < 500) {
        return 'Client error';
      }
      if (status >= 500) {
        return 'Server error';
      }
      return 'Request failed';
  }
}

/**
 * Get summary for network-level errors
 */
function getNetworkErrorSummary(message: string): string {
  if (message.includes('Network Error') || message.includes('network')) {
    return 'Network error';
  }
  if (message.includes('timeout')) {
    return 'Request timeout';
  }
  if (message.includes('ECONNREFUSED')) {
    return 'Server unavailable';
  }
  return 'Connection error';
}
