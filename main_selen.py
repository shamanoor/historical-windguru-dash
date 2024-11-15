import datetime
import os
import pickle

from dotenv import load_dotenv
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
import time

load_dotenv()

class WindguruScraper:
    def __init__(self, url: str = "https://www.windguru.cz/archive.php"):
        self.driver = webdriver.Chrome()
        # Is dit nodig? Effe checken wat de beste wait strategy is.. en hoe dat werkt enzo...
        self.driver.implicitly_wait(3)
        self.data = None

        # Default url to archive
        self.url = url

        # global variables, ergens anders neerzetten?
        self.variables = {'windspeed': '//*[@id="archive_filter"]/fieldset/label[1]',
                     'winddirection': '//*[@id="archive_filter"]/fieldset/label[2]',
                     'gust': '//*[@id="archive_filter"]/fieldset/label[3]',
                     'waveheight': '//*[@id="archive_filter"]/fieldset/label[4]',
                     'wavedirection': '//*[@id="archive_filter"]/fieldset/label[5]',
                     'waveperiod': '//*[@id="archive_filter"]/fieldset/label[6]',
                     'temperature': '//*[@id="archive_filter"]/fieldset/label[7]',
                     'rain': '//*[@id="archive_filter"]/fieldset/label[8]',
                     'cloudcover': '//*[@id="archive_filter"]/fieldset/label[9]',
                     'highclouds': '//*[@id="archive_filter"]/fieldset/label[10]',
                     'middleclouds': '//*[@id="archive_filter"]/fieldset/label[11]',
                     'lowclouds': '//*[@id="archive_filter"]/fieldset/label[12]',
                     'humidity': '//*[@id="archive_filter"]/fieldset/label[13]',
                     'airpressure': '//*[@id="archive_filter"]/fieldset/label[14]',
                     'isotherm': '//*[@id="archive_filter"]/fieldset/label[15]',
                     }

        # Open the Windguru home page
        self.driver.get(url)

        self._login()

    def _login(self):
        # Set your login credentials
        username = os.getenv("WG_USERNAME") # naar constructor?
        password = os.getenv("WG_PASSWORD") # naar constructor?

        # Allow the page to load (you can adjust the sleep time as needed)
        time.sleep(1)

        # Find and click on the login button
        login_button = self.driver.find_element(By.ID, "wg_login_link")
        login_button.click()

        # Allow the login page to load
        time.sleep(4)

        # Find the username and password input fields
        username_field = self.driver.find_element(By.XPATH, '//*[@id="inputusername"]')
        password_field = self.driver.find_element(By.XPATH, '/html/body/div[17]/div/div[2]/form/label[2]/input')

        # Input your credentials
        username_field.click()
        time.sleep(1)
        username_field.send_keys(username)
        time.sleep(1)

        password_field.click()
        time.sleep(1)
        password_field.send_keys(password)
        time.sleep(1)

        submit_button = self.driver.find_element(By.XPATH, '/html/body/div[17]/div/div[2]/form/button[1]')
        submit_button.click()

        time.sleep(2)


    def set_date_range(self, date_start: str, date_end: str):
        """
        Set the date range for which to retrieve data.

        You can go back in the past by a maximum of 5 years.

        Parameters
        ----------
        date_start: str
            Start of date range. The passed format must be yyy-mm-dd, e.g. "2024-01-01". Can be maximum 5 years in the
            past.
        date_end: str
            End of date range. The passed format must be yyy-mm-dd, e.g. "2024-01-01".


        """
        start_date = self.driver.find_element(By.XPATH, '//*[@id="archive_filter"]/label[1]/span/input[2]')
        start_date.click()
        start_date.clear()
        start_date.send_keys(date_start)

        end_date = self.driver.find_element(By.XPATH, '//*[@id="archive_filter"]/label[2]/span/input[2]')
        end_date.clear()
        end_date.send_keys(date_end)

    def set_variables(self, selected_variables: list[str], spot_id: str = 15):
        """
        Set the spot and variables to be retrieved for the given surf spot.

        Parameters
        ----------
        selected_variables: list[str]
            List of variables to be selected. Mind that by default the variables windspeed, winddirection and temperature
            are selected. Adding these variables to this list will cause them to be DESELECTED.
            Options: ['windspeed', 'winddirection', 'gust', 'waveheight', 'wavedirection', 'waveperiod', 'temperature',
            'rain', 'cloudcover', 'highclouds', 'middleclouds', 'lowclouds', 'humidity', 'airpressure', 'isotherm']
        spot_id: int = 15
            Spot id of the spot for which data will be retrieved. Defaults to France - Biarritz, with spot id 15.

        """
        # BUG: exclude temperature and windspeed because they are selected by default and for some reason the selectors to see if it is already checked don't work...
        self.driver.get(f"https://www.windguru.cz/archive.php?id_spot={spot_id}") # Specific spot ID for Biarritz... where best to configure?

        for var in selected_variables:
            var_xpath = self.variables[var]
            variable = self.driver.find_element(By.XPATH, var_xpath)
            print(f'before: {variable.get_attribute("checked"), variable.is_selected()} for variable {var}')
            if not variable.get_attribute("checked"):
                self.driver.execute_script('arguments[0].setAttribute("checked", "checked");', variable)
                variable.click()
            clicked = variable.get_attribute("checked")
            time.sleep(0.5)
            print(f"For {var} the value of checked is {clicked}")
        time.sleep(2)

    def run(self, save_pickle: bool = True):
        """

        Parameters
        ----------


        Returns
        -------
        df: pd.DataFrame
            The dataframe with multicolumn index containing all the data.
        """
        # Submit query search
        submit_search = self.driver.find_element(By.XPATH, '//*[@id="archive_filter"]/button[1]')
        submit_search.click()

        time.sleep(40) # Give time to load data... Find better way to perform load

        # Obtain tables
        # div_id = 'archive_results'
        # nested is a table with "class = forecast-ram"
        table = self.driver.find_element(By.ID, "archive_results")
        print("*******************")
        print("Table elements: ", table.find_elements(By.XPATH, "./table"))
        print(table)

        # driver.quit()
        rows = []
        for row in table.find_elements(By.XPATH, ".//tbody//tr"):
            cells = row.find_elements(By.TAG_NAME, "td")
            row_data = [cell.text for cell in cells]
            rows.append(row_data)

        df = pd.DataFrame(rows)

        # Pre-process data
        iterables = [
            ["Windsnelheid (knopen)", "Windstoten (knopen)", "Golven (m)", "Golfperiode (s)", "Temperatuur (°C)",
             "Druk (hPa)"],
            ["00h", "02h", "04h", "06h", "08h", "10h", "12h", "14h", "16h", "18h", "20h", "22h"]]

        multi_index = pd.MultiIndex.from_product(iterables, names=["first", "second"])
        # Make reusable the line below, which columns to select...
        dff = df[[i for i in range(6 * 12 + 1)]].iloc[3:].set_index(0)

        multi_index = pd.MultiIndex.from_product(iterables, names=["feature", "time"])
        dff.columns = multi_index

        # Filter out default added column (wind direction, which is empty for our data retrieval method)
        dff = dff[["Windsnelheid (knopen)", "Windstoten (knopen)", "Golven (m)", "Golfperiode (s)", "Temperatuur (°C)", "Druk (hPa)"]]

        self.data = dff
        if not pickle:
            return dff

        with open(f'data_biarritz_{datetime.datetime.now()}.pkl', 'wb') as f:  # open a text file
            pickle.dump(dff, f)  # serialize the list



if __name__ == "__main__":
    scraper = WindguruScraper()

    # Beter om run() functie te maken waar je variabelen in passt
    scraper.set_date_range("2024-10-01", "2024-11-12")
    scraper.set_variables(['winddirection', 'gust', 'waveheight', 'waveperiod', 'airpressure'])
    scraper.run()
    df = scraper.data
