import logging
import asyncio
from bot import FcuCourseMaster, TargetCourse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s][%(asctime)s]%(message)s",
    datefmt="%Y/%m/%d %H:%M:%S",
    handlers=[logging.StreamHandler()],
)

# Create bot instance
bot = FcuCourseMaster(
    username="D1234567",
    password="password",
    target_courses=[
        TargetCourse("1234", 2, True),
    ],
)

# Run the bot
asyncio.get_event_loop().run_until_complete(bot.start())