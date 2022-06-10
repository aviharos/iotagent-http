FROM python:3.10.5-alpine3.16

ARG USER=iotagent

ENV HOME /home/$USER

RUN addgroup --system $USER && \
    adduser --system --group $USER

USER $USER

WORKDIR $HOME

COPY dependencies.txt ./

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r dependencies.txt

RUN rm dependencies.txt

COPY iotagent/* .

ENTRYPOINT ["python3", "./iotagent.py"]

