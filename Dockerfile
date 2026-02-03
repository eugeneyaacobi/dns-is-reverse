FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY dns_is_reverse/ dns_is_reverse/
COPY README.md .

RUN pip install --no-cache-dir .

EXPOSE 53/udp

USER nobody

ENTRYPOINT ["dns-is-reverse"]
CMD ["--configfile", "/etc/dns-is-reverse.conf", "--querylog"]