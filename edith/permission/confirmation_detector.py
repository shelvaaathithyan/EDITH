from typing import Optional

class ConfirmationDetector:
    """
    Lightweight local text detector for hybrid confirmations.
    Prevents round-trips to the AI Planner for basic 'Yes'/'No' answers.
    """
    def __init__(self):
        self.affirmative = {"yes", "yeah", "yep", "sure", "go ahead", "continue", "proceed", "do it", "confirm", "ok", "okay"}
        self.negative = {"no", "nope", "cancel", "stop", "abort", "never mind", "forget it", "don't"}

    def detect(self, text: str) -> Optional[bool]:
        """
        Returns True if explicitly confirmed, False if explicitly cancelled.
        Returns None if it's a complex response requiring Planner processing.
        """
        # Clean up punctuation and convert to lowercase
        clean_text = "".join(c for c in text.lower() if c.isalnum() or c.isspace()).strip()
        
        # If the phrase matches exactly, or is very close
        if clean_text in self.affirmative:
            return True
        if clean_text in self.negative:
            return False
            
        # Optional: check if it STARTS with "yes" but has more words.
        # "Yes, but only delete the screenshots folder." -> starts with yes, but complex.
        # Since we want complex responses to hit the planner, we ONLY match exact or highly similar phrases.
        return None

confirmation_detector = ConfirmationDetector()
