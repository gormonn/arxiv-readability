FROM python:3.6.5
RUN apt-get update -qq && apt-get install -qy netcat
RUN pip install -U pip pipenv
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
COPY Pipfile Pipfile.lock /code/
RUN pipenv install --system --deploy
COPY . /code/
RUN SECRET_KEY=unset python manage.py collectstatic --no-input
ENV WEB_CONCURRENCY 3
ENV WORKER_CONNECTIONS 100
ENV PORT 8000
CMD gunicorn arxiv_html.wsgi -k gevent --worker-connections $WORKER_CONNECTIONS --bind 0.0.0.0:$PORT --config gunicorn_config.py --max-requests 10000 --max-requests-jitter 1000 --access-logfile -
