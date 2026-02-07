<template>
  <output class="gallery-stats-container" aria-live="polite">
    <div class="stats-pill">
      <div class="stat-item">
        <output class="stat-value" aria-label="Total photos">{{ totalCount }}</output>
        <span class="stat-label">{{ totalCount === 1 ? 'photo' : 'photos' }}</span>
      </div>
      <div v-if="totalCount !== visibleCount" class="separator" aria-hidden="true"></div>
      <div v-if="totalCount !== visibleCount" class="stat-item">
        <output class="stat-value">{{ visibleCount }}</output>
        <span class="stat-label">showing</span>
      </div>
    </div>
  </output>
</template>

<script setup lang="ts">
defineProps<{
  totalCount: number;
  visibleCount: number;
}>();
</script>

<style scoped>
.gallery-stats-container {
  display: flex;
  justify-content: center;
  width: 100%;
  margin-bottom: 2.5rem;
}

.stats-pill {
  display: flex;
  align-items: center;
  gap: 2rem;
  padding: 0.875rem 2.5rem;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(8px);
  border-radius: 100px;
  box-shadow:
    0 4px 6px -1px rgba(0, 0, 0, 0.02),
    0 2px 4px -1px rgba(0, 0, 0, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.5);
  transition: all 0.3s ease;
}

.stats-pill:hover {
  transform: translateY(-2px);
  box-shadow:
    0 10px 15px -3px rgba(0, 0, 0, 0.05),
    0 4px 6px -2px rgba(0, 0, 0, 0.025);
  background: rgba(255, 255, 255, 0.95);
}

.stat-item {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
}

.stat-value {
  font-family: 'Nunito', sans-serif;
  font-size: 1.25rem;
  font-weight: 800;
  color: #5a4632;
  line-height: 1;
}

.stat-label {
  font-family: 'Inter', sans-serif;
  font-size: 0.875rem;
  font-weight: 500;
  color: #7d7d7d;
  text-transform: lowercase;
  letter-spacing: 0.02em;
}

.separator {
  width: 1px;
  height: 24px;
  background: linear-gradient(to bottom, transparent, #cbd5e0, transparent);
}
</style>
