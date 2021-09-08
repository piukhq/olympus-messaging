from dataclasses import dataclass
from typing import Callable, Mapping, Optional, Type

"""
Maps message_type strings to message classes.
"""
_message_classes: dict[str, Type["Message"]] = {}


def build_message(properties: Mapping[str, str], body: Mapping[str, str]) -> "Message":
    message_type = properties["type"]
    message_class = _message_classes[message_type]
    property_fields = Message.properties_to_fields(properties)
    return message_class(**property_fields, **body)


def message_type(message_type: str) -> Callable:
    def wrapper(cls: Type) -> Type:
        cls.message_type = property(lambda self: message_type)
        _message_classes[message_type] = cls
        return cls

    return wrapper


@dataclass(frozen=True)
class Message:
    channel: str
    transaction_id: Optional[str]
    bink_user_id: Optional[str]
    request_id: str
    loyalty_plan: str
    account_id: Optional[str]

    def __post_init__(self) -> None:
        if not self.message_type:
            raise TypeError(f"{type(self).__name__} has no message_type")

    @staticmethod
    def properties_to_fields(properties: Mapping[str, str]) -> dict:
        return {
            "channel": properties["channel"],
            "transaction_id": properties.get("transaction-id"),
            "bink_user_id": properties.get("bink-user-id"),
            "request_id": properties["request-id"],
            "loyalty_plan": properties["loyalty-plan"],
            "account_id": properties.get("account-id"),
        }

    @property
    def message_type(self) -> str:
        raise NotImplementedError(f"{type(self).__name__} must implement message_type")

    @property
    def properties(self) -> dict:
        properties = {
            "type": self.message_type,
            "channel": self.channel,
            "request-id": self.request_id,
            "loyalty-plan": self.loyalty_plan,
        }

        if self.transaction_id:
            properties["transaction-id"] = self.transaction_id

        if self.bink_user_id:
            properties["bink-user-id"] = self.bink_user_id

        if self.account_id:
            properties["account-id"] = self.account_id

        return properties

    @property
    def body(self) -> dict:
        return self.serialize_body()

    def serialize_body(self) -> dict:
        raise NotImplementedError(
            f"{type(self).__name__} must implement serialize_body"
        )


@dataclass(frozen=True)
@message_type("loyalty_account.join.application")
class JoinApplication(Message):
    join_data: Mapping[str, str]

    def serialize_body(self) -> dict:
        return {"join_data": self.join_data}
