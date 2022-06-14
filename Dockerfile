FROM python:3.7.13-alpine3.16

ARG USER=iotagent

ARG GROUP=iotagent

ENV HOME /home/$USER

RUN addgroup -S $GROUP && \
    adduser -S $USER -G $GROUP

USER $USER

WORKDIR $HOME

COPY dependencies.txt ./

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r dependencies.txt

RUN rm dependencies.txt

COPY iotagent/* ./

ENTRYPOINT ["python3", "./iotagent.py"]

