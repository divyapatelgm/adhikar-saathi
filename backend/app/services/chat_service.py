import json
import logging
from typing import Optional, List
from pathlib import Path

from ..config import settings
from ..models.api import ChatRequest, ChatResponse, SourceCitation
from ..models.scheme import Scheme
from ..models.rights import RightsEntry
from .cache_service import response_cache, ResponseCacheService
from .retrieval_service import retrieval_service, RetrievalService
from .tier3_linkout import Tier3LinkOutService
from ..pipeline.llm_client import LLMClient, get_llm_client

logger = logging.getLogger(__name__)

PROMPT_VERSION = "v2"

class ChatService:
    """
    Orchestrates grounded multilingual chat across:
    1. Response Cache
    2. Retrieval (Rights & Schemes)
    3. Tier 3 Link-Out for unknown/unmatched queries
    4. Anti-hallucination source attribution and disclaimers
    """

    def __init__(
        self,
        retrieval: Optional[RetrievalService] = None,
        cache: Optional[ResponseCacheService] = None,
        llm_client: Optional[LLMClient] = None,
    ):
        self.retrieval = retrieval or retrieval_service
        self.cache = cache or response_cache
        self.llm = llm_client or get_llm_client()
        self.prompts_dir = settings.BASE_DIR / "backend" / "app" / "prompts" / PROMPT_VERSION

    async def handle_chat(self, request: ChatRequest) -> ChatResponse:
        """Processes a citizen's query in en/kn/hi with strict source citations."""
        lang = request.language.lower() if request.language in ("en", "kn", "hi") else "en"
        query = request.message.strip()

        # 1. Check SQLite Response Cache
        cached_response = self.cache.get_cached_chat(query, lang, PROMPT_VERSION)
        if cached_response:
            logger.info("Chat query served from SQLite cache: '%s' (%s)", query[:30], lang)
            return cached_response

        # 2. Retrieve Candidate
        match_type, item, score = self.retrieval.retrieve(query)
        logger.info("Retrieval result for '%s': match_type=%s, score=%.2f", query[:30], match_type, score)

        # 3. Handle Tier 3: No relevant record found
        if match_type == "none" or item is None:
            response = Tier3LinkOutService.generate_linkout_response(
                query=query,
                language=lang,
                region="karnataka"
            )
            self.cache.save_cached_chat(query, lang, response, PROMPT_VERSION)
            return response

        # 4. Handle Rights Question
        if match_type == "rights" and isinstance(item, RightsEntry):
            response = await self._generate_rights_response(query, item, lang)
            self.cache.save_cached_chat(query, lang, response, PROMPT_VERSION)
            return response

        # 5. Handle Scheme Question
        if match_type == "scheme" and isinstance(item, Scheme):
            response = await self._generate_scheme_response(query, item, lang)
            self.cache.save_cached_chat(query, lang, response, PROMPT_VERSION)
            return response

        # Fallback safe link-out
        return Tier3LinkOutService.generate_linkout_response(query, lang)

    async def _generate_rights_response(self, query: str, rights: RightsEntry, lang: str) -> ChatResponse:
        """Generates grounded, empathetic explanation of legal / civic rights."""
        steps_bullet = "\n".join(f"{i+1}. {step}" for i, step in enumerate(rights.steps))

        if lang == "kn":
            reply_text = (
                f"ನಮಸ್ಕಾರ! **ವಿಷಯ: {rights.topic}**\n\n"
                f"ಕಾನೂನಿನ ಪ್ರಕಾರ ನಿಮ್ಮ ಹಕ್ಕುಗಳ ವಿವರ ಇಲ್ಲಿದೆ:\n{rights.answer_en}\n\n"
                f"📋 **ನೀವು ತೆಗೆದುಕೊಳ್ಳಬೇಕಾದ ಕ್ರಮಗಳು:**\n{steps_bullet}\n\n"
                f"📞 **ಸಂಪರ್ಕಿಸಬೇಕಾದ ಪ್ರಾಧಿಕಾರ / ಸಹಾಯವಾಣಿ:**\n{rights.helpline_or_authority}\n\n"
                f"💡 ನೆನಪಿಡಿ, ಸರ್ಕಾರಿ ನಿಯಮಗಳ ಪ್ರಕಾರ ಈ ಸೌಲಭ್ಯವನ್ನು ಪಡೆಯುವುದು ನಿಮ್ಮ ಶಾಸನಬದ್ಧ ಹಕ್ಕಾಗಿದೆ."
            )
            clean_first = rights.answer_en.split('.')[0]
            audio_summary = f"ನಮಸ್ಕಾರ! {rights.topic} ಕುರಿತು: {clean_first}. ಹೆಚ್ಚಿನ ಸಹಾಯಕ್ಕಾಗಿ {rights.helpline_or_authority} ಸಂಪರ್ಕಿಸಬಹುದು."
        elif lang == "hi":
            reply_text = (
                f"नमस्ते! **विषय: {rights.topic}**\n\n"
                f"कानून के अनुसार आपके अधिकारों की स्पष्ट जानकारी:\n{rights.answer_en}\n\n"
                f"📋 **कार्रवाई के कदम:**\n{steps_bullet}\n\n"
                f"📞 **संपर्क प्राधिकरण / हेल्पलाइन:**\n{rights.helpline_or_authority}\n\n"
                f"💡 ध्यान दें, सरकारी नियमों के अंतर्गत समय पर यह सेवा प्राप्त करना आपका वैधानिक अधिकार है।"
            )
            clean_first = rights.answer_en.split('.')[0]
            audio_summary = f"नमस्ते! {rights.topic} के संबंध में: {clean_first}. सहायता हेतु हेल्पलाइन {rights.helpline_or_authority} पर संपर्क करें।"
        else:
            reply_text = (
                f"Hello! Here is citizen guidance regarding **{rights.topic}**:\n\n"
                f"{rights.answer_en}\n\n"
                f"📋 **Action Steps You Can Take:**\n{steps_bullet}\n\n"
                f"📞 **Grievance Authority / Helpline:**\n{rights.helpline_or_authority}\n\n"
                f"💡 Note: Under Indian statutory law, receiving these entitlements in a timely manner is your legal citizen right."
            )
            clean_first = rights.answer_en.split('.')[0]
            audio_summary = f"Hello! Regarding {rights.topic}: {clean_first}. You can contact {rights.helpline_or_authority} for assistance."

        sources = [
            SourceCitation(
                source_name=rights.source_name,
                official_url=rights.source_url,
                last_verified=rights.last_verified,
                tier="tier-1-verified"
            )
        ]

        return ChatResponse(
            reply_text=reply_text,
            language=lang,
            audio_summary=audio_summary,
            sources=sources,
            is_link_out=False,
            disclaimer="Information only, not legal advice. Please verify at the official office/portal."
        )

    async def _generate_scheme_response(self, query: str, scheme: Scheme, lang: str) -> ChatResponse:
        """Generates warm, humanized scheme explanation with benefit, docs, and application steps."""
        name = scheme.names.get(lang) or scheme.names.get("en") or scheme.id
        docs_bullet = "\n".join(f"• {doc}" for doc in scheme.documents_required)
        steps_bullet = "\n".join(f"{i+1}. {st}" for i, st in enumerate(scheme.how_to_apply.steps))

        if lang == "kn":
            reply_text = (
                f"ನಮಸ್ಕಾರ! **{name}** ಕುರಿತು ವಿವರ ಇಲ್ಲಿದೆ:\n\n"
                f"**ವಿಷಯ ಹಾಗೂ ವಿವರ:** {scheme.summary_en}\n\n"
                f"🎁 **ನಿಮಗೆ ಸಿಗುವ ಪ್ರಮುಖ ಪ್ರಯೋಜನ:**\n{scheme.benefit.description} ({scheme.benefit.amount_text})\n\n"
                f"📋 **ಅಗತ್ಯವಿರುವ ದಾಖಲೆಗಳು:**\n{docs_bullet}\n\n"
                f"🏢 **ಅರ್ಜಿ ಸಲ್ಲಿಸುವ ಕ್ರಮಗಳು ({scheme.how_to_apply.mode}):**\n{steps_bullet}\n\n"
                f"⏳ **ಅಂತಿಮ ದಿನಾಂಕ:** {scheme.deadline_text}\n\n"
                f"💡 **ಸಲಹೆ:** ಅರ್ಜಿ ಸಲ್ಲಿಸಲು ನಿಮ್ಮ ಹತ್ತಿರದ ಗ್ರಾಮ ಒನ್ (Grama One) ಅಥವಾ ಸೇವಾ ಸಿಂಧು ಕೇಂದ್ರಕ್ಕೆ ಭೇಟಿ ನೀಡಿ."
            )
            audio_summary = f"ನಮಸ್ಕಾರ! {name} ಕುರಿತು ಇಲ್ಲಿದೆ ಮಾಹಿತಿ. {scheme.benefit.description}. ನೀವು ನಿಮ್ಮ ಹತ್ತಿರದ ಗ್ರಾಮ ಒನ್ ಅಥವಾ ಸೇವಾ ಸಿಂಧು ಕೇಂದ್ರದಲ್ಲಿ ಅಗತ್ಯ ದಾಖಲೆಗಳೊಂದಿಗೆ ಸುಲಭವಾಗಿ ಅರ್ಜಿ ಸಲ್ಲಿಸಬಹುದು."
        elif lang == "hi":
            reply_text = (
                f"नमस्ते! **{name}** के बारे में आवश्यक जानकारी:\n\n"
                f"**विवरण:** {scheme.summary_en}\n\n"
                f"🎁 **मुख्य लाभ:**\n{scheme.benefit.description} ({scheme.benefit.amount_text})\n\n"
                f"📋 **आवश्यक दस्तावेज:**\n{docs_bullet}\n\n"
                f"🏢 **आवेदन के कदम ({scheme.how_to_apply.mode}):**\n{steps_bullet}\n\n"
                f"⏳ **अंतिम तिथि:** {scheme.deadline_text}\n\n"
                f"💡 **सुझाव:** आवेदन सहायता के लिए आप अपने नजदीकी ग्राम वन या नागरिक सेवा केंद्र (CSC) पर जा सकते हैं।"
            )
            audio_summary = f"नमस्ते! {name} के तहत {scheme.benefit.description}. आप अपने नजदीकी ग्राम वन केंद्र पर जरूरी दस्तावेजों के साथ आवेदन कर सकते हैं।"
        else:
            reply_text = (
                f"Hello! Here is a friendly explanation of the **{name}**:\n\n"
                f"**Overview:** {scheme.summary_en}\n\n"
                f"🎁 **Key Benefit for You:**\n{scheme.benefit.description} ({scheme.benefit.amount_text})\n\n"
                f"📋 **Checklist of Required Documents:**\n{docs_bullet}\n\n"
                f"🏢 **How to Apply ({scheme.how_to_apply.mode}):**\n{steps_bullet}\n\n"
                f"⏳ **Application Deadline:** {scheme.deadline_text}\n\n"
                f"💡 **Helpful Tip:** You can easily apply or get guided assistance at your nearest Grama One, Seva Sindhu, or CSC center."
            )
            audio_summary = f"Hello! The {name} provides {scheme.benefit.description}. You can easily apply through {scheme.how_to_apply.mode} with your required documents."

        sources = [
            SourceCitation(
                source_name=scheme.source_name,
                official_url=scheme.official_url,
                last_verified=scheme.last_verified,
                tier=scheme.tier.value
            )
        ]

        return ChatResponse(
            reply_text=reply_text,
            language=lang,
            audio_summary=audio_summary,
            sources=sources,
            is_link_out=False,
            disclaimer="Information only, not legal advice. Please verify at the official office/portal."
        )

chat_service = ChatService()
