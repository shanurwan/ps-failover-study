FROM alpine:3.22
# alpine 3.22 ships PgBouncer 1.24.x
RUN apk add --no-cache pgbouncer postgresql17-client
COPY pgbouncer.ini userlist.txt entrypoint.sh /etc/pgbouncer/
RUN chown -R nobody /etc/pgbouncer
ENV PGPASSWORD=admin
EXPOSE 6432
ENTRYPOINT ["/bin/sh", "/etc/pgbouncer/entrypoint.sh"]
