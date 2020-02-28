import logging
import os
from concurrent.futures._base import Executor
from concurrent.futures.thread import ThreadPoolExecutor

from cli.internal.apis.mason import MasonApi
from cli.internal.utils.analytics import MasonAnalytics
from cli.internal.utils.constants import AUTH
from cli.internal.utils.constants import ENDPOINTS
from cli.internal.utils.interactive import Interactivity
from cli.internal.utils.remote import RequestHandler
from cli.internal.utils.store import Store


class Config(object):
    """
    Global config object, utilized to set verbosity of logging events
    and other flags.
    """

    def __init__(
        self,
        logger: logging.Logger = None,
        auth_store: Store = AUTH,
        endpoints_store: Store = ENDPOINTS,
        api: MasonApi = None,
        analytics: MasonAnalytics = None,
        interactivity: Interactivity = None,
        executor: Executor = None
    ):
        logger = logger or logging.getLogger(__name__)
        api = api or MasonApi(RequestHandler(self), auth_store, endpoints_store)
        if not analytics:
            analytics = MasonAnalytics(self)
            if os.environ.get('_MASON_CLI_TEST_MODE'):
                endpoints_store['analytics_url'] = None
        interactivity = interactivity or Interactivity()

        self.logger = logger
        self.auth_store = auth_store
        self.endpoints_store = endpoints_store
        self.api = api
        self.analytics = analytics
        self.interactivity = interactivity
        self.executor = executor or ThreadPoolExecutor()
