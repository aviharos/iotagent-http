FROM python:3.10.5-alpine3.16

ARG USER=appuser

ARG GROUP=appuser

ENV HOME /home/$USER

RUN addgroup -S $GROUP && \
    adduser -S $USER -G $GROUP

WORKDIR $HOME/app

USER $USER

COPY --chown=$USER:$GROUP dependencies.txt ./

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r dependencies.txt

COPY --chown=$USER:$GROUP app/* ./

ENTRYPOINT ["python3", "./main.py"]

