# Stripe Environment Setup

To enable the Subscription and Treats features, you need to configure your Stripe account and update the `.env` files.

## Backend `.env` (`c:\purrfect-spots\backend\.env`)

Add the following keys:

```ini
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_... (Your Secret Key)
STRIPE_WEBHOOK_SECRET=whsec_... (Your Webhook Secret)

# Product Price IDs (Create these in Stripe Dashboard)
# Subscription
STRIPE_PRO_PRICE_ID=price_... (Price ID for Monthly Subscription)

# One-time Treats
STRIPE_TREAT_SMALL_PRICE_ID=price_... (Price for Small Treat Pack)
STRIPE_TREAT_MEDIUM_PRICE_ID=price_... (Price for Medium Treat Pack)
STRIPE_TREAT_LARGE_PRICE_ID=price_... (Price for Large Treat Pack)
```

## Frontend `.env` (`c:\purrfect-spots\frontend\.env`)

Add the publishable key (if you use Stripe Elements in frontend, though we used Checkout redirection which mainly uses backend, but good to have):

```ini
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_...
VITE_STRIPE_PRO_PRICE_ID=price_... (Same as backend PRO price ID)
```

## Stripe Dashboard Setup

1.  **Create Products**:
    *   **Pro Subscription**: Recurring, Monthly. Copy the Price ID to `STRIPE_PRO_PRICE_ID`.
    *   **Small Treats**: One-time product. Copy Price ID to `STRIPE_TREAT_SMALL_PRICE_ID`.
    *   **Medium Treats**: One-time product. Copy Price ID to `STRIPE_TREAT_MEDIUM_PRICE_ID`.
    *   **Large Treats**: One-time product. Copy Price ID to `STRIPE_TREAT_LARGE_PRICE_ID`.
    
2.  **Webhooks**:
    *   Add a local listener endpoint (using Stripe CLI): `stripe listen --forward-to localhost:8000/api/v1/subscription/webhook`
    *   Or configure in dashboard for production URL.
    *   Copy the Signing Secret to `STRIPE_WEBHOOK_SECRET`.
