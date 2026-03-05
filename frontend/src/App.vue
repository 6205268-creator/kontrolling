<script setup lang="ts">
import { Toaster } from 'vue-sonner';
</script>

<template>
  <router-view />
  <Toaster
    rich-colors
    theme="system"
    position="top-right"
    :duration="4000"
    :visible-toasts="5"
  />
</template>

<style>
/* Global styles in style.css */
</style>
