FROM python:3.12-alpine3.19

LABEL maintainer = "o.cadman@live.co.uk"

ENV PYTHONUNBUFFERED 1

COPY /src /src
COPY ./requirements.txt /tmp/requirements.txt

EXPOSE 8000

WORKDIR /src

RUN python -m venv /venv && \
    /venv/bin/pip install --upgrade pip && \
    apk add --update --no-cache --virtual libpq5 && \
    apk add --update --no-cache bind-tools postgresql-client && \
    apk add --update vim && \
    /venv/bin/pip install -r /tmp/requirements.txt && \
    rm -rf /tmp && \
    adduser \
    --disabled-password \
    djangouser


ENV PATH="/venv/bin:$PATH"
ENV PYTHONPATH="${PYTHONPATH}:/venv/lib/python3.12/site-packages"

USER djangouser

CMD ["python manage.py runserver"]

