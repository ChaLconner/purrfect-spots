import { ref } from 'vue'

export function useUploadCat() {
  const isUploading = ref(false)
  const error = ref<string | null>(null)

  /**
   * @param file   ไฟล์รูป (File object จาก <input type="file">)
   * @param meta   { name, description, latitude, longitude }
   */
  const uploadCat = async (
    file: File,
    meta: {
      name: string
      description: string
      latitude: number
      longitude: number
    }
  ): Promise<boolean> => {
    isUploading.value = true
    error.value = null

    try {
      /* ---------- 1) ขอ presigned URL จาก backend ---------- */
      const presignRes = await fetch('/api/presigned-url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename: file.name,
          content_type: file.type
        })
      })

      if (!presignRes.ok) {
        throw new Error('Failed to get presigned URL')
      }

      const { upload_url, public_url } = await presignRes.json()

      /* ---------- 2) PUT ไฟล์ขึ้น S3 โดยตรง ---------- */
      const uploadRes = await fetch(upload_url, {
        method: 'PUT',
        body: file,
        headers: { 'Content-Type': file.type }
      })

      if (!uploadRes.ok) {
        throw new Error('Failed to upload file to S3')
      }

      /* ---------- 3) Insert row เข้า Supabase ผ่าน backend ---------- */
      const saveRes = await fetch('/api/add-location', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: meta.name,
          description: meta.description,
          latitude: meta.latitude,
          longitude: meta.longitude,
          image_url: public_url
        })
      })

      if (!saveRes.ok) {
        throw new Error('Failed to save cat data to database')
      }

      return true
    } catch (err: any) {
      console.error('uploadCat error:', err)
      error.value = err?.message ?? 'Unexpected error occurred'
      return false
    } finally {
      isUploading.value = false
    }
  }

  return { uploadCat, isUploading, error }
}
