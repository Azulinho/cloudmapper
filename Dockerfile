FROM python:3
RUN apt-get update && apt-get install -y make
COPY src/ /app/
WORKDIR /app
RUN make setup
