# ROLE
You are a senior full-stack + AI engineer building a hackathon project. Work in phases. Produce a plan first and WAIT for my approval before writing code. After each phase, summarize what you did, how to run it, and what I should test.

# PROJECT
Name: "Adhikar Saathi" (placeholder; suggest a better name)
Hackathon: IDEA//FORGE Online Hackathon, Track 1, Problem 1:
"Multilingual Policy, Rights & Scheme Explainer. An AI that reads government notices, welfare schemes and local laws, and explains them in simple language and regional languages. It helps people check scheme eligibility and understand their rights, and can answer by voice."

# TARGET USERS
Farmers, students, women, senior citizens and daily-wage workers in Karnataka, India, many with low literacy. Languages: Kannada (kn), Hindi (hi), English (en).

# CORE VALUE
A user speaks or types in their own language, answers a few simple questions, and learns which schemes they qualify for, why, what documents are needed and how to apply. They can also photograph a government notice and get a plain-language explanation with the deadline and next steps. Behind this sits a scalable data pipeline that turns official documents into structured scheme records, with human review.

# SCALE GOAL
This is a hackathon product, not a toy. Target: 50+ verified schemes and 150+ extracted schemes, built through the ingestion pipeline. Never claim more coverage than what is actually loaded. Show real counts (verified vs extracted) in the UI.

# MUST-HAVE FEATURES (MVP)
1. Voice + text chat in en/kn/hi with spoken replies (TTS) and a language switcher.
2. Guided eligibility flow: ask 4-6 simple questions (age, state, occupation, annual income, category, gender, land ownership, etc. as needed), then return a ranked list of schemes with verdict Eligible / Not eligible / Maybe, one-line reason, and the missing question for "Maybe".
3. Scheme explainer: simple language (about 6th-grade reading level, no jargon), benefit, documents checklist, how to apply, official link.
4. Notice scanner: user uploads/photographs a government notice; Gemini vision returns summary, what is demanded, deadline, urgency, next steps, in the user's language.
5. Rights explainer: answers common rights questions (unpaid wages, RTI, consumer complaints, etc.) grounded ONLY in the rights knowledge base.
6. Data ingestion pipeline + admin review page that promotes extracted schemes to verified.
7. Every answer shows its SOURCE (name + URL + last_verified) and the disclaimer: "Information only, not legal advice. Please verify at the official office/portal."

# STRETCH (only after MVP works)
- "Schemes for me": save a profile once, see ranked schemes.
- Simple application tracker (manual notes).
- Analytics page: most-asked schemes, languages used.

# THREE-TIER KNOWLEDGE BASE
- Tier 1 VERIFIED: /data/schemes_verified.json. Hand-verified, structured eligibility rules. Used by the rules engine for firm verdicts.
- Tier 2 EXTRACTED: /data/schemes_extracted.json. Produced by the pipeline from documents I place in /data/raw/. Status "unverified", with confidence score. Verdicts capped at "Likely/Maybe" and always labelled "auto-extracted, please verify".
- Tier 3 LINK-OUT: anything not in the data. Reply with the official portal link and say details are not available. Never invent.

# NON-NEGOTIABLE RULES
- NO HALLUCINATION: answer only from the records/documents passed into the prompt. If it is not there, say so and give the official link.
- Eligibility verdicts come from a deterministic rules engine over structured JSON, NOT from LLM guessing. The LLM only explains results in plain language.
- Ambiguity returns "Maybe" with the exact missing question.
- NEVER hardcode API keys. Use .env and provide .env.example (GNANI_API_KEY, GEMINI_API_KEY, LLM_PROVIDER, LLM_MODEL). Never print or log keys.
- DO NOT write or run scrapers, crawlers or bulk downloaders against myscheme.gov.in or any site whose terms forbid automated access (myScheme's terms prohibit bots/scrapers without written permission). The pipeline reads only local files I place in /data/raw/.
- Do not send real personal data to the LLM. Use sample data for demos and tests.
- Every record keeps official_url, source_name and last_verified.
- Mobile-first, accessible UI: large buttons, prominent mic, high contrast, minimal typing.
- Simple, readable code with short comments. I am a student and must be able to explain every part.

# TECH STACK
- Frontend: React + Vite (PWA), Tailwind CSS.
- Backend: Python FastAPI.
- LLM + vision/OCR: Gemini API (structured JSON output). Provider and model configurable via .env (LLM_PROVIDER, LLM_MODEL) behind an interface so providers can be swapped.
- Embeddings + vector store: Gemini embeddings + ChromaDB (local).
- DB: SQLite (schemes, review status, response cache, logs).
- Speech: Gnani API (GNANI_API_KEY) behind a SpeechProvider interface (transcribe(), synthesize()). Do NOT guess Gnani endpoints, parameters or supported languages: I will paste the official docs; implement exactly what they say. Fallback to the browser Web Speech API when Gnani lacks a language or fails. Tell me which of en/kn/hi each provider covers.
- Deploy: Vercel (frontend) + Render (backend). Add CORS and env config.

# COST CONTROL
- Response cache in SQLite keyed by (scheme_id, language, prompt_version). Pre-generate explanations and translations for verified schemes.
- Use the rules engine, not the LLM, for verdicts.
- Retry with exponential backoff on 429 errors; friendly "try again" message; if the LLM fails, serve the cached explanation and official link.
- Batch extraction jobs and cache every extraction output.
- No fine-tuning. Use retrieval + prompts + rules engine only.

# DATA SCHEMAS
Define JSON Schema (and Pydantic models) for: Scheme, EligibilityRule, UserProfile, RightsEntry, ExtractionResult. I will give detailed schemas in a later prompt; for now propose them in Phase 0.

# ELIGIBILITY ENGINE
- Criteria support numeric ranges (age, income), enums (occupation, category, gender, state), booleans (owns land, is student), and exclusions.
- Output per scheme: verdict, matched_criteria[], failed_criteria[], missing_info[], tier, confidence.
- At least 20 unit tests including boundary cases.

# LLM PROMPTS (store in /backend/prompts/, versioned)
extract_scheme, explain_scheme, eligibility_explainer, notice_scanner, rights_answer, question_flow, translate_glossary_check. All must: use only the provided context, use simple words, reply in the requested language, never invent schemes, amounts or deadlines, and return JSON where specified.

# API ENDPOINTS
POST /api/chat, POST /api/eligibility, POST /api/notice/scan, POST /api/stt, POST /api/tts, GET /api/schemes, GET /api/stats, POST /api/admin/ingest, GET /api/admin/review, POST /api/admin/review/{id}, GET /api/health

# PHASES
Phase 0: Read this prompt. Propose folder structure, schemas, task list, risks, questions. WAIT for approval.
Phase 1: Backend skeleton, schemas, loader/validator, eligibility engine + tests.
Phase 2: Ingestion pipeline (PDF/text -> extraction -> validation -> embeddings).
Phase 3: Chat with retrieval, citations, language handling, cache.
Phase 4: Frontend: chat UI, mic, language switcher, eligibility flow, result cards, stats bar.
Phase 5: Admin review page.
Phase 6: Notice scanner.
Phase 7: Voice (Gnani + fallback), error/loading states, polish.
Phase 8: README, .env.example, deployment, 30-question evaluation set (en/kn/hi), demo script.

# ACCEPTANCE CRITERIA
- Kannada voice question returns Kannada spoken + text answer with a source (or a clear fallback message if unsupported).
- Eligibility flow passes all unit tests.
- Pipeline turns a sample PDF into a validated Tier 2 record.
- Admin can approve an extracted record and it becomes Tier 1.
- Sample notice returns summary, deadline, next steps.
- No answer without a source; unknown questions fall back to the official link.
- Backend and frontend each run with one setup command.

# WORKING STYLE
- Ask clarifying questions only if blocked; otherwise state assumptions.
- Flag anything needing my action (API keys, Gnani docs, data verification).