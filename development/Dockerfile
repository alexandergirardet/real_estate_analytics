FROM google/cloud-sdk:latest

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

COPY /app /usr/src/app

# CMD [ "./launch-scrape.sh" ]