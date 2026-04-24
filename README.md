# CustomPythonApp

## Support Page

This project includes a dedicated support and feedback page at `/support`.

What it does:

- shows the Konticode support/donation experience
- starts Stripe Checkout for one-time and monthly support
- opens a feedback form that posts to `/api/feedback`

Main files:

- `static/index.html`
- `static/styles.css`
- `static/css/konticode-theme.css`
- `static/config.js`
- `static/widget.js`
- `templates/donation_success.html`
- `main.py`

### Stripe Configuration

The live support flow uses backend-created Stripe Checkout Sessions, not static payment links.

Required environment variables:

- `STRIPE_SECRET_KEY`
- `STRIPE_PRICE_DONATION_5`
- `STRIPE_PRICE_MONTHLY_SUPPORT`

Optional:

- `STRIPE_WEBHOOK_SECRET`
- `PUBLIC_BASE_URL`

Recommended Stripe setup:

1. Create a one-time Stripe Price for the `$5` donation.
2. Create a recurring monthly Stripe Price for ongoing support.
3. Copy those `price_...` IDs into `.env`.
4. Add your `STRIPE_SECRET_KEY`.
5. Restart the app and test `/support`.

Example `.env` values:

```env
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PRICE_DONATION_5=price_...
STRIPE_PRICE_MONTHLY_SUPPORT=price_...
STRIPE_WEBHOOK_SECRET=whsec_...
PUBLIC_BASE_URL=https://konticode.com
```

How the donation flow works:

1. The support page shows the donation/support UI.
2. Clicking `Donate now` or `Become a supporter` calls `POST /api/create-checkout-session`.
3. The Flask backend reads the configured Stripe Price ID from `.env`.
4. Stripe returns a hosted Checkout URL.
5. The browser redirects to Stripe Checkout.
6. After payment, Stripe returns the donor to `/support/success`.

Current plans wired in code:

- one-time donation: `STRIPE_PRICE_DONATION_5`
- monthly support: `STRIPE_PRICE_MONTHLY_SUPPORT`

Related endpoints:

- `POST /api/create-checkout-session`
- `POST /api/create-portal-session`
- `POST /api/stripe-webhook`

### Feedback Configuration

The support page feedback form submits JSON to:

- `POST /api/feedback`

The backend then sends the message through the configured Gmail OAuth mail flow.

## External Budget Tracker Link

You can redirect Budget Tracker traffic to an external app (for example Railway) without changing templates.

Set this environment variable in local `.env` and Railway variables:

- `BUDGET_TRACKER_URL=https://your-budget-tracker.up.railway.app`

Behavior:

1. `/budget-tracker` redirects to `BUDGET_TRACKER_URL` when set.
2. `/budget-tracker/<path>` forwards to `BUDGET_TRACKER_URL/<path>` when set.
3. If `BUDGET_TRACKER_URL` is missing or invalid, the local `templates/budget_tracker.html` page is served.

## Marketing Analytics Playbook

This project uses Google Analytics (gtag) to track conversion behavior across marketing pages.

### Goals

1. Keep **contact-first conversion** as the primary path.
2. Keep **agent-first exploration** as the secondary path.
3. Track both paths with consistent event naming so results are comparable over time.

## Event Taxonomy

### Event: `cta_click`

Fired when a user clicks any tracked CTA element with `data-cta`.

Required params:

- `cta_name`: normalized action key (example: `book_intro_call`)
- `cta_location`: page and section key (example: `landing_hero`)
- `destination`: CTA href value

### Event: `contact_form_submit`

Fired after successful submit of the main contact form.

Required params:

- `form_name`: static key for form identity
- `subject`: selected contact subject value

## Naming Conventions

### `cta_name`

Use snake_case, verb-first where possible.

Preferred examples:

- `book_intro_call`
- `try_live_agent`
- `open_dashboard`
- `view_capabilities`
- `see_delivery_model`
- `see_platform_stack`
- `contact_submit`

### `cta_location`

Use `<page>_<section>` in snake_case.

Preferred examples:

- `landing_header`, `landing_hero`, `landing_footer`
- `about_header`, `about_hero`, `about_footer`
- `features_header`, `features_footer`
- `demo_header`, `demo_footer`
- `tech_header`, `tech_footer`
- `contact_header`, `contact_sidebar`, `contact_form`
- `affiliate_header`, `affiliate_cards`, `affiliate_footer`

## Current Funnel Map

### Stage 1: Awareness

Pages:

- landing
- about
- features
- demo
- tech
- affiliate

Signal:

- `cta_click` from header and hero CTA locations

### Stage 2: Exploration

Pages:

- features
- demo
- contact sidebar

Signal:

- `cta_click` where `cta_name = try_live_agent`

### Stage 3: Intent

Pages:

- landing/footer
- about/footer
- features/footer
- demo/footer
- tech/footer
- affiliate/footer

Signal:

- `cta_click` where `cta_name = book_intro_call`

### Stage 4: Lead Conversion

Page:

- contact

Signals:

- `cta_click` where `cta_name = contact_submit`
- `contact_form_submit`

## Where Tracking Is Implemented

- `templates/landing.html`
- `templates/about.html`
- `templates/features.html`
- `templates/demo.html`
- `templates/tech.html`
- `templates/contact.html`
- `templates/affiliatehub.html`

## Add New CTA Tracking (Checklist)

1. Add `data-cta="..."` to the CTA element.
2. Add `data-cta-location="..."` to the CTA element.
3. Reuse existing page-level click listener (or add one only if missing).
4. Keep names in snake_case and aligned to taxonomy above.
5. Validate no template errors in editor.

## QA Verification

1. Open a page with tracked CTA.
2. Click CTA in browser.
3. Confirm GA DebugView receives event:
   - `cta_click` with correct params.
4. Submit contact form successfully.
5. Confirm GA DebugView receives:
   - `contact_form_submit` with `form_name` and `subject`.

## Reporting Recommendations (GA4)

Create the following views:

1. **Primary CTA Performance**
   - Filter `cta_click` where `cta_name = book_intro_call`
   - Breakdown by `cta_location`

2. **Secondary CTA Performance**
   - Filter `cta_click` where `cta_name = try_live_agent`
   - Breakdown by `cta_location`

3. **Contact Conversion Rate Proxy**
   - `contact_form_submit` count
   - Divided by `book_intro_call` click count

4. **Affiliate Exit Performance**
   - Filter `cta_click` where `cta_name` starts with `affiliate_`
   - Breakdown by `cta_name`

## GA4 Custom Dimensions Setup

Use this checklist in GA4 so event parameters appear in standard reports and Explorations.

Navigation:

1. GA4 Admin
2. Data display
3. Custom definitions
4. Create custom dimension

### Create Event-Scoped Custom Dimensions

Create the following dimensions exactly:

1. Dimension name: `CTA Name`
   - Scope: Event
   - Event parameter: `cta_name`
