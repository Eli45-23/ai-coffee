# AIChatFlows Configuration

## Email Configuration

The following environment variables are required for email functionality:

### Required Variables
- `SMTP_USERNAME` - Gmail username for sending emails
- `SMTP_PASSWORD` - Gmail app password (not regular password)
- `ADMIN_EMAIL` - Email address to receive admin notifications (defaults to eliascolon23@gmail.com)

### Optional Variables
- `SMTP_SERVER` - SMTP server (defaults to smtp.gmail.com)
- `SMTP_PORT` - SMTP port (defaults to 587)
- `FROM_EMAIL` - Email address shown as sender (defaults to noreply@aichatflows.com)

## Email Flow

1. **After form submission**: User receives confirmation email, admin receives notification email
2. **After payment completion**: User receives payment confirmation email, admin receives payment notification email

## Stripe Configuration

- `STRIPE_STARTER_URL` - Stripe checkout URL for Starter plan
- `STRIPE_PRO_URL` - Stripe checkout URL for Pro plan
- `SUCCESS_URL` - URL to redirect after successful payment (defaults to /thank-you)

## Development Commands

- `python -m uvicorn app.main:app --reload` - Start development server
- `npm run lint` - Run linting (if available)
- `npm run typecheck` - Run type checking (if available)