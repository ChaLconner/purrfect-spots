# Code Quality Refactoring - Component Splitting

## 📅 Date: 2026-01-29

## 🎯 Objective
แยก components และ services ที่มีขนาดใหญ่เกินไปออกเป็น sub-components/services ตามหลัก Single Responsibility Principle

---

## 📊 Before vs After

### Backend Services

| Original File | Size | Action |
|--------------|------|--------|
| `auth_service.py` | 689 lines / 29KB | แยกเป็น 3 services ใหม่ |

**New Services Created:**

| New Service | Purpose | Size |
|-------------|---------|------|
| `password_service.py` | Password hashing, verification, HIBP checking | ~85 lines |
| `oauth_service.py` | Google OAuth token verification & exchange | ~240 lines |
| `user_service.py` | User CRUD operations | ~180 lines |

### Frontend Components

| Original Component | Size | Action |
|-------------------|------|--------|
| `NavBar.vue` | 966 lines / 23KB | แยกเป็น 3 sub-components |
| `AuthForm.vue` | 864 lines / 23KB | แยกเป็น 2 sub-components |

**New NavBar Sub-Components:**

| New Component | Purpose | Location |
|--------------|---------|----------|
| `SearchBox.vue` | Search functionality | `components/navbar/` |
| `UserMenu.vue` | User dropdown menu | `components/navbar/` |
| `MobileMenu.vue` | Mobile navigation drawer | `components/navbar/` |

**New Auth Sub-Components:**

| New Component | Purpose | Location |
|--------------|---------|----------|
| `GoogleButton.vue` | Google OAuth button with PKCE | `components/auth/` |
| `EmailPasswordForm.vue` | Email/Password form | `components/auth/` |

---

## 📁 New Directory Structure

```
backend/
└── services/
    ├── __init__.py          # Updated exports
    ├── auth_service.py      # Original (can be refactored later)
    ├── password_service.py  # NEW - Password operations
    ├── oauth_service.py     # NEW - Google OAuth
    ├── user_service.py      # NEW - User CRUD
    └── ...

frontend/
└── src/
    └── components/
        ├── navbar/          # NEW - NavBar sub-components
        │   ├── index.ts
        │   ├── SearchBox.vue
        │   ├── UserMenu.vue
        │   └── MobileMenu.vue
        ├── auth/            # NEW - Auth sub-components
        │   ├── index.ts
        │   ├── GoogleButton.vue
        │   └── EmailPasswordForm.vue
        └── ...
```

---

## ✅ Benefits

1. **Single Responsibility Principle** - แต่ละ component/service ทำหน้าที่เดียว
2. **Better Testability** - สามารถ test แต่ละส่วนแยกกันได้
3. **Improved Maintainability** - แก้ไขง่ายขึ้นเมื่อแยกเป็นไฟล์เล็กๆ
4. **Code Reusability** - สามารถ reuse components ได้ง่าย
5. **Better Developer Experience** - ค้นหาและเข้าใจ code ได้ง่ายขึ้น

---

## 🔧 How to Use New Components

### Frontend - NavBar Sub-Components
```typescript
import { SearchBox, UserMenu, MobileMenu } from '@/components/navbar';
```

### Frontend - Auth Sub-Components
```typescript
import { GoogleButton, EmailPasswordForm } from '@/components/auth';
```

### Backend - New Services
```python
from services.password_service import password_service
from services.oauth_service import OAuthService
from services.user_service import UserService
```

---

## 📝 Notes

- Original `auth_service.py` และ `NavBar.vue`, `AuthForm.vue` ยังคงทำงานได้ปกติ
- Components ใหม่สามารถใช้ทดแทนได้ทันที
- ควร migrate ไปใช้ components ใหม่เพื่อลดขนาดไฟล์หลัก

---

## 🚀 Next Steps

1. อัพเดท `NavBar.vue` ให้ใช้ sub-components
2. อัพเดท `AuthForm.vue` ให้ใช้ sub-components
3. อัพเดท `auth_service.py` ให้ใช้ services ใหม่
4. เพิ่ม unit tests สำหรับ components ใหม่
