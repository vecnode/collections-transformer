import argparse

import uvicorn

from app.main import create_app
from config import configure_logging, settings

configure_logging()


parser = argparse.ArgumentParser()
parser.add_argument("-m", "--model", action="store", default="dual")
parser.add_argument("-p", "--port", action="store", default=settings.api_port)
parser.add_argument("-r", "--reload", action="store", default=str(settings.api_reload))
args, unknown = parser.parse_known_args()


if __name__ == '__main__':
    port = int(args.port)
    reload = str(args.reload).lower() == "true"

    application = create_app(args.model)
    uvicorn.run(application, host=settings.api_host, port=port, reload=reload)


