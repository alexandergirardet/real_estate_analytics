# Extract rightmove outcode unique IDs
import pandas as pd
import mysql.connector
import re

# Function that returns right ID for a given outcode
def get_outcode_value(postcode, driver):
    driver.get("https://www.rightmove.co.uk/property-to-rent.html")
    input_box = driver.find_element(By.XPATH, '//*[@id="searchLocation"]')
    input_box.send_keys(postcode)
    search_box = driver.find_element(By.XPATH, '//*[@id="search"]')
    search_box.click()
    
    try:
        submit = driver.find_element(By.ID, "submit")
        submit.click()
        url = driver.current_url
        outcode_value = re.findall("(?<=locationIdentifier=OUTCODE%5E)(.*)(?=&insId)", url)[0]
    except:
        header_title = driver.find_element(By.ID, "headerTitle")
        outcode_value = None
    
        
    return outcode_value

# Function that connects to a local mysql database
def connect_to_mysql(database):

    config = {
            'user': 'root',
            'password': 'Alex6581',
            'host': 'localhost',
            }

    con = mysql.connector.connect(**config)

    cursor = con.cursor(buffered=True)

    cursor.execute(f'USE {database}')
    cursor.execute('SET FOREIGN_KEY_CHECKS = 0')

    return cursor

# Function to fetch currently loaded outcodes in case selenium crashed
def fetch_current_rightmove_outcodes(cursor):
    cursor.execute("SELECT outcode FROM rightmove_outcodes")
    fetched_outcodes = cursor.fetchall()
    outcode_list = [x[0] for x in fetched_outcodes]

    return outcode_list

def fetch_outcodes(df, cursor, driver):
    for row in df.itertuples():
        outcode = row.postcode
        index = row.Index
        
        if outcode not in current_outcodes:
            outcode_value = get_outcode_value(outcode, driver)
            
            if outcode_value is not None:

                transaction = "INSERT IGNORE INTO rightmove_outcodes(outcode, rightmove_code) VALUES ('{}', {});".format(
                outcode, outcode_value)

                cursor.execute(transaction)

                con.commit()
            else:
                pass
        else:
            pass

def run():
    driver = webdriver.Firefox()
    cursor = connect_to_mysql("real_estate")

    current_outcodes = fetch_current_rightmove_outcodes(driver)

    # Load UK outcode csv file into pandas
    df = pd.read_csv("../../data/outcodes.csv", index_col=0)

    fetch_outcodes(df, cursor, driver) 

# Run function
run()
