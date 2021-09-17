import dataclasses
from unittest.mock import MagicMock, call

import pytest

from olympus_messaging import JoinApplication, Message, MessageDispatcher, build_message
from olympus_messaging.message import message_type


@pytest.fixture
def join_message() -> JoinApplication:
    return JoinApplication(
        channel="barclays.tba",
        request_id="test-request-123",
        loyalty_plan="iceland-bonus-card",
        transaction_id=None,
        bink_user_id=None,
        account_id=None,
        join_data={
            "card_number": "test-card-number-123",
            "barcode": "test-barcode-123",
        },
    )


def test_join_dispatch(join_message: JoinApplication) -> None:
    mock_receivers = [MagicMock(), MagicMock(), MagicMock()]
    dispatcher = MessageDispatcher()

    for receiver in mock_receivers:
        dispatcher.connect(JoinApplication, receiver)

    dispatcher.dispatch(join_message)

    for receiver in mock_receivers:
        assert receiver.call_count == 1
        assert receiver.call_args == call(join_message)

    dispatcher.disconnect(JoinApplication, mock_receivers[1])

    dispatcher.dispatch(join_message)

    assert mock_receivers[0].call_count == 2
    assert mock_receivers[1].call_count == 1
    assert mock_receivers[2].call_count == 2


def test_serialization_with_standard_metadata(join_message: JoinApplication) -> None:
    expected_metadata = {
        "type": join_message.message_type,
        "channel": join_message.channel,
        "request-id": join_message.request_id,
        "loyalty-plan": join_message.loyalty_plan,
    }
    expected_body = {"join_data": join_message.join_data}

    assert join_message.metadata == expected_metadata
    assert join_message.body == expected_body


def test_serialization_with_optional_metadata(join_message: JoinApplication) -> None:
    join_message = dataclasses.replace(
        join_message,
        transaction_id="test-transaction-id-123",
        bink_user_id="test-bink-user-id-123",
        account_id="test-account-id-123",
    )
    expected_metadata = {
        "type": join_message.message_type,
        "channel": join_message.channel,
        "request-id": join_message.request_id,
        "loyalty-plan": join_message.loyalty_plan,
        "transaction-id": join_message.transaction_id,
        "bink-user-id": join_message.bink_user_id,
        "account-id": join_message.account_id,
    }
    expected_body = {"join_data": join_message.join_data}

    assert join_message.metadata == expected_metadata
    assert join_message.body == expected_body


def test_message_with_no_type_override() -> None:
    class TestMessage(Message):
        pass

    with pytest.raises(NotImplementedError) as exc:
        TestMessage(
            channel="barclays.tba",
            request_id="test-request-123",
            loyalty_plan="iceland-bonus-card",
            transaction_id=None,
            bink_user_id=None,
            account_id=None,
        )
    assert "TestMessage must implement message_type" in str(exc.value)


def test_message_with_blank_type() -> None:
    @message_type("")
    class TestMessage(Message):
        pass

    with pytest.raises(TypeError) as exc:
        TestMessage(
            channel="barclays.tba",
            request_id="test-request-123",
            loyalty_plan="iceland-bonus-card",
            transaction_id=None,
            bink_user_id=None,
            account_id=None,
        )
    assert "TestMessage has no message_type" in str(exc.value)


def test_message_with_no_serialize_body() -> None:
    @message_type("test-message")
    class TestMessage(Message):
        pass

    message = TestMessage(
        channel="barclays.tba",
        request_id="test-request-123",
        loyalty_plan="iceland-bonus-card",
        transaction_id=None,
        bink_user_id=None,
        account_id=None,
    )

    with pytest.raises(NotImplementedError) as exc:
        message.body

    assert "TestMessage must implement serialize_body" in str(exc.value)


def test_build_message(join_message: JoinApplication) -> None:
    metadata = join_message.metadata
    body = join_message.body

    message = build_message(metadata, body)

    assert message == join_message
