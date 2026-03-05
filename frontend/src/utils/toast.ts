/**
 * Toast notifications utility
 * Uses vue-sonner for beautiful toast notifications
 */
import { toast } from 'vue-sonner';

/**
 * Show success toast
 */
export function success(message: string, description?: string) {
  toast.success(message, {
    description,
    duration: 4000,
  });
}

/**
 * Show error toast
 */
export function error(message: string, description?: string) {
  toast.error(message, {
    description,
    duration: 5000,
  });
}

/**
 * Show info toast
 */
export function info(message: string, description?: string) {
  toast.info(message, {
    description,
    duration: 4000,
  });
}

/**
 * Show warning toast
 */
export function warning(message: string, description?: string) {
  toast.warning(message, {
    description,
    duration: 5000,
  });
}

/**
 * Show loading toast (returns dismiss function)
 */
export function loading(message: string, description?: string) {
  return toast.loading(message, {
    description,
  });
}

/**
 * Show promise toast (automatically shows success/error based on promise result)
 */
export function promise<T>(
  promise: Promise<T>,
  messages: {
    loading: string;
    success: string;
    error: string;
  },
  description?: string
) {
  return toast.promise(promise, {
    loading: messages.loading,
    success: (data: T) => {
      return messages.success;
    },
    error: (error: unknown) => {
      const msg = error instanceof Error ? error.message : messages.error;
      return msg;
    },
  });
}
