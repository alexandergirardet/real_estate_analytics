FROM google/cloud-sdk:latest

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

COPY /real_estate_extraction .

CMD [ "./launch-scrape.sh" ]