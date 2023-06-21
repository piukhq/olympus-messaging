# olympus-messaging

### Defines a standalone messaging protocol for use between Olympus projects.

   * It is message transport agnostic so does not add unnecessary dependencies 
   * See `example.py` for a usage example where a simple data structure acts as a queue. 
   * Current implementations use RabbitMQ and define messages from Hermes to Midas using RabbitMQ 
   * The message structure defines metadata which can be used for all messages and is passed in the message header
   * The body of the message contains business data which can be empty or bespoke per message 
   * For more information about the join message and some proposed future messages see: https://hellobink.atlassian.net/wiki/spaces/ARCH/pages/2408513601/Join+Application+Message+to+Midas

### To use Olympus Messaging:
1. Added to your project using pip, pipenv or poetry.
2. On the sending side refer to the message class eg this example from Hermes:
```python

from olympus_messaging import Message, LoyaltyCardRemovedBink
from message_broker import SendingService

message_sender = SendingService(dsn=RABBIT_DSN)

# This is example from Hermes uses this low level function based on SendingService 
def to_midas(message: Message) -> None:
    message_sender.send(message.body, message.metadata, MIDAS_QUEUE_NAME)

# This function is called when the last linked Loyalty card is deleted
def send_midas_last_loyalty_card_removed(scheme_account_entry: SchemeAccountEntry):

    message = LoyaltyCardRemovedBink(
        channel=scheme_account_entry.user.bundle_id,
        transaction_id=str(uuid.uuid1()),
        bink_user_id=str(scheme_account_entry.user.id),
        request_id=str(scheme_account_entry.scheme_account.id),
        account_id=get_main_answer(scheme_account_entry.scheme_account),
        loyalty_plan=scheme_account_entry.scheme_account.scheme.slug,
        message_data={}  # Empty body, but we may need to send join_data credentials
        # - the above data is in header of message!
    )
    to_midas(message) 


```
        

3. On receiving side:
    The example shows how MessageDispatcher() works.  To illustrate how this may be used with a transport
    layer see this example from Midas using kombu:
```python
import kombu
from kombu.mixins import ConsumerMixin
from olympus_messaging import LoyaltyCardRemovedBink, Message, MessageDispatcher, build_message
import settings
from app.scheme_account import JourneyTypes, SchemeAccountStatus
from app.journeys.common import get_agent_class

class TaskConsumer(ConsumerMixin):
    loyalty_request_queue = kombu.Queue(settings.LOYALTY_REQUEST_QUEUE)

    def __init__(self, connection: kombu.Connection) -> None:
        self.connection = connection
        self.dispatcher = MessageDispatcher()
        
        # you will need a similar entry for each per message linked to an on message receive method:
        self.dispatcher.connect(LoyaltyCardRemovedBink, self.on_loyalty_card_removed_bink)

    def on_message(self, body: dict, message: kombu.Message) -> None:  # pragma: no cover
        try:
            self.dispatcher.dispatch(build_message(message.headers, body))
        finally:
            message.ack()

    

    @staticmethod
    def on_loyalty_card_removed_bink(message: Message) -> None:
        message = cast(LoyaltyCardRemovedBink, message)

        message_info = {
            "user_set": message.bink_user_id,
            "bink_user_id": message.bink_user_id,
            "scheme_account_id": int(message.request_id),
            "channel": message.channel,
            "account_id": message.account_id,  # merchant's main answer from hermes eg card number
            "scheme_identifier": message.loyalty_plan,
            "message_uid": message.transaction_id
        }

        try:
            agent_class = get_agent_class(message_info["scheme_identifier"])
            agent_class.loyalty_card_removed_bink(message_info)
        except:
            pass


```
### To add a new message to Olympus Messaging:

1. Define the message dataclass in olympus_messaging.message.py In this example only meta data is required eg.
```python
@dataclass(frozen=True)
@message_type("loyalty_card.removed.bink")
class LoyaltyCardRemovedBink(Message):
    message_data: Mapping[str, str]

    def serialize_body(self) -> dict:
        return {"message_data": self.message_data}

```
2. Add the message dataclass name to the imports in __init.py
3. Add a test to the test_messaging - only a simple entry may be required eg
```python
def test_loyalty_card_removed_bink_dispatch(loyalty_card_removed_bink_message: LoyaltyCardRemovedBink) -> None:
    _message_dispatch_test(loyalty_card_removed_bink_message, LoyaltyCardRemovedBink)
````
4. Run pytest on tests directory. 
    * Although this is a library when used it can still be set up with```poetry install --sync``` 
    * Then Tests can be run normally with pytest
    * There is of course no code module to run
    * Please ensure poetry lock and pyproject.toml are consistent as it may go undetected in use but will affect installing for testing
   

