from collections import defaultdict
from typing import Callable, Mapping, Type

from .message import Message

MessageHandler = Callable[[Message], None]
MessageHandlerMapping = Mapping[Type[Message], set[MessageHandler]]


class MessageDispatcher:
    def __init__(self) -> None:
        self.handlers: MessageHandlerMapping = defaultdict(set)

    def connect(self, message_class: Type[Message], receiver: MessageHandler) -> None:
        self.handlers[message_class].add(receiver)

    def disconnect(self, message_class: Type[Message], receiver: MessageHandler) -> None:
        self.handlers[message_class].remove(receiver)

    def dispatch(self, message: Message) -> None:
        for handler in self.handlers[type(message)]:
            handler(message)
