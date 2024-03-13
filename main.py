from flask import Flask, request
from add_event import add_event
from get_analytics import get_analytics_data
from pyspark.sql import SparkSession

app = Flask(__name__)

spark = SparkSession.builder.appName("my_app").getOrCreate()


@app.route('/event', methods=['POST'])
def handle_add_event():
    return add_event(request, spark)


@app.route('/analytics/query', methods=['GET'])
def handle_get_analytics_data():
    return get_analytics_data(request, spark)


if __name__ == '__main__':
    app.run(debug=True)