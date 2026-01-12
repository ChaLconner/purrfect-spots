# 🔧 Dependency Update Guide

This document outlines the deprecation warnings and recommended updates for external dependencies.

## Current Deprecation Warnings

### 1. `asyncio.iscoroutinefunction` Deprecation (Python 3.16)

**Affected Libraries:**
- `slowapi` - Rate limiting library
- `sentry_sdk` - Error tracking

**Source of Warning:**
```
DeprecationWarning: 'asyncio.iscoroutinefunction' is deprecated and slated for 
removal in Python 3.16; use inspect.iscoroutinefunction() instead
```

**Action Required:** Wait for library updates
- Monitor [slowapi releases](https://github.com/laurentS/slowapi/releases)
- Monitor [sentry-python releases](https://github.com/getsentry/sentry-python/releases)

**Workaround:** These warnings don't affect functionality and Python 3.16 is not yet released.

---

### 2. `Pillow Image.getdata()` Deprecation (Pillow 14)

**Location:** `backend/utils/image_utils.py:59`

**Current Code:**
```python
img_data = list(img.getdata())
```

**Recommended Fix:**
```python
# Use get_flattened_data instead (Pillow 14+)
img_data = list(img.get_flattened_data())
```

**Timeline:** Pillow 14 release scheduled for October 2027

**Action:** Update when upgrading to Pillow 14+

---

### 3. `datetime.utcnow()` Deprecation (Python 3.12+)

**Status:** ✅ FIXED

We have updated all occurrences to use timezone-aware datetime:

**Old Code:**
```python
datetime.utcnow().isoformat()
```

**New Code:**
```python
from utils.datetime_utils import utc_now, utc_now_iso
utc_now_iso()  # For ISO strings
utc_now()      # For datetime objects
```

---

## Recommended Dependency Updates

Run these commands to update dependencies:

### Backend (Python)

```bash
cd backend

# Update all dependencies to latest compatible versions
pip install --upgrade slowapi sentry-sdk pillow

# Check for outdated packages
pip list --outdated
```

### Frontend (Node.js)

```bash
cd frontend

# Install new linting dependencies
npm install --save-dev eslint eslint-plugin-vue @typescript-eslint/parser @typescript-eslint/eslint-plugin prettier typescript-eslint

# Update all packages
npm update

# Check for outdated packages
npm outdated
```

---

## Version Compatibility Matrix

| Package | Current | Recommended | Notes |
|---------|---------|-------------|-------|
| **Backend** |
| Python | 3.14.2 | 3.12+ | Current version works |
| slowapi | latest | latest | Wait for asyncio fix |
| sentry-sdk | latest | latest | Wait for asyncio fix |
| Pillow | latest | <14.0 | Update image_utils when upgrading |
| **Frontend** |
| Vue | 3.5.17 | 3.5+ | ✅ Up to date |
| TypeScript | 5.8.3 | 5.8+ | ✅ Up to date |
| Vite | 7.0.0 | 7.0+ | ✅ Up to date |
| ESLint | 8.57.0 | 9.0+ | New flat config format |

---

## Testing After Updates

After updating dependencies, run:

```bash
# Backend tests
cd backend
python -m pytest --tb=short

# Frontend tests  
cd frontend
npm test

# Type checking
npm run type-check

# Linting (new)
npm run lint:check
```

---

## Monitoring Resources

- [Python Release Schedule](https://devguide.python.org/versions/)
- [Pillow Changelog](https://pillow.readthedocs.io/en/stable/releasenotes/)
- [Vue.js Blog](https://blog.vuejs.org/)
- [ESLint Blog](https://eslint.org/blog/)

---

Last Updated: 2026-01-12
