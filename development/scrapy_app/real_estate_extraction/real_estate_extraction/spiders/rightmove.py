import scrapy
import psycopg2
import csv

from bs4 import BeautifulSoup
import pkgutil


class RightmoveSpider(scrapy.Spider):
    name = 'rightmove'
    
    def __init__(self, *args, **kwargs):
        
        self.headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Referer': 'https://www.rightmove.co.uk/property-to-rent/find.html?locationIdentifier=REGION%5E87490&index=24&propertyTypes=&includeLetAgreed=false&mustHave=&dontShow=&furnishTypes=&keywords=',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.88 Safari/537.36',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="100", "Google Chrome";v="100"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"'
        }

        conn = psycopg2.connect(
            host="postgres",
            database="rightmove",
            port=5432, 
            user='airflow', 
            password='airflow'
            )

        cursor = conn.cursor()

        cursor.execute("SELECT rightmove_id FROM rightmove_landing_zone")

        fetched_ids = cursor.fetchall()

        self.rightmove_ids = [int(x[0]) for x in fetched_ids]

        self.fetched_outcodes = self.get_outcodes()

        conn.close()

    def start_requests(self):
        for codes in self.fetched_outcodes:
            rightmove_code = codes[1]
            postcode = codes[0]
            for index_jump in range(0, 100, 25): # Adjusting to 100 so I can have some extra values to test with
                url = f"https://www.rightmove.co.uk/api/_search?locationIdentifier=OUTCODE%5E{rightmove_code}&numberOfPropertiesPerPage=24&radius=10.0&sortType=6&index={index_jump}&includeLetAgreed=false&viewType=LIST&channel=RENT&areaSizeUnit=sqft&currencyCode=GBP&isFetching=false"

                yield scrapy.Request(method='GET', url = url, headers= self.headers, callback=self.parse)

    def parse(self, response):
        listings = response.json()['properties']
        for listing in listings:

            property_id = listing['id']

            if property_id not in self.rightmove_ids:
                property_url = f"https://www.rightmove.co.uk/properties/{property_id}"

                yield scrapy.Request(method='GET', url = property_url, headers= self.headers, callback=self.parse_property, meta={"item":listing})
            else:
                print("Already loaded in")

    def parse_property(self, response):
        soup = BeautifulSoup(response.text, 'lxml')

        item = response.meta['item']

        # Get image urls

        images = soup.find_all("meta", {"property":"og:image"})
        image_urls = [image['content'] for image in images]

        # Get feature list
        try:
            uls = soup.find("ul", {"class": "_1uI3IvdF5sIuBtRIvKrreQ"})
            features = uls.find_all("li")
            feature_list = [feature.text for feature in features]
        except:
            feature_list = None

        # Get full summary

        summary = soup.find("div", {"class": "OD0O7FWw1TjbTD4sdRi1_"}).div.text

        # Asign content to item 
        item['feature_list'] = feature_list
        item['summary'] = summary

        yield item

    def get_outcodes(self) -> list:
    #     with open('/extraction_data/rightmove_outcodes.csv', 'r') as f:
    #         reader = csv.reader(f)
    #         outcodes = list(reader)
    #         outcodes = outcodes[1:]
    #         outcodes = [(outcode[1], outcode[2]) for outcode in outcodes]
    #     return outcodes
    
        with open('/Users/alexandergirardet/projects/estatewise/real_estate_analytics/development/scrapy_app/extraction_data/rightmove_outcodes.csv', 'r') as f:
            reader = csv.reader(f)
            outcodes = list(reader)
            outcodes = outcodes[1:]
            outcodes = [(outcode[1], outcode[2]) for outcode in outcodes]
        return outcodes