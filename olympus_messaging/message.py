from dataclasses import dataclass
from typing import Callable, Mapping, Optional, Type

"""
Maps message_type strings to message classes.
"""
_message_classes: dict[str, Type["Message"]] = {}


def build_message(metadata: Mapping[str, str], body: Mapping[str, str]) -> "Message":
    message_type = metadata["type"]
    message_class = _message_classes[message_type]
    metadata_fields = Message.metadata_to_fields(metadata)
    return message_class(**metadata_fields, **body)


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
    def metadata_to_fields(metadata: Mapping[str, str]) -> dict:
        return {
            "channel": metadata["channel"],
            "transaction_id": metadata.get("transaction-id"),
            "bink_user_id": metadata.get("bink-user-id"),
            "request_id": metadata["request-id"],
            "loyalty_plan": metadata["loyalty-plan"],
            "account_id": metadata.get("account-id"),
        }

    @property
    def message_type(self) -> str:
        raise NotImplementedError(f"{type(self).__name__} must implement message_type")

    @property
    def metadata(self) -> dict:
        metadata = {
            "type": self.message_type,
            "channel": self.channel,
            "request-id": self.request_id,
            "loyalty-plan": self.loyalty_plan,
        }

        if self.transaction_id:
            metadata["transaction-id"] = self.transaction_id

        if self.bink_user_id:
            metadata["bink-user-id"] = self.bink_user_id

        if self.account_id:
            metadata["account-id"] = self.account_id

        return metadata

    @property
    def body(self) -> dict:
        return self.serialize_body()

    def serialize_body(self) -> dict:
        raise NotImplementedError(f"{type(self).__name__} must implement serialize_body")


@dataclass(frozen=True)
@message_type("loyalty_account.join.application")
class JoinApplication(Message):
    join_data: Mapping[str, str]

    def serialize_body(self) -> dict:
        return {"join_data": self.join_data}


@dataclass(frozen=True)
@message_type("loyalty_card.removed.bink")
class LoyaltyCardRemovedBink(Message):
    loyalty_id: str

    def serialize_body(self) -> dict:
        return {"loyalty_id": self.loyalty_id}
