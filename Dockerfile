FROM python:3.10.7-alpine3.16

ARG USER=appuser

ARG GROUP=appuser

ENV HOME /home/$USER

RUN addgroup -S $GROUP && \
    adduser -S $USER -G $GROUP

WORKDIR $HOME

USER $USER

COPY --chown=$USER:$GROUP requirements.txt ./

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY --chown=$USER:$GROUP app/ ./app/

WORKDIR $HOME/app

ENTRYPOINT ["python3", "./main.py"]

