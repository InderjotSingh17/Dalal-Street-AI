# ============================================================
# MODULE 2 — LEARNING ENGINE
# Tracks what the user has learned, selects next concept,
# updates learning profile after each mentor card is shown.
# ============================================================

from django.utils import timezone
from accounts.models import LearningProfile
from market.mentor.constants import (
    CONCEPT_LIBRARY,
    CONCEPT_TEACHING_ORDER,
    KNOWLEDGE_BEGINNER,
    KNOWLEDGE_INTERMEDIATE,
    KNOWLEDGE_ADVANCED,
    LESSONS_TO_INTERMEDIATE,
    LESSONS_TO_ADVANCED,
    PILLAR_EDUCATIONAL,
)


class LearningContext:
    """
    Output of the Learning Engine.
    Passed to Prompt Builder.
    """
    def __init__(self):
        self.knowledge_level = KNOWLEDGE_BEGINNER
        self.concept_key = None
        self.concept_name = None
        self.concept_explanation = None
        self.concepts_taught_count = 0
        self.is_review = False  # True if repeating a concept for reinforcement

    def to_dict(self):
        return {
            'knowledge_level': self.knowledge_level,
            'concept_key': self.concept_key,
            'concept_name': self.concept_name,
            'concept_explanation': self.concept_explanation,
            'concepts_taught_count': self.concepts_taught_count,
            'is_review': self.is_review,
        }


class LearningEngine:

    def __init__(self, user):
        self.user = user
        self.profile = LearningProfile.get_or_create_for_user(user)

    def get_learning_context(self, event_type=None, stock=None):
        """
        Main entry point.
        Returns a LearningContext with the next concept to teach.
        """
        context = LearningContext()
        context.knowledge_level = self.profile.knowledge_level
        context.concepts_taught_count = self.profile.total_lessons_received

        # Select next concept
        concept_key = self._select_next_concept(stock=stock)

        if concept_key and concept_key in CONCEPT_LIBRARY:
            concept = CONCEPT_LIBRARY[concept_key]
            level = self.profile.knowledge_level

            # Get explanation for appropriate level
            explanation = self._get_explanation(concept, level)

            context.concept_key = concept_key
            context.concept_name = concept['name']
            context.concept_explanation = explanation
        else:
            # All concepts taught — pick a review concept
            context = self._get_review_context(context)

        return context

    def _select_next_concept(self, stock=None):
        """
        Selects the next concept to teach.
        Priority:
        1. If stock has high/low PE — teach PE if not taught
        2. If stock has high D/E — teach D/E if not taught
        3. Otherwise follow CONCEPT_TEACHING_ORDER
        """
        taught = set(self.profile.concepts_taught)
        level = self.profile.knowledge_level

        # Context-aware selection based on stock data
        if stock:
            # High PE stock — teach PE ratio first if not taught
            if stock.pe_ratio and float(stock.pe_ratio) > 30 and 'pe_ratio' not in taught:
                return 'pe_ratio'
            # High debt stock — teach D/E if not taught
            if stock.debt_to_equity and float(stock.debt_to_equity) > 1 and 'debt_to_equity' not in taught:
                return 'debt_to_equity'
            # New user buying first stock — teach market cap
            if len(taught) == 0:
                return 'market_cap'

        # Follow teaching order, skip already taught
        for concept_key in CONCEPT_TEACHING_ORDER:
            if concept_key not in taught:
                concept = CONCEPT_LIBRARY.get(concept_key)
                if concept and level in concept.get('levels', []):
                    return concept_key

        return None  # All relevant concepts taught

    def _get_explanation(self, concept, level):
        """
        Returns the right explanation for the user's knowledge level.
        Falls back to beginner if level-specific not available.
        """
        if level == KNOWLEDGE_ADVANCED and 'advanced' in concept:
            return concept['advanced']
        elif level == KNOWLEDGE_INTERMEDIATE and 'intermediate' in concept:
            return concept['intermediate']
        elif 'beginner' in concept:
            return concept['beginner']
        # Fallback — use whatever is available
        for key in ['beginner', 'intermediate', 'advanced']:
            if key in concept:
                return concept[key]
        return ""

    def _get_review_context(self, context):
        """
        When all concepts are taught, pick one for review/reinforcement.
        Picks the concept least recently reviewed.
        """
        taught = self.profile.concepts_taught
        if not taught:
            return context

        # Pick the first taught concept for review (oldest)
        review_key = taught[0] if taught else None
        if review_key and review_key in CONCEPT_LIBRARY:
            concept = CONCEPT_LIBRARY[review_key]
            level = self.profile.knowledge_level
            context.concept_key = review_key
            context.concept_name = concept['name']
            context.concept_explanation = self._get_explanation(concept, level)
            context.is_review = True

        return context

    def mark_concept_taught(self, concept_key):
        """
        Called after a mentor card is shown to the user.
        Updates the learning profile.
        """
        if not concept_key:
            return

        taught = list(self.profile.concepts_taught)

        # Add concept if not already taught
        if concept_key not in taught:
            taught.append(concept_key)
            self.profile.concepts_taught = taught

        # Increment lesson count
        self.profile.total_lessons_received += 1
        self.profile.current_topic = concept_key
        self.profile.last_lesson_date = timezone.now().date()

        # Set next topic
        next_key = self._get_next_after(concept_key)
        self.profile.next_topic = next_key or ''

        # Check if knowledge level should be upgraded
        self._check_level_upgrade()

        self.profile.save()

    def _get_next_after(self, current_key):
        """Returns the concept key that comes after current in teaching order."""
        taught = set(self.profile.concepts_taught)
        found_current = False
        for key in CONCEPT_TEACHING_ORDER:
            if found_current and key not in taught:
                return key
            if key == current_key:
                found_current = True
        return None

    def _check_level_upgrade(self):
        """Upgrades knowledge level based on lessons received."""
        lessons = self.profile.total_lessons_received
        current = self.profile.knowledge_level

        if current == KNOWLEDGE_BEGINNER and lessons >= LESSONS_TO_INTERMEDIATE:
            self.profile.knowledge_level = KNOWLEDGE_INTERMEDIATE

        elif current == KNOWLEDGE_INTERMEDIATE and lessons >= LESSONS_TO_ADVANCED:
            self.profile.knowledge_level = KNOWLEDGE_ADVANCED

    def get_knowledge_summary(self):
        """
        Returns a summary for the Prompt Builder to include in prompts.
        Tells the LLM what the user already knows.
        """
        taught = self.profile.concepts_taught
        level = self.profile.knowledge_level
        lessons = self.profile.total_lessons_received

        if not taught:
            already_knows = "This is a complete beginner. They have not been taught any investing concepts yet."
        else:
            concept_names = [
                CONCEPT_LIBRARY[k]['name']
                for k in taught
                if k in CONCEPT_LIBRARY
            ]
            already_knows = f"Already taught: {', '.join(concept_names)}. Do not re-explain these unless directly relevant."

        return {
            'level': level,
            'lessons_received': lessons,
            'already_knows': already_knows,
            'next_topic': self.profile.next_topic,
        }