"""Domain-session state machine.

Owns all state/rules for the in-domain challenge flow, driven only by
observable signals (labels, timer digits, reward prompt) - never by pixel
guesses. Isolated here so domain handling never bleeds into other detection
paths.
"""
import re
import time


class DomainHandler:
    """Owns ALL domain-session state and rules.

    Lifecycle (driven only by observable signals - labels, timer digits,
    reward prompt - never by pixel guesses):
      1. Domain banner label   -> activate
      2. Challenge timer digits (top-center region, ~3s cadence) -> keep-alive
      3. "Skip Reward Cutscene" prompt (after the timer disappeared) ->
         reset the grace countdown (still mid-domain, clearing rewards)
      4. Timer gone > GRACE    -> exit to overworld (exploring fallback)
      5. Timer digits reappear -> re-activate (challenge retry)

    All state is private except `active`; callers go through the feed
    methods so domain state never bleeds into other detection paths.
    """

    GRACE_AFTER_TIMER_GONE = 20.0   # covers reward screens + exit loading
    REWARD_RESET_MIN_GONE = 5.0     # prompt only counts if timer gone this long
    TIMER_PATTERN = re.compile(r"\d{1,2}:\d{2}")

    def __init__(self, log_fn):
        self._log = log_fn
        self.active = False
        self.last_domain = None       # resolved domain data for re-entry
        self._timer_seen = False      # timer spotted at least once this session
        self._timer_last_seen = 0.0
        self._timer_gone_since = None

    def activate(self, found):
        """Enter (or re-enter) a domain session."""
        if found is not None:
            self.last_domain = found
        if not self.active:
            self.active = True
            self._timer_seen = False
            self._timer_gone_since = None
            self._timer_last_seen = time.time()
            self._log(f"Domain session started: "
                      f"{getattr(found, 'domain_name', None)}")

    def feed_timer(self, seen: bool):
        """Call every tick with whether timer/label text is currently visible."""
        now = time.time()
        if seen:
            self._timer_seen = True
            self._timer_last_seen = now
            self._timer_gone_since = None
        elif self.active and self._timer_seen and self._timer_gone_since is None:
            self._timer_gone_since = now

    def feed_reward_cutscene(self, seen: bool):
        """'Skip Reward Cutscene' visible -> still mid-domain.

        Only counts after the timer was seen and has been gone for a few
        seconds (i.e., the post-clear reward flow), never in the overworld.
        """
        if (
            self.active
            and seen
            and self._timer_seen
            and self._timer_gone_since is not None
            and time.time() - self._timer_gone_since >= self.REWARD_RESET_MIN_GONE
        ):
            self._timer_last_seen = time.time()
            self._timer_gone_since = None

    def tick(self):
        """Advance the session. Returns True if the domain just expired."""
        if not self.active:
            return False
        if (
            self._timer_seen
            and self._timer_gone_since is not None
            and time.time() - self._timer_last_seen >= self.GRACE_AFTER_TIMER_GONE
        ):
            self.deactivate()
            return True
        return False

    def deactivate(self):
        self.active = False
        self._timer_seen = False
        self._timer_gone_since = None

    def matches_timer(self, text: str) -> bool:
        return bool(text and self.TIMER_PATTERN.search(text))

    def suppresses_boss(self) -> bool:
        """While a domain session is live, timer digits must not be allowed
        to leak into world-boss detection."""
        return self.active