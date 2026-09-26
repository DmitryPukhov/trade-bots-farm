import logging
import os
from datetime import date

from pyspark import SparkConf
from pyspark.sql import SparkSession

from common_tools import CommonTools


class ProcessBatchStagingAlorApp:

    def __init__(self):
        CommonTools.init_logging()

        self.kind = os.environ["KIND"]
        self.ticket = os.environ["TICKET"]
        self.date = date.fromisoformat(os.environ["DATE"])
        self._s3_access_key = os.environ.get("S3_ACCESS_KEY")
        self._s3_secret_key = os.environ.get("S3_SECRET_KEY")
        self._s3_src_dir = os.environ.get("S3_SRC_DIR") or "data"
        self._spark_jars_packages = os.environ.get("SPARK_JARS_PACKAGES")
        self.app_name = f"pytrade2-staging-alor-{self.ticket}-{self.kind}"

        self._spark: SparkSession = self.create_spark_session(self.app_name)

    def run(self):
        #src_dir = f"{self._s3_src_dir}/year=2025/month=08/day=31"
        src_dir = self._s3_src_dir
        logging.info(f"Reading data from S3: {src_dir}")
        df = self._spark \
            .read \
            .text(src_dir)
        df.show()

    def create_spark_session(self, app_name) -> SparkSession:
        endpoint_url = os.environ.get("S3_ENDPOINT_URL")
        access_key = os.environ.get("S3_ACCESS_KEY")
        secret_key = os.environ.get("S3_SECRET_KEY")

        # Prepare Spark configuration
        conf = SparkConf()
        conf.set("spark.hadoop.fs.s3a.endpoint", endpoint_url)
        conf.set("spark.hadoop.fs.s3a.access.key", access_key)
        conf.set("spark.hadoop.fs.s3a.secret.key", secret_key)
        conf.set("spark.hadoop.fs.s3a.path.style.access", "true")
        conf.set("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        conf.set("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        conf.set("spark.jars.packages", self._spark_jars_packages)
        conf.set("spark.hadoop.fs.s3a.aws.credentials.provider",
                 "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")
        logging.info(
            f"Creating Spark Session for app {app_name}, endpoint_url={endpoint_url}, access_key=***{access_key[-3:]}, secret_key=***{secret_key[-3:]},")

        spark = (SparkSession.builder
                 .appName(app_name)
                 .config(conf=conf)
                 .getOrCreate())
        # spark.sparkContext.setLogLevel("DEBUG")
        return spark


if __name__ == '__main__':
    ProcessBatchStagingAlorApp().run()
