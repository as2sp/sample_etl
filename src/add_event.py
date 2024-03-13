from flask import jsonify
from pyspark.sql import SparkSession

def add_event(request, spark):
    event_data = request.get_json()

    # Создаем датафрейм из JSON данных события
    events_df = spark.createDataFrame([Row(**event) for event in event_data])

    # Сохраняем датафрейм в таблицу "events" в витрину в PostgreSQL
    events_df.write.format("jdbc").options(
        url="jdbc:postgresql://postgres:5432/my_database_name",
        dbtable="events",
        user="myname",
        password="mypass"
    ).mode("append").save()

    return jsonify({'success': True})