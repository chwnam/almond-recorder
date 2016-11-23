"""
This file is written for the purpose of investigation.

MBC On-air TV provides not bad quality for free, so I thought this could be a source of recording, until
  I have noticed that streaming url is hard to get.

You may successfully login by using any connectors, and fetch XML responses from the URL
 "http://vodmall.imbc.com/util/player/onairurlutil_secure.ashx" without any trouble,
 but they are fake. True URLs have slightly different 'secure' parameter values.

I think 'secure' parameter values are slightly modified in the flash player, but not sure.

The streaming quality of KBS is very poor, and that of SBS is not free.
"""
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

import pyautogui
import pyperclip

from time import sleep


class MbcOnAirTvSimulator(object):
    """
    Just an experimental simulator script using selenium, pyAutoGUI, and pyperclip
    """

    def __init__(self):
        self.driver = webdriver.Chrome()

    def go(self, user_id, user_pw):
        self.driver.get('http://www.imbc.com')

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href="javascript:iMbc_login();"]'))
            )
        finally:
            pass

        try:
            login = self.driver.find_element_by_css_selector('a[href="javascript:iMbc_login();"]')
            login.click()
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'lbl_id'))
            )
        finally:
            pass

        try:
            self.driver.execute_script('document.getElementById("lbl_id").setAttribute("value", "%s");' % user_id)
            self.driver.execute_script('document.getElementById("lbl_pwd").setAttribute("value", "%s");' % user_pw)
            self.driver.find_element_by_css_selector('input.btn_login').click()
        except NoSuchElementException:
            pass
        finally:
            pass

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'p.copyright'))
            )
        finally:
            pass

        self.driver.get('http://vodmall.imbc.com/player/onair.aspx')

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'f_Player'))
            )
        finally:
            pass

    def play_or_stop(self):
        player = self.driver.find_element_by_id('f_Player')
        ActionChains(self.driver).move_to_element_with_offset(player, 16, 457).click().perform()

    def click(self):
        position = self.driver.get_window_position()
        browser_rect = self.driver.execute_script("return document.getElementById('f_Player').getBoundingClientRect();")

        mouse_coord_x = position['x'] + browser_rect['left'] + browser_rect['width'] // 2
        mouse_coord_y = position['y'] + browser_rect['top'] + browser_rect['height'] // 2

        pyautogui.click(x=mouse_coord_x, y=mouse_coord_y, button='right')
        pyautogui.press(['down', 'down', 'down', 'enter'], interval=1)

        return pyperclip.paste()

    def run(self):
        self.go()
        print('sleep for 5 seconds...')
        sleep(5)
        link = ''
        limit = 10
        while not link.startswith('rtmp://') and limit > 0:
            self.play_or_stop()  # started
            print('link is invalid. sleep for 20 seconds...')
            sleep(20)
            link = self.click()
            limit -= 1

        if limit == 0:
            link = ''

        if link:
            print(link)
        else:
            print('failed')
