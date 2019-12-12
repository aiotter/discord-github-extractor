import os
from dotenv import load_dotenv
from . import bot
from . import history

import logging
logging.basicConfig(level=logging.INFO)
# history.logger.setLevel(logging.DEBUG)

load_dotenv()
token = os.getenv('TOKEN')

bot.client.run(token)
