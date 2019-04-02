import logging

from mx_crm.connector_controller import reconnecting, disconnect
from mx_crm.utils import start_scrapyd, kill_scrapyd, print_traceback

logger = logging.getLogger(__name__)


def scrapyd_work(log=None):
    log = log or logger

    def inner_scrapyd_work(fn):
        def wrapped(*args, **kwargs):
            reconnecting()
            scrapyd, scrapyd_process = start_scrapyd(log=log)
            try:
                result = fn(*args, **kwargs)
            except Exception as e:
                log.error(e)
                print_traceback()
                result = None
                kill_scrapyd(scrapyd, scrapyd_process, log=log)
                disconnect()
            kill_scrapyd(scrapyd, scrapyd_process)
            disconnect()
            return result
        return wrapped
    return inner_scrapyd_work


def log_completers(type, description='', additional_data=''):
        def inner(fn):
            def wrapped(self, *args, **kwargs):
                result = None
                status, error = ('success', '')

                self.log_start(type=type, description=description, additional_data=additional_data)

                try:
                    result = fn(self, *args, **kwargs)
                except Exception as e:
                    status, error = ('error', e.message)
                    logger.error(e)
                    print_traceback()
                self.log_end(status, error)
                return result
            return wrapped
        return inner
