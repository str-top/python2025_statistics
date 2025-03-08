import logging

# Configure logging
logging.basicConfig(
    # level=logging.CRITICAL + 1,
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("python2025_statistics.log"),  # Log to a file
        logging.StreamHandler()          # Log to console
    ]
)

def get_logger(name):
    return logging.getLogger(name)