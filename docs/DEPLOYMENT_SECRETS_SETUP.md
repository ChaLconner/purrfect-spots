# 🔐 Deployment Secrets Setup Guide

คู่มือการตั้งค่า Secrets สำหรับ CI/CD Pipeline ของ Purrfect Spots

> **สำคัญ**: Secrets ทั้งหมดต้องเพิ่มใน GitHub Repository Settings → Secrets and variables → Actions → New repository secret

---

## 📋 สารบัญ

1. [Vercel Secrets (Frontend)](#1-vercel-secrets-frontend)
2. [Railway Secrets (Backend - Option A)](#2-railway-secrets-backend---option-a)
3. [Render Secrets (Backend - Option B)](#3-render-secrets-backend---option-b)
4. [Environment URLs](#4-environment-urls)
5. [Backup Configuration (Optional)](#5-backup-configuration-optional)
6. [Quick Copy Checklist](#6-quick-copy-checklist)

---

## 1. Vercel Secrets (Frontend)

### 1.1 VERCEL_TOKEN

**วิธีสร้าง:**
1. ไปที่ [Vercel Dashboard](https://vercel.com/account/tokens)
2. คลิก "Create Token"
3. ตั้งชื่อ: `purrfect-spots-github-actions`
4. เลือก Scope: `Full Account` หรือเฉพาะ project
5. คลิก "Create"
6. **คัดลอก Token ทันที** (จะไม่แสดงอีก)

**รูปแบบ:**
```
VERCEL_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxx
```

**ตัวอย่าง (ความยาวจริง ~24 ตัวอักษร):**
```
pghHmNdKxxxxxXXXXX1234
```

---

### 1.2 VERCEL_ORG_ID และ VERCEL_PROJECT_ID

**วิธีสร้าง:**
1. ติดตั้ง Vercel CLI:
   ```bash
   npm install -g vercel
   ```
2. Login และ Link project:
   ```bash
   cd frontend
   vercel login
   vercel link
   ```
3. ดูไฟล์ `.vercel/project.json` ที่สร้างขึ้น:
   ```json
   {
     "orgId": "team_xxxxxxxxxxxxxxxxxx",
     "projectId": "prj_yyyyyyyyyyyyyyyyyy"
   }
   ```

**รูปแบบ:**
```
VERCEL_ORG_ID=team_xxxxxxxxxxxxxxxxxx
VERCEL_PROJECT_ID=prj_yyyyyyyyyyyyyyyyyy
```

**ตัวอย่าง:**
```
VERCEL_ORG_ID=team_1a2b3c4d5e6f7g8h
VERCEL_PROJECT_ID=prj_9i8h7g6f5e4d3c2b
```

---

## 2. Railway Secrets (Backend - Option A)

> ใช้ถ้าคุณ deploy Backend บน [Railway](https://railway.app)

### 2.1 RAILWAY_TOKEN

**วิธีสร้าง:**
1. ไปที่ [Railway Dashboard](https://railway.app/account/tokens)
2. คลิก "Create Token"
3. ตั้งชื่อ: `purrfect-spots-github-actions`
4. คัดลอก Token

**รูปแบบ:**
```
RAILWAY_TOKEN=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

**ตัวอย่าง:**
```
RAILWAY_TOKEN=a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

---

### 2.2 RAILWAY_PROJECT_ID

**วิธีหา:**
1. เปิด Railway Project ของคุณ
2. ไปที่ Settings → General
3. คัดลอก "Project ID"

**รูปแบบ:**
```
RAILWAY_PROJECT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

**ตัวอย่าง:**
```
RAILWAY_PROJECT_ID=b2c3d4e5-f6a7-8901-bcde-f23456789012
```

---

## 3. Render Secrets (Backend - Option B)

> ใช้ถ้าคุณ deploy Backend บน [Render](https://render.com)

### 3.1 RENDER_DEPLOY_HOOK_STAGING

**วิธีสร้าง:**
1. ไปที่ Render Dashboard → เลือก Service (Staging)
2. Settings → Deploy Hook
3. คลิก "Create Deploy Hook"
4. คัดลอก URL

**รูปแบบ:**
```
RENDER_DEPLOY_HOOK_STAGING=https://api.render.com/deploy/srv-xxxxxxxxxx?key=yyyyyyyyyy
```

**ตัวอย่าง:**
```
RENDER_DEPLOY_HOOK_STAGING=https://api.render.com/deploy/srv-abc123def456?key=rnd_XyZ789AbC
```

---

### 3.2 RENDER_DEPLOY_HOOK_PRODUCTION

**วิธีสร้าง:** เหมือนกับ Staging แต่ทำใน Production Service

**รูปแบบ:**
```
RENDER_DEPLOY_HOOK_PRODUCTION=https://api.render.com/deploy/srv-xxxxxxxxxx?key=yyyyyyyyyy
```

**ตัวอย่าง:**
```
RENDER_DEPLOY_HOOK_PRODUCTION=https://api.render.com/deploy/srv-xyz789ghi012?key=rnd_AbC123XyZ
```

---

## 4. Environment URLs

### 4.1 STAGING_API_URL

URL ของ Backend API บน Staging environment

**รูปแบบ:**
```
STAGING_API_URL=https://your-staging-api-domain.com
```

**ตัวอย่างตามแต่ละ Platform:**

| Platform | ตัวอย่าง URL |
|----------|-------------|
| Railway | `https://purrfect-spots-staging.up.railway.app` |
| Render | `https://purrfect-spots-staging.onrender.com` |
| Custom Domain | `https://staging-api.purrfect-spots.com` |

---

### 4.2 PROD_API_URL

URL ของ Backend API บน Production environment

**รูปแบบ:**
```
PROD_API_URL=https://your-production-api-domain.com
```

**ตัวอย่าง:**
```
PROD_API_URL=https://api.purrfect-spots.com
```

---

### 4.3 STAGING_SUPABASE_URL และ PROD_SUPABASE_URL (Optional)

**วิธีหา:**
1. ไปที่ [Supabase Dashboard](https://supabase.com/dashboard)
2. เลือก Project → Settings → API
3. คัดลอก "Project URL"

**รูปแบบ:**
```
STAGING_SUPABASE_URL=https://xxxxxxxx.supabase.co
PROD_SUPABASE_URL=https://yyyyyyyy.supabase.co
```

---

## 5. Backup Configuration (Optional)

> ใช้สำหรับ trigger database backup ก่อน production deployment

### 5.1 BACKUP_WEBHOOK_URL

URL ของ Backup Service (ถ้ามี)

**ตัวอย่าง:**
```
BACKUP_WEBHOOK_URL=https://your-backup-service.com/api/trigger-backup
```

### 5.2 BACKUP_API_KEY

API Key สำหรับ authenticate กับ Backup Service

**ตัวอย่าง:**
```
BACKUP_API_KEY=bkp_xxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 6. Quick Copy Checklist

### ✅ รายการ Secrets ทั้งหมดที่ต้องเพิ่ม

คัดลอก checklist นี้ไปใช้ตรวจสอบ:

```markdown
## Required Secrets

### Vercel (Frontend) ✅
- [ ] VERCEL_TOKEN
- [ ] VERCEL_ORG_ID
- [ ] VERCEL_PROJECT_ID

### Backend Hosting (เลือก 1 option)

#### Option A: Railway
- [ ] RAILWAY_TOKEN
- [ ] RAILWAY_PROJECT_ID

#### Option B: Render
- [ ] RENDER_DEPLOY_HOOK_STAGING
- [ ] RENDER_DEPLOY_HOOK_PRODUCTION

### Environment URLs ✅
- [ ] STAGING_API_URL
- [ ] PROD_API_URL

### Optional
- [ ] STAGING_SUPABASE_URL
- [ ] PROD_SUPABASE_URL
- [ ] BACKUP_WEBHOOK_URL
- [ ] BACKUP_API_KEY
```

---

## 📝 Template สำหรับ Copy-Paste ไป GitHub

### ขั้นตอนการเพิ่ม Secret ใน GitHub:

1. ไปที่ Repository → **Settings** → **Secrets and variables** → **Actions**
2. คลิก **"New repository secret"**
3. กรอก **Name** และ **Secret**
4. คลิก **"Add secret"**

### รายการ Secrets พร้อมชื่อ:

| Secret Name | คำอธิบาย | ตัวอย่างค่า |
|-------------|----------|-------------|
| `VERCEL_TOKEN` | Vercel API Token | `pghHmNdK...` |
| `VERCEL_ORG_ID` | Vercel Organization ID | `team_1a2b3c4d5e6f7g8h` |
| `VERCEL_PROJECT_ID` | Vercel Project ID | `prj_9i8h7g6f5e4d3c2b` |
| `RAILWAY_TOKEN` | Railway API Token | `a1b2c3d4-e5f6-...` |
| `RAILWAY_PROJECT_ID` | Railway Project ID | `b2c3d4e5-f6a7-...` |
| `STAGING_API_URL` | Staging Backend URL | `https://staging-api.example.com` |
| `PROD_API_URL` | Production Backend URL | `https://api.example.com` |

---

## 🔗 ลิงก์ที่เกี่ยวข้อง

- [Vercel Tokens](https://vercel.com/account/tokens)
- [Railway Tokens](https://railway.app/account/tokens)
- [Render Deploy Hooks](https://render.com/docs/deploy-hooks)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Supabase Project Settings](https://supabase.com/dashboard)

---

## ⚠️ ข้อควรระวัง

1. **อย่าเปิดเผย Secrets** ใน code หรือ commit ลง git
2. **หมุนเวียน Tokens** เป็นประจำ (ทุก 6-12 เดือน)
3. **ใช้ Environment Secrets** สำหรับ production เพื่อเพิ่มความปลอดภัย
4. **ตรวจสอบ Token Scope** ให้มีสิทธิ์เท่าที่จำเป็นเท่านั้น

---

*สร้างโดย Purrfect Spots Team | อัปเดตล่าสุด: 2026-01-22*
