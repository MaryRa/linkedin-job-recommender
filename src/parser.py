import datetime
import os
import time

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import langid


class LinkedInParser:
    def __init__(self,
                 chrome_driver_path,
                 vacancy_path,
                 urls):
        self.chrome_driver_path = chrome_driver_path
        self.vacancy_path = vacancy_path
        self.urls = urls

        self._wd = None

    def _open_chrome_page(self):
        service = Service(self.chrome_driver_path)
        options = Options()
        options.add_argument("--start-maximized")
        self._wd = webdriver.Chrome(service=service, options=options)

    def _open_url(self, url_name):
        print(url_name)
        url = self.urls[url_name]
        self._wd.get(url)
        time.sleep(5)

    def _turn_off_cookies(self):
        try:
            self._wd.find_element(By.XPATH,
                                  "//button[@action-type='DENY']").click()
            time.sleep(5)
        except:
            pass

    def _close_login_warning(self):
        try:
            self._wd.find_element(By.CLASS_NAME, 'cta-modal__dismiss-btn'
                                  ).click()
        except:
            pass

    def _read_parsed_vacancies(self):
        max_ind = 0
        if self.vacancy_path in os.listdir('.'):
            df = pd.read_csv(self.vacancy_path, index_col=0)
            max_ind = df.index.max() + 1
        else:
            df = pd.DataFrame(columns=['title', 'company_name',
                                       'location', 'salary',
                                       'date', 'link', 'text'])
        return df, max_ind

    def _get_vacancy_list(self):
        list_inst = self._wd.find_element(
            By.CLASS_NAME, "jobs-search__results-list")
        return list_inst.find_elements(By.TAG_NAME, 'li')

    def _go_to_end_list(self):
        body = self._wd.find_element(By.CSS_SELECTOR, 'body')
        body.send_keys(Keys.END)
        time.sleep(2)

    def _press_show_more_button(self):
        self._wd.find_element(By.CLASS_NAME,
                              'infinite-scroller__show-more-button').click()

    def _press_home_end(self):
        body = self._wd.find_element(By.CSS_SELECTOR, 'body')
        for i in range(5):
            body.send_keys(Keys.HOME)
            time.sleep(0.5)
            body.send_keys(Keys.END)
            time.sleep(0.5)

    def _open_more_vacancies(self, list_vacancies):
        self._go_to_end_list()
        new_list_vacancies = self._get_vacancy_list()
        if len(new_list_vacancies) == len(list_vacancies):
            try:
                self._press_show_more_button()
            except:
                self._press_home_end()
            time.sleep(2)
            new_list_vacancies = self._get_vacancy_list()
            if len(new_list_vacancies) == len(list_vacancies):
                print('End of the list reached')
        self._close_login_warning()
        return new_list_vacancies

    @staticmethod
    def _read_date(vacancy):
        try:
            date = vacancy.find_element(
                By.CLASS_NAME, "job-search-card__listdate"
            ).get_attribute('datetime')
        except:
            date = vacancy.find_element(
                By.CLASS_NAME,
                "job-search-card__listdate--new"
            ).get_attribute('datetime')
        return date

    def _read_brief_info(self, vacancy):
        res = pd.Series(dtype=str)
        res['title'] = vacancy.find_element(
            By.CLASS_NAME, "base-search-card__title").text
        res['company_name'] = vacancy.find_element(
            By.CLASS_NAME, "base-search-card__subtitle").text
        res['location'] = vacancy.find_element(
            By.CLASS_NAME, "job-search-card__location").text
        try:
            res['salary'] = vacancy.find_element(
                By.CLASS_NAME, "job-search-card__salary-info").text
        except:
            pass
        res['date'] = self._read_date(vacancy)
        try:
            res['link'] = vacancy.find_element(
                By.CLASS_NAME, 'base-card__full-link').get_attribute('href')
        except:
            pass
        return res

    @staticmethod
    def _was_it_parsed(df, info):
        same_indexes = (df[['title', 'company_name',
                            'location', 'date']] ==
                        info.loc[['title', 'company_name',
                                  'location', 'date']]).all(
            axis=1)
        if same_indexes.sum() > 1:
            if 'link' in info.index and info['link'] is not None:
                df.loc[same_indexes, 'link'] = info['link']
        return same_indexes.sum() > 1, df

    def _window_opened(self, info):
        top_card_title = None
        top_card_company = None
        refreshed = False
        initial_start = datetime.datetime.now()
        time_start = datetime.datetime.now()
        while not ((top_card_title == info['title']) and
                   (top_card_company == info['company_name'])):
            time.sleep(0.5)
            try:
                top_card_title = self._wd.find_element(
                    By.CLASS_NAME, "top-card-layout__title").text
                top_card_company = self._wd.find_element(
                    By.CLASS_NAME, "topcard__flavor").text
            except:
                pass

            if (datetime.datetime.now() - time_start).seconds > 5:
                self._wd.refresh()
                refreshed = True
                time.sleep(1)
                time_start = datetime.datetime.now()
            if (datetime.datetime.now() - initial_start).seconds > 10:
                return False, refreshed
            time.sleep(0.5)
        return True, refreshed

    def _read_vacancy_text(self):
        try:
            self._wd.find_element(
                By.XPATH,
                "//button[@data-tracking-control-name='public_jobs_show-more-html-btn']"
            ).click()
            text = self._wd.find_element(By.CLASS_NAME,
                                         "show-more-less-html__markup").text
            return text
        except:
            return None

    def _save_data(self, df):
        df = df[~df['text'].isna()].drop_duplicates().reset_index(drop=True)
        print(f"Number data saved: {df.shape[0]}")
        df.to_csv(self.vacancy_path)

    def run(self, n_save=50):
        self._open_chrome_page()
        new = 0
        for url_key in self.urls.keys():
            df, max_ind = self._read_parsed_vacancies()
            i = 0
            fresh = True
            try:
                self._open_url(url_key)
                self._turn_off_cookies()
                list_vacancies = []
                while len(list_vacancies) > i or fresh:

                    if len(list_vacancies) - i < 2 or fresh:
                        list_vacancies = self._open_more_vacancies(
                            list_vacancies)
                        fresh = False
                    n = len(list_vacancies)

                    vacancy = list_vacancies[i]
                    info = self._read_brief_info(vacancy)
                    it_was_parsed, df = self._was_it_parsed(df, info)
                    if it_was_parsed:
                        i += 1
                        time.sleep(0.3)
                        continue
                    else:
                        df.loc[max_ind + i, info.index] = info
                    vacancy.click()

                    success, refreshed = self._window_opened(info)
                    if success:
                        text = self._read_vacancy_text()
                        df.loc[max_ind+i, 'text'] = text
                        try:
                            df.loc[max_ind+i, 'language'
                            ] = langid.classify(text)[0]
                        except:
                            pass
                    if refreshed:
                        list_vacancies = []
                        while n > len(list_vacancies):
                            list_vacancies = self._open_more_vacancies(
                                list_vacancies)
                    i += 1
                    time.sleep(1)
                    new += 1
                    if new % n_save == 0:
                        self._save_data(df)

            except KeyboardInterrupt:
                raise Exception('You have pressed ctrl-c button.')
                sys.exit()
            else:
                pass
            finally:
                self._save_data(df)
                print('Number of vacancies were viewed:', i)
