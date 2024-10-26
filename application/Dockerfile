FROM python:3.12.6

COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt

COPY database/ /app/database/
COPY routers/ /app/routers/
COPY templates/ /app/templates/
COPY main.py /app/
COPY schemas.py /app/

WORKDIR /app

CMD python -m uvicorn main:app --host 0.0.0.0 --port 8000
