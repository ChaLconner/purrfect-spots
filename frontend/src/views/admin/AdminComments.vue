<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center sm:flex-row flex-col gap-4">
      <div class="flex flex-col">
        <h1 class="text-3xl font-bold text-brown-900 font-display">
          {{ t('admin.comments.title') }}
        </h1>
        <p class="text-brown-500 mt-1">{{ t('admin.comments.subtitle') }}</p>
      </div>

      <div class="flex items-center gap-3 w-full sm:w-auto">
        <div class="flex bg-sand-100 p-1 rounded-xl">
          <button
            class="px-4 py-1.5 rounded-lg text-sm font-bold transition-all"
            :class="
              !showReportedOnly
                ? 'bg-white text-terracotta-600 shadow-sm'
                : 'text-brown-500 hover:text-brown-700'
            "
            @click="showReportedOnly = false"
          >
            {{ t('admin.comments.all') }}
          </button>
          <button
            class="px-4 py-1.5 rounded-lg text-sm font-bold transition-all flex items-center gap-1.5"
            :class="
              showReportedOnly
                ? 'bg-white text-terracotta-600 shadow-sm'
                : 'text-brown-500 hover:text-brown-700'
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
      class="bg-white rounded-2xl shadow-sm border border-sand-200 p-4 flex flex-col sm:flex-row gap-4 justify-between items-center"
    >
      <div class="flex items-center gap-4 w-full sm:w-auto">
        <label class="flex items-center gap-3 cursor-pointer group">
          <input
            type="checkbox"
            class="w-5 h-5 rounded border-sand-300 text-terracotta-500 focus:ring-terracotta-400 cursor-pointer"
            :checked="isAllSelected"
            @change="toggleSelectAll"
          />
          <span
            class="text-sm font-bold text-brown-600 group-hover:text-brown-900 transition-colors"
            >{{ t('common.selectAll') }}</span
          >
        </label>

        <div
          v-if="selectedCommentIds.length > 0"
          class="flex items-center gap-2 animate-in fade-in slide-in-from-left-2 duration-300"
        >
          <button
            class="px-3 py-1.5 bg-red-50 text-red-600 rounded-lg text-xs font-bold hover:bg-red-100 transition-colors border border-red-100 flex items-center gap-1.5"
            @click="bulkAction('delete')"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-3.5 w-3.5"
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
            class="px-3 py-1.5 bg-green-50 text-green-600 rounded-lg text-xs font-bold hover:bg-green-100 transition-colors border border-green-100 flex items-center gap-1.5"
            @click="bulkAction('dismiss')"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-3.5 w-3.5"
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

      <div class="relative w-full sm:max-w-md">
        <svg
          class="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-brown-400"
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
          class="w-full pl-10 pr-4 py-2.5 border border-sand-300 rounded-xl bg-sand-50 focus:bg-white focus:ring-2 focus:ring-terracotta-400 focus:border-terracotta-400 transition-all font-medium text-brown-800 placeholder-brown-400 outline-none"
          @input="handleSearch"
        />
        <button
          v-if="searchQuery"
          class="absolute right-3 top-1/2 -translate-y-1/2 text-brown-400 hover:text-brown-700"
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

      <div class="flex items-center gap-2 text-sm font-bold text-brown-600">
        <span>{{ totalItems }}</span>
        <span class="text-brown-400 uppercase tracking-wider text-xs">{{
          t('admin.comments.total')
        }}</span>
      </div>
    </div>

    <!-- Comments List -->
    <div class="bg-white rounded-2xl shadow-sm border border-sand-200 overflow-hidden">
      <!-- Loading State -->
      <div v-if="loading" class="flex flex-col items-center justify-center p-24 text-brown-400">
        <div
          class="w-10 h-10 border-4 border-sand-200 border-t-terracotta-500 rounded-full animate-spin mb-4"
        ></div>
        <p class="font-bold">{{ t('common.loading') }}</p>
      </div>

      <!-- Empty State -->
      <div
        v-else-if="comments.length === 0"
        class="flex flex-col items-center justify-center p-24 text-center"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-24 w-24 text-sand-300 mb-6"
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
        <h3 class="text-xl font-bold text-brown-800 mb-2 font-display">
          {{ t('admin.comments.no_results') }}
        </h3>
        <p class="text-brown-500 max-w-sm">{{ t('admin.comments.no_results_desc') }}</p>
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
            class="p-6 transition-all border-b border-sand-100 hover:bg-sand-50 flex flex-col sm:flex-row gap-6 relative"
            :class="selectedCommentIds.includes(comment.id) ? 'bg-terracotta-50/50' : ''"
          >
            <!-- Checkbox -->
            <div class="flex-shrink-0 pt-2">
              <input
                type="checkbox"
                class="w-5 h-5 rounded border-sand-300 text-terracotta-500 focus:ring-terracotta-400 cursor-pointer transition-transform"
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
                        class="font-bold text-brown-900 text-base truncate hover:text-brown-500 transition-colors"
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
                        class="px-2 py-0.5 bg-red-100 text-red-600 rounded text-[10px] font-bold uppercase tracking-wider border border-red-200"
                      >
                        {{ t('admin.comments.banned_status') }}
                      </span>
                    </div>
                    <div class="flex items-center gap-3 mt-0.5">
                      <span
                        class="text-[10px] text-brown-400 font-medium uppercase tracking-tight"
                        >{{ formatDate(comment.created_at) }}</span
                      >
                      <span
                        v-if="comment.violation_count > 0"
                        class="text-[10px] text-red-500 font-bold bg-red-50 px-1.5 py-0.5 rounded border border-red-100 uppercase tracking-tighter"
                      >
                        {{ t('admin.comments.violations', { n: comment.violation_count }) }}
                      </span>
                    </div>
                  </div>

                  <div
                    v-if="comment.report_count > 0"
                    class="flex items-center gap-1.5 px-2.5 py-1 bg-red-50 text-red-600 rounded-lg text-xs font-bold whitespace-nowrap border border-red-100 shadow-sm cursor-pointer hover:bg-red-100 transition-colors"
                    @click="viewReports(comment)"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      class="h-3.5 w-3.5"
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
                  class="text-brown-700 leading-relaxed text-sm break-words line-clamp-3 sm:line-clamp-none"
                >
                  {{ comment.content }}
                </p>
              </div>

              <div class="mt-4 flex items-center justify-end gap-2 border-t border-sand-100 pt-3">
                <router-link
                  v-if="comment.cat_photo_id"
                  :to="`/photos/${comment.cat_photo_id}`"
                  target="_blank"
                  class="mr-auto px-3 py-1.5 text-brown-500 hover:text-terracotta-600 hover:bg-sand-50 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="h-3.5 w-3.5"
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
                  class="px-3 py-1.5 text-brown-400 hover:text-red-500 hover:bg-red-50 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 group"
                  @click="handleBanUser(comment)"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="h-3.5 w-3.5 group-hover:scale-110 transition-transform"
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
                  class="px-4 py-1.5 text-green-600 hover:bg-green-50 hover:text-green-700 rounded-xl text-sm font-bold transition-all flex items-center gap-1.5"
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
                  class="px-4 py-1.5 text-red-600 hover:bg-red-50 hover:text-red-700 rounded-xl text-sm font-bold transition-all flex items-center gap-1.5"
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
        class="px-6 py-4 border-t border-sand-100 bg-sand-50/50 flex justify-center items-center gap-2"
      >
        <button
          :disabled="currentPage === 1"
          class="w-10 h-10 flex items-center justify-center rounded-xl border border-sand-200 bg-white text-brown-600 hover:bg-sand-50 hover:border-terracotta-200 transition-all disabled:opacity-50 disabled:cursor-not-allowed group"
          @click="changePage(currentPage - 1)"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-5 w-5 group-hover:-translate-x-0.5 transition-transform"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M15 19l-7-7 7-7"
            />
          </svg>
        </button>

        <div class="flex items-center gap-1">
          <button
            v-for="page in displayedPages"
            :key="page"
            class="min-w-[40px] h-10 px-2 flex items-center justify-center rounded-xl text-sm font-bold transition-all"
            :class="
              page === currentPage
                ? 'bg-terracotta-500 text-white shadow-sm'
                : page === '...'
                  ? 'cursor-default text-brown-400'
                  : 'bg-white border border-sand-200 text-brown-600 hover:bg-sand-50 hover:border-terracotta-200'
            "
            :disabled="page === '...'"
            @click="page !== '...' ? changePage(page as number) : null"
          >
            {{ page }}
          </button>
        </div>

        <button
          :disabled="currentPage === totalPages"
          class="w-10 h-10 flex items-center justify-center rounded-xl border border-sand-200 bg-white text-brown-600 hover:bg-sand-50 hover:border-terracotta-200 transition-all disabled:opacity-50 disabled:cursor-not-allowed group"
          @click="changePage(currentPage + 1)"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-5 w-5 group-hover:translate-x-0.5 transition-transform"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 5l7 7-7 7"
            />
          </svg>
        </button>
      </div>
    </div>

    <!-- Confirm Delete Modal -->
    <Teleport to="body">
      <div
        v-if="deleteModalOpen"
        class="fixed inset-0 bg-brown-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-200"
      >
        <div
          class="bg-white rounded-3xl shadow-xl max-w-md w-full overflow-hidden animate-in zoom-in-95 duration-200"
        >
          <div class="p-6 sm:p-8">
            <div
              class="w-16 h-16 bg-red-50 rounded-2xl flex items-center justify-center mx-auto mb-6 transform -rotate-6"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-8 w-8 text-red-500"
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
            </div>

            <h3 class="text-2xl font-bold text-center text-brown-900 mb-2 font-display">
              {{ t('admin.comments.delete_confirm') }}
            </h3>
            <p class="text-center text-brown-500 mb-6">{{ t('admin.comments.delete_desc') }}</p>

            <div class="bg-sand-50 rounded-xl p-4 mb-8 border border-sand-100">
              <p class="text-sm text-brown-800 italic line-clamp-3">
                "{{ commentToDelete?.content }}"
              </p>
            </div>

            <div class="flex gap-4">
              <button
                class="flex-1 px-4 py-3 bg-white border-2 border-sand-200 text-brown-700 font-bold rounded-xl hover:bg-sand-50 hover:border-sand-300 transition-all"
                :disabled="deleting"
                @click="cancelDelete"
              >
                {{ t('common.cancel') }}
              </button>
              <button
                class="flex-1 px-4 py-3 bg-red-500 text-white font-bold rounded-xl hover:bg-red-600 shadow-sm hover:shadow-md transition-all flex items-center justify-center gap-2"
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
        class="fixed inset-0 bg-brown-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-200"
      >
        <div
          class="bg-white rounded-3xl shadow-xl max-w-lg w-full overflow-hidden animate-in zoom-in-95 duration-200"
        >
          <div class="p-6 sm:p-8">
            <div class="flex justify-between items-center mb-6">
              <h3 class="text-2xl font-bold text-brown-900 font-display">
                {{ t('admin.comments.report_details') }}
              </h3>
              <button
                class="text-brown-400 hover:text-brown-600 p-2"
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

            <div v-if="loadingReports" class="py-12 flex flex-col items-center">
              <div
                class="w-8 h-8 border-3 border-sand-200 border-t-terracotta-500 rounded-full animate-spin mb-3"
              ></div>
              <p class="text-sm text-brown-500">{{ t('common.loading') }}</p>
            </div>

            <div v-else-if="activeReports.length === 0" class="py-12 text-center text-brown-400">
              <p>{{ t('admin.comments.no_reports_found') }}</p>
            </div>

            <div v-else class="space-y-4 max-h-[60vh] overflow-y-auto pr-2 custom-scrollbar">
              <div
                v-for="report in activeReports"
                :key="report.created_at"
                class="bg-sand-50 rounded-2xl p-4 border border-sand-100"
              >
                <div class="flex justify-between items-start mb-2">
                  <router-link
                    :to="{
                      path: '/admin/users',
                      query: { search: report.reporter?.username || report.reporter?.display_name },
                    }"
                    class="flex items-center gap-2 hover:opacity-80 transition-opacity"
                  >
                    <OptimizedImage
                      :src="report.reporter?.avatar_url || '/default-avatar.png'"
                      alt="avatar"
                      class="w-8 h-8 rounded-full border border-sand-dark"
                      :width="32"
                      :height="32"
                    />
                    <div class="flex flex-col">
                      <span class="font-bold text-brown">{{
                        report.reporter?.display_name || t('admin.comments.unknown_user')
                      }}</span>
                      <span v-if="report.reporter?.username" class="text-xs text-brown/60"
                        >@{{ report.reporter.username }}</span
                      >
                    </div>
                  </router-link>
                  <span
                    class="px-2 py-0.5 bg-red-100 text-red-600 rounded text-[10px] font-bold uppercase tracking-wider"
                  >
                    {{ report.reason }}
                  </span>
                </div>
                <p
                  v-if="report.details"
                  class="text-sm text-brown-700 italic border-l-2 border-red-200 pl-3 py-1 mt-2"
                >
                  "{{ report.details }}"
                </p>
              </div>
            </div>

            <div class="mt-8 flex gap-3">
              <button
                class="flex-1 px-4 py-3 bg-white border-2 border-sand-200 text-brown-700 font-bold rounded-xl hover:bg-sand-50 transition-all"
                @click="reportDetailsModalOpen = false"
              >
                {{ t('common.close') }}
              </button>
              <button
                class="flex-1 px-4 py-3 bg-red-500 text-white font-bold rounded-xl hover:bg-red-600 shadow-sm transition-all"
                @click="
                  () => {
                    reportDetailsModalOpen = false;
                    confirmDelete(activeCommentForReports!);
                  }
                "
              >
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
const limit = ref(500); // Increased for virtual scrolling
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
      limit: limit.value.toString(),
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

const displayedPages = computed(() => {
  const current = currentPage.value;
  const total = totalPages.value;
  const delta = 1; // How many pages to show on each side of current

  const left = current - delta;
  const right = current + delta;
  const range = [];
  const rangeWithDots = [];
  let l;

  for (let i = 1; i <= total; i++) {
    if (i === 1 || i === total || (i >= left && i <= right)) {
      range.push(i);
    }
  }

  for (const i of range) {
    if (l) {
      if (i - l === 2) {
        rangeWithDots.push(l + 1);
      } else if (i - l !== 1) {
        rangeWithDots.push('...');
      }
    }
    rangeWithDots.push(i);
    l = i;
  }

  return rangeWithDots;
});

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

/* Modal Animations */
@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes zoomIn {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.animate-in.fade-in {
  animation: fadeIn 0.2s ease-out forwards;
}

.animate-in.zoom-in-95 {
  animation: zoomIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
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
