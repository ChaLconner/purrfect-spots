import { ref } from 'vue'

export function useUploadCat() {
  const isUploading = ref(false)
  const error = ref<string | null>(null)

  return { isUploading, error }
}
