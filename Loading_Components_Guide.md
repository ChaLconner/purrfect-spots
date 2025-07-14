# 🐱 Loading Components Documentation

## LoadingSpinner Component

### การใช้งานพื้นฐาน
```vue
<template>
  <LoadingSpinner size="md" :show-text="true" />
</template>

<script setup>
import LoadingSpinner from './components/common/LoadingSpinner.vue';
</script>
```

### Props
- `size`: 'sm' | 'md' | 'lg' | 'xl' - ขนาดของ animation
- `showText`: boolean - แสดงข้อความหรือไม่
- `text`: string - ข้อความที่จะแสดง (default: "กำลังโหลด...")
- `textColor`: string - สีของข้อความ (default: "text-gray-600")
- `animation`: 'cat' | 'loading' | 'spinner' - ประเภท animation

### ตัวอย่างการใช้งาน
```vue
<!-- ขนาดเล็กไม่มีข้อความ -->
<LoadingSpinner size="sm" :show-text="false" />

<!-- ขนาดกลางพร้อมข้อความ -->
<LoadingSpinner size="md" :show-text="true" text="กำลังประมวลผล..." />

<!-- ขนาดใหญ่ -->
<LoadingSpinner size="lg" :show-text="true" />
```

## CatLoading Component

### การใช้งานพื้นฐาน
```vue
<template>
  <CatLoading 
    size="lg" 
    title="กำลังอัปโหลด..." 
    subtitle="กรุณารอสักครู่"
  />
</template>

<script setup>
import CatLoading from './components/common/CatLoading.vue';
</script>
```

### Props
- `size`: 'sm' | 'md' | 'lg' | 'xl' | 'hero' - ขนาดของ animation
- `showText`: boolean - แสดงข้อความหรือไม่ (default: true)
- `title`: string - หัวข้อหลัก (default: "🐱 กำลังประมวลผล...")
- `subtitle`: string - ข้อความรอง (default: "กรุณารอสักครู่ เราพยายามหาแมวให้คุณ")
- `centered`: boolean - จัดกึ่งกลางหรือไม่ (default: true)

### ตัวอย่างการใช้งาน
```vue
<!-- สำหรับ Upload -->
<CatLoading 
  size="lg" 
  title="🐱 กำลังอัปโหลดรูปแมว..."
  subtitle="กรุณารอสักครู่ เราพยายามประมวลผลรูปภาพของคุณ"
/>

<!-- สำหรับ Gallery -->
<CatLoading 
  size="xl" 
  title="🐱 กำลังโหลดแกลเลอรี่..."
  subtitle="เรากำลังรวบรวมรูปแมวน่ารักทั้งหมดให้คุณ"
/>

<!-- สำหรับ Map -->
<CatLoading 
  size="md" 
  title="🗺️ กำลังโหลดแผนที่..."
  subtitle="เรากำลังค้นหาตำแหน่งแมวทั้งหมดให้คุณ"
/>

<!-- แบบ Hero -->
<CatLoading 
  size="hero" 
  title="🎉 ยินดีต้อนรับสู่ PurrFect Spots!"
  subtitle="โลกของแมวน่ารักรอคุณอยู่"
/>
```

## Implementation ในโปรเจค

### ✅ Components ที่อัปเดตแล้ว:

1. **LoadingSpinner.vue** - ใช้ Lottie animation แทน CSS spinner
2. **CatLoading.vue** - Component แยกสำหรับ full-screen loading
3. **Upload.vue** - ใช้ CatLoading สำหรับ upload progress
4. **Gallery.vue** - ใช้ CatLoading สำหรับ loading photos
5. **Map.vue** - ใช้ CatLoading สำหรับ loading map data
6. **GoogleOAuthButton.vue** - ใช้ LoadingSpinner สำหรับ login state

### 🎨 Design Features:

- **Responsive**: ปรับขนาดตามหน้าจออัตโนมัติ
- **Smooth Animation**: ใช้ Lottie สำหรับ animation ที่ลื่นไหล
- **Thai Language**: ข้อความเป็นภาษาไทยที่เป็นมิตร
- **Contextual**: ข้อความเหมาะสมกับแต่ละสถานการณ์
- **Accessible**: รองรับ screen readers และ keyboard navigation

### 🔧 Technical Details:

- **Library**: @lottiefiles/dotlottie-vue
- **Performance**: Lazy loading และ optimized animations
- **Fallback**: มี fallback สำหรับกรณีที่ animation ไม่โหลด
- **TypeScript**: Support TypeScript อย่างเต็มรูปแบบ

### 🎯 การใช้งานแนะนำ:

```vue
<!-- สำหรับ loading state ธรรมดา -->
<LoadingSpinner size="sm" />

<!-- สำหรับ page loading -->
<CatLoading size="lg" />

<!-- สำหรับ hero section -->
<CatLoading size="hero" title="Welcome!" />
```

### 📱 Responsive Breakpoints:

- **Mobile**: ขนาด animation ลดลง 20%
- **Tablet**: ขนาดปกติ
- **Desktop**: ขนาดเต็ม

### 🎨 Animation Details:

- **Duration**: 2-3 วินาที per loop
- **Easing**: ease-in-out สำหรับ smooth transition
- **Colors**: เข้ากับ brand colors ของโปรเจค

## การ Customize

### เปลี่ยน Animation URL:
```vue
<!-- ใน LoadingSpinner.vue -->
const animationSrc = computed(() => {
  return 'https://your-custom-lottie-url.json';
});
```

### เพิ่ม Animation ใหม่:
```vue
const animations = {
  cat: 'url-to-cat-animation',
  dog: 'url-to-dog-animation',
  loading: 'url-to-loading-animation',
};
```

### Custom Styling:
```vue
<style scoped>
.loading-spinner :deep(.dotlottie-canvas) {
  filter: hue-rotate(45deg); /* เปลี่ยนสี */
  opacity: 0.8; /* เปลี่ยนความโปร่งใส */
}
</style>
```
