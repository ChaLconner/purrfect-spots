# 🚀 Production Setup Guide

This guide details exactly how to obtain and configure the necessary tokens and secrets for:
1. Production Environment (Vercel)
2. CI/CD Pipeline (GitHub Actions)

---

## 1. Getting the Values (วิธีรับค่าต่างๆ)

### A. Sentry DSN (Error Monitoring)
1. Log in to [Sentry.io](https://sentry.io/).
2. Create a new Vue.js project (for frontend).
3. Go to **Settings** > **Client Keys (DSN)**.
4. Copy the DSN URL.

### B. AWS S3 Keys (Image Storage)
1. Log in to [AWS Console](https://console.aws.amazon.com/).
2. Go to **IAM** service.
3. Users > Create User (e.g., `purrfect-spots-app`).
4. Attach policies: `AmazonS3FullAccess` (or strict bucket policy).
5. Open the User > **Security credentials** tab.
6. Click **Create access key**.
7. **Copy explicitly:** `Access key ID` and `Secret access key`.

### C. Vercel Tokens (Deployment)
1. Log in to [Vercel Account Tokens](https://vercel.com/account/tokens).
2. Click **Create Token**.
3. Name: `GitHub Actions CI`.
4. Copy the token string.

### D. Vercel Project IDs
Run these commands in your local project root:
```bash
# Link your project if not already linked
vercel link
```
Check `.vercel/project.json` (this file is git-ignored):
- `orgId` -> This is your `VERCEL_ORG_ID`
- `projectId` -> This is your `VERCEL_PROJECT_ID` (note: you might have separate IDs for frontend and backend projects if you deployed them separately).

---

## 2. Setting Production Environment Variables (Vercel)

These variables are used by the running application in production.

### Option 1: Via Dashboard (Easier)
1. Go to your Project Settings on Vercel.
2. Select **Environment Variables**.
3. Add the following:

| Variable Name | Environment | Description |
|---------------|-------------|-------------|
| `VITE_SENTRY_DSN` | Production | From Step 1A |
| `AWS_ACCESS_KEY_ID` | Production | From Step 1B |
| `AWS_SECRET_ACCESS_KEY` | Production | From Step 1B |
| `DB_POOL_SIZE` | Production | Set to `20` (recommended) |

### Option 2: Via CLI
```bash
vercel env add VITE_SENTRY_DSN production
vercel env add AWS_ACCESS_KEY_ID production
vercel env add AWS_SECRET_ACCESS_KEY production
```

**After adding variables, you MUST redeploy:**
```bash
vercel --prod
```

---

## 3. Setting GitHub Secrets (CI/CD)

These secrets allow GitHub Actions to deploy your code.

1. Go to your GitHub Repository.
2. Click **Settings** > **Secrets and variables** > **Actions**.
3. Click **New repository secret**.
4. Add the following secrets:

### Required Secrets

| Secret Name | Value Needed |
|-------------|--------------|
| `VERCEL_TOKEN` | Token from Step 1C |
| `VERCEL_ORG_ID` | `orgId` from Step 1D |
| `VERCEL_PROJECT_ID` | `projectId` from Step 1D (Frontend) |
| `VERCEL_PROJECT_ID_BACKEND` | `projectId` of Backend Project (if separate) |

### Optional Secrets (For Testing/Build)

| Secret Name | Description |
|-------------|-------------|
| `CODECOV_TOKEN` | If using Codecov for coverage |
| `VITE_GOOGLE_CLIENT_ID` | For frontend tests |
| `VITE_GOOGLE_MAPS_API_KEY`| For frontend tests |
| `JWT_SECRET` | Use a dummy value for CI tests |

---

## 4. Troubleshooting Permission Issues

### S3 Access Denied
If you see `Access Denied` when uploading images:
1. Go to AWS S3 Console > Your Bucket > Permissions.
2. **CORS Configuration**:
   ```json
   [
       {
           "AllowedHeaders": ["*"],
           "AllowedMethods": ["GET", "PUT", "POST", "HEAD"],
           "AllowedOrigins": ["https://your-vercel-domain.app"],
           "ExposeHeaders": []
       }
   ]
   ```
3. **Bucket Policy** (Ensure the user has access):
   ```json
   {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Effect": "Allow",
               "Principal": { "AWS": "arn:aws:iam::[ACCOUNT_ID]:user/[USER_NAME]" },
               "Action": "s3:*",
               "Resource": [
                   "arn:aws:s3:::[BUCKET_NAME]",
                   "arn:aws:s3:::[BUCKET_NAME]/*"
               ]
           }
       ]
   }
   ```
