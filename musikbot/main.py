import os

from musikbot.classes.bot import MusikBot
import logging
from musikbot.classes.logger import CustomFormatter
import datetime

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
log_dir = os.path.join(os.path.normpath(os.getcwd() + os.sep + os.pardir), "musikbot" + os.sep + 'logs')
log_fname = os.path.join(log_dir, f'discord_{datetime.datetime.now().strftime("%M-%H__%d-%m-%Y")}.log')
open(log_fname, "w").close()
handler = logging.FileHandler(filename=log_fname, encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
handler.setFormatter(CustomFormatter())
logger.addHandler(handler)

musikBot = MusikBot(logger=logger, prefix=".!")
musikBot.run()
