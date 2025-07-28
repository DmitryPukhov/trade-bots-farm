FROM quay.io/strimzi/kafka:0.46.1-kafka-4.0.0
USER root:root

# install s3-sink
RUN mkdir -p /opt/kafka/plugins/s3-sink
ADD https://hub-downloads.confluent.io/api/plugins/confluentinc/kafka-connect-s3/versions/10.6.7/confluentinc-kafka-connect-s3-10.6.7.zip /tmp/s3-sink.zip
RUN microdnf install -y unzip && \
    mkdir -p /opt/kafka/plugins/s3-sink && \
    unzip /tmp/s3-sink.zip -d /opt/kafka/plugins/s3-sink/ && \
    rm /tmp/s3-sink.zip && \
    microdnf remove -y unzip && \
    microdnf clean all -y

# Force AWS SDK to use MinIO
RUN echo "aws.s3.endpoint=http://minio:9000" >> /opt/kafka/config/connect-distributed.properties && \
    echo "aws.s3.path.style.access=true" >> /opt/kafka/config/connect-distributed.properties

USER 1001