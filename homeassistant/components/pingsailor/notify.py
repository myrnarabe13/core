"""PingSailor platform for notify component."""
from http import HTTPStatus
import json
import logging

import requests
import voluptuous as vol

from homeassistant.components.notify import PLATFORM_SCHEMA, BaseNotificationService
from homeassistant.const import (
    CONF_API_KEY,
    CONF_RECIPIENT,
    CONF_SENDER,
    CONF_USERNAME,
    CONTENT_TYPE_JSON,
)
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

BASE_API_URL = "https://pingsailor.com/api"
DEFAULT_SENDER = "hass"
TIMEOUT = 5

HEADERS = {"Content-Type": CONTENT_TYPE_JSON}


PLATFORM_SCHEMA = vol.Schema(
    vol.All(
        PLATFORM_SCHEMA.extend(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_API_KEY): cv.string,
                vol.Required(CONF_RECIPIENT, default=[]): vol.All(
                    cv.ensure_list, [cv.string]
                ),
                vol.Optional(CONF_SENDER, default=DEFAULT_SENDER): cv.string,
            }
        )
    )
)


def get_service(hass, config, discovery_info=None):
    """Get the PingSailor notification service."""
    if not _authenticate(config):
        _LOGGER.error("You are not authorized to access PingSailor")
        return None
    return PingSailorNotificationService(config)


class PingSailorNotificationService(BaseNotificationService):
    """Implementation of a notification service for the PingSailor service."""

    def __init__(self, config):
        """Initialize the service."""
        self.username = config[CONF_USERNAME]
        self.api_key = config[CONF_API_KEY]
        self.recipients = config[CONF_RECIPIENT]
        self.sender = config[CONF_SENDER]

    def send_message(self, message="", **kwargs):
        """Send a message to a user."""
        data = {"messages": []}
        for recipient in self.recipients:
            data["messages"].append(
                {
                    "from": self.sender,
                    "to": recipient,
                    "body": message,
                }
            )

        api_url = f"{BASE_API_URL}/sms/send"
        resp = requests.post(
            api_url,
            data=json.dumps(data),
            headers=HEADERS,
            auth=(self.username, self.api_key),
            timeout=TIMEOUT,
        )
        if resp.status_code == HTTPStatus.OK:
            return

        obj = json.loads(resp.text)
        response_msg = obj.get("response_msg")
        response_code = obj.get("response_code")
        _LOGGER.error(
            "Error %s : %s (Code %s)", resp.status_code, response_msg, response_code
        )


def _authenticate(config):
    """Authenticate with PingSailor."""
    api_url = f"{BASE_API_URL}/account"
    resp = requests.get(
        api_url,
        headers=HEADERS,
        auth=(config[CONF_USERNAME], config[CONF_API_KEY]),
        timeout=TIMEOUT,
    )
    return resp.status_code == HTTPStatus.OK