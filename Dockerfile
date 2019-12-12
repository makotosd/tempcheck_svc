#
#
#
FROM python:3.7-alpine
#RUN apk --no-cache add python-pip && \
#    pip install jsonify flask
RUN pip install jsonify flask m2x python-dateutil
COPY tempcheck_svc.py /

EXPOSE 8080

ENTRYPOINT ["python", "/tempcheck_svc.py"]
