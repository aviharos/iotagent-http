FROM python:3.8.13-alpine3.16

RUN groupadd -r iotagent && \
    useradd -g iotagent iotagent

RUN mkdir -p /usr/src/iotagent

RUN chown -R iotagent:iotagent /usr/src/iotagent

USER iotagent

WORKDIR /usr/src/iotagent

COPY dependencies.txt ./

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r dependencies.txt

RUN rm dependencies.txt

COPY iotagent/* .

CMD ["python", "./iotagent.py"]

