# Adhikar Saathi — Live Hackathon Demo Script (5 Minutes)

**Track**: Track 1, Problem 1 (Multilingual Policy, Rights & Scheme Explainer)  
**Target Audience**: Karnataka citizens (farmers, daily-wage workers, students, senior citizens)  
**Supported Languages**: Kannada (ಕನ್ನಡ), Hindi (हिन्दी), English  

---

## ⏱️ Timeline & Flow Overview

```
[0:00 - 0:45] Problem & Core Innovation (No Hallucination Architecture)
[0:45 - 2:00] Multilingual Voice & Guided Dynamic Eligibility Flow
[2:00 - 3:00] Notice Scanner (Gemini Vision OCR on Karnataka Notice)
[3:00 - 3:45] Citizen Rights Explainer (Unpaid MGNREGA Wages & RTI)
[3:45 - 4:30] Data Pipeline & DBControl Governance Console (Tier 2 -> Tier 1)
[4:30 - 5:00] Zero-Hallucination Tier 3 Fallback & Wrap-up
```

---

## 🎙️ Step-by-Step Script & Actions

### Scene 1: The Problem & The Solution (0:00 – 0:45)
- **Speaker Cue**:  
  *"Every year, billions in government welfare schemes never reach the deserving citizens in rural India because government notifications are dense, official portals are complicated, and citizens speak regional dialects. Furthermore, conventional LLMs hallucinate rules and deadlines.  
  Today, we present **Adhikar Saathi** — an AI-powered multilingual policy and citizen rights explainer with a **deterministic rules engine**, ensuring 100% verified verdicts with zero hallucination."*
- **Action**: Open the landing page (`http://localhost:5173`). Highlight the clean, accessible, high-contrast mobile-first interface and the live scheme counters (Verified vs. Extracted).

---

### Scene 2: Kannada Voice & Dynamic Eligibility Flow (0:45 – 2:00)
- **Speaker Cue**:  
  *"Let's look at Ramappa, a small farmer from Mandya who speaks only Kannada."*
- **Action**:
  1. Click the Language Switcher in the top bar and select **ಕನ್ನಡ (Kannada)**. Notice how the entire UI instantly adapts.
  2. Tap the large microphone icon or enter the guided **ಅರ್ಹತೆ ಪರೀಕ್ಷೆ (Check Eligibility)** wizard.
  3. Answer 4 quick questions:
     - Age: `45`
     - State: `Karnataka`
     - Occupation: `ರೈತ (Farmer)`
     - Land Owned: `Yes, 2 acres dryland`
  4. Submit profile.
- **Outcome**:
  - The deterministic rules engine evaluates against `/data/schemes_verified.json`.
  - Results show **Raitha Siri** and **PM-KISAN** ranked as **ಅರ್ಹರು (Eligible)**.
  - Plain-language explanation in Kannada: *₹10,000 per hectare incentive for minor millets*.
  - Displays required documents list, application steps, and clickable official portal link.
  - Speaks out the Kannada summary aloud via the voice synthesizer.

---

### Scene 3: Notice Scanner via Gemini Vision (2:00 – 3:00)
- **Speaker Cue**:  
  *"Citizens frequently receive official government notices or tax demands in the mail and panic because they cannot understand the legal jargon or deadline."*
- **Action**:
  1. Navigate to the **ನೋಟಿಸ್ ಸ್ಕ್ಯಾನರ್ (Notice Scanner)** tab.
  2. Upload a sample notice photo (e.g., Gram Panchayat Water/Property Tax Demand Notice).
  3. Click **Scan Notice**.
- **Outcome**:
  - Structured extraction returns in under 3 seconds:
    - **Summary**: Plain Kannada / English explanation of what the letter demands.
    - **Urgency Level**: 🔴 High / 🟡 Medium.
    - **Exact Deadline**: Clear date highlighted in bold.
    - **Required Citizen Actions**: Step 1, Step 2, and appeal authority contact.

---

### Scene 4: Citizen Rights Directory (3:00 – 3:45)
- **Speaker Cue**:  
  *"What happens when citizen rights are violated—such as withheld MGNREGA wages or RTI obstruction?"*
- **Action**:
  1. Open the Chat / Rights view.
  2. Ask: *"ನರೇಗಾ ಕೂಲಿ ಕೆಲಸ ಮಾಡಿ 2 ತಿಂಗಳಾದರೂ ಹಣ ಬಂದಿಲ್ಲ. ನಾನು ಎಲ್ಲಿ ದೂರು ನೀಡಬೇಕು?"* (I worked on MGNREGA for 2 months without pay. Where do I complain?).
- **Outcome**:
  - Grounded retrieval from `data/rights_kb.json`.
  - System cites Section 3 of MGNREGA Act (compensatory delay payment after 15 days), toll-free helpline number (`1800-425-8666`), and the exact grievance procedure before the Ombudsman.
  - Displays mandatory source citation and legal disclaimer.

---

### Scene 5: Data Ingestion & DBControl Admin Console (3:45 – 4:30)
- **Speaker Cue**:  
  *"How do we maintain this without manual data entry? Our background ingestion pipeline automatically turns raw PDF documents into structured schema records."*
- **Action**:
  1. Open the Admin DBControl console at `/admin` (or `http://localhost:8000/admin`).
  2. Authenticate with master admin password or session token.
  3. Show the **Extracted Queue (Tier 2)** containing pipeline-processed schemes.
  4. Review confidence score and diff view.
  5. Click **Approve & Promote to Tier 1 (Verified)**.
- **Outcome**:
  - Scheme is immediately validated by `SchemeValidator` and added to `schemes_verified.json`.
  - Live stats counter increments from 5 to 6 verified schemes dynamically.

---

### Scene 6: Zero-Hallucination Tier 3 Fallback & Wrap-up (4:30 – 5:00)
- **Speaker Cue**:  
  *"What happens if a user asks about an internet rumor or a non-existent scheme?"*
- **Action**:
  1. In chat, type: *"How to apply for PM Free Flying Car Scheme 2026?"*
- **Outcome**:
  - System strictly refuses to fabricate benefits or eligibility criteria.
  - Tier 3 Link-Out triggers: clearly states no verified record exists, directs the user to `myscheme.gov.in` and `karnataka.gov.in`, and provides the official verification disclaimer.
- **Closing**:
  *"Adhikar Saathi bridges the last-mile gap between public policy and real citizens through regional voice, verifiable facts, and zero AI hallucinations. Thank you!"*
