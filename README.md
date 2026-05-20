# ♻️ E-RECYCLO v2.0
### Next-Gen AI-Powered E-Waste Recycling & Logistics Ecosystem
*Transforming electronic waste management through automated AI classification, double-layer OTP-secured logistics, and seamless Razorpay financial clearing.*

---

[![Django](https://img.shields.io/badge/Django-4.2.7-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://supabase.com/)
[![Vercel](https://img.shields.io/badge/Vercel-Deploys-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com/)
[![Razorpay](https://img.shields.io/badge/Razorpay-Gateway-02042B?style=for-the-badge&logo=razorpay&logoColor=blue)](https://razorpay.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](https://github.com/beprojectdyp15/E-RECYCLO.v02.O/blob/main/LICENSE)

---

## 🏗️ Project Overview

**E-RECYCLO** is a comprehensive, production-grade **e-waste management platform** designed to solve the structural logistics, validation, and payout problems in modern electronic recycling. 

Built on a single-account multi-role custom authentication system, the platform orchestrates interactions between **Clients** (household recyclers), **Vendors** (certified recycling centers), **Collectors** (delivery agents), and **System Administrators**. It features automatic **AI-powered image classification**, **GPS-tracked pickup paths**, **dual-OTP transaction handshakes**, and a **fully automated financial layer** utilizing Razorpay Wallets and secure Admin Payouts.

> **BE Capstone Project**  
> 🎓 **Department of Computer Engineering (AI & Data Science)**  
> 🏫 **Dr. D. Y. Patil College of Engineering and Innovation, Varale, Pune**  
> 📅 **Academic Period:** Dec 2024 - May 2026

---

## 👥 Role-Based Architecture & Flow

The system runs on a highly secure, centralized `Account` model extending Django's `AbstractBaseUser` using **email** as the login identifier. Role control is managed by strict boolean flags:

```
[Register Account] ──▶ [Email OTP verification (10m Expiry)] ──▶ [Active Session]
                                                                        │
    ┌───────────────────────────┬───────────────────────────────────────┤
    ▼                           ▼                                       ▼
[is_client]                [is_vendor]                            [is_collector]
  - Immediate access         - Blocked until verified               - Blocked until verified
  - E-waste uploads          - Complete GST/EPR profile             - Complete RC/License profile
  - Wallet withdrawals       - Dynamic bid evaluations              - Real-time earnings panel
```

### 📱 Client Portal
- **Instant Access:** Fast, secure registration using email OTP verification (60-second cooldown, max 5 attempts lockout).
- **AI PhotoPost Upload:** Upload electronic waste images with automated AI category matching, condition detection, confidence score calculation, and estimated market value tiering.
- **Appreciation Gamification:** Accumulate `AppreciationPoints` on zero-value or carbon-saving items, unlocking ranks from *Casual Recycler* up to *Eco Legend*.
- **Integrated Wallet ledger:** Accept vendor payout offers directly into an active client wallet, and request bank/UPI withdrawals (minimum ₹50).

### 🏭 Vendor Portal
- **Strict Compliance Onboarding:** Requires 15 administrative and regulatory inputs including GSTIN, PAN, Aadhaar, Alternate Contacts, GPS location coordinates, and **E-Waste Authorization Documents** (SPCB, CPCB EPR, CTO, or Hazardous Waste ID).
- **Interactive Inventory Management:** Monitor and accept assigned pickup posts, evaluate transit items in real time, review pricing tiers, and issue final recycling offers.
- **Flexible Wallets:** Secure Razorpay checkout integration for instant wallet top-ups (minimum ₹10) to cover collector fees and transaction payments.
- **Evaluation History Ledger:** Complete historical logs of all bid-reviews, pricing breakdowns, and condition assessments.

### 🚴 Collector Logistics
- **Authorized Courier Onboarding:** Requires vehicle details (Vehicle type, RC number, RC uploaded scan), Aadhaar documentation, Alternate Emergency contacts, and valid Driving License credentials.
- **Double-Layer OTP Handshake:** Fraud-proof logistics path. Collector must verify a `pickup_otp` (obtained from the Client) at pickup, and a `delivery_otp` (obtained from the Vendor) at delivery to complete the trip.
- **Automated Pricing Fees:** Collector earnings calculated using a robust distance-pricing model:
  $$\text{Trip Earnings} = \text{Base Fare } (₹50) + [\text{Distance } (km) \times ₹5]$$
- **Logistics History Tracker:** Tracks trip duration (`trip_start_at` to `completed_at`), active status, and real-time wallet settlement.

### 🔐 Administrative Authority
- **Central Compliance Center:** Verify, approve, or reject pending Vendor and Collector profiles (rejections require mandatory review comments and trigger automatic notification dispatches).
- **Generic Dynamic CRUD System:** Complete model inspection interface offering robust search, filter, and pagination options, running on a dynamic `modelform_factory` for instant updates.
- **Financial Clearing House:** Full control over pending wallet withdrawals, with automatic Razorpay Payout API integration on approval, or automated ledger refunds on rejection.
- **Analytics Dashboard:** Graphical breakdowns of monthly upload volumes, role-based signup statistics, and total ecosystem transactions processed.

---

## 🔄 Core E-Waste Lifecycle Path

```
 [CLIENT]                      [AI ENGINE]                [SYSTEM/ADMIN]              [COLLECTOR]                 [VENDOR]
    │                               │                            │                         │                         │
    │── 1. Uploads E-Waste Photo ──▶│                            │                         │                         │
    │                               │── 2. Analyzes Category ───▶│                         │                         │
    │                               │   & Estimated Value        │                         │                         │
    │                                                            │── 3. Assigns Post ───────────────────────────────▶│
    │                                                            │                                                   │── 4. Accepts Bid
    │                                                            │◀── Dispatches Collector ──────────────────────────│
    │                                                            │
    │◀─ 5. Receives pickup_otp ──────────────────────────────────│
    │                                                            │
    │── 6. Hands E-Waste + OTP ───────────────────────────────────────────────────────────▶│
    │                                                                                      │── 7. Verifies OTP & Starts Trip
    │                                                                                      │── 8. Arrives & Enters delivery_otp
    │                                                                                      │◀── (Generated by Vendor) ───────│
    │                                                                                      │
    │                                                                                      │── 9. Completed Trip & Paid ────▶│
    │                                                                                                                        │── 10. Evaluates Post
    │                                                                                                                        │── 11. Submits Offer
    │◀─ 12. Receives Final Payout Bid ───────────────────────────────────────────────────────────────────────────────────────│
    │── 13. ACCEPTS OFFER ──────────────────────────────────────────────────────────────────────────────────────────────────▶│
    │                                                                                                                        │── 14. Wallet Debited
    │◀─ 15. Wallet Credited & Request Payout ────────────────────────────────────────────────────────────────────────────────│
```

---

## 📂 System Folder Structure

```
E-RECYCLO/
├── apps/                         # Core Django application modules
│   ├── accounts/                 # Custom user authentication (Email OTP, Profile management)
│   ├── admin_custom/             # Custom analytics dashboard, profile review, & generic CRUD
│   ├── ai_services/              # AI classification engine for e-waste photo posts
│   ├── certificates/             # Certification generation for green recycling credits
│   ├── client/                   # Client upload portal, post lifecycle, & wallet dashboard
│   ├── collector/                # Collector pickup logs, OTP verification, & trip tracking
│   ├── notifications/            # Transactional system email logs & dispatch
│   ├── pages/                    # Public pages (Home, Privacy, Terms, Contact)
│   ├── payments/                 # Financial layer (Razorpay top-up, Payouts, Wallet ledger)
│   └── vendor/                   # Vendor pricing evaluation & e-waste inventory control
├── config/                       # Settings and routing configuration
│   ├── settings/                 # Modular settings (base, development, production)
│   │   ├── base.py               # Shared settings
│   │   ├── development.py        # Local settings
│   │   └── production.py         # Supabase & Vercel deployment settings
│   ├── urls.py                   # Global system URL patterns
│   └── validators.py             # Aadhaar, GSTIN, PAN, and phone formats
├── static/                       # Custom CSS, JS, and image assets
│   ├── css/                      # Structured Vanilla CSS styling
│   │   ├── unified-cards.css     # Unified dashboard styling
│   │   └── custom-forms.css      # Custom input fields styling
│   ├── images/                   # UI graphics & icons
│   └── js/                       # Interactive page behaviors
├── templates/                    # Dynamic HTML templates (organized by role)
│   ├── accounts/                 # OTP verification and authentication forms
│   ├── admin_custom/             # Custom analytics and approval layouts
│   ├── client/                   # Client-specific pages
│   ├── collector/                # Collector-specific pages
│   ├── payments/                 # Wallet, top-up, & withdrawal views
│   └── vendor/                   # Vendor-specific dashboards & forms
├── build_files.sh                # Vercel deployment shell script
├── manage.py                     # Django CLI gateway
├── requirements.txt              # Standard system dependencies
├── vercel.json                   # Vercel serverless functions configuration
└── .env-sample                   # Sample environment configuration template
```

---

## 🚀 Setup & Installation Guide

### 📋 Prerequisites
- Python 3.10 or higher installed.
- PostgreSQL database running (locally or on Supabase).
- Git installed.

### 💻 Step-by-Step Instructions

#### 1. Clone the repository
```bash
git clone https://github.com/beprojectdyp15/E-RECYCLO.v02.O.git
cd E-RECYCLO
```

#### 2. Create and activate a Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install core dependencies
```bash
pip install -r requirements.txt
```

#### 4. Configure local environment variables
Copy the sample environment configuration file:
```bash
# Windows
copy .env-sample .env

# macOS / Linux
cp .env-sample .env
```
Open the newly created `.env` file and enter your actual local values:
- Generate a unique Django `SECRET_KEY`.
- Set local PostgreSQL database credentials or paste your live Supabase connection string.
- Provide a valid Gmail account and a 16-character **Gmail App Password** for OTP delivery.
- Input your **Razorpay Test Keys** for sandboxed payment operations.

#### 5. Apply Database Migrations
```bash
python manage.py migrate
```

#### 6. Create a Superuser / Administrator
```bash
python manage.py createsuperuser
```

#### 7. Launch the Development Server
```bash
python manage.py runserver
```

Open your browser and navigate to: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## 🔐 Advanced Security Features

### 🍯 The Honeypot Dashboard
E-RECYCLO uses a strict **honeypot security strategy** to block unauthorized access to the admin interface:
- Visiting the default Django `/admin/` path displays a **fake, authentic-looking login page**.
- Any login attempts made on this honeypot are flagged, automatically terminated, and logged in the system security reports.
- The **real, authorized administrative gateway** is routed privately under `/securelogin/`.

### 🛡️ Real-Time Regulatory Validation
To ensure full SPCB compliance, all registration forms run regex validation checks:
- **GSTIN Number:** Verified against standard `^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$` formats.
- **PAN Number:** Validated against alphanumeric `^[A-Z]{5}[0-9]{4}[A-Z]{1}$` patterns.
- **Aadhaar Number:** Evaluated under length-specific `^\d{12}$` constraints.
- **Phone Fields:** Enforced to strictly matching Indian ten-digit formats.

### 💳 Double-Verification Payment Protection
- **HMAC Signature Check:** Client-side payment approvals are verified on the backend using server-side HMAC-SHA256 signature calculations to protect against client tampering.
- **Idempotent Webhooks:** Razorpay webhook triggers are tracked using custom `RazorpayOrder` models to prevent double-crediting wallets on network delays.

---

## 🛠️ CLI Management Commands

The platform features a custom Django administrative CLI utility to manage database cleanup and sandboxed payment configurations:

```bash
python manage.py mark_system_transactions [flags]
```

### 💡 Available Options:
*   **Dry-run (default):**  
    Running the command without any parameters scans the database, lists current records, and previews transaction updates without altering the database:
    ```bash
    python manage.py mark_system_transactions
    ```
*   **Apply Changes (`--apply`):**  
    Applies the changes, converting old development transactions into system-archived tags for testing clean Razorpay payment loops:
    ```bash
    python manage.py mark_system_transactions --apply
    ```
*   **Archive PhotoPosts (`--reset-posts`):**  
    Pairs with `--apply` to archive all old finished `PhotoPosts`, clearing out dashboard clutter:
    ```bash
    python manage.py mark_system_transactions --apply --reset-posts
    ```

---

## 👨‍💻 Primary Developer

**Aayan Mulla**  
🎓 BE Computer Engineering (AI & Data Science)  
🏫 Dr. D. Y. Patil College of Engineering and Innovation, Varale, Pune.

---

## 📄 License
This project is open-source and released under the [MIT License](https://github.com/beprojectdyp15/E-RECYCLO.v02.O/blob/main/LICENSE).
