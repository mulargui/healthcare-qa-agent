"""Logging configuration — sets up format with filename and line number, plus agent callback."""

import logging

from langchain_core.callbacks import BaseCallbackHandler

from config import IS_PRODUCTION

LOG_FORMAT = "%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s"

_LOG_LEVEL = logging.INFO if IS_PRODUCTION else logging.DEBUG
logging.basicConfig(format=LOG_FORMAT, level=_LOG_LEVEL)
logging.getLogger().setLevel(_LOG_LEVEL)

_logger = logging.getLogger("agent_callback")


def get_logger(name):
    return logging.getLogger(name)


class AgentLoggingCallback(BaseCallbackHandler):
    def on_tool_start(self, tool, input_str, **kwargs):
        _logger.info("Tool call: %s input: %s", tool.get("name"), input_str)

    def on_tool_end(self, output, **kwargs):
        _logger.info("Tool result: %.200s", output)
