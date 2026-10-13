import logging

import uvicorn

from classifier.api.settings import api_settings

if __name__ == "__main__":
    logging.basicConfig(level=api_settings.log_level.upper(), format="%(levelname)s %(name)s: %(message)s")
    uvicorn.run(
        "classifier.api.app:app",
        host=api_settings.host,
        port=api_settings.port,
        log_level=api_settings.log_level,
    )
