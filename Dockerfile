FROM python:3.12
WORKDIR /app
RUN apt-get update && apt-get install -y curl build-essential

RUN curl https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

COPY . /app

RUN poetry install

CMD ["poetry", "run", "uvicorn", "lecture_2.hw.shop_api.main:app", "--port", "8000"]