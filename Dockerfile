FROM python:3.9.14-slim

WORKDIR /app

COPY requirements.txt streamlit_app.py /app/

RUN pip install -r requirements.txt && \
    rm -rf ~/.cache src

CMD ["streamlit", "run", "streamlit_app.py"]
