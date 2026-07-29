class UnknownToolError(Exception):
    pass


class ApiError(Exception):
    pass


class LoopError(Exception):
    pass


class UnsupportedModelError(Exception):
    pass


# Python-only addition (no Ruby counterpart): raised by Agent.run() when a
# cancel_event is set between iterations, so Repl/Tui can unwind a turn
# cleanly. Ruby achieves the same effect via Thread#raise(Interrupt) from
# outside the agent loop, which Python threads cannot safely replicate.
class TurnCancelled(Exception):
    pass
