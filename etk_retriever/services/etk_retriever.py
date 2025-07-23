import time
import uuid

from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from etk_retriever.models import Credentials


class EtkRetriever:
    # Константы селекторов и идентификаторов элементов
    LOGIN_BUTTON_SELECTOR = "button.login-button"
    LOGIN_INPUT_ID = "login"
    PASSWORD_INPUT_ID = "password"
    CAPTCHA_DIV_SELECTOR = "div.esia-captcha"
    CAPTCHA_IMG_SELECTOR = "img.esia-captcha__image"
    CAPTCHA_INPUT_SELECTOR = "input.esia-captcha__input"
    MFA_ELEMENT_TAG = "esia-enter-mfa"
    CODE_INPUT_TAG = "code-input"
    CODE_INPUT_FIELD_TAG = "input"
    STATEMENT_FORM_URL = "https://www.gosuslugi.ru/600302/1/form"
    GET_STATEMENT_BTN_XPATH = "//button[contains(text(), 'Получить выписку') or contains(., 'Получить выписку')]"
    MAIN_URL = "https://www.gosuslugi.ru/"

    def request_etk_statement(self):
        creds = (
            Credentials.objects.filter(is_active=True).order_by("last_used_at").first()
        )
        if not creds:
            raise Exception("Нет активных учетных данных")

        session_id = str(uuid.uuid4())

        # Настройка Selenium (headless Chrome).
        chrome_options = Options()
        # Для запуска в контейнере.
        # chrome_options.add_argument('--headless')
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(
            options=chrome_options,
            # Для запуска в контейнере.
            # service=Service("/usr/bin/chromedriver")
        )

        # TODO: Обрабатывать ошибки и помечать запрос как неудавшийся, отправлять уведомление в мониторинг.
        #  Либо отправлять на повторное исполнение (в Celery).
        self.login(driver, creds, session_id)
        self.handle_captcha(driver, creds, session_id)
        self.handle_2fa(driver, creds, session_id)
        time.sleep(5)
        self.request_statement(driver)

    def login(self, driver: WebDriver, creds: Credentials, session_id: str):
        # Открываем сайт.
        driver.get(self.MAIN_URL)
        # Ждём пока пройдут все редиректы.
        time.sleep(5)

        # Начинаем вход.
        login_btn = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, self.LOGIN_BUTTON_SELECTOR))
        )
        login_btn.click()
        time.sleep(2)

        # Вводим логин и пароль.
        login_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, self.LOGIN_INPUT_ID))
        )
        login_input.send_keys(creds.login)
        login_input.send_keys(Keys.TAB)
        time.sleep(1)
        password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, self.PASSWORD_INPUT_ID))
        )
        password_input.send_keys(creds.password)
        password_input.send_keys(Keys.ENTER)
        time.sleep(3)

    def handle_captcha(self, driver: WebDriver, creds: Credentials, session_id: str):
        # Проверяем появление капчи
        try:
            captcha_div = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, self.CAPTCHA_DIV_SELECTOR)
                )
            )
        except TimeoutException:
            return

        from etk_retriever.services.captcha_solver import CaptchaSolver

        solver = CaptchaSolver()

        captcha_img = captcha_div.find_element(
            By.CSS_SELECTOR, self.CAPTCHA_IMG_SELECTOR
        )
        # TODO: Выгружать изображения на S3.
        img_src = captcha_img.get_attribute("src")

        captcha_id = solver.set_captcha_to_solve(img_src, creds, session_id)

        # Ожидание решения капчи.
        solver.wait_for_captcha_solution(captcha_id)

        # Получаем текст капчи и вводим его в поле.
        captcha_text = solver.get_captcha_text(captcha_id)
        captcha_input = captcha_div.find_element(
            By.CSS_SELECTOR, self.CAPTCHA_INPUT_SELECTOR
        )
        captcha_input.clear()
        captcha_input.send_keys(captcha_text)
        captcha_input.send_keys(Keys.ENTER)
        time.sleep(2)

    def handle_2fa(self, driver: WebDriver, creds: Credentials, session_id: str):
        # Проверяем появление формы для ввода СМС.
        try:
            mfa_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, self.MFA_ELEMENT_TAG))
            )
        except TimeoutException:
            return

        from etk_retriever.services.two_factor_awaiter import TwoFactorAwaiter

        two_factor = TwoFactorAwaiter()
        task_id = two_factor.set_second_factor_to_capture(creds, session_id)

        # Ожидание SMS от пользователя.
        two_factor.wait_for_second_factor_capture(task_id)

        # Получаем код из SMS и вводим его в поле.
        factor_text = two_factor.get_second_factor(task_id)
        code_input_element = mfa_element.find_element(By.TAG_NAME, self.CODE_INPUT_TAG)
        factor_input = code_input_element.find_element(
            By.TAG_NAME, self.CODE_INPUT_FIELD_TAG
        )
        factor_input.send_keys(factor_text)
        time.sleep(2)

    def request_statement(self, driver: WebDriver):
        # Идём на нужную страницу для запроса выписки.
        driver.get(self.STATEMENT_FORM_URL)
        time.sleep(2)

        # Ищем нужную кнопку и нажимаем её.
        get_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    self.GET_STATEMENT_BTN_XPATH,
                )
            )
        )
        get_btn.click()
        time.sleep(2)
