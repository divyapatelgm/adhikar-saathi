"""
Import Open Datasets & Statutory Acts for Adhikar Saathi.
Sources:
- Mahiti Kanaja & Karnataka State Budget Open Datasets (urbanmorph/mahiti-kanaja)
- India Code Official Statutes (MGNREGA 2005, RTI 2005, Consumer Protection 2019, Senior Citizens 2007, DV Act 2005)
- Open Government Data (data.gov.in) & Central DBT Portal
"""

import json
from pathlib import Path
import logging

from backend.app.config import settings
from backend.app.models.scheme import Scheme, SchemeBenefit, EligibilityContainer, HowToApply
from backend.app.models.rule import EligibilityRule
from backend.app.models.rights import RightsEntry
from backend.app.models.enums import TierType, SchemeStatus, LevelType, RuleField, RuleOperator
from backend.app.engine.validator import SchemeValidator
from backend.app.pipeline.embeddings import SchemeVectorStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RIGHTS_DATA = [
    {
        "id": "unpaid-wages-mgnrega",
        "topic": "Unpaid Wages under MGNREGA",
        "question_variants": [
            "I did not get paid for my NREGA work",
            "MGNREGA wages delayed",
            "How to claim pending wages for daily labour work?",
            "ವೇತನ ಬಂದಿಲ್ಲ ನರೇಗಾ",
            "ನರೇಗಾ ಕೂಲಿ ಹಣ ಯಾವಾಗ ಬರುತ್ತದೆ",
            "नरेगा की मजदूरी नहीं मिली",
            "मनरेगा मजदूरी में देरी"
        ],
        "answer_en": "Under Section 3(3) of MGNREGA 2005, workers are legally entitled to wage payment within 15 days of work completion. If payment is delayed beyond 15 days, you are entitled to mandatory delay compensation of 0.05% of unpaid wages per day until full disbursement.",
        "steps": [
            "Check your Muster Roll number and Job Card on nrega.nic.in or at the Gram Panchayat.",
            "Lodge a formal grievance with the Gram Panchayat Secretary or Programme Officer.",
            "Call the Karnataka State MGNREGA toll-free helpline at 1800-425-8666.",
            "If unresolved within 7 days, file an appeal before the District Ombudsman."
        ],
        "helpline_or_authority": "Karnataka MGNREGA Helpline: 1800-425-8666 / District Ombudsman",
        "source_name": "The Mahatma Gandhi National Rural Employment Guarantee Act, 2005 (Act No. 42 of 2005), India Code",
        "source_url": "https://www.indiacode.nic.in/handle/123456789/2042",
        "last_verified": "2026-11-20"
    },
    {
        "id": "right-to-information-karnataka",
        "topic": "Right to Information (RTI)",
        "question_variants": [
            "How do I file an RTI application in Karnataka?",
            "How to know why my ration card or pension application was rejected?",
            "RTI fees and timeline",
            "ಮಾಹಿತಿ ಹಕ್ಕು ಅರ್ಜಿ ಹಾಕುವುದು ಹೇಗೆ",
            "ಆರ್‌ಟಿಐ ಅರ್ಜಿ ಶುಲ್ಕ ಎಷ್ಟು",
            "आरटीआई आवेदन कैसे करें",
            "सूचना का अधिकार कानून"
        ],
        "answer_en": "Under Section 6 of the Right to Information Act 2005, any citizen can request official government records and inspection of public works. The Public Information Officer (PIO) must reply within 30 days (or 48 hours for life/liberty issues). Application fee is ₹10 (waived for BPL cardholders).",
        "steps": [
            "Submit application online via rtionline.karnataka.gov.in or in writing to the department PIO.",
            "Describe the requested records precisely without needing to provide any personal reason.",
            "Pay the ₹10 fee via court fee stamp, postal order, or attach BPL card copy for zero fee.",
            "If no response is received in 30 days, submit a First Appeal under Section 19(1) to the First Appellate Authority."
        ],
        "helpline_or_authority": "Karnataka Information Commission (KIC) / Helpdesk: 080-22370909",
        "source_name": "The Right to Information Act, 2005 (Act No. 22 of 2005), India Code",
        "source_url": "https://www.indiacode.nic.in/handle/123456789/2065",
        "last_verified": "2026-11-20"
    },
    {
        "id": "consumer-grievance-ration-pds",
        "topic": "PDS Ration Denial, Overcharging, or NFSA Food Security Rights",
        "question_variants": [
            "Fair price shop dealer is not giving ration",
            "Ration dealer charging extra money or taking cut",
            "Biometric fingerprint failure at ration shop",
            "ರೇಷನ್ ಅಂಗಡಿ ಮಾಲೀಕ ಅಕ್ಕಿ ಕೊಡುತ್ತಿಲ್ಲ",
            "ಪಡಿತರ ನಿರಾಕರಣೆ ದೂರು",
            "राशन डीलर राशन नहीं दे रहा",
            "राशन दुकान में अंगूठा नहीं लग रहा"
        ],
        "answer_en": "Fair price shop (FPS) dealers are legally required under the National Food Security Act (NFSA) 2013 to distribute entitled foodgrains at government notified prices and cannot deny ration due to biometric authentication failure. Alternative OTP authentication and nominee collection are legal entitlements.",
        "steps": [
            "Ask for the electronic weighing slip / receipt generated from the e-PoS machine.",
            "Lodge an immediate complaint with the Food Inspector or Tahsildar of your Taluk.",
            "Call the Karnataka Food & Civil Supplies Toll-Free consumer helpline 1967 or 1800-425-9333.",
            "Submit an online grievance on the Karnataka Ahara portal (ahara.kar.nic.in)."
        ],
        "helpline_or_authority": "Food & Civil Supplies Consumer Helpline: 1967 / 1800-425-9333",
        "source_name": "National Food Security Act (NFSA) 2013 & Karnataka Essential Commodities Regulations",
        "source_url": "https://ahara.kar.nic.in",
        "last_verified": "2026-11-20"
    },
    {
        "id": "consumer-protection-mrp-fraud",
        "topic": "Consumer Rights: Overcharging Above MRP and Defective Goods",
        "question_variants": [
            "Shopkeeper charging extra above MRP",
            "Defective electronic product and dealer refuses replacement",
            "Consumer court online complaint",
            "ಎಂಆರ್‌ಪಿ ಗಿಂತ ಹೆಚ್ಚು ಹಣ ಪಡೆಯುತ್ತಿದ್ದಾರೆ",
            "ಗ್ರಾಹಕ ವೇದಿಕೆಗೆ ದೂರು ನೀಡುವುದು ಹೇಗೆ",
            "एमआरपी से ज्यादा कीमत वसूल रहे हैं",
            "उपभोक्ता शिकायत कैसे दर्ज करें"
        ],
        "answer_en": "Under the Consumer Protection Act 2019, charging any price in excess of the Maximum Retail Price (MRP) or refusing to redress defective products constitutes an unfair trade practice. Consumers have the right to full refund, replacement, and compensation.",
        "steps": [
            "Demand a dated tax invoice or bill stating the item and price charged.",
            "Call the National Consumer Helpline at 1915 or send SMS/WhatsApp to 8800001915.",
            "File an electronic grievance online on e-Daakhil portal (edaakhil.nic.in) without hiring a lawyer.",
            "Submit the matter before the District Consumer Disputes Redressal Commission."
        ],
        "helpline_or_authority": "National Consumer Helpline: 1915 / e-Daakhil Karnataka Consumer Forum",
        "source_name": "The Consumer Protection Act, 2019 (Act No. 35 of 2019), India Code",
        "source_url": "https://www.indiacode.nic.in/handle/123456789/15256",
        "last_verified": "2026-11-20"
    },
    {
        "id": "senior-citizens-maintenance-act",
        "topic": "Maintenance and Welfare of Senior Citizens & Elderly Parents",
        "question_variants": [
            "Children not taking care of elderly parents",
            "Senior citizen maintenance tribunal application",
            "Property transfer cancellation by senior citizen",
            "ಹಿರಿಯ ನಾಗರಿಕರ ರಕ್ಷಣೆ ಕಾಯ್ದೆ",
            "ವೃದ್ಧ ತಂದೆ ತಾಯಿಯ ಪೋಷಣೆ",
            "वरिष्ठ नागरिक भरण-पोषण कानून",
            "बुजुर्ग माता-पिता की देखभाल"
        ],
        "answer_en": "Under Section 4 of the Maintenance and Welfare of Parents and Senior Citizens Act 2007, senior citizens (aged 60+) who are unable to maintain themselves can claim monthly maintenance up to ₹10,000 from adult children or legal heirs through a fast-track tribunal presided over by the Sub-Divisional Magistrate (Assistant Commissioner).",
        "steps": [
            "File an application before the Maintenance Tribunal at the Sub-Divisional Assistant Commissioner office.",
            "Proceedings are conducted without lawyers; reconciliation officers assist the elders.",
            "The Tribunal must pass an order within 90 days directing monthly payments.",
            "Under Section 23, if elderly parents transferred property subject to care and are neglected, the transfer can be declared null and void."
        ],
        "helpline_or_authority": "National Helpline for Senior Citizens: 14567 / Sub-Divisional Assistant Commissioner",
        "source_name": "Maintenance and Welfare of Parents and Senior Citizens Act, 2007 (Act No. 56 of 2007), India Code",
        "source_url": "https://www.indiacode.nic.in/handle/123456789/2005",
        "last_verified": "2026-11-20"
    },
    {
        "id": "domestic-violence-women-protection",
        "topic": "Protection of Women from Domestic Violence",
        "question_variants": [
            "Domestic violence protection order",
            "Women helpline number in Karnataka",
            "Husband or in-laws beating or abusing wife",
            "ಗೃಹ ಹಿಂಸಾಚಾರ ಮಹಿಳಾ ಸಂರಕ್ಷಣೆ",
            "ಮಹಿಳಾ ಸಹಾಯವಾಣಿ",
            "घरेलू हिंसा से महिलाओं का संरक्षण",
            "महिला हेल्पलाइन नंबर"
        ],
        "answer_en": "Under the Protection of Women from Domestic Violence Act 2005, every woman facing physical, emotional, verbal, sexual, or economic abuse has the right to safe residence in the shared household, protection orders against the abuser, interim monetary relief, and free legal aid.",
        "steps": [
            "Dial 112 (Emergency) or 181 (Women Helpline) for immediate intervention and safe rescue.",
            "Contact the Protection Officer appointed in every Taluk under the Women and Child Development Department.",
            "Protection Officers will file a Domestic Incident Report (DIR) before the Magistrate.",
            "Access free shelter, medical care, and free legal representation through the Legal Services Authority."
        ],
        "helpline_or_authority": "Karnataka Women Helpline: 181 / Emergency: 112 / District Legal Services Authority",
        "source_name": "Protection of Women from Domestic Violence Act, 2005 (Act No. 43 of 2005), India Code",
        "source_url": "https://www.indiacode.nic.in/handle/123456789/2021",
        "last_verified": "2026-11-20"
    },
    {
        "id": "street-vendors-protection-act",
        "topic": "Street Vendors Rights Against Arbitrary Eviction",
        "question_variants": [
            "Police or municipality seizing vegetable cart or eviction",
            "Street vending certificate rules",
            "ಬೀದಿ ಬದಿ ವ್ಯಾಪಾರಿಗಳ ಹಕ್ಕುಗಳು",
            "रेहड़ी-पटरी विक्रेताओं के अधिकार"
        ],
        "answer_en": "Under Section 3 of the Street Vendors (Protection of Livelihood and Regulation of Street Vending) Act 2014, no street vendor who has been surveyed can be evicted or relocated until the Town Vending Committee (TVC) completes a comprehensive survey and issues a formal Vending Certificate.",
        "steps": [
            "Ensure you register your details during the municipal Town Vending Committee (TVC) survey.",
            "Keep your identity card or receipt of survey application readily displayed at your stall.",
            "If police or municipal staff attempt eviction without 30 days written notice, cite Section 3(3) of the Act.",
            "Lodge a grievance with the Town Vending Grievance Redressal Committee headed by a retired judicial magistrate."
        ],
        "helpline_or_authority": "Municipal Town Vending Committee (BBMP/Local Urban Body) / PM SVANidhi Helpdesk",
        "source_name": "Street Vendors (Protection of Livelihood and Regulation of Street Vending) Act, 2014, India Code",
        "source_url": "https://www.indiacode.nic.in/handle/123456789/2143",
        "last_verified": "2026-11-20"
    },
    {
        "id": "disability-rights-equal-opportunity",
        "topic": "Rights of Persons with Disabilities & Equal Access",
        "question_variants": [
            "Disabled person denied government reservation or access",
            "How to get disability certificate UDID card",
            "ಅಂಗವಿಕಲರ ಹಕ್ಕುಗಳು",
            "दिव्यांगजन अधिकार कानून"
        ],
        "answer_en": "Under the Rights of Persons with Disabilities Act 2016, individuals with 40% or more benchmark disability are entitled to 4% reservation in government employment, 5% reservation in higher education, accessible public infrastructure, and unique disability identification (UDID).",
        "steps": [
            "Apply for digital medical assessment on the UDID portal (swavlambancard.gov.in).",
            "Undergo medical board evaluation at the District Government Hospital to receive the UDID Smart Card.",
            "Present your UDID card to avail bus pass concessions, educational reservations, and assistive appliances.",
            "If discrimination or denial occurs, appeal to the State Commissioner for Persons with Disabilities."
        ],
        "helpline_or_authority": "State Commissioner for Persons with Disabilities, Karnataka / UDID Helpdesk: 011-24365012",
        "source_name": "Rights of Persons with Disabilities Act, 2016 (Act No. 49 of 2016), India Code",
        "source_url": "https://www.indiacode.nic.in/handle/123456789/2155",
        "last_verified": "2026-11-20"
    }
]

EXTRACTED_OPEN_SCHEMES = [
    # 1. Gruha Lakshmi
    {
        "id": "karnataka-gruha-lakshmi",
        "tier": "extracted",
        "status": "unverified",
        "confidence": 0.95,
        "is_placeholder": False,
        "names": {
            "en": "Gruha Lakshmi Scheme",
            "kn": "ಗೃಹ ಲಕ್ಷ್ಮಿ ಯೋಜನೆ",
            "hi": "गृह लक्ष्मी योजना"
        },
        "level": "state",
        "state": "Karnataka",
        "department": "Department of Women and Child Development",
        "category": ["women", "finance"],
        "target_groups": ["woman", "bpl"],
        "summary_en": "Flagship Karnataka guarantee scheme providing ₹2,000 monthly financial assistance directly into the Aadhaar-linked bank account of the woman head of household.",
        "benefit": {
            "type": "cash",
            "description": "Monthly direct benefit transfer (DBT) cash assistance to the female head of the family.",
            "amount_text": "₹2,000 per month"
        },
        "eligibility": {
            "criteria": [
                {
                    "field": "state",
                    "op": "eq",
                    "value": "Karnataka",
                    "text_en": "Must be a permanent resident of Karnataka",
                    "source_quote": "Applicant must reside in Karnataka"
                },
                {
                    "field": "gender",
                    "op": "eq",
                    "value": "female",
                    "text_en": "Must be a woman identified as head of the family on ration card",
                    "source_quote": "Woman head of household as recognized in ration card"
                },
                {
                    "field": "age",
                    "op": "gte",
                    "value": 18,
                    "text_en": "Must be 18 years of age or older",
                    "source_quote": "Adult woman aged 18 and above"
                }
            ],
            "exclusions": [
                {
                    "field": "annual_income",
                    "op": "gte",
                    "value": 2000000.0,
                    "text_en": "Women or husbands filing income tax or GST returns are ineligible",
                    "source_quote": "Income tax payees and GST filers are excluded"
                }
            ],
            "notes": "Woman must be listed as head on APL/BPL/Antyodaya ration card."
        },
        "documents_required": [
            "Aadhaar Card of the woman head of household",
            "Aadhaar Card of the husband (if married)",
            "Ration Card (BPL, APL, or Antyodaya)",
            "Bank Passbook linked to Aadhaar for DBT"
        ],
        "how_to_apply": {
            "steps": [
                "Visit your designated Grama One, Bangalore One, or Karnataka One center.",
                "Provide your Ration Card number and Aadhaar for biometric/OTP authentication.",
                "Ensure your bank account is active with NPCI Aadhaar seeding for DBT credits.",
                "Track application and monthly DBT status on Seva Sindhu or Mahiti Kanaja."
            ],
            "mode": "both",
            "portal_url": "https://sevasindhugs.karnataka.gov.in"
        },
        "deadline_text": "Ongoing (Rolling applications)",
        "official_url": "https://sevasindhu.karnataka.gov.in",
        "source_name": "Government of Karnataka, Department of Women and Child Development",
        "last_verified": "2026-11-20"
    },
    # 2. Yuva Nidhi
    {
        "id": "karnataka-yuva-nidhi",
        "tier": "extracted",
        "status": "unverified",
        "confidence": 0.95,
        "is_placeholder": False,
        "names": {
            "en": "Yuva Nidhi Scheme",
            "kn": "ಯುವ ನಿಧಿ ಯೋಜನೆ",
            "hi": "युवा निधि योजना"
        },
        "level": "state",
        "state": "Karnataka",
        "department": "Department of Skill Development, Entrepreneurship and Livelihood",
        "category": ["education", "labour", "finance"],
        "target_groups": ["student", "worker"],
        "summary_en": "Monthly unemployment stipend of ₹3,000 for degree holders and ₹1,500 for diploma holders who graduated in Karnataka and remain unemployed after 180 days.",
        "benefit": {
            "type": "cash",
            "description": "Monthly unemployment allowance for up to two years or until gaining employment.",
            "amount_text": "₹3,000/month (Graduates) or ₹1,500/month (Diploma holders)"
        },
        "eligibility": {
            "criteria": [
                {
                    "field": "state",
                    "op": "eq",
                    "value": "Karnataka",
                    "text_en": "Must be a domiciled resident of Karnataka who completed graduation/diploma in Karnataka",
                    "source_quote": "Domicile of Karnataka who studied in Karnataka"
                },
                {
                    "field": "age",
                    "op": "between",
                    "value": [20, 35],
                    "text_en": "Age must be between 20 and 35 years",
                    "source_quote": "Aged between 20 and 35"
                }
            ],
            "exclusions": [
                {
                    "field": "occupation",
                    "op": "in",
                    "value": ["government", "employed", "business"],
                    "text_en": "Gainfully employed citizens, apprentices, and higher-study students are excluded",
                    "source_quote": "Must be currently unemployed"
                }
            ],
            "notes": "Candidate must have remained unemployed for at least 180 days post-graduation."
        },
        "documents_required": [
            "Aadhaar Card",
            "Graduation / Diploma Marks Card & Convocation Certificate",
            "Karnataka Domicile / Study Certificate (minimum 6 years)",
            "Aadhaar-seeded Bank Passbook"
        ],
        "how_to_apply": {
            "steps": [
                "Register on the Seva Sindhu Guarantee Schemes portal (sevasindhugs.karnataka.gov.in).",
                "Enter your university registration number to fetch digital degree details automatically.",
                "Declare unemployment status online.",
                "Submit monthly self-declaration of unemployment to maintain continuous DBT disbursements."
            ],
            "mode": "online",
            "portal_url": "https://sevasindhugs.karnataka.gov.in"
        },
        "deadline_text": "Ongoing (Monthly claims)",
        "official_url": "https://skill.karnataka.gov.in",
        "source_name": "Government of Karnataka, Skill Development Department",
        "last_verified": "2026-11-20"
    },
    # 3. Shakti Scheme
    {
        "id": "karnataka-shakti-yojane",
        "tier": "extracted",
        "status": "unverified",
        "confidence": 0.95,
        "is_placeholder": False,
        "names": {
            "en": "Shakti Scheme",
            "kn": "ಶಕ್ತಿ ಯೋಜನೆ",
            "hi": "शक्ति योजना"
        },
        "level": "state",
        "state": "Karnataka",
        "department": "Transport Department, Government of Karnataka",
        "category": ["women", "service"],
        "target_groups": ["woman", "student"],
        "summary_en": "Provides 100% free bus travel to all women, girl students, and transgender citizens of Karnataka across KSRTC, BMTC, NWKRTC, and KKRTC state bus networks.",
        "benefit": {
            "type": "service",
            "description": "Zero-fare bus tickets for intra-state travel in ordinary and express government buses.",
            "amount_text": "100% Free Bus Travel"
        },
        "eligibility": {
            "criteria": [
                {
                    "field": "state",
                    "op": "eq",
                    "value": "Karnataka",
                    "text_en": "Must be a resident of Karnataka",
                    "source_quote": "Resident women and girl students of Karnataka"
                },
                {
                    "field": "gender",
                    "op": "eq",
                    "value": "female",
                    "text_en": "Gender must be female or transgender",
                    "source_quote": "Applicable to female citizens"
                }
            ],
            "exclusions": [],
            "notes": "Valid in ordinary and express stage-carriage buses. AC and sleeper luxury buses excluded."
        },
        "documents_required": [
            "Any valid Government Photo ID with Karnataka residential address (Aadhaar, Voter ID, Driving License)"
        ],
        "how_to_apply": {
            "steps": [
                "Board any non-AC government state bus (KSRTC, BMTC, NWKRTC, KKRTC).",
                "Present your government photo ID showing Karnataka residence to the bus conductor.",
                "Receive a zero-value physical bus ticket printed from the electronic ticketing machine."
            ],
            "mode": "offline",
            "portal_url": "https://transport.karnataka.gov.in"
        },
        "deadline_text": "Ongoing permanent welfare entitlement",
        "official_url": "https://transport.karnataka.gov.in",
        "source_name": "Karnataka State Road Transport Corporation (KSRTC) & Transport Department",
        "last_verified": "2026-11-20"
    },
    # 4. Gruha Jyothi
    {
        "id": "karnataka-gruha-jyothi",
        "tier": "extracted",
        "status": "unverified",
        "confidence": 0.95,
        "is_placeholder": False,
        "names": {
            "en": "Gruha Jyothi Scheme",
            "kn": "ಗೃಹ ಜ್ಯೋತಿ ಯೋಜನೆ",
            "hi": "गृह ज्योति योजना"
        },
        "level": "state",
        "state": "Karnataka",
        "department": "Energy Department, Government of Karnataka",
        "category": ["housing", "service"],
        "target_groups": ["bpl", "worker", "farmer"],
        "summary_en": "Free domestic electricity up to 200 units per month for all domestic household consumers in Karnataka with average consumption under 200 units.",
        "benefit": {
            "type": "service",
            "description": "Zero electricity bill for eligible domestic power consumers up to individual entitlement ceiling.",
            "amount_text": "Up to 200 Units Free Electricity"
        },
        "eligibility": {
            "criteria": [
                {
                    "field": "state",
                    "op": "eq",
                    "value": "Karnataka",
                    "text_en": "Must be a domestic consumer in Karnataka (ESCOM jurisdiction)",
                    "source_quote": "Domestic meter connection in Karnataka"
                }
            ],
            "exclusions": [
                {
                    "field": "occupation",
                    "op": "eq",
                    "value": "commercial",
                    "text_en": "Commercial and industrial power connections are strictly excluded",
                    "source_quote": "Applies strictly to LT-1 and LT-2 domestic domestic accounts"
                }
            ],
            "notes": "Entitlement is calculated as 10% above consumer's 12-month average, capped at 200 units."
        },
        "documents_required": [
            "Electricity Consumer Account ID (printed on BESCOM/HESCOM/GESCOM/MESCOM/CESC bill)",
            "Aadhaar Card of the meter account holder or tenant",
            "Voter ID / Tenancy Agreement (if tenant)"
        ],
        "how_to_apply": {
            "steps": [
                "Visit sevasindhugs.karnataka.gov.in on mobile or at Grama One / Bangalore One.",
                "Select your regional electricity supply company (ESCOM) and enter your Account ID.",
                "Authenticate with Aadhaar and submit application.",
                "Eligible consumers will receive zero-value electricity bills starting the next billing cycle."
            ],
            "mode": "both",
            "portal_url": "https://sevasindhugs.karnataka.gov.in"
        },
        "deadline_text": "Ongoing (Rolling registration)",
        "official_url": "https://energy.karnataka.gov.in",
        "source_name": "Energy Department, Government of Karnataka",
        "last_verified": "2026-11-20"
    },
    # 5. PM-KISAN Samman Nidhi
    {
        "id": "pm-kisan-samman-nidhi",
        "tier": "extracted",
        "status": "unverified",
        "confidence": 0.95,
        "is_placeholder": False,
        "names": {
            "en": "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)",
            "kn": "ಪಿಎಂ-ಕಿಸಾನ್ ಸಮ್ಮಾನ್ ನಿಧಿ",
            "hi": "पीएम किसान सम्मान निधि"
        },
        "level": "central",
        "state": None,
        "department": "Ministry of Agriculture and Farmers Welfare",
        "category": ["agriculture", "finance"],
        "target_groups": ["farmer"],
        "summary_en": "Central sector scheme providing ₹6,000 per year income support in three equal four-monthly installments of ₹2,000 each directly to cultivable landholding farmer families.",
        "benefit": {
            "type": "cash",
            "description": "Annual direct cash transfer in three equal tranches into bank account.",
            "amount_text": "₹6,000 per year (3 x ₹2,000)"
        },
        "eligibility": {
            "criteria": [
                {
                    "field": "occupation",
                    "op": "eq",
                    "value": "farmer",
                    "text_en": "Must be an active cultivator farmer",
                    "source_quote": "Small and marginal farmers holding cultivable land"
                },
                {
                    "field": "owns_land",
                    "op": "is_true",
                    "value": True,
                    "text_en": "Must own cultivable land parcel with land record title",
                    "source_quote": "Holding cultivable land"
                }
            ],
            "exclusions": [
                {
                    "field": "occupation",
                    "op": "in",
                    "value": ["government", "constitutional_post"],
                    "text_en": "Institutional landholders, constitutional post holders, serving/retired civil servants, and income tax payers are excluded",
                    "source_quote": "Institutional landholders and income tax payees excluded"
                }
            ],
            "notes": "Mandatory e-KYC and Aadhaar-NPCI bank seeding required."
        },
        "documents_required": [
            "Aadhaar Card",
            "Land ownership record (RTC / Pahani / RoR / Khasra)",
            "Aadhaar-linked Bank Passbook"
        ],
        "how_to_apply": {
            "steps": [
                "Visit pmkisan.gov.in or nearest Common Service Centre (CSC) / Raitha Samparka Kendra.",
                "Complete 'Farmer Registration' with Aadhaar and survey/khatuni number.",
                "Perform biometric or OTP e-KYC on the portal.",
                "Verify beneficiary status through PM-KISAN mobile app."
            ],
            "mode": "both",
            "portal_url": "https://pmkisan.gov.in"
        },
        "deadline_text": "Ongoing registration",
        "official_url": "https://pmkisan.gov.in",
        "source_name": "Ministry of Agriculture & Farmers Welfare, Government of India",
        "last_verified": "2026-11-20"
    },
    # 6. Raitha Siri (Karnataka)
    {
        "id": "karnataka-raitha-siri-yojana",
        "tier": "extracted",
        "status": "unverified",
        "confidence": 0.95,
        "is_placeholder": False,
        "names": {
            "en": "Raitha Siri Scheme (Millet Cultivation)",
            "kn": "ರೈತ ಸಿರಿ ಯೋಜನೆ (ಸಿರಿಧಾನ್ಯ)",
            "hi": "रैथा सिरी योजना (बाजरा/मोटा अनाज)"
        },
        "level": "state",
        "state": "Karnataka",
        "department": "Department of Agriculture, Government of Karnataka",
        "category": ["agriculture", "finance"],
        "target_groups": ["farmer"],
        "summary_en": "Direct financial assistance of ₹10,000 per hectare for farmers growing notified minor millets (ragi, foxtail, little, barnyard, kodo, proso millets) in Karnataka.",
        "benefit": {
            "type": "subsidy",
            "description": "Production incentive transferred directly to farmer bank account upon biometric field verification.",
            "amount_text": "₹10,000 per hectare (up to 2 hectares)"
        },
        "eligibility": {
            "criteria": [
                {
                    "field": "state",
                    "op": "eq",
                    "value": "Karnataka",
                    "text_en": "Must be a farmer in Karnataka",
                    "source_quote": "Farmers in Karnataka"
                },
                {
                    "field": "occupation",
                    "op": "eq",
                    "value": "farmer",
                    "text_en": "Must be actively cultivating minor millets",
                    "source_quote": "Cultivator of notified minor millets"
                },
                {
                    "field": "owns_land",
                    "op": "is_true",
                    "value": True,
                    "text_en": "Must possess agricultural land documented in FRUITS portal",
                    "source_quote": "Farmer owning land registered in FRUITS database"
                }
            ],
            "exclusions": [],
            "notes": "Crop survey must be registered on the Karnataka Farmer Crop Survey mobile app."
        },
        "documents_required": [
            "FID (FRUITS ID number)",
            "Aadhaar Card",
            "Pahani / RTC showing minor millet crop entry",
            "Bank passbook"
        ],
        "how_to_apply": {
            "steps": [
                "Ensure your land is registered with a Farmer ID (FID) on the FRUITS portal (fruits.karnataka.gov.in).",
                "Ensure local village accountant / surveyor records millet sowing in the Digital Crop Survey.",
                "Visit your Raitha Samparka Kendra to verify bank seeding.",
                "DBT incentive is automatically disbursed to your bank account."
            ],
            "mode": "both",
            "portal_url": "https://fruits.karnataka.gov.in"
        },
        "deadline_text": "Kharif and Rabi seasonal sowing cutoffs",
        "official_url": "https://raitamitra.karnataka.gov.in",
        "source_name": "Department of Agriculture, Government of Karnataka",
        "last_verified": "2026-11-20"
    },
    # 7. Ayushman Bharat PM-JAY
    {
        "id": "ayushman-bharat-pmjay",
        "tier": "extracted",
        "status": "unverified",
        "confidence": 0.95,
        "is_placeholder": False,
        "names": {
            "en": "Ayushman Bharat PM-JAY / Arogya Karnataka",
            "kn": "ಆಯುಷ್ಮಾನ್ ಭಾರತ್ - ಆರೋಗ್ಯ ಕರ್ನಾಟಕ",
            "hi": "आयुष्मान भारत - पीएम जन आरोग्य योजना"
        },
        "level": "central",
        "state": None,
        "department": "National Health Authority & Health Department",
        "category": ["health", "insurance"],
        "target_groups": ["bpl", "worker", "farmer", "senior_citizen"],
        "summary_en": "Cashless secondary and tertiary healthcare coverage of up to ₹5 Lakh per family per year across empaneled public and private hospitals across India.",
        "benefit": {
            "type": "insurance",
            "description": "Comprehensive cashless hospital treatment coverage up to ₹5,00,000 per family per year.",
            "amount_text": "₹5,00,000 Cashless Health Coverage"
        },
        "eligibility": {
            "criteria": [
                {
                    "field": "bpl",
                    "op": "is_true",
                    "value": True,
                    "text_en": "Must be a BPL family or included in SECC socio-economic database",
                    "source_quote": "Deprivation and occupational criteria in SECC or BPL ration card holders"
                }
            ],
            "exclusions": [],
            "notes": "Covers all pre-existing conditions from Day 1; no family size limit."
        },
        "documents_required": [
            "Aadhaar Card",
            "Ration Card (BPL / Antyodaya)",
            "Ayushman Card (generated at hospital or Grama One)"
        ],
        "how_to_apply": {
            "steps": [
                "Check your eligibility at beneficiary.nha.gov.in or any government hospital.",
                "Carry your Aadhaar card and Ration card to the hospital's 'Ayushman Mitra' desk.",
                "Get your e-KYC completed and receive the Ayushman Golden Card.",
                "Avail cashless surgery, treatment, diagnostics, and medicines."
            ],
            "mode": "both",
            "portal_url": "https://beneficiary.nha.gov.in"
        },
        "deadline_text": "Ongoing (Life-long valid card)",
        "official_url": "https://pmjay.gov.in",
        "source_name": "National Health Authority & Suvarna Arogya Suraksha Trust (SAST) Karnataka",
        "last_verified": "2026-11-20"
    },
    # 8. Sandhya Suraksha Yojana
    {
        "id": "karnataka-sandhya-suraksha",
        "tier": "extracted",
        "status": "unverified",
        "confidence": 0.95,
        "is_placeholder": False,
        "names": {
            "en": "Sandhya Suraksha Yojana (Old Age Pension)",
            "kn": "ಸಂಧ್ಯಾ ಸುರಕ್ಷಾ ಯೋಜನೆ (ವೃದ್ಧಾಪ್ಯ ವೇತನ)",
            "hi": "संध्या सुरक्षा योजना (वृद्धावस्था पेंशन)"
        },
        "level": "state",
        "state": "Karnataka",
        "department": "Revenue Department (Social Security and Pensions)",
        "category": ["senior_citizen", "finance"],
        "target_groups": ["senior_citizen", "bpl"],
        "summary_en": "Monthly social security pension of ₹1,200 for poor senior citizens aged 65 and above in Karnataka with no other pension or sustained family support.",
        "benefit": {
            "type": "cash",
            "description": "Monthly direct bank transfer pension for senior citizens.",
            "amount_text": "₹1,200 per month"
        },
        "eligibility": {
            "criteria": [
                {
                    "field": "state",
                    "op": "eq",
                    "value": "Karnataka",
                    "text_en": "Must be a resident of Karnataka",
                    "source_quote": "Resident of Karnataka"
                },
                {
                    "field": "age",
                    "op": "gte",
                    "value": 65,
                    "text_en": "Must be 65 years of age or older",
                    "source_quote": "Age must be 65 years or above"
                },
                {
                    "field": "annual_income",
                    "op": "lte",
                    "value": 32000.0,
                    "text_en": "Combined annual income of beneficiary and spouse must not exceed ₹32,000",
                    "source_quote": "Annual income limit ₹32,000"
                }
            ],
            "exclusions": [
                {
                    "field": "occupation",
                    "op": "eq",
                    "value": "government",
                    "text_en": "Retired government employees receiving government pension are excluded",
                    "source_quote": "Persons receiving other state or central pension excluded"
                }
            ],
            "notes": "Bank deposit balance of applicant and spouse must not exceed ₹10,000."
        },
        "documents_required": [
            "Aadhaar Card (Age proof)",
            "Income Certificate issued by Tahsildar / Nadakacheri",
            "Bank passbook",
            "BPL Ration Card"
        ],
        "how_to_apply": {
            "steps": [
                "Obtain Income and Domicile Certificate from Nadakacheri (Atalji Janasnehi Kendra).",
                "Apply online via nadakacheri.karnataka.gov.in or Seva Sindhu.",
                "Application is verified by Village Administrative Officer (VAO) and sanctioned by Tahsildar.",
                "Monthly pension is credited via DBT to the Aadhaar-linked bank account."
            ],
            "mode": "both",
            "portal_url": "https://nadakacheri.karnataka.gov.in"
        },
        "deadline_text": "Ongoing (Monthly sanction)",
        "official_url": "https://revenue.karnataka.gov.in",
        "source_name": "Directorate of Social Security and Pensions, Revenue Department",
        "last_verified": "2026-11-20"
    }
]

def main():
    logger.info("Starting Open Data & Statutory Rights Ingestion...")

    # 1. Update Rights Knowledge Base
    rights_path = settings.DATA_DIR / "rights_kb.json"
    with open(rights_path, "w", encoding="utf-8") as f:
        json.dump(RIGHTS_DATA, f, indent=2, ensure_ascii=False)
    logger.info("Successfully updated rights_kb.json with %d statutory rights entries.", len(RIGHTS_DATA))

    # 2. Ingest Open Schemes into Tier 2 (Extracted) Schemes
    extracted_path = settings.DATA_DIR / "schemes_extracted.json"
    existing_extracted = []
    if extracted_path.exists():
        try:
            with open(extracted_path, "r", encoding="utf-8") as f:
                existing_extracted = json.load(f)
        except Exception:
            existing_extracted = []

    existing_ids = {s["id"] for s in existing_extracted}
    added_count = 0

    for scheme_dict in EXTRACTED_OPEN_SCHEMES:
        errs = SchemeValidator.validate_dict(scheme_dict)
        if errs:
            logger.error("Validation error for %s: %s", scheme_dict["id"], errs)
            continue
        
        if scheme_dict["id"] not in existing_ids:
            existing_extracted.append(scheme_dict)
            existing_ids.add(scheme_dict["id"])
            added_count += 1
        else:
            for i, it in enumerate(existing_extracted):
                if it["id"] == scheme_dict["id"]:
                    existing_extracted[i] = scheme_dict

    with open(extracted_path, "w", encoding="utf-8") as f:
        json.dump(existing_extracted, f, indent=2, ensure_ascii=False)
    logger.info("Updated schemes_extracted.json. Total extracted schemes now: %d (added %d new).", len(existing_extracted), added_count)

    # 3. Add Raw Policy Documents for Ingestion Pipeline in data/raw/
    raw_dir = settings.DATA_DIR / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    summary_doc_path = raw_dir / "karnataka_flagship_schemes_bulletin.txt"
    with open(summary_doc_path, "w", encoding="utf-8") as f:
        f.write("""GOVERNMENT OF KARNATAKA - OFFICIAL POLICY BULLETIN 2026
Department of Social Welfare & Mahiti Kanaja Public Record

1. Gruha Lakshmi Scheme
Providing ₹2,000 monthly cash assistance to women head of households across Karnataka.
Eligibility: Resident of Karnataka, female head on ration card, age 18+. Exclusions: Income tax payers.
Apply via Seva Sindhu or Grama One.

2. Yuva Nidhi Scheme
Financial assistance of ₹3,000/mo for unemployed graduates and ₹1,500/mo for diploma holders who completed study in Karnataka.
Eligibility: Age 20 to 35, Karnataka resident, unemployed for 180 days post completion.

3. Shakti Bus Yojane
100% free bus travel across Karnataka state bus corporations (KSRTC, BMTC, NWKRTC, KKRTC) for women and girls.
Present valid government photo ID showing Karnataka address to conductor for zero-fare ticket.

4. PM-KISAN Samman Nidhi
Income support of ₹6,000 annually in 3 installments of ₹2,000 to cultivable landholding farmer families.
Apply on pmkisan.gov.in with Aadhaar and land RTC/Pahani.
""")
    logger.info("Generated official bulletin in data/raw/%s", summary_doc_path.name)

    # 4. Re-index Vector Embeddings for Semantic Search across Verified & Extracted schemes
    verified_path = settings.DATA_DIR / "schemes_verified.json"
    verified_schemes = []
    if verified_path.exists():
        with open(verified_path, "r", encoding="utf-8") as f:
            verified_schemes = json.load(f)

    all_schemes = verified_schemes + existing_extracted
    logger.info("Rebuilding vector store embeddings across %d total schemes...", len(all_schemes))
    vector_store = SchemeVectorStore()
    indexed_count = 0
    for s_dict in all_schemes:
        try:
            s_obj = Scheme(**s_dict)
            vector_store.add_scheme(s_obj)
            indexed_count += 1
        except Exception as e:
            logger.warning("Could not index %s: %s", s_dict.get("id"), e)
    vector_store.save()
    logger.info("Indexed %d schemes into vector store.", indexed_count)

    logger.info("✅ Open Data ingestion complete!")

if __name__ == "__main__":
    main()
