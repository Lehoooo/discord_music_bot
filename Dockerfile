FROM python:3.6.9

WORKDIR /

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY cogs/ cogs/

CMD [ "python", "./main.py" ]
