from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from real_estate_extraction.spiders.rightmove import RightmoveSpider
 
 
process = CrawlerProcess(get_project_settings())
process.crawl(RightmoveSpider)
process.start()