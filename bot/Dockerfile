FROM python:3.12.6

COPY requirements.txt /bot/
RUN pip install -r /bot/requirements.txt

COPY run.py /bot/

WORKDIR /bot

CMD python run.py