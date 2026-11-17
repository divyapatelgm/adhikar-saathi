import logging
from typing import List, Optional, Tuple, Any, Dict
from ..models.enums import TierType, VerdictType, RuleOperator, RuleField
from ..models.scheme import Scheme
from ..models.rule import EligibilityRule
from ..models.profile import UserProfile
from ..models.verdict import EligibilityEvaluation, EvaluationCriterionResult

logger = logging.getLogger(__name__)

class RulesEngine:
    """
    Deterministic evaluation engine for welfare schemes against user profiles.
    100% deterministic logic without LLM guesswork.
    """

    @classmethod
    def evaluate_rule(cls, rule: EligibilityRule, profile: UserProfile) -> Tuple[str, str, Any, Any]:
        """
        Evaluates a single EligibilityRule against a UserProfile.
        Returns (status, reason, citizen_val, required_val):
          - status: "matched" | "failed" | "missing"
        """
        field_name = rule.field.value
        citizen_val = getattr(profile, field_name, None)

        if field_name == RuleField.OTHER.value:
            # "other" field cannot be automatically evaluated from profile
            return "missing", f"Special criterion '{rule.text_en}' requires manual verification", None, rule.value

        if citizen_val is None:
            return "missing", f"Missing information for {field_name}: {rule.text_en}", None, rule.value

        op = rule.op
        req_val = rule.value

        try:
            # Numeric operators
            if op == RuleOperator.GTE:
                if float(citizen_val) >= float(req_val):
                    return "matched", f"{field_name} ({citizen_val}) is >= {req_val}", citizen_val, req_val
                else:
                    return "failed", f"{field_name} ({citizen_val}) is less than required {req_val}", citizen_val, req_val

            elif op == RuleOperator.LTE:
                if float(citizen_val) <= float(req_val):
                    return "matched", f"{field_name} ({citizen_val}) is <= {req_val}", citizen_val, req_val
                else:
                    return "failed", f"{field_name} ({citizen_val}) exceeds limit of {req_val}", citizen_val, req_val

            elif op == RuleOperator.BETWEEN:
                min_v, max_v = float(req_val[0]), float(req_val[1])
                c_num = float(citizen_val)
                if min_v <= c_num <= max_v:
                    return "matched", f"{field_name} ({c_num}) is within [{min_v}, {max_v}]", citizen_val, req_val
                else:
                    return "failed", f"{field_name} ({c_num}) is outside [{min_v}, {max_v}]", citizen_val, req_val

            # Equality & inequality operators
            elif op == RuleOperator.EQ:
                if cls._equals(citizen_val, req_val):
                    return "matched", f"{field_name} matches '{req_val}'", citizen_val, req_val
                else:
                    return "failed", f"{field_name} '{citizen_val}' does not match required '{req_val}'", citizen_val, req_val

            elif op == RuleOperator.NE:
                if not cls._equals(citizen_val, req_val):
                    return "matched", f"{field_name} is not '{req_val}'", citizen_val, req_val
                else:
                    return "failed", f"{field_name} '{citizen_val}' cannot be '{req_val}'", citizen_val, req_val

            # Set membership operators
            elif op == RuleOperator.IN:
                norm_req = [str(x).strip().lower() for x in req_val]
                if str(citizen_val).strip().lower() in norm_req:
                    return "matched", f"{field_name} '{citizen_val}' is in eligible list", citizen_val, req_val
                else:
                    return "failed", f"{field_name} '{citizen_val}' is not in allowed list {req_val}", citizen_val, req_val

            elif op == RuleOperator.NOT_IN:
                norm_req = [str(x).strip().lower() for x in req_val]
                if str(citizen_val).strip().lower() not in norm_req:
                    return "matched", f"{field_name} '{citizen_val}' is not in excluded list", citizen_val, req_val
                else:
                    return "failed", f"{field_name} '{citizen_val}' is in disqualified list {req_val}", citizen_val, req_val

            # Boolean operators
            elif op == RuleOperator.IS_TRUE:
                if bool(citizen_val) is True:
                    return "matched", f"{field_name} is True", citizen_val, True
                else:
                    return "failed", f"{field_name} must be True", citizen_val, True

            elif op == RuleOperator.IS_FALSE:
                if bool(citizen_val) is False:
                    return "matched", f"{field_name} is False", citizen_val, False
                else:
                    return "failed", f"{field_name} must be False", citizen_val, False

            else:
                return "failed", f"Unsupported operator '{op}'", citizen_val, req_val

        except (ValueError, TypeError) as e:
            logger.warning("Error evaluating rule on %s: %s", field_name, e)
            return "failed", f"Data format mismatch for {field_name}: {e}", citizen_val, req_val

    @staticmethod
    def _equals(val1: Any, val2: Any) -> bool:
        if isinstance(val1, str) and isinstance(val2, str):
            return val1.strip().lower() == val2.strip().lower()
        if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
            return float(val1) == float(val2)
        return val1 == val2

    @classmethod
    def evaluate_scheme(cls, profile: UserProfile, scheme: Scheme, language: str = "en") -> EligibilityEvaluation:
        """
        Evaluates a complete Scheme against a citizen profile.
        Determines:
          - Matched criteria
          - Failed criteria
          - Missing info
          - Exclusions
          - Final verdict (Eligible, Likely, Not eligible, Maybe)
        """
        matched: List[str] = []
        failed: List[str] = []
        missing_fields: List[str] = []
        detailed_results: List[EvaluationCriterionResult] = []

        # 1. State restriction check for state schemes
        if scheme.level.value == "state" and scheme.state:
            if profile.state is None:
                missing_fields.append("state")
                detailed_results.append(EvaluationCriterionResult(
                    field="state",
                    text_en=f"Must reside in {scheme.state}",
                    status="missing",
                    reason="State of residence is unknown"
                ))
            elif profile.state.strip().lower() != scheme.state.strip().lower():
                failed.append(f"Requires residence in {scheme.state} (Citizen is in {profile.state})")
                detailed_results.append(EvaluationCriterionResult(
                    field="state",
                    text_en=f"Must reside in {scheme.state}",
                    status="failed",
                    citizen_value=profile.state,
                    required_value=scheme.state,
                    reason=f"State '{profile.state}' does not match required '{scheme.state}'"
                ))

        # 2. Check Exclusions (Disqualifications)
        for exclusion in scheme.eligibility.exclusions:
            status, reason, c_val, r_val = cls.evaluate_rule(exclusion, profile)
            if status == "matched":
                # Matched an EXCLUSION rule means the citizen is disqualified!
                failed.append(f"Excluded: {exclusion.text_en}")
                detailed_results.append(EvaluationCriterionResult(
                    field=exclusion.field.value,
                    text_en=f"Exclusion: {exclusion.text_en}",
                    status="failed",
                    citizen_value=c_val,
                    required_value=r_val,
                    reason=f"Citizen triggers exclusion: {reason}"
                ))
            elif status == "missing":
                missing_fields.append(exclusion.field.value)
                detailed_results.append(EvaluationCriterionResult(
                    field=exclusion.field.value,
                    text_en=f"Check potential exclusion: {exclusion.text_en}",
                    status="missing",
                    citizen_value=None,
                    required_value=r_val,
                    reason=reason
                ))

        # 3. Check Criteria (Qualifications)
        for criterion in scheme.eligibility.criteria:
            status, reason, c_val, r_val = cls.evaluate_rule(criterion, profile)
            detailed_results.append(EvaluationCriterionResult(
                field=criterion.field.value,
                text_en=criterion.text_en,
                status=status,
                citizen_value=c_val,
                required_value=r_val,
                reason=reason
            ))
            if status == "matched":
                matched.append(criterion.text_en)
            elif status == "failed":
                failed.append(criterion.text_en)
            elif status == "missing":
                missing_fields.append(criterion.field.value)

        # Deduplicate missing fields maintaining order
        dedup_missing: List[str] = []
        for mf in missing_fields:
            if mf not in dedup_missing:
                dedup_missing.append(mf)

        # 4. Compute Final Verdict
        # Rule A: Any definitive failure or triggered exclusion -> NOT_ELIGIBLE
        if len(failed) > 0:
            verdict = VerdictType.NOT_ELIGIBLE
            reason = f"Disqualified on {len(failed)} criteria: " + "; ".join(failed[:2])
            missing_q = None

        # Rule B: Missing info needed to confirm eligibility -> MAYBE
        elif len(dedup_missing) > 0:
            verdict = VerdictType.MAYBE
            reason = f"May be eligible, but {len(dedup_missing)} question(s) need clarification: " + ", ".join(dedup_missing)
            missing_q = f"What is your {dedup_missing[0].replace('_', ' ')}?"

        # Rule C: All criteria matched and no exclusions triggered
        else:
            if scheme.tier == TierType.VERIFIED:
                verdict = VerdictType.ELIGIBLE
                reason = f"All {len(matched)} verified eligibility criteria satisfied."
                missing_q = None
            else:
                # Tier 2 (Extracted) records
                # User Requirement: Tier 2 records return only LIKELY or MAYBE (never ELIGIBLE).
                # Tier 2 with confidence < 0.7 is capped at MAYBE.
                if scheme.confidence >= 0.7:
                    verdict = VerdictType.LIKELY
                    reason = f"Likely eligible based on auto-extracted record (confidence: {scheme.confidence:.0%}). Official verification recommended."
                else:
                    verdict = VerdictType.MAYBE
                    reason = f"Potentially eligible, but extraction confidence is low ({scheme.confidence:.0%}). Needs human verification."
                missing_q = None

        scheme_name = scheme.names.get(language) or scheme.names.get("en") or scheme.id

        return EligibilityEvaluation(
            scheme_id=scheme.id,
            scheme_name=scheme_name,
            verdict=verdict,
            confidence=scheme.confidence,
            tier=scheme.tier,
            matched_criteria=matched,
            failed_criteria=failed,
            missing_info=dedup_missing,
            detailed_criteria=detailed_results,
            reason_en=reason,
            missing_question=missing_q,
            official_url=scheme.official_url,
            source_name=scheme.source_name,
            last_verified=scheme.last_verified,
        )

    @classmethod
    def evaluate_all(
        cls,
        profile: UserProfile,
        schemes: List[Scheme],
        language: str = "en"
    ) -> List[EligibilityEvaluation]:
        """
        Evaluates a list of schemes against a profile and returns them sorted by:
        1. Verdict priority: ELIGIBLE > LIKELY > MAYBE > NOT_ELIGIBLE
        2. Confidence descending
        3. Fewest missing info count ascending
        """
        evaluations = [cls.evaluate_scheme(profile, s, language=language) for s in schemes]

        verdict_rank = {
            VerdictType.ELIGIBLE: 0,
            VerdictType.LIKELY: 1,
            VerdictType.MAYBE: 2,
            VerdictType.NOT_ELIGIBLE: 3,
        }

        evaluations.sort(
            key=lambda ev: (
                verdict_rank.get(ev.verdict, 99),
                -ev.confidence,
                len(ev.missing_info)
            )
        )

        return evaluations
