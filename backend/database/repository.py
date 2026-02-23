import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from sqlalchemy.orm import selectinload

from database.models import (
    Session, Transcript, Speakers, Utterances, Guest, GeneratedContent,
    PromptTemplate, PromptUsage, TokenUsage, UsageSummary
)

logger = logging.getLogger(__name__)


class Repository:
    """Async database repository for all CRUD operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== Session Operations ====================

    async def create_session(self, session_id: str, title: str = "") -> Session:
        """Create a new session"""
        session = Session(session_id=session_id, title=title or session_id, status="processing")
        self.db.add(session)
        await self.db.flush()
        logger.info(f"Created session: {session_id}")
        return session

    async def get_session(self, session_id: str, load_relations: bool = True) -> Optional[Session]:
        """Get a session by session_id"""
        query = select(Session).where(Session.session_id == session_id)
        if load_relations:
            query = query.options(
                selectinload(Session.transcript).selectinload(Transcript.utterances),
                selectinload(Session.speakers),
                selectinload(Session.guest),
                selectinload(Session.generated_content),
                selectinload(Session.prompt_usage),
                selectinload(Session.token_usage)
            )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_session_status(self, session_id: str, status: str) -> None:
        """Update session status"""
        query = select(Session).where(Session.session_id == session_id)
        result = await self.db.execute(query)
        session = result.scalar_one()
        session.status = status
        session.updated_at = datetime.utcnow()
        await self.db.flush()

    # ==================== Transcript Operations ====================

    async def save_transcript(self, session_id: str, raw_text: str, transcript_json: List[Dict],
                             duration_seconds: float, speaker_labels_enabled: bool = False,
                             speaker_identification_enabled: bool = False) -> Transcript:
        """Save transcript data for a session"""
        transcript = Transcript(
            session_id=session_id,
            raw_text=raw_text,
            transcript_json=transcript_json,
            duration_seconds=duration_seconds,
            speaker_labels_enabled=speaker_labels_enabled,
            speaker_identification_enabled=speaker_identification_enabled
        )
        self.db.add(transcript)
        await self.db.flush()
        logger.info(f"Saved transcript for session: {session_id}")
        return transcript

    async def get_transcript(self, session_id: str) -> Optional[Transcript]:
        """Get transcript for a session"""
        query = select(Transcript).where(
            Transcript.session_id == session_id
        ).options(selectinload(Transcript.utterances).selectinload(Utterances.speaker))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    # ==================== Speaker Operations ====================

    async def save_speaker(self, session_id: str, speaker_num: str, name: str,
                          role: Optional[str] = None, confidence: Optional[float] = None,
                          metadata: Optional[Dict] = None) -> Speakers:
        """Save a speaker record"""
        speaker = Speakers(
            session_id=session_id,
            speaker_num=speaker_num,
            name=name,
            role=role,
            confidence=confidence,
            metadata_json=metadata
        )
        self.db.add(speaker)
        await self.db.flush()
        return speaker

    async def get_speakers(self, session_id: str) -> List[Speakers]:
        """Get all speakers for a session"""
        query = select(Speakers).where(Speakers.session_id == session_id)
        result = await self.db.execute(query)
        return result.scalars().all()

    # ==================== Utterance Operations ====================

    async def save_utterance(self, transcript_id: int, speaker_id: Optional[int],
                            text: str, start_time_ms: int, end_time_ms: int,
                            confidence: Optional[float] = None,
                            words_json: Optional[List[Dict]] = None) -> Utterances:
        """Save a single utterance"""
        utterance = Utterances(
            transcript_id=transcript_id,
            speaker_id=speaker_id,
            text=text,
            start_time_ms=start_time_ms,
            end_time_ms=end_time_ms,
            confidence=confidence,
            words_json=words_json
        )
        self.db.add(utterance)
        await self.db.flush()
        return utterance

    async def save_utterances_batch(self, transcript_id: int, utterances_data: List[Dict]) -> None:
        """Save multiple utterances at once"""
        for u in utterances_data:
            utterance = Utterances(
                transcript_id=transcript_id,
                speaker_id=u.get("speaker_id"),
                text=u["text"],
                start_time_ms=u["start_time_ms"],
                end_time_ms=u["end_time_ms"],
                confidence=u.get("confidence"),
                words_json=u.get("words_json")
            )
            self.db.add(utterance)
        await self.db.flush()

    # ==================== Guest Operations ====================

    async def save_guest(self, session_id: str, name: str, title: str,
                        company: str, linkedin_url: str, notes: Optional[str] = None) -> Guest:
        """Save guest information"""
        guest = Guest(
            session_id=session_id,
            name=name,
            title=title,
            company=company,
            linkedin_url=linkedin_url,
            notes=notes
        )
        self.db.add(guest)
        await self.db.flush()
        logger.info(f"Saved guest for session: {session_id}")
        return guest

    async def get_guest(self, session_id: str) -> Optional[Guest]:
        """Get guest info for a session"""
        query = select(Guest).where(Guest.session_id == session_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    # ==================== Generated Content Operations ====================

    async def save_generated_content(self, session_id: str, content: Dict, model: str) -> GeneratedContent:
        """Save all AI-generated content"""
        gen_content = GeneratedContent(
            session_id=session_id,
            youtube_summary=content.get("youtube_summary"),
            blog_post=content.get("blog_post"),
            clickbait_titles=content.get("clickbait_titles"),
            two_line_summary=content.get("two_line_summary"),
            quotes=content.get("quotes"),
            chapter_timestamps=content.get("chapter_timestamps"),
            linkedin_post=content.get("linkedin_post"),
            keywords=content.get("keywords"),
            hashtags=content.get("hashtags"),
            full_episode_description=content.get("full_episode_description"),
            openai_model_used=model
        )
        self.db.add(gen_content)
        await self.db.flush()
        logger.info(f"Saved generated content for session: {session_id}")
        return gen_content

    async def get_generated_content(self, session_id: str) -> Optional[GeneratedContent]:
        """Get generated content for a session"""
        query = select(GeneratedContent).where(GeneratedContent.session_id == session_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    # ==================== Prompt Template Operations ====================

    async def get_prompt_template(self, name: str) -> Optional[PromptTemplate]:
        """Get active prompt template by name"""
        query = select(PromptTemplate).where(
            and_(PromptTemplate.name == name, PromptTemplate.is_active == True)
        ).order_by(desc(PromptTemplate.version)).limit(1)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_all_templates(self) -> List[PromptTemplate]:
        """List all active prompt templates"""
        query = select(PromptTemplate).where(PromptTemplate.is_active == True).order_by(PromptTemplate.name)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_prompt_template(self, name: str, template: str, notes: str = "") -> PromptTemplate:
        """Create a new prompt template"""
        # Check if template exists and increment version
        query = select(func.max(PromptTemplate.version)).where(PromptTemplate.name == name)
        result = await self.db.execute(query)
        max_version = result.scalar() or 0
        
        prompt = PromptTemplate(
            name=name,
            template=template,
            version=max_version + 1,
            is_active=True,
            notes=notes
        )
        self.db.add(prompt)
        await self.db.flush()
        logger.info(f"Created prompt template: {name} v{prompt.version}")
        return prompt

    async def update_prompt_template(self, name: str, new_template: str, notes: str = "") -> PromptTemplate:
        """Create a new version of a prompt template (soft delete old version)"""
        # Mark old version as inactive
        query = select(PromptTemplate).where(
            and_(PromptTemplate.name == name, PromptTemplate.is_active == True)
        )
        result = await self.db.execute(query)
        old_template = result.scalar_one_or_none()
        
        if old_template:
            old_template.is_active = False
        
        # Create new version
        return await self.create_prompt_template(name, new_template, notes)

    # ==================== Prompt Usage Operations ====================

    async def save_prompt_usage(self, session_id: str, template_id: int, prompt_text: str) -> PromptUsage:
        """Record prompt usage before OpenAI call"""
        usage = PromptUsage(
            session_id=session_id,
            prompt_template_id=template_id,
            prompt_text_used=prompt_text
        )
        self.db.add(usage)
        await self.db.flush()
        return usage

    async def get_prompt_usage_for_session(self, session_id: str) -> List[PromptUsage]:
        """Get all prompt usages for a session"""
        query = select(PromptUsage).where(
            PromptUsage.session_id == session_id
        ).options(selectinload(PromptUsage.prompt_template))
        result = await self.db.execute(query)
        return result.scalars().all()

    # ==================== Token Usage Operations ====================

    async def save_token_usage(self, session_id: str, prompt_usage_id: int, template_id: int,
                              prompt_tokens: int, completion_tokens: int, total_tokens: int,
                              model: str, cost_usd: float) -> TokenUsage:
        """Record token usage and cost after OpenAI call"""
        usage = TokenUsage(
            session_id=session_id,
            prompt_usage_id=prompt_usage_id,
            prompt_template_id=template_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            model=model,
            cost_usd=cost_usd
        )
        self.db.add(usage)
        await self.db.flush()
        
        # Update daily summary
        today = datetime.utcnow().date().isoformat()
        await self._update_usage_summary(today, total_tokens, cost_usd)
        
        return usage

    async def get_token_usage_for_session(self, session_id: str) -> List[TokenUsage]:
        """Get all token usage records for a session"""
        query = select(TokenUsage).where(
            TokenUsage.session_id == session_id
        ).options(
            selectinload(TokenUsage.prompt_template),
            selectinload(TokenUsage.prompt_usage)
        ).order_by(TokenUsage.generated_at)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_usage_summary_for_session(self, session_id: str) -> Dict[str, Any]:
        """Get aggregated usage summary for a session"""
        query = select(TokenUsage).where(TokenUsage.session_id == session_id)
        result = await self.db.execute(query)
        usages = result.scalars().all()
        
        total_tokens = sum(u.total_tokens for u in usages)
        total_cost = sum(u.cost_usd for u in usages)
        
        # Breakdown by prompt
        breakdown = {}
        for usage in usages:
            template_name = usage.prompt_template.name if usage.prompt_template else "unknown"
            if template_name not in breakdown:
                breakdown[template_name] = {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                    "cost_usd": 0.0,
                    "count": 0
                }
            breakdown[template_name]["prompt_tokens"] += usage.prompt_tokens
            breakdown[template_name]["completion_tokens"] += usage.completion_tokens
            breakdown[template_name]["total_tokens"] += usage.total_tokens
            breakdown[template_name]["cost_usd"] += usage.cost_usd
            breakdown[template_name]["count"] += 1
        
        return {
            "session_id": session_id,
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 4),
            "request_count": len(usages),
            "breakdown_by_prompt": breakdown
        }

    # ==================== Usage Summary Operations ====================

    async def _update_usage_summary(self, date: str, tokens: int, cost: float) -> None:
        """Update daily usage summary"""
        query = select(UsageSummary).where(UsageSummary.date == date)
        result = await self.db.execute(query)
        summary = result.scalar_one_or_none()
        
        if summary:
            summary.total_tokens += tokens
            summary.total_cost_usd += cost
            summary.request_count += 1
            summary.updated_at = datetime.utcnow()
        else:
            summary = UsageSummary(
                date=date,
                total_tokens=tokens,
                total_cost_usd=cost,
                request_count=1
            )
            self.db.add(summary)
        
        await self.db.flush()

    async def get_usage_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get aggregate usage stats for the last N days"""
        start_date = (datetime.utcnow() - timedelta(days=days)).date().isoformat()
        
        query = select(UsageSummary).where(
            UsageSummary.date >= start_date
        ).order_by(desc(UsageSummary.date))
        result = await self.db.execute(query)
        summaries = result.scalars().all()
        
        total_tokens = sum(s.total_tokens for s in summaries)
        total_cost = sum(s.total_cost_usd for s in summaries)
        
        # Get top prompts by cost
        query_tokens = select(TokenUsage).where(
            TokenUsage.generated_at >= datetime.fromisoformat(start_date)
        )
        result_tokens = await self.db.execute(query_tokens)
        token_usages = result_tokens.scalars().all()
        
        prompt_costs = {}
        for usage in token_usages:
            template_name = usage.prompt_template.name if usage.prompt_template else "unknown"
            if template_name not in prompt_costs:
                prompt_costs[template_name] = 0.0
            prompt_costs[template_name] += usage.cost_usd
        
        top_prompts = sorted(
            [(k, v) for k, v in prompt_costs.items()],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            "period_days": days,
            "total_tokens_all_time": total_tokens,
            "total_cost_all_time": round(total_cost, 4),
            "daily_breakdown": [
                {
                    "date": s.date,
                    "tokens": s.total_tokens,
                    "cost": round(s.total_cost_usd, 4),
                    "requests": s.request_count
                }
                for s in summaries
            ],
            "top_prompts_by_cost": [
                {"prompt": name, "cost": round(cost, 4)}
                for name, cost in top_prompts
            ]
        }

    # ==================== Commit Operations ====================

    async def commit(self) -> None:
        """Commit all pending changes"""
        await self.db.commit()

    async def rollback(self) -> None:
        """Rollback all pending changes"""
        await self.db.rollback()
