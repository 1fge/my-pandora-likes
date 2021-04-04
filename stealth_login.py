import asyncio
import random
import pyppeteer
import sys
from pyppeteer_stealth import stealth

class StealthLogin:
    def __init__(self, email, password):
        self.email = email
        self.password = password

    async def initiate_browser(self):
        """Initialize a pyppeteer browser with stealth settings"""
        self.browser = await pyppeteer.launch(headless=False)
        self.page = await self.browser.newPage()
        await stealth(self.page)

    async def stealth_typer(self, text):
        """Input characters with a random delay between each keypress instead of static delay"""
        for character in text:
            await self.page.keyboard.type(character, delay=random.randrange(35,50))

    async def get_window_dimensions(self):
        """Get window dimensions for valid mouse moves"""
        dimensions = await self.page.evaluate('''() => {
            return {
                width: window.innerWidth,
                height: window.innerHeight
            }
        }''')

        return (dimensions["width"], dimensions["height"])

    async def stealth_input_details(self, selector, text, sleep=False):
        """Stealthily input desired text into an element"""
        if sleep:
            await asyncio.sleep(random.randrange(500,1250) / 1000)

        window_width, window_height = await self.get_window_dimensions()

        await self.page.mouse.move(random.randrange(0,window_width), random.randrange(0,window_height))
        await self.page.waitForSelector(selector)
        await self.page.click(selector)
        await self.stealth_typer(text)

    async def fetch_login_data(self):
        """Attempt to login to Pandora.com, intercept login request, and wait to be redirected from login page"""
        attempted_logins = 0

        while attempted_logins < 3:
            attempted_logins += 1
            print(f"Browser Login Attempt ({attempted_logins})")
            await self.page.goto("https://www.pandora.com/account/sign-in")

            # Enter email and password
            email_selector = "#form-template > div:nth-child(1) > div > label > div.FormInput__container > input"
            password_selector = "#form-template > div:nth-child(2) > div > label > div.FormInput__container > input"
            await self.stealth_input_details(email_selector, self.email, sleep=True)
            await self.stealth_input_details(password_selector, self.password, sleep=True)

            # Submit login details
            window_width, window_height = await self.get_window_dimensions()
            await self.page.mouse.move(random.randrange(0,window_width), random.randrange(0,window_height))
            await self.page.hover("#form-template > div:nth-child(3) > div > button")
            await self.page.click("#form-template > div:nth-child(3) > div > button")

            try:
                response = await self.page.waitForResponse("https://www.pandora.com/api/v1/auth/login")
                await self.page.waitForNavigation(timeout=7500)
                print("Successfully Logged In!\n")

                cookies = await self.page.cookies()
                response_data = await response.json()
                await self.browser.close()

                return cookies, response_data
            except pyppeteer.errors.TimeoutError:
                pass

        sys.exit("Login Failure! Ensure email and password are valid")

