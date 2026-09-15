# Shared security headers. Nginx stops inheriting server-level headers when a
# location has any add_header directive, so include this file at both scopes.
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "accelerometer=(), camera=(), geolocation=(self), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()" always;
# Keep CSP strict for SPA routes while allowing required third-party services.
add_header Content-Security-Policy "default-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'; form-action 'self' https://accounts.google.com; script-src 'self' https://accounts.google.com https://maps.googleapis.com https://vercel.live https://*.vercel.live; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://vercel.live; font-src 'self' https://fonts.gstatic.com data:; img-src 'self' data: blob: https:; frame-src 'self' https://accounts.google.com https://vercel.live https://*.vercel.live; worker-src 'self' blob:; connect-src 'self' https://accounts.google.com https://maps.googleapis.com https://maps.gstatic.com https://poubdfhpujvqrkbcdzmc.supabase.co https://o4510681445761024.ingest.us.sentry.io wss://poubdfhpujvqrkbcdzmc.supabase.co https://ipapi.co https://purrfect-spots-backend.vercel.app;" always;
