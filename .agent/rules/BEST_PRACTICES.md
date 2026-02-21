# Purrfect Spots Best Practices & Patterns

This document provides concrete code examples for the rules outlined in [`CODING_STANDARDS.md`](./CODING_STANDARDS.md).

## 1. API Responses & Error Handling

**Bad Pattern:** Inconsistent error responses returned directly from routes.
```python
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    user = db.get_user(user_id)
    if not user:
        return {"error": "User not found"} # Inconsistent!
    return user
```

**Good Pattern:** Raise a custom exception in the service; Global Error Handler formats it.
```python
# service.py
def get_user(user_id: int):
    user = db.get_user(user_id)
    if not user:
        raise ResourceNotFoundError(message="User not found", details={"user_id": user_id})
    return user

# global_handler.py (FastAPI exception handler)
@app.exception_handler(ResourceNotFoundError)
async def not_found_handler(request: Request, exc: ResourceNotFoundError):
    return JSONResponse(
        status_code=404,
        content={
            "error_code": "RESOURCE_NOT_FOUND",
            "message": exc.message,
            "details": exc.details
        }
    )
```

## 2. Database & ORM (N+1 Problem)

**Bad Pattern:** Lazy loading relations inside a loop (N+1 queries).
```python
# This triggers 1 query for users, and N queries for each user's profile
users = session.scalars(select(User)).all()
for user in users:
    print(user.profile.bio) 
```

**Good Pattern:** Eager loading relations.
```python
# Triggers only 1 query with a JOIN
from sqlalchemy.orm import selectinload

users = session.scalars(select(User).options(selectinload(User.profile))).all()
for user in users:
    print(user.profile.bio)
```

## 3. Frontend Async / API Calls

**Bad Pattern:** No error handling or loading state.
```vue
<script setup lang="ts">
const users = ref([])

onMounted(async () => {
  // If this fails, the UI breaks silently
  const res = await api.get('/users')
  users.value = res.data
})
</script>
```

**Good Pattern:** Proper loading and error states with try/catch.
```vue
<script setup lang="ts">
const users = ref([])
const isLoading = ref(false)
const error = ref<string | null>(null)

onMounted(async () => {
  isLoading.value = true
  error.value = null
  try {
    const res = await api.get('/users')
    users.value = res.data
  } catch (err: any) {
    error.value = err.message || 'Failed to fetch users'
    // Log to structured logger or Sentry if critical
  } finally {
    isLoading.value = false
  }
})
</script>
```

## 4. Logging & Monitoring

**Bad Pattern:** Using `print` and logging sensitive data.
```python
def login(username, password):
    print(f"User {username} trying to log in with password {password}") # CRITICAL SILENT LEAK
    # ...
```

**Good Pattern:** Structured logging with Scrubbed Data and context.
```python
import structlog

logger = structlog.get_logger()

def login(username):
    logger.info("user_login_attempt", user_id=username) 
    # Password is not logged. Sentry integration automatically picks this up.
```

## 5. Tailwind CSS & Styling

**Bad Pattern:** Hardcoding arbitrary values (e.g., `w-[245px]`, `bg-[#3b82f6]`) and repeating the same long list of utility classes everywhere instead of building a reusable component.
```vue
<template>
  <button class="bg-[#3b82f6] hover:bg-[#2563eb] text-white px-[20px] py-[10px] rounded-[5px]">
    Submit
  </button>
  <button class="bg-[#ef4444] hover:bg-[#dc2626] text-white px-[20px] py-[10px] rounded-[5px]">
    Cancel
  </button>
</template>
```

**Good Pattern:** Using design system tokens (e.g., `px-4`, `bg-blue-600`) and extracting repeatable UI elements into reusable Vue components using props and computed classes. This makes global design updates trivial.

```vue
<!-- components/BaseButton.vue -->
<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  variant?: 'primary' | 'secondary' | 'danger'
  type?: 'button' | 'submit' | 'reset'
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  type: 'button',
  disabled: false
})

const variantClasses = computed(() => {
  switch (props.variant) {
    case 'primary':
      return 'bg-blue-600 hover:bg-blue-700 text-white focus:ring-blue-500'
    case 'secondary':
      return 'bg-gray-200 hover:bg-gray-300 text-gray-900 focus:ring-gray-500'
    case 'danger':
      return 'bg-red-600 hover:bg-red-700 text-white focus:ring-red-500'
  }
})
</script>

<template>
  <button 
    :type="props.type"
    :disabled="props.disabled"
    class="inline-flex items-center justify-center px-4 py-2 text-sm font-medium rounded-md transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
    :class="variantClasses"
  >
    <slot></slot>
  </button>
</template>
```

**How to use the component:**
```vue
<!-- views/ExampleView.vue -->
<script setup lang="ts">
import BaseButton from '@/components/BaseButton.vue'

const handleSubmit = () => {
  console.log('Form submitted!')
}
</script>

<template>
  <div class="flex gap-4 p-6">
    <BaseButton variant="primary" @click="handleSubmit">
      Submit Form
    </BaseButton>
    <BaseButton variant="danger" type="reset">
      Cancel
    </BaseButton>
  </div>
</template>
```

## 6. Componentization & File Size Limits

**Bad Pattern:** A single massive file handling too many responsibilities (e.g., API calls, complex state management, and large amounts of markup in one 500+ line component). This makes the code difficult to read, test, and maintain.

**Good Pattern:** Keep files small, focused, and ideally under 250-300 lines. Break down large components into smaller, single-responsibility sub-components, and extract complex logic into composables (frontend) or separate services (backend).

```vue
<!-- components/Dashboard/Dashboard.vue (Parent Component) -->
<script setup lang="ts">
import DashboardStats from './DashboardStats.vue'
import DashboardChart from './DashboardChart.vue'
// Logic extracted to a composable
import { useDashboardData } from '@/composables/useDashboardData'

const { stats, chartData, isLoading } = useDashboardData()
</script>

<template>
  <div class="space-y-6">
    <!-- UI broken down into smaller components -->
    <DashboardStats :data="stats" :is-loading="isLoading" />
    <DashboardChart :data="chartData" :is-loading="isLoading" />
  </div>
</template>
```
