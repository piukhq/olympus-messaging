from pprint import pprint
from typing import Mapping

from olympus_messaging import JoinApplication, Message, MessageDispatcher, build_message

Queue = list[tuple[Mapping[str, str], Mapping[str, str]]]


def publisher(queue: Queue) -> None:
    message = JoinApplication(
        channel="barclays.tba",
        transaction_id="example-transaction",
        bink_user_id="12345",
        request_id="example-request",
        loyalty_plan="iceland-bonus-card",
        account_id="example@testbink.com",
        join_data={
            "name": "mr example",
            "postcode": "AB12 3CD",
        },
    )

    queue.append((message.properties, message.body))

    print(f"Publisher sent: {type(message).__name__}")
    pprint(vars(message))
    print()


def on_message(message: Message) -> None:
    print(f"Consumer received: {type(message).__name__}")
    pprint(vars(message))
    print()


def consumer(queue: Queue) -> None:
    # connect message types to callbacks
    dispatcher = MessageDispatcher()
    dispatcher.connect(JoinApplication, on_message)

    # process messages off the queue
    while queue:
        properties, body = queue.pop(0)
        message = build_message(properties, body)
        dispatcher.dispatch(message)


def main():
    queue: Queue = []
    publisher(queue)
    consumer(queue)


if __name__ == "__main__":
    main()
