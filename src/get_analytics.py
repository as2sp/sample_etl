from flask import jsonify
from pyspark.sql import functions as F


def get_analytics_data(request, spark):
    # Получаем параметры запроса
    group_by = request.args.get('groupBy').split(',')
    filters = request.args.get('filters')
    metrics = request.args.get('metrics').split(',')
    granularity = request.args.get('granularity')
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')

    # Фильтруем данные по дате
    filtered_data = spark.table('events').filter((F.col('date') >= start_date) & (F.col('date') <= end_date))

    # Группируем и агрегируем данные
    grouped_data = filtered_data.groupBy(group_by).agg({metric: "sum" for metric in metrics})

    # Преобразовываем результаты в JSON
    results = grouped_data.toJSON().collect()

    return jsonify({'results': [row.asDict() for row in results]})