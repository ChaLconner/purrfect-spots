import { ref } from 'vue'

export function useUploadCat() {
  const isUploading = ref(false)
  const error = ref<string | null>(null)

  const uploadCat = async (
    file: File,
    locationData: {
      name: string
      description: string
      latitude: number
      longitude: number
    }
  ): Promise<boolean> => {
    isUploading.value = true
    error.value = null

    try {
      // ✅ ใช้ FormData เพื่อส่งไฟล์และข้อมูลไปยัง backend
      const formData = new FormData()
      formData.append("file", file)
      formData.append("name", locationData.name)
      formData.append("description", locationData.description)
      formData.append("latitude", locationData.latitude.toString())
      formData.append("longitude", locationData.longitude.toString())

      const res = await fetch("/api/add-location", {
        method: "POST",
        body: formData,
      })

      if (!res.ok) throw new Error("Upload failed")
      return true
    } catch (err: any) {
      error.value = err?.message || "Upload error"
      return false
    } finally {
      isUploading.value = false
    }
  }

  return { uploadCat, isUploading, error }
}
