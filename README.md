# CustomPythonApp

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
	- Description: Primary action key for CTA click events.

2. Dimension name: `CTA Location`
	- Scope: Event
	- Event parameter: `cta_location`
	- Description: Page/section identifier for CTA placement.

3. Dimension name: `CTA Destination`
	- Scope: Event
	- Event parameter: `destination`
	- Description: CTA href target URL or path.

4. Dimension name: `Contact Subject`
	- Scope: Event
	- Event parameter: `subject`
	- Description: Subject selected on successful contact submissions.

5. Dimension name: `Form Name`
	- Scope: Event
	- Event parameter: `form_name`
	- Description: Identifier for submitted forms.

### Custom Metrics Note

No custom metrics are required for this setup.

Use GA4's built-in **Event count** metric with filters on:

1. `event_name = cta_click`
2. `event_name = contact_form_submit`

Only create custom metrics if you later send numeric event parameters (for example, `lead_value`).

### Verification Checklist After Setup

1. Wait for new event traffic (or use DebugView immediately).
2. Open Explore in GA4 and add dimensions:
	- `CTA Name`
	- `CTA Location`
	- `CTA Destination`
3. Add metrics:
	- Event count
	- Key events (if configured)
4. Confirm `cta_click` rows show all three CTA dimensions.
5. Confirm `contact_form_submit` rows show `Contact Subject` and `Form Name`.

### Common Pitfalls

1. Parameter name mismatch (must exactly match code keys).
2. Creating user-scoped instead of event-scoped dimensions.
3. Expecting historical backfill before definition creation.
4. Forgetting to publish/submit the new definitions in GA4.

## 30-Minute GA4 Launch Checklist

Use this quick runbook after deployment to confirm conversion tracking is usable on day one.

### 0-5 Minutes: Property and Stream Sanity

1. Confirm the GA4 Measurement ID in templates matches the intended property (`G-HXPJGHXTBV`).
2. Open the live site and verify page views appear in Realtime.
3. Open DebugView in GA4 for immediate event validation.

### 5-12 Minutes: Trigger Core Events

1. Click a primary CTA (`book_intro_call`) from:
	- landing header
	- landing hero
	- landing footer
2. Click a secondary CTA (`try_live_agent`) from:
	- landing hero
	- features footer
3. Submit contact form successfully once.

Expected in DebugView:

1. `cta_click` with populated params:
	- `cta_name`
	- `cta_location`
	- `destination`
2. `contact_form_submit` with populated params:
	- `form_name`
	- `subject`

### 12-20 Minutes: Build Explorations

Create one Exploration with these tabs.

Tab 1: `Primary CTA Performance`

1. Rows: `CTA Location`
2. Filter:
	- `Event name` exactly matches `cta_click`
	- `CTA Name` exactly matches `book_intro_call`
3. Metric: `Event count`

Tab 2: `Secondary CTA Performance`

1. Rows: `CTA Location`
2. Filter:
	- `Event name` exactly matches `cta_click`
	- `CTA Name` exactly matches `try_live_agent`
3. Metric: `Event count`

Tab 3: `Contact Submit Quality`

1. Rows: `Contact Subject`
2. Filter:
	- `Event name` exactly matches `contact_form_submit`
3. Metric: `Event count`

Tab 4: `Affiliate Outbound Clicks`

1. Rows: `CTA Name`
2. Secondary rows (optional): `CTA Location`
3. Filter:
	- `Event name` exactly matches `cta_click`
	- `CTA Name` contains `affiliate_`
4. Metric: `Event count`

### 20-25 Minutes: Create Key Event(s)

In GA4 Admin > Data display > Events:

1. Mark `contact_form_submit` as a Key event.
2. Optionally mark `cta_click` as Key event only if you want broad micro-conversion tracking.

Recommendation:

1. Keep `contact_form_submit` as the primary Key event for lead conversion.
2. Use `cta_click` mostly for behavioral analysis.

### 25-30 Minutes: Baseline Snapshot

Record the first baseline counts for:

1. `book_intro_call` clicks
2. `try_live_agent` clicks
3. `contact_form_submit` submits
4. `affiliate_` clicks

Store baseline in an internal note so week-over-week changes are measurable.

## Weekly Monitoring Rhythm

1. Compare primary CTA clicks vs contact submits.
2. Identify top and weakest `cta_location` values.
3. Review subject distribution from `contact_form_submit`.
4. Review affiliate click mix by `cta_name`.
5. Ship one CTA copy or placement improvement per week.