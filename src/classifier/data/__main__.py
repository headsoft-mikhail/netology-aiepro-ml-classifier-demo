import logging

from classifier.data.download import download_dataset
from classifier.data.settings import DataSettings

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    download_dataset(DataSettings())
