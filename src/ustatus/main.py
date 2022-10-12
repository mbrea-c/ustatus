import asyncio, gbulb, logging, logging.handlers
from multiprocessing import Process
from python_dbus_system_api import start_server

from ustatus.ustatus import Ustatus

from ustatus.utils.notifications import notify_error


def main():
    setup_logging()
    # Ensure API is running (if already running this will just queue to get the
    # bus name)
    api_process = Process(target=start_server)
    api_process.start()
    gbulb.install(gtk=True)  # only necessary if you're using GtkApplication
    application = Ustatus()
    loop = asyncio.get_event_loop()
    try:
        loop.run_forever(application=application)
    except Exception as e:
        notify_error(summary="Uncaught error", body=f"e")


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        style="{",
        format="[{levelname}({name}):{filename}:{funcName}] {message}",
    )
    root_logger = logging.getLogger()
    sys_handler = logging.handlers.SysLogHandler(address="/dev/log")
    root_logger.addHandler(sys_handler)


if __name__ == "__main__":
    main()
