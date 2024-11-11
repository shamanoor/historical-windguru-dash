import os

import pandas as pd

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By



load_dotenv()

driver = webdriver.Chrome()

# Apparently not the best but definitely the easiest approach:

username = os.environ["WG_USERNAME"]
password = os.environ["WG_PASSWORD"]
driver.get(f"https://{username}:{password}@www.windguru.cz/archive.php?id_spot=15&id_model=3&date_from=2024-10-11&date_to=2024-11-11")

driver.implicitly_wait(3)

variables = {'windspeed': 'WINDSPD',
             'winddirection': 'WINDDIR',
             'gust': 'GUST',
             'waveheight': 'HTSGW',
             'wavedirection': 'DIRPW',
             'waveperiod': 'PERPW',
             'temperature': 'TMP',
             'rain': 'APCP1',
             'cloudcover': 'TCDC',
             'highclouds': 'HCDC',
             'middleclouds': 'MCDC',
             'lowclouds': 'LCDC',
             'humidity': 'RH',
             'airpressure': 'SLP',
             'isotherm': 'FLHGT',
             }

selected_variables = ['WINDSPD', 'WINDDIR', 'GUST', 'HTSGW', 'DIRPW', 'PERPW', 'SLP']


# Select checkboxes
for included_variable in variables.values():
    print(included_variable)
    nested_element = driver.find_element(By.XPATH, f".//*[@value='{included_variable}']")

    # Wait for the elements to be interactable
    if not nested_element.get_attribute('checked') and included_variable in selected_variables:
        driver.execute_script("arguments[0].checked = true;", nested_element)
    clicked = nested_element.get_attribute('checked')
    print(clicked)



# Obtain tables
# div_id = 'archive_results'
# nested is a table with "class = forecast-ram"
table = driver.find_element(By.ID, "archive_results")
print("*******************")
print("Table elements: ", table.find_elements(By.XPATH, "./table"))

print(table)
# # driver.quit()
rows = []
for row in table.find_elements(By.XPATH, ".//tbody//tr"):
    cells = row.find_elements(By.TAG_NAME, "td")
    row_data = [cell.text for cell in cells]
    rows.append(row_data)


# Create a Pandas DataFrame
df = pd.DataFrame(rows)

# Print the DataFrame
print(df)#### In case nested is needed...
