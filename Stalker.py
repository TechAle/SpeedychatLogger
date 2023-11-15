import json
import time
from random import randint
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
import os
import logging


class Stalker:
    def __init__(self):
        self.tags = []
        self.name = ""
        self.startingLink = "https://ragazzi.speedychat.it"
        self.driver = None
        self.wait = None
        self.loggers = {}
        self._setupVariabiles()
        self.prepareLoggers()

    def prepareLoggers(self):
        def setup_logger(name, log_file, level=logging.INFO):
            """To setup as many loggers as you want"""

            handler = logging.FileHandler(log_file)
            handler.setFormatter(formatter)

            logger = logging.getLogger(name)
            logger.setLevel(level)
            logger.addHandler(handler)

            return logger

        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        # Create directory logs if not exists
        if not os.path.exists("logs"):
            os.makedirs("logs")
        # Create 3 logs files with the name of the tags
        for tag in self.tags:
            # Create a logger
            self.loggers[tag] = setup_logger(tag, 'logs/' + tag + '.log')

    def _setupVariabiles(self):
        # Read file configration.json and put in tags and name the values
        with open('configuration.json') as json_file:
            data = json.load(json_file)
            self.tags = data["tags"]
            self.name = data["names"][randint(0, len(data["names"]) - 1)]
        opts = webdriver.ChromeOptions()
        opts.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        self.driver = webdriver.Chrome(options=opts)
        self.wait = WebDriverWait(self.driver, 300)

    def setupBot(self):
        self.getToCaptcha()
        for tag in self.tags:
            self.subscribeToChannel(tag)

    def getToCaptcha(self):
        self.driver.get(self.startingLink)
        # Complete beginning form
        self.driver.find_element(By.ID, "nickname").send_keys(self.name)
        self.driver.find_element(By.ID, "invia").click()
        # Enter the iframe where the application all is
        self.driver.switch_to.frame(self.driver.find_element(By.XPATH, "/html/body/div[3]/div/div[2]/iframe"))

    def subscribeToChannel(self, tag):
        # Click the button for the channel list
        self.waitAndClickXPath("/html/body/div[1]/div[1]/div[4]/div/div/div[1]/a")
        # Click the button for displaying the channel list
        self.waitAndClickXPath("/html/body/div[1]/div[2]/div[2]/div[3]/div/div/div/div[1]/a[2]")
        tag = '#' + tag
        channels = []
        while len(channels) == 0: #kiwi-statebrowser-network-name
            # Click the button for loading the channel list
            self.waitAndClickClass("kiwi-channellist-refresh")
            time.sleep(10)
            channels = self.driver.find_elements(By.CLASS_NAME, "kiwi-channellist-grid")
        # Check for every channel if there is a tag with what we have to subscribe
        # Note: everytime we subscribe to a channel, the list of channels is reloaded, so we need to redo everything
        for channel in channels:
            if tag in channel.text:
                toClick = channel.find_elements(By.CLASS_NAME, "kiwi-channellist-join")
                if len(toClick) > 0:
                    toClick[0].click()
                    break

    def waitAndClickClass(self, className):
        self.wait.until(lambda driver: driver.find_element(By.CLASS_NAME, className))
        self.driver.find_element(By.CLASS_NAME, className).click()

    def waitAndClickXPath(self, xpath):
        self.wait.until(lambda driver: driver.find_element(By.XPATH, xpath))
        self.driver.find_element(By.XPATH, xpath).click()

    def startListening(self):
        while True:
            for entry in self.driver.get_log('performance'):
                # Read entry as JSON
                method = json.loads(entry['message'])['message']["method"]
                # Trying to fix a segmentation error
                method = method.split(".")
                if len(method) == 2:
                    a = method[0] == "Network"
                    b = method[1] == "webSocketFrameReceived"
                    if a and b:
                        message = json.loads(entry['message'])["message"]["params"]["response"]["payloadData"]
                        if message[0] == 'a':
                            splitted = message[1:].split(" ")
                            if len(splitted) > 5:
                                if splitted[1].__contains__("time="):
                                    autore = splitted[2][1:].split("!")[0]
                                    orario = splitted[1].split("time=")[1].split(";")[0]
                                    tipologia = splitted[3]
                                    tag = splitted[4]
                                    messaggio = ' '.join(splitted[5:])[:-2]
                                    if self.loggers.__contains__(tag[1:]) and tipologia == "PRIVMSG":
                                        self.loggers[tag[1:]].info("%s %s" % (autore, messaggio))
                                    # Else it's a private msg lol
                # if "Network.webSocketFrameReceived".__eq__(method):
                #    a = 0
            time.sleep(1)