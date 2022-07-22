from typing import List, Callable

import logging

logger = logging.getLogger(__name__)

class Event:
    """ Simple event class which allows handlers to be registered and called when the event gets fired or called. """

    def __init__(self):
        self._handlers: List[Callable] = list()

    def __iadd__(self, handler):
        self._handlers.append(handler)
        return self

    def __isub__(self, handler):
        self._handlers.remove(handler)
        return self

    def __call__(self, *args, **kwargs):
        for handler in self._handlers:
            try:
                handler(*args, **kwargs)
            except Exception as ex:
                logger.exception(ex)
    
    def add(self, handler: Callable):
        self += handler
    
    def remove(self, handler: Callable):
        self -= handler

    def fire(self, *args, **kwargs):
        self(*args, **kwargs)