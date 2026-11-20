from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from backend.app.models.evidence import EvidenceModel, ClaimEvidenceModel
from backend.app.repositories.evidence_repository import EvidenceRepository
from backend.app.repositories.claim_repository import ClaimRepository
from backend.app.schemas.evidence import EvidenceCreate
from backend.app.integrations.evidence_provider import (
    CorporateDisclosuresProvider,
    NSEDisclosuresProvider,
    SECDisclosuresProvider,
    BaseEvidenceProvider
)


def _parse_datetime(val: Any) -> Optional[datetime]:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        cleaned = val.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(cleaned)
        except Exception:
            return None
    return None


class EvidenceService:
    def __init__(self, db: Session, provider: Optional[BaseEvidenceProvider] = None):
        self.db = db
        self.repository = EvidenceRepository(db)
        self.claim_repo = ClaimRepository(db)
        self.provider = provider or CorporateDisclosuresProvider()

    def store_evidence(self, evidence_in: EvidenceCreate) -> EvidenceModel:
        """Stores a verified evidence record with strict provenance tracking."""
        model = EvidenceModel(
            title=evidence_in.title,
            document_title=evidence_in.document_title or evidence_in.title,
            publisher=evidence_in.publisher,
            source_url=evidence_in.source_url,
            publication_date=evidence_in.publication_date,
            evidence_category=evidence_in.evidence_category.value,
            company_identifier=evidence_in.company_identifier,
            company_symbol=evidence_in.company_symbol,
            company_isin=evidence_in.company_isin,
            source_jurisdiction=evidence_in.source_jurisdiction,
            exchange=evidence_in.exchange,
            content_summary=evidence_in.content_summary,
            provenance_status=evidence_in.provenance_status.value,
            raw_payload=evidence_in.raw_payload
        )
        return self.repository.create_evidence(model)

    def associate_evidence(
        self,
        claim_id: str,
        evidence_id: str,
        relevance_score: float = 1.0,
        notes: Optional[str] = None
    ) -> ClaimEvidenceModel:
        return self.repository.associate_with_claim(
            claim_id=claim_id,
            evidence_id=evidence_id,
            relevance_score=relevance_score,
            notes=notes
        )

    async def retrieve_for_claim(self, claim_id: str) -> List[ClaimEvidenceModel]:
        """
        Retrieves real evidence from verifiable external sources for a claim,
        stores them, and establishes association.
        Enforces strict entity resolution: unverified or ambiguous companies return empty.
        """
        claim = self.claim_repo.get_by_id(claim_id)
        if not claim:
            return []

        # STRICT GUARD: If entity reference is inherently ambiguous, do not auto-retrieve
        if claim.is_ambiguous_entity:
            return []

        # Retrieve through provider (NSE for Indian home market, SEC for verified ADRs)
        items = await self.provider.retrieve_evidence(
            company_name=claim.company_name,
            ticker=claim.ticker
        )

        existing_associations = self.repository.get_claim_evidence(claim_id)
        existing_urls = {a.evidence.source_url for a in existing_associations}

        for item in items:
            source_url = item["source_url"]
            # Deduplicate by source URL
            if source_url in existing_urls:
                continue

            pub_date = _parse_datetime(item.get("publication_date"))
            ev_model = EvidenceModel(
                title=item["title"],
                document_title=item.get("document_title") or item["title"],
                publisher=item["publisher"],
                source_url=source_url,
                publication_date=pub_date,
                evidence_category=item["evidence_category"],
                company_identifier=item.get("company_identifier"),
                company_symbol=item.get("company_symbol"),
                company_isin=item.get("company_isin"),
                source_jurisdiction=item.get("source_jurisdiction", "IN"),
                exchange=item.get("exchange", "NSE"),
                content_summary=item["content_summary"],
                provenance_status=item.get("provenance_status", "REAL"),
                raw_payload=item.get("raw_payload")
            )
            created_ev = self.repository.create_evidence(ev_model)
            self.repository.associate_with_claim(
                claim_id=claim_id,
                evidence_id=created_ev.id,
                relevance_score=1.0,
                notes=f"Primary statutory disclosure ({item.get('exchange', 'NSE')})"
            )
            existing_urls.add(source_url)

        return self.repository.get_claim_evidence(claim_id)

    def get_claim_evidence(self, claim_id: str) -> List[ClaimEvidenceModel]:
        return self.repository.get_claim_evidence(claim_id)

    def get_evidence_item(self, evidence_id: str) -> Optional[EvidenceModel]:
        return self.repository.get_by_id(evidence_id)
