<template>
  <div class="skeleton" :class="[`skeleton--${variant}`, { 'skeleton--animated': animated }]"></div>
</template>

<script setup lang="ts">
interface Props {
  variant?: 'text' | 'circular' | 'rectangular' | 'rounded';
  animated?: boolean;
}

withDefaults(defineProps<Props>(), {
  variant: 'text',
  animated: true,
});
</script>

<style scoped>
.skeleton {
  background: linear-gradient(
    90deg,
    var(--color-bg-subtle) 0%,
    var(--color-bg-elevated) 50%,
    var(--color-bg-subtle) 100%
  );
  background-size: 200% 100%;
  border-radius: var(--radius-md);
}

.skeleton--text {
  height: 1rem;
  width: 100%;
}

.skeleton--circular {
  border-radius: 50%;
}

.skeleton--rectangular {
  border-radius: var(--radius-sm);
}

.skeleton--rounded {
  border-radius: var(--radius-lg);
}

.skeleton--animated {
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>
