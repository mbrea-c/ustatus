import asyncio
from typing import Callable

from python_reactive_ui import Component
from python_reactive_ui.lib.hooks import use_effect


def use_timer(
    component: Component, timer_secs: float, callback: Callable, repeat: bool = True
):
    def set_timer():
        # get loop as a kwarg or take the default one
        loop = asyncio.get_event_loop()
        # record the loop's time when call_periodic was called
        start = loop.time()

        def run(handle):
            # XXX: we could record before = loop.time() and warn when callback(*args) took longer than interval
            # call callback now (possibly blocks run)
            callback()
            # reschedule run at the soonest time n * interval from start
            # re-assign delegate to the new handle
            if repeat:
                handle.delegate = loop.call_later(
                    timer_secs - ((loop.time() - start) % timer_secs), run, handle
                )

        class PeriodicHandle:  # not extending Handle, needs a lot of arguments that make no sense here
            def __init__(self):
                self.delegate = None

            def cancel(self):
                assert isinstance(
                    self.delegate, asyncio.Handle
                ), "no delegate handle to cancel"
                self.delegate.cancel()

        periodic = (
            PeriodicHandle()
        )  # can't pass result of loop.call_at here, it needs periodic as an arg to run
        # set the delegate to be the Handle for call_at, causes periodic.cancel() to cancel the call to run
        periodic.delegate = loop.call_at(start + timer_secs, run, periodic)
        # return the 'wrapperk'
        return periodic

    use_effect(component, set_timer, [])
