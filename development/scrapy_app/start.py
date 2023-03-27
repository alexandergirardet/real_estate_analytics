from scrapyd_api import ScrapydAPI
scrapyd = ScrapydAPI('http://localhost:6800')
print(scrapyd.list_projects())
print(scrapyd.list_spiders('real_estate_extraction'))
scrapyd.schedule('real_estate_extraction', 'rightmove')