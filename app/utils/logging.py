import logging
from loguru import logger

# Configure loguru for FastAPI
logger.add("logs/knowledgehub.log", rotation="10 MB")

# Standard logging setup
logging.basicConfig(level=logging.INFO)

# Log user actions for audit
async def log_action(user_id: str, action: str, target_id: str) -> None:
    logger.info(f"User {user_id} performed {action} on {target_id}")
