class VoiceRewriterError(Exception):
    """Base exception for Voice-Rewriter."""
    pass

class OptimisticLockError(VoiceRewriterError):
    """Raised when queue_revision does not match expected revision during OCC claim/update."""
    pass

class LeaseActiveError(VoiceRewriterError):
    """Raised when an operation is attempted on an active lease held by another worker."""
    pass

class InvalidQueueEnvelopeError(VoiceRewriterError):
    """Raised when a queue envelope violates the JSON schema."""
    pass

class SecurityViolationError(VoiceRewriterError):
    """Raised when an operation violates least privilege or access boundaries."""
    pass

class IllegalStateTransitionError(VoiceRewriterError):
    """Raised when an illegal state transition is attempted."""
    pass
