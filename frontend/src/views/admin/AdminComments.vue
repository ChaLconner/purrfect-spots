<template>
  <div class="space-y-4">
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
      <div class="flex flex-col">
        <h1 class="text-2xl font-bold text-brown-900 font-display tracking-tight">
          {{ t('admin.comments.title') }}
        </h1>
        <p class="text-sm text-brown-500 font-medium mt-0.5">{{ t('admin.comments.subtitle') }}</p>
      </div>

      <div class="flex items-center gap-3 w-full sm:w-auto">
        <div class="flex bg-sand-100/50 p-1.5 rounded-2xl border border-sand-100">
          <button
            class="px-5 py-2 rounded-lg text-xs font-medium uppercase tracking-wider transition-all"
            :class="
              !showReportedOnly
                ? 'bg-white text-terracotta-600 shadow-sm'
                : 'text-brown-400 hover:text-brown-600'
            "
            @click="showReportedOnly = false"
          >
            {{ t('admin.comments.all') }}
          </button>
          <button
            class="px-5 py-2 rounded-lg text-xs font-medium uppercase tracking-wider transition-all flex items-center gap-2"
            :class="
              showReportedOnly
                ? 'bg-white text-terracotta-600 shadow-sm'
                : 'text-brown-400 hover:text-brown-600'
            "
            @click="showReportedOnly = true"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9"
              />
            </svg>
            {{ t('admin.comments.reported') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Filters & Search -->
    <div
      class="bg-white rounded-xl shadow-sm border border-sand-100 p-4 flex flex-col sm:flex-row gap-4 justify-between items-center"
    >
      <div class="flex flex-wrap items-center gap-4 w-full sm:w-auto">
        <label class="flex items-center gap-3 cursor-pointer group select-none">
          <input
            type="checkbox"
            class="w-5 h-5 rounded-lg border-sand-200 text-terracotta-500 focus:ring-terracotta-400/20 focus:ring-offset-0 cursor-pointer transition-all bg-sand-50"
            :checked="isAllSelected"
            @change="toggleSelectAll"
          />
          <span
            class="text-xs font-medium text-brown-500 group-hover:text-brown-600 transition-colors"
            >{{ t('common.selectAll') }}</span
          >
        </label>

        <div
          v-if="selectedCommentIds.length > 0"
          class="flex items-center gap-3 animate-in fade-in slide-in-from-left-4 duration-500"
        >
          <button
            class="px-3 py-1.5 bg-red-50 text-red-600 rounded-lg text-sm font-medium hover:bg-red-500 hover:text-white transition-colors border border-red-200 flex items-center gap-2"
            @click="bulkAction('delete')"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              />
            </svg>
            {{ t('admin.comments.bulk_delete') }} ({{ selectedCommentIds.length }})
          </button>
          <button
            class="px-3 py-1.5 bg-green-50 text-green-600 rounded-lg text-sm font-medium hover:bg-green-500 hover:text-white transition-colors border border-green-200 flex items-center gap-2"
            @click="bulkAction('dismiss')"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M5 13l4 4L19 7"
              />
            </svg>
            {{ t('admin.comments.bulk_dismiss') }}
          </button>
        </div>
      </div>

      <div class="relative w-full sm:max-w-md group">
        <svg
          class="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-brown-400 group-focus-within:text-terracotta-500 transition-colors pointer-events-none"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          :placeholder="t('admin.comments.search')"
          class="w-full pl-10 pr-10 py-2 border border-sand-300 rounded-lg bg-white focus:ring-2 focus:ring-terracotta-500 focus:border-terracotta-500 transition-colors font-medium text-brown-800 outline-none"
          @input="handleSearch"
        />
        <button
          v-if="searchQuery"
          class="absolute right-4 top-1/2 -translate-y-1/2 text-brown-400 hover:text-brown-700 p-1 rounded-full hover:bg-sand-100 transition-colors"
          @click="clearSearch"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      <div class="flex items-center gap-2 text-sm text-brown-600">
        <span>{{ totalItems }}</span>
        <span>{{ t('admin.comments.total') }}</span>
      </div>
    </div>

    <!-- Comments List -->
    <div class="bg-white rounded-xl shadow-sm border border-sand-200 overflow-hidden">
      <!-- Loading State -->
      <div v-if="loading" class="flex flex-col items-center justify-center p-12 text-brown-400">
        <div
          class="w-12 h-12 border-4 border-sand-100 border-t-terracotta-500 rounded-full animate-spin mb-6"
        ></div>
        <p class="text-sm text-brown-500">{{ t('common.loading') }}</p>
      </div>

      <!-- Empty State -->
      <div
        v-else-if="comments.length === 0"
        class="flex flex-col items-center justify-center p-12 text-center"
      >
        <div class="w-24 h-24 bg-sand-50 rounded-full flex items-center justify-center mb-6">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-12 w-12 text-sand-300"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.5"
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
            />
          </svg>
        </div>
        <h3 class="text-xl font-bold text-brown-800 mb-2">
          {{ t('admin.comments.no_results') }}
        </h3>
        <p class="text-brown-500 max-w-sm font-medium">{{ t('admin.comments.no_results_desc') }}</p>
      </div>

      <!-- Comments List -->
      <div v-else class="h-[700px]">
        <RecycleScroller
          v-slot="{ item: comment }"
          class="scroller h-full"
          :items="comments"
          :item-size="180"
          key-field="id"
        >
          <div
            class="px-6 py-4 transition-colors border-b border-sand-100 hover:bg-sand-50 flex flex-col sm:flex-row gap-6 relative group/item"
            :class="selectedCommentIds.includes(comment.id) ? 'bg-terracotta-50/30' : ''"
          >
            <!-- Checkbox -->
            <div class="flex-shrink-0 pt-1.5">
              <input
                type="checkbox"
                class="w-5 h-5 rounded-lg border-sand-200 text-terracotta-500 focus:ring-terracotta-400/20 focus:ring-offset-0 cursor-pointer transition-all bg-sand-50"
                :checked="selectedCommentIds.includes(comment.id)"
                @change="toggleSelection(comment.id)"
              />
            </div>

            <!-- Content -->
            <div class="flex-1 flex flex-col justify-between min-w-0">
              <div>
                <div class="flex flex-wrap items-center gap-2 mb-2">
                  <div class="flex flex-col flex-1 min-w-[200px]">
                    <div class="flex items-center gap-2">
                      <router-link
                        :to="{
                          path: '/admin/users',
                          query: {
                            search:
                              comment.user_username ||
                              comment.user_email ||
                              comment.user_display_name,
                          },
                        }"
                        class="text-sm font-medium text-brown-900 truncate hover:text-brown-500 transition-colors"
                        :title="t('admin.users.view_profile')"
                      >
                        {{
                          comment.user_username ||
                          comment.user_email ||
                          t('admin.comments.unknown_user')
                        }}
                      </router-link>
                      <span
                        v-if="comment.is_user_banned"
                        class="px-2 py-0.5 bg-red-50 text-red-500 rounded-full text-xs font-semibold border border-red-100"
                      >
                        {{ t('admin.comments.banned_status') }}
                      </span>
                    </div>
                    <div class="flex items-center gap-3 mt-1">
                      <span
                        class="text-xs text-brown-500"
                        >{{ formatDate(comment.created_at) }}</span
                      >
                      <span
                        v-if="comment.violation_count > 0"
                        class="text-xs text-red-500 font-semibold bg-red-50 px-2 py-0.5 rounded-full border border-red-100"
                      >
                        {{ t('admin.comments.violations', { n: comment.violation_count }) }}
                      </span>
                    </div>
                  </div>

                  <div
                    v-if="comment.report_count > 0"
                    class="flex items-center gap-2 px-3 py-1.5 bg-red-50 text-red-600 rounded-full text-xs font-semibold whitespace-nowrap border border-red-100 cursor-pointer hover:bg-red-500 hover:text-white transition-colors group/report"
                    @click="viewReports(comment)"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      class="h-3.5 w-3.5 group-hover/report:scale-110 transition-transform"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                      />
                    </svg>
                    {{ t('admin.comments.reported') }} ({{ comment.report_count }})
                  </div>
                </div>
                <p
                  class="text-brown-700 leading-relaxed text-sm break-words line-clamp-3 sm:line-clamp-none font-medium"
                >
                  {{ comment.content }}
                </p>
              </div>

              <div class="mt-2 flex items-center justify-end gap-2 border-t border-sand-100 pt-2">
                <router-link
                  v-if="comment.cat_photo_id"
                  :to="`/photos/${comment.cat_photo_id}`"
                  target="_blank"
                  class="mr-auto text-brown-600 hover:text-terracotta-600 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="h-4 w-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                    />
                  </svg>
                  {{ t('admin.comments.view_photo') }}
                </router-link>

                <button
                  v-if="!comment.is_user_banned"
                  class="text-brown-600 hover:text-red-600 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 group/ban"
                  @click="handleBanUser(comment)"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="h-4 w-4 group-hover/ban:scale-110 transition-transform"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"
                    />
                  </svg>
                  {{ t('admin.comments.ban_user') }}
                </button>

                <button
                  v-if="comment.report_count > 0"
                  class="px-3 py-1.5 bg-green-50 text-green-600 rounded-lg text-sm font-medium hover:bg-green-500 hover:text-white transition-colors border border-green-200 flex items-center gap-2"
                  @click="dismissReports(comment)"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="h-4 w-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                  {{ t('admin.comments.dismiss') }}
                </button>

                <button
                  class="px-3 py-1.5 bg-red-50 text-red-600 rounded-lg text-sm font-medium hover:bg-red-500 hover:text-white transition-colors border border-red-200 flex items-center gap-2"
                  @click="confirmDelete(comment)"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="h-4 w-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                    />
                  </svg>
                  {{ t('common.delete') }}
                </button>
              </div>
            </div>
          </div>
        </RecycleScroller>
      </div>

      <!-- Pagination -->
      <div
        v-if="totalPages > 1"
        class="px-6 py-4 border-t border-sand-200 flex items-center justify-between"
      >
        <span class="text-sm text-brown-600">
          {{ t('admin.comments.total') }}: {{ totalItems }}
        </span>
        <div class="flex items-center gap-3">
          <button
            :disabled="currentPage === 1"
            class="px-4 py-2 border border-sand-300 rounded-md text-sm font-medium text-brown-700 bg-white hover:bg-sand-50 disabled:opacity-50 disabled:cursor-not-allowed"
            @click="changePage(currentPage - 1)"
          >
            {{ t('admin.pagination.previous') }}
          </button>
          <span class="text-sm text-brown-600">
            {{ currentPage }} / {{ totalPages }}
          </span>
          <button
            :disabled="currentPage === totalPages"
            class="px-4 py-2 border border-sand-300 rounded-md text-sm font-medium text-brown-700 bg-white hover:bg-sand-50 disabled:opacity-50 disabled:cursor-not-allowed"
            @click="changePage(currentPage + 1)"
          >
            {{ t('admin.pagination.next') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Confirm Delete Modal -->
    <Teleport to="body">
      <div
        v-if="deleteModalOpen"
        class="fixed inset-0 bg-black bg-opacity-50 z-[100] flex items-center justify-center p-4"
      >
        <div
          class="bg-white rounded-xl shadow-xl max-w-md w-full overflow-hidden border border-sand-100"
        >
          <div class="p-6">
            <h3 class="text-lg font-bold text-center text-brown-900 mb-2">
              {{ t('admin.comments.delete_confirm') }}
            </h3>
            <p class="text-center text-sm text-brown-600 mb-4">
              {{ t('admin.comments.delete_desc') }}
            </p>

            <div class="bg-sand-50 rounded-lg p-4 mb-6 border border-sand-100">
              <p class="text-sm text-brown-700 italic line-clamp-4 font-medium leading-relaxed">
                "{{ commentToDelete?.content }}"
              </p>
            </div>

            <div class="flex justify-end gap-3 mt-6">
              <button
                class="px-4 py-2 border border-sand-300 rounded-lg text-brown-600 hover:bg-sand-50"
                :disabled="deleting"
                @click="cancelDelete"
              >
                {{ t('common.cancel') }}
              </button>
              <button
                class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 shadow-sm transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                :disabled="deleting"
                @click="executeDelete"
              >
                <svg
                  v-if="deleting"
                  class="animate-spin h-5 w-5 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    class="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    stroke-width="4"
                  />
                  <path
                    class="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                <span v-else>{{ t('common.delete') }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Report Details Modal -->
    <Teleport to="body">
      <div
        v-if="reportDetailsModalOpen"
        class="fixed inset-0 bg-black bg-opacity-50 z-[100] flex items-center justify-center p-4"
      >
        <div
          class="bg-white rounded-xl shadow-xl max-w-lg w-full overflow-hidden border border-sand-100"
        >
          <div class="p-6">
            <div class="flex justify-between items-center mb-4">
              <h3 class="text-lg font-bold text-brown-900">
                {{ t('admin.comments.report_details') }}
              </h3>
              <button
                class="text-brown-300 hover:text-brown-600 hover:bg-sand-50 p-2 rounded-xl transition-all active:scale-90"
                @click="reportDetailsModalOpen = false"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-6 w-6"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>

            <div v-if="loadingReports" class="py-16 flex flex-col items-center">
              <div
                class="w-12 h-12 border-4 border-sand-100 border-t-terracotta-500 rounded-full animate-spin mb-6"
              ></div>
              <p class="text-sm text-brown-500">
                {{ t('common.loading') }}
              </p>
            </div>

            <div v-else-if="activeReports.length === 0" class="py-16 text-center text-brown-400">
              <p class="font-medium">{{ t('admin.comments.no_reports_found') }}</p>
            </div>

            <div v-else class="space-y-4 max-h-[50vh] overflow-y-auto pr-3 custom-scrollbar">
              <div
                v-for="report in activeReports"
                :key="report.created_at"
                class="bg-sand-50 rounded-lg p-4 border border-sand-100 hover:bg-sand-50 transition-colors"
              >
                <div class="flex justify-between items-start mb-4">
                  <router-link
                    :to="{
                      path: '/admin/users',
                      query: { search: report.reporter?.username || report.reporter?.display_name },
                    }"
                    class="flex items-center gap-3 hover:opacity-80 transition-opacity min-w-0"
                  >
                    <div class="relative">
                      <OptimizedImage
                        :src="report.reporter?.avatar_url || '/default-avatar.png'"
                        alt="avatar"
                        class="w-10 h-10 rounded-2xl border-2 border-white shadow-sm object-cover"
                        :width="40"
                        :height="40"
                      />
                      <div class="absolute -bottom-1 -right-1 w-4 h-4 bg-terracotta-500 rounded-full border-2 border-white flex items-center justify-center">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-2 w-2 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                        </svg>
                      </div>
                    </div>
                    <div class="flex flex-col min-w-0">
                      <span class="font-bold text-brown-900 truncate">{{
                        report.reporter?.display_name || t('admin.comments.unknown_user')
                      }}</span>
                      <span v-if="report.reporter?.username" class="text-xs text-brown-500"
                        >@{{ report.reporter.username }}</span
                      >
                    </div>
                  </router-link>
                  <span
                    class="px-2 py-0.5 bg-red-50 text-red-500 rounded-full text-xs font-semibold border border-red-100"
                  >
                    {{ report.reason }}
                  </span>
                </div>
                <div v-if="report.details" class="relative">
                  <div class="absolute inset-y-0 left-0 w-1 bg-red-200 rounded-full"></div>
                  <p class="text-sm text-brown-700 italic pl-5 py-1.5 font-medium leading-relaxed">
                    "{{ report.details }}"
                  </p>
                </div>
                <div class="mt-3 flex justify-end">
                   <span class="text-xs text-brown-400">
                     {{ formatDate(report.created_at) }}
                   </span>
                </div>
              </div>
            </div>

            <div class="mt-6 flex justify-end gap-3">
              <button
                class="px-4 py-2 border border-sand-300 rounded-lg text-brown-600 hover:bg-sand-50"
                @click="reportDetailsModalOpen = false"
              >
                {{ t('common.close') }}
              </button>
              <button
                class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 shadow-sm transition-colors flex items-center justify-center gap-2"
                @click="
                  () => {
                    reportDetailsModalOpen = false;
                    confirmDelete(activeCommentForReports!);
                  }
                "
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-5 w-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
                {{ t('common.delete') }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Ban User Modal -->
    <BaseConfirmModal
      :is-open="banConfirmOpen"
      :title="t('admin.comments.ban_user')"
      :message="t('admin.comments.ban_confirm')"
      :confirm-text="t('admin.comments.ban_user')"
      variant="danger"
      :is-loading="banning"
      @close="banConfirmOpen = false"
      @confirm="executeBan"
    />

    <!-- Bulk Action Modal -->
    <BaseConfirmModal
      :is-open="bulkConfirmOpen"
      :title="
        currentBulkType === 'delete'
          ? t('admin.comments.bulk_delete')
          : t('admin.comments.bulk_dismiss')
      "
      :message="
        currentBulkType === 'delete'
          ? t('admin.comments.bulk_delete_confirm', { count: selectedCommentIds.length })
          : t('admin.comments.bulk_dismiss_confirm', { count: selectedCommentIds.length })
      "
      :confirm-text="
        currentBulkType === 'delete' ? t('common.delete') : t('admin.comments.dismiss')
      "
      :variant="currentBulkType === 'delete' ? 'danger' : 'warning'"
      :is-loading="bulkProcessing"
      @close="bulkConfirmOpen = false"
      @confirm="executeBulkAction"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { RecycleScroller } from 'vue-virtual-scroller';
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css';
import { apiV1 } from '@/utils/api';
import { useToast } from '@/components/toast/use-toast';
import { BaseConfirmModal, OptimizedImage } from '@/components/ui';

interface AdminComment {
  id: string;
  cat_photo_id: string;
  user_id: string;
  content: string;
  created_at: string;
  report_count: number;
  user_email: string | null;
  photo_url: string | null;
  is_user_banned: boolean;
  violation_count: number;
}

const { t } = useI18n();
const { toast } = useToast();

const comments = ref<AdminComment[]>([]);
const loading = ref(true);
const totalItems = ref(0);
const totalPages = ref(1);
const currentPage = ref(1);
const limit = ref(100); // Reduced for better initial load performance while maintaining scroll fluidity
const searchQuery = ref('');
const showReportedOnly = ref(false);

const selectedCommentIds = ref<string[]>([]);
const reportDetailsModalOpen = ref(false);
const activeReports = ref<CommentReport[]>([]);
const loadingReports = ref(false);
const activeCommentForReports = ref<AdminComment | null>(null);

const deleteModalOpen = ref(false);
const commentToDelete = ref<AdminComment | null>(null);
const deleting = ref(false);

// Ban User Modal
const banConfirmOpen = ref(false);
const commentToBan = ref<AdminComment | null>(null);
const banning = ref(false);

// Bulk Action Modal
const bulkConfirmOpen = ref(false);
const currentBulkType = ref<'delete' | 'dismiss'>('delete');
const bulkProcessing = ref(false);

interface CommentReport {
  id: string;
  reporter_id: string;
  reporter_name: string;
  reason: string;
  created_at: string;
}

const toggleSelection = (id: string): void => {
  const index = selectedCommentIds.value.indexOf(id);
  if (index === -1) {
    selectedCommentIds.value.push(id);
  } else {
    selectedCommentIds.value.splice(index, 1);
  }
};

const isAllSelected = computed(() => {
  return comments.value.length > 0 && selectedCommentIds.value.length === comments.value.length;
});

const toggleSelectAll = (): void => {
  if (isAllSelected.value) {
    selectedCommentIds.value = [];
  } else {
    selectedCommentIds.value = comments.value.map((c) => c.id);
  }
};

const viewReports = async (comment: AdminComment): Promise<void> => {
  activeCommentForReports.value = comment;
  reportDetailsModalOpen.value = true;
  loadingReports.value = true;
  activeReports.value = [];
  try {
    const response = await apiV1.get<CommentReport[]>(`/admin/comments/${comment.id}/reports`);
    activeReports.value = response || [];
  } catch {
    toast({
      description: t('admin.comments.load_error'),
      variant: 'destructive',
    });
  } finally {
    loadingReports.value = false;
  }
};

const dismissReports = async (comment: AdminComment): Promise<void> => {
  try {
    await apiV1.put(`/admin/comments/${comment.id}/resolve`, {});
    toast({
      description: t('admin.comments.dismiss_success'),
      variant: 'success',
    });
    fetchComments();
  } catch {
    toast({
      description: t('admin.comments.dismiss_error'),
      variant: 'destructive',
    });
  }
};

const handleBanUser = (comment: AdminComment): void => {
  commentToBan.value = comment;
  banConfirmOpen.value = true;
};

const executeBan = async (): Promise<void> => {
  if (!commentToBan.value) return;

  banning.value = true;
  try {
    await apiV1.post(`/admin/comments/${commentToBan.value.id}/ban-user`, {});
    toast({
      description: t('admin.comments.user_banned'),
      variant: 'success',
    });
    banConfirmOpen.value = false;
    commentToBan.value = null;
    fetchComments();
  } catch {
    toast({
      description: t('admin.comments.failed_to_ban'),
      variant: 'destructive',
    });
  } finally {
    banning.value = false;
  }
};

const bulkAction = (type: 'delete' | 'dismiss'): void => {
  if (selectedCommentIds.value.length === 0) return;
  currentBulkType.value = type;
  bulkConfirmOpen.value = true;
};

const executeBulkAction = async (): Promise<void> => {
  bulkProcessing.value = true;
  try {
    const endpoint =
      currentBulkType.value === 'delete'
        ? '/admin/comments/bulk-delete'
        : '/admin/comments/bulk-resolve';
    await apiV1.post(endpoint, { comment_ids: selectedCommentIds.value });

    toast({
      description:
        currentBulkType.value === 'delete'
          ? t('admin.comments.delete_success')
          : t('admin.comments.dismiss_success'),
      variant: 'success',
    });

    bulkConfirmOpen.value = false;
    selectedCommentIds.value = [];
    fetchComments();
  } catch {
    toast({
      description: t('admin.comments.bulk_action_failed'),
      variant: 'destructive',
    });
  } finally {
    bulkProcessing.value = false;
  }
};

let searchTimeout: ReturnType<typeof setTimeout>;

const fetchComments = async (): Promise<void> => {
  loading.value = true;
  try {
    const params = new URLSearchParams({
      page: currentPage.value.toString(),
      page_size: limit.value.toString(),
    });

    if (searchQuery.value) {
      params.append('search', searchQuery.value);
    }

    if (showReportedOnly.value) {
      params.append('reported_only', 'true');
    }

    interface CommentsResponse {
      items: AdminComment[];
      total: number;
      pages: number;
    }

    const response = await apiV1.get<CommentsResponse>(`/admin/comments?${params.toString()}`);
    comments.value = response.items || []; // Backend returns 'items' now in my previous mock/refactor
    totalItems.value = response.total || 0;
    totalPages.value = response.pages || 1;
  } catch {
    toast({
      title: t('common.error'),
      description: t('admin.comments.load_error'),
      variant: 'destructive',
    });
  } finally {
    loading.value = false;
  }
};

const handleSearch = (): void => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    currentPage.value = 1;
    fetchComments();
  }, 300);
};

const clearSearch = (): void => {
  searchQuery.value = '';
  currentPage.value = 1;
  fetchComments();
};

const changePage = (page: number): void => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page;
    fetchComments();
  }
};

const confirmDelete = (comment: AdminComment): void => {
  commentToDelete.value = comment;
  deleteModalOpen.value = true;
};

const cancelDelete = (): void => {
  deleteModalOpen.value = false;
  commentToDelete.value = null;
};

const executeDelete = async (): Promise<void> => {
  if (!commentToDelete.value) return;

  deleting.value = true;
  try {
    await apiV1.delete(`/admin/comments/${commentToDelete.value.id}`);
    toast({
      description: t('admin.comments.delete_success'),
      variant: 'success',
    });
    deleteModalOpen.value = false;
    commentToDelete.value = null;
    fetchComments(); // Refresh list
  } catch {
    toast({
      title: t('common.error'),
      description: t('admin.comments.delete_error'),
      variant: 'destructive',
    });
  } finally {
    deleting.value = false;
  }
};

const formatDate = (dateStr: string): string => {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return new Intl.DateTimeFormat(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
};


watch(showReportedOnly, () => {
  currentPage.value = 1;
  fetchComments();
});

onMounted(() => {
  fetchComments();
});
</script>

<style scoped>
.font-display {
  font-family: 'Outfit', sans-serif;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #e5e7eb;
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #d1d5db;
}


.scroller {
  height: 100%;
}

.scroller::-webkit-scrollbar {
  width: 6px;
}
.scroller::-webkit-scrollbar-track {
  background: transparent;
}
.scroller::-webkit-scrollbar-thumb {
  background: #e6e0dc;
  border-radius: 10px;
}
.scroller::-webkit-scrollbar-thumb:hover {
  background: #d1c7c1;
}
</style>
