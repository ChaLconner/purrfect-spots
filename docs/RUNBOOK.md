# 📋 Operations Runbook - Purrfect Spots

This runbook provides operational procedures for common issues and maintenance tasks.

---

## 📊 Health Check Endpoints

| Endpoint | Purpose | Expected Response |
|----------|---------|-------------------|
| `GET /health/live` | Liveness probe | `{"status": "alive"}` |
| `GET /health/ready` | Readiness probe | `{"status": "ready", "checks": {...}}` |
| `GET /health/dependencies` | Detailed health | Full dependency status |
| `GET /health/metrics` | Basic metrics | Cache stats, env info |

---

## 🚨 Common Issues & Solutions

### 1. High Error Rate (>5%)

**Symptoms:**
- Sentry alerts showing spike in errors
- Users reporting "Something went wrong" messages
- Increased 5xx responses in logs

**Diagnosis:**
```bash
# Check Sentry dashboard for error patterns
# https://sentry.io/organizations/[your-org]/issues/

# Check application logs
vercel logs --app=purrfect-spots-api

# Check health endpoint
curl https://api.purrfect-spots.com/health/dependencies
```

**Resolution Steps:**
1. Identify the most common error in Sentry
2. Check if error started after a recent deployment
3. If yes, consider rollback:
   ```bash
   vercel rollback
   ```
4. If database related, check Supabase dashboard for issues
5. Escalate if unresolvable in 30 minutes

---

### 2. Database Connection Issues

**Symptoms:**
- `/health/ready` shows `database: unhealthy`
- "Connection timeout" or "Pool exhausted" errors
- Slow API responses

**Diagnosis:**
```bash
# Check database health
curl https://api.purrfect-spots.com/health/dependencies | jq '.dependencies.database'

# Expected output for healthy:
# {"status": "healthy", "latency_ms": 50, "connection": "active"}
```

**Resolution Steps:**

1. **Check Supabase Dashboard:**
   - Visit https://app.supabase.com/project/[project-id]
   - Check "Database" → "System Health"
   - Look for high connection count or CPU usage

2. **If connection pool exhausted:**
   - Increase `DB_POOL_SIZE` in environment variables
   - Default: 10, Safe max: 50
   ```bash
   vercel env add DB_POOL_SIZE 20 production
   vercel --prod
   ```

3. **If slow queries:**
   - Check Supabase "SQL Editor" → "Query Performance"
   - Look for missing indexes
   - Consider adding indexes per `docs/DATABASE_SCHEMA.md`

4. **Emergency: Connection leak:**
   - Restart the serverless function:
   ```bash
   vercel --prod --force
   ```

---

### 3. Redis Connection Failed

**Symptoms:**
- `/health/ready` shows `redis: unhealthy`
- Rate limiting not working (all requests passing)
- Cache not working (slow responses)

**Impact:** Medium - Application still works but without caching/rate limiting.

**Diagnosis:**
```bash
curl https://api.purrfect-spots.com/health/dependencies | jq '.dependencies.redis'
```

**Resolution Steps:**

1. **Check Redis provider dashboard:**
   - Upstash: https://console.upstash.com
   - Redis Labs: https://app.redislabs.com

2. **Verify REDIS_URL is correct:**
   ```bash
   vercel env pull
   cat .vercel/.env.production.local | grep REDIS
   ```

3. **Test connection manually:**
   ```bash
   redis-cli -u $REDIS_URL ping
   ```

4. **If Redis is down:**
   - Application continues with in-memory fallback
   - Monitor Sentry for rate-limit bypass abuse
   - Contact Redis provider support

---

### 4. S3 Upload Failures

**Symptoms:**
- Upload button shows error
- `/health/dependencies` shows `s3: unhealthy`
- "Access Denied" or "Bucket not found" errors

**Diagnosis:**
```bash
curl https://api.purrfect-spots.com/health/dependencies | jq '.dependencies.s3'
```

**Resolution Steps:**

1. **Check AWS Console:**
   - Verify S3 bucket exists
   - Check IAM credentials haven't expired

2. **Verify credentials:**
   ```bash
   aws s3 ls s3://$AWS_S3_BUCKET/ --max-items 1
   ```

3. **Rotate credentials if compromised:**
   - Create new IAM access key in AWS Console
   - Update in Vercel:
   ```bash
   vercel env rm AWS_ACCESS_KEY_ID production
   vercel env add AWS_ACCESS_KEY_ID [NEW_KEY] production
   vercel env rm AWS_SECRET_ACCESS_KEY production
   vercel env add AWS_SECRET_ACCESS_KEY [NEW_SECRET] production
   vercel --prod
   ```

---

### 5. Rate Limiting Too Aggressive

**Symptoms:**
- Users complaining about "Too many requests" errors
- Legitimate API calls being blocked
- 429 responses in logs

**Diagnosis:**
```bash
# Check current rate limits
curl https://api.purrfect-spots.com/health/metrics | jq '.cache'
```

**Resolution Steps:**

1. **Adjust rate limits:**
   Update environment variables:
   ```bash
   # Default values - adjust as needed
   RATE_LIMIT_AUTH=10/minute        # Login attempts
   RATE_LIMIT_API_DEFAULT=100/minute # General API
   UPLOAD_RATE_LIMIT=10/minute      # File uploads
   ```

2. **If specific IP is affected:**
   - Check if it's a legitimate user vs. attacker
   - Redis: Delete rate limit key manually
   ```bash
   redis-cli -u $REDIS_URL keys "rate:*:$IP" | xargs redis-cli del
   ```

---

### 6. Cat Detection Not Working

**Symptoms:**
- Uploads failing at cat detection step
- "No cat detected" for images with cats
- Vision API errors in logs

**Diagnosis:**
```bash
curl https://api.purrfect-spots.com/health/dependencies | jq '.dependencies.google_vision'
```

**Resolution Steps:**

1. **Check Google Cloud Console:**
   - Visit https://console.cloud.google.com/apis/credentials
   - Verify Vision API is enabled
   - Check quota usage

2. **Verify credentials file:**
   - Ensure `keys/google_vision.json` exists
   - File should have valid service account JSON

3. **If quota exceeded:**
   - Wait for quota reset (usually daily)
   - Or request quota increase in GCP Console

---

## 🔄 Routine Maintenance

### Daily
- [ ] Check Sentry for new errors (https://sentry.io)
- [ ] Review health endpoint status
- [ ] Check Vercel deployment status

### Weekly
- [ ] Review error trends in Sentry
- [ ] Check database size and growth
- [ ] Review rate limiting effectiveness
- [ ] Check S3 storage usage

### Monthly
- [ ] Rotate JWT secrets (see `docs/KEY_ROTATION.md`)
- [ ] Update dependencies (`npm update`, `pip install -U`)
- [ ] Review and update security headers
- [ ] Backup database (Supabase handles automatically)

---

## 📞 Escalation Contacts

| Issue Type | Primary Contact | Escalation |
|------------|-----------------|------------|
| Application Errors | Dev Team | Tech Lead |
| Database Issues | Dev Team | Supabase Support |
| AWS/S3 Issues | Dev Team | AWS Support |
| Security Incident | Tech Lead | Security Team |

---

## 🔧 Useful Commands

### Vercel
```bash
# View logs
vercel logs --app=purrfect-spots-api

# Rollback to previous deployment
vercel rollback

# Force redeploy
vercel --prod --force

# Check environment variables
vercel env ls production
```

### Database (Supabase)
```bash
# Access via Supabase CLI
supabase login
supabase db push
supabase db diff
```

### Redis
```bash
# Check connection
redis-cli -u $REDIS_URL ping

# View keys
redis-cli -u $REDIS_URL keys "*"

# Clear all cache
redis-cli -u $REDIS_URL flushdb
```

---

## 📝 Incident Response Template

When reporting an incident, include:

```markdown
## Incident Report

**Date/Time:** YYYY-MM-DD HH:MM UTC
**Severity:** Critical/High/Medium/Low
**Duration:** X minutes/hours

### Summary
Brief description of what happened.

### Impact
- Number of users affected
- Features impacted
- Business impact

### Timeline
- HH:MM - Issue detected
- HH:MM - Root cause identified
- HH:MM - Fix deployed
- HH:MM - Issue resolved

### Root Cause
Technical explanation of why this happened.

### Resolution
What was done to fix it.

### Prevention
What changes will prevent recurrence.
```
