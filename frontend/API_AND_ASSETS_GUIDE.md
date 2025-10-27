# API and Assets Management Guide

## API Management

### Centralized Error Handling

This project uses a centralized error management system through the file `src/utils/api.ts` which has the following features:

- **ApiError Types**: Define different types of errors (NETWORK_ERROR, AUTHENTICATION_ERROR, AUTHORIZATION_ERROR, VALIDATION_ERROR, SERVER_ERROR, UNKNOWN_ERROR)
- **Automatic Token Management**: System will add token in request headers automatically
- **Error Interceptors**: Handle errors from server automatically and convert to easy-to-understand messages
- **Automatic Logout**: If token expires, system will clear authentication data and redirect to login page

### API Usage

```typescript
import { api, ApiError, ApiErrorType } from '../utils/api';

// GET request
try {
  const data = await api.get('/endpoint');
  console.log(data);
} catch (error) {
  if (error instanceof ApiError) {
    // Handle specific error types
    switch (error.type) {
      case ApiErrorType.NETWORK_ERROR:
        // Handle network error
        break;
      case ApiErrorType.AUTHENTICATION_ERROR:
        // Handle authentication error
        break;
      // ... other error types
    }
  }
}

// POST request
try {
  const result = await api.post('/endpoint', { key: 'value' });
  console.log(result);
} catch (error) {
  // Handle error
}

// File upload
try {
  const result = await uploadFile('/upload/endpoint', file, additionalData, (progressEvent) => {
    const percentCompleted = Math.round(
      (progressEvent.loaded * 100) / progressEvent.total
    );
    console.log(`Upload progress: ${percentCompleted}%`);
  });
} catch (error) {
  // Handle upload error
}
```

## Assets Management

### CDN Configuration

For production usage, you can set up CDN for static assets by:

1. Create a `.env` file in the frontend folder
2. Add the variable `VITE_CDN_BASE_URL`:

```
VITE_CDN_BASE_URL=https://your-cdn-domain.com/assets
```

### Image Optimization

This project has an image management system using the file `src/utils/imageUtils.ts` which has the following functions:

- **optimizeImage**: Resize and optimize image quality before upload
- **validateImageFile**: Validate file type and size
- **generateThumbnail**: Create small thumbnail
- **getCDNUrl**: Create URL for images via CDN
- **createResponsiveImage**: Create img element with srcset for responsive images

### Image Optimization Usage

```typescript
import { optimizeImage, validateImageFile, getCDNUrl } from '../utils/imageUtils';

// Validate image file
const validation = validateImageFile(file);
if (!validation.valid) {
  console.error(validation.error);
  return;
}

// Optimize image before upload
const optimizedFile = await optimizeImage(file, {
  maxWidth: 1920,
  maxHeight: 1080,
  quality: 85,
  format: 'jpeg',
});

// Get CDN URL for an image
const cdnUrl = getCDNUrl(imageUrl, {
  maxWidth: 800,
  quality: 80,
});
```

### Image Optimization Configuration

You can configure image management through environment variables:

```
# Maximum image width for optimization (in pixels)
VITE_MAX_IMAGE_WIDTH=1920

# Maximum image height for optimization (in pixels)
VITE_MAX_IMAGE_HEIGHT=1080

# Image quality for optimization (0-100)
VITE_IMAGE_QUALITY=85

# Maximum file size for upload (in MB)
VITE_MAX_FILE_SIZE=10
```

## Production Configuration

### CDN Configuration for Production

1. Set `VITE_CDN_BASE_URL` in your environment variables
2. Upload assets from `dist/assets` folder to your CDN
3. Configure CDN to work with your assets

### Production Build

```bash
# Build for production with CDN support
npm run build:prod
```

## Notes

1. **Token Management**: System will manage tokens automatically, but you must ensure to call `initializeAuth()` when the application starts
2. **Error Handling**: Should use try-catch with every API call to handle errors appropriately
3. **Image Optimization**: Image resizing will occur on the client side before upload, which may take some time for large images
4. **CDN Configuration**: Ensure that your CDN is properly configured before using in production