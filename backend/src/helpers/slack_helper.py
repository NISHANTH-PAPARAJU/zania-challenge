from dotenv import load_dotenv
import logging
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

load_dotenv()
client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
logger = logging.getLogger(__name__)
channel_id = os.getenv("SLACK_CHANNEL_ID")

def post_to_slack(message: str, user_id: str, request_id: str) -> None:
    """
    Useful for posting a message onto the slack channel.
    Args:
        message (str): The message that needs to be posted into the slack channel.  
        user_id (str): The user id you requested this, which can be optional.
        request_id (str): The unique identifier uuid for the request.
    """
    client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))    
    channel_id = os.getenv("SLACK_CHANNEL_ID")
    try:
        result = client.chat_postMessage(
            channel=channel_id, 
            text=f"""The following is the response for the req_id: {request_id} by user <@{user_id}>.
            {message}
            """
        )
        logger.info("Message Posted.", extra={"req_id": {request_id}, "user_id": {user_id}})

    except SlackApiError as e:
        logger.error(f"Error posting message: {e}", extra={"req_id": {request_id}, "user_id": {user_id}})

