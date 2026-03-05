<template>
  <div class="data-table-component">
    <!-- Search and Filters -->
    <div v-if="searchable || $slots.filters" class="table-controls">
      <div class="table-controls-left">
        <slot name="filters" />
      </div>
      <div v-if="searchable" class="table-controls-right">
        <div class="search-wrapper">
          <Search class="search-icon" />
          <input
            v-model="searchQuery"
            type="text"
            class="table-search"
            :placeholder="searchPlaceholder"
          />
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th
              v-for="(column, index) in columns"
              :key="index"
              :class="{ sortable: column.sortable }"
              @click="column.sortable && sortBy(column.key)"
            >
              <div class="th-content">
                <span>{{ column.label }}</span>
                <span v-if="column.sortable" class="sort-icon">
                  <ChevronUp v-if="sortKey === column.key && sortAsc" class="sort-arrow" />
                  <ChevronDown v-else class="sort-arrow" />
                </span>
              </div>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="paginatedData.length === 0">
            <td :colspan="columns.length" class="empty">
              <div class="empty-state">
                <Inbox class="empty-icon" />
                <span>{{ emptyMessage }}</span>
              </div>
            </td>
          </tr>
          <tr
            v-for="(item, rowIndex) in paginatedData"
            :key="rowIndex"
            @click="$emit('rowClick', item)"
            :class="{ 'clickable': $attrs.onRowClick }"
          >
            <td v-for="(column, colIndex) in columns" :key="colIndex">
              <slot :name="`cell-${column.key}`" :item="item" :value="item[column.key]">
                {{ formatValue(item[column.key], column.format) }}
              </slot>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div v-if="pagination && totalPages > 1" class="pagination">
      <div class="pagination-info">
        Показано {{ startItem }}-{{ endItem }} из {{ totalItems }}
      </div>
      <div class="pagination-controls">
        <button
          class="pagination-btn"
          :disabled="currentPage === 1"
          @click="currentPage = 1"
          aria-label="Первая страница"
        >
          <ChevronsLeft class="pagination-icon" />
        </button>
        <button
          class="pagination-btn"
          :disabled="currentPage === 1"
          @click="currentPage--"
          aria-label="Предыдущая страница"
        >
          <ChevronLeft class="pagination-icon" />
        </button>
        
        <div class="pagination-pages">
          <button
            v-for="page in visiblePages"
            :key="page"
            class="pagination-page"
            :class="{ active: currentPage === page }"
            @click="currentPage = page"
          >
            {{ page }}
          </button>
        </div>

        <button
          class="pagination-btn"
          :disabled="currentPage === totalPages"
          @click="currentPage++"
          aria-label="Следующая страница"
        >
          <ChevronRight class="pagination-icon" />
        </button>
        <button
          class="pagination-btn"
          :disabled="currentPage === totalPages"
          @click="currentPage = totalPages"
          aria-label="Последняя страница"
        >
          <ChevronsRight class="pagination-icon" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import {
  Search,
  ChevronUp,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  Inbox,
} from 'lucide-vue-next';

interface Column {
  key: string;
  label: string;
  sortable?: boolean;
  format?: 'number' | 'date' | 'currency' | 'percent';
}

interface Props {
  data: unknown[];
  columns: Column[];
  searchable?: boolean;
  searchPlaceholder?: string;
  pagination?: boolean;
  pageSize?: number;
  emptyMessage?: string;
}

const props = withDefaults(defineProps<Props>(), {
  searchable: true,
  searchPlaceholder: 'Поиск...',
  pagination: true,
  pageSize: 10,
  emptyMessage: 'Нет данных',
});

const emit = defineEmits<{
  rowClick: [item: unknown];
}>();

// Search
const searchQuery = ref('');

// Sorting
const sortKey = ref<string | null>(null);
const sortAsc = ref(true);

// Pagination
const currentPage = ref(1);

// Reset page when search changes
watch(searchQuery, () => {
  currentPage.value = 1;
});

// Filtered data
const filteredData = computed(() => {
  if (!searchQuery.value) return props.data;
  
  const query = searchQuery.value.toLowerCase();
  return props.data.filter((item: Record<string, unknown>) => {
    return Object.values(item).some((value) => {
      return String(value).toLowerCase().includes(query);
    });
  });
});

// Sorted data
const sortedData = computed(() => {
  if (!sortKey.value) return filteredData.value;
  
  return [...filteredData.value].sort((a: Record<string, unknown>, b: Record<string, unknown>) => {
    const aVal = a[sortKey.value as string];
    const bVal = b[sortKey.value as string];
    
    if (aVal < bVal) return sortAsc.value ? -1 : 1;
    if (aVal > bVal) return sortAsc.value ? 1 : -1;
    return 0;
  });
});

// Paginated data
const totalPages = computed(() => {
  if (!props.pagination) return 1;
  return Math.ceil(sortedData.value.length / props.pageSize);
});

const paginatedData = computed(() => {
  if (!props.pagination) return sortedData.value;
  
  const start = (currentPage.value - 1) * props.pageSize;
  const end = start + props.pageSize;
  return sortedData.value.slice(start, end);
});

// Pagination helpers
const totalItems = computed(() => sortedData.value.length);
const startItem = computed(() => {
  if (totalItems.value === 0) return 0;
  return (currentPage.value - 1) * props.pageSize + 1;
});
const endItem = computed(() => {
  const end = currentPage.value * props.pageSize;
  return end > totalItems.value ? totalItems.value : end;
});

// Visible pages for pagination
const visiblePages = computed(() => {
  const pages: number[] = [];
  const total = totalPages.value;
  const current = currentPage.value;
  
  if (total <= 7) {
    for (let i = 1; i <= total; i++) pages.push(i);
  } else {
    if (current <= 4) {
      for (let i = 1; i <= 5; i++) pages.push(i);
      pages.push(-1); // ellipsis
      pages.push(total);
    } else if (current >= total - 3) {
      pages.push(1);
      pages.push(-1); // ellipsis
      for (let i = total - 4; i <= total; i++) pages.push(i);
    } else {
      pages.push(1);
      pages.push(-1); // ellipsis
      pages.push(current - 1);
      pages.push(current);
      pages.push(current + 1);
      pages.push(-1); // ellipsis
      pages.push(total);
    }
  }
  
  return pages.filter((p) => p !== -1);
});

// Methods
function sortBy(key: string) {
  if (sortKey.value === key) {
    sortAsc.value = !sortAsc.value;
  } else {
    sortKey.value = key;
    sortAsc.value = true;
  }
}

function formatValue(value: unknown, format?: string): string {
  if (value === null || value === undefined) return '';
  
  switch (format) {
    case 'number':
      return Number(value).toLocaleString('ru-RU');
    case 'currency':
      return Number(value).toLocaleString('ru-RU', {
        style: 'currency',
        currency: 'BYN',
      });
    case 'percent':
      return `${Number(value).toFixed(1)}%`;
    case 'date':
      return new Date(value as string).toLocaleDateString('ru-RU');
    default:
      return String(value);
  }
}
</script>

<style scoped>
.data-table-component {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
}

/* Controls */
.table-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--color-border-light);
  gap: 1rem;
  flex-wrap: wrap;
}

.table-controls-left,
.table-controls-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.search-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 0.75rem;
  width: 1rem;
  height: 1rem;
  color: var(--color-text-muted);
  pointer-events: none;
}

.table-search {
  padding: 0.5rem 0.75rem 0.5rem 2.25rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-family: var(--font-sans);
  font-size: var(--text-sm);
  color: var(--color-text);
  background: var(--color-bg-card);
  min-width: 240px;
  transition: all var(--transition-base);
}

.table-search:focus {
  outline: none;
  border-color: var(--color-border-focus);
  box-shadow: 0 0 0 3px var(--color-primary-light);
}

/* Table */
.table-wrap {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-sm);
}

.data-table th,
.data-table td {
  padding: 1rem 1.25rem;
  text-align: left;
  border-bottom: 1px solid var(--color-border-light);
}

.data-table th {
  font-weight: var(--font-semibold);
  color: var(--color-text-muted);
  background: var(--color-bg-subtle);
  text-transform: none;
  letter-spacing: 0;
  font-size: var(--text-xs);
  white-space: nowrap;
  user-select: none;
}

.data-table th.sortable {
  cursor: pointer;
  transition: color var(--transition-fast);
}

.data-table th.sortable:hover {
  color: var(--color-primary);
}

.th-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.sort-icon {
  display: inline-flex;
  align-items: center;
  opacity: 0.5;
}

.sort-arrow {
  width: 0.875rem;
  height: 0.875rem;
}

.data-table th.sortable:hover .sort-icon {
  opacity: 1;
  color: var(--color-primary);
}

.data-table tbody tr {
  transition: background var(--transition-fast);
}

.data-table tbody tr:hover {
  background: var(--color-primary-subtle);
}

.data-table tbody tr.clickable {
  cursor: pointer;
}

.data-table td {
  color: var(--color-text);
}

.data-table td.empty {
  color: var(--color-text-muted);
  text-align: center;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 3rem 1.5rem;
}

.empty-icon {
  width: 3rem;
  height: 3rem;
  color: var(--color-text-muted);
  opacity: 0.5;
}

.empty-state span {
  font-size: var(--text-base);
}

/* Pagination */
.pagination {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  border-top: 1px solid var(--color-border-light);
  flex-wrap: wrap;
  gap: 1rem;
}

.pagination-info {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.pagination-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.375rem;
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.pagination-btn:hover:not(:disabled) {
  background: var(--color-bg-subtle);
  border-color: var(--color-border-focus);
  color: var(--color-primary);
}

.pagination-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.pagination-icon {
  width: 1rem;
  height: 1rem;
}

.pagination-pages {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.pagination-page {
  min-width: 2rem;
  height: 2rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.25rem 0.5rem;
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  font-family: var(--font-sans);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.pagination-page:hover {
  background: var(--color-bg-subtle);
  color: var(--color-text);
}

.pagination-page.active {
  background: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

/* Responsive */
@media (max-width: 768px) {
  .table-controls {
    flex-direction: column;
    align-items: stretch;
  }
  
  .table-controls-left,
  .table-controls-right {
    width: 100%;
  }
  
  .table-search {
    width: 100%;
    min-width: auto;
  }
  
  .pagination {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  
  .pagination-pages {
    justify-content: center;
  }
}
</style>
