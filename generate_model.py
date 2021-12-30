import requests
from sklearn.linear_model import LinearRegression
import numpy
import MySQLdb


def generate_model(future_code):
    url_str = ('http://stock2.finance.sina.com.cn/futures/api/json.php/IndexService.getInnerFuturesDailyKLine?symbol=' +
                future_code)
    #sina.finance
    r = requests.get(url_str)
    r_json = r.json()
    r_lists = list(r_json)

    close_price = []
    for dataset in r_lists:
        close_price.append(float(dataset[4]))
    # y dataset
    y_train = close_price[9: len(close_price)]

    x_train = []
    for COUNT in range(9, len(close_price)):
        A3 = numpy.mean(close_price[(COUNT-3):COUNT])
        A9 = numpy.mean(close_price[(COUNT-9):COUNT])
        # x dataset
        x_train.append([A3, A9])

    linear = LinearRegression().fit(x_train, y_train)

    # get the peremeters
    m1 = linear.coef_[0]
    m2 = linear.coef_[1]
    c = linear.intercept_

    return[m1, m2, c]

db = MySQLdb.connect(host='localhost', port=3306, user='root', passwd='619000ab', db='futures', charset='utf8')
conn = db.cursor()
conn.execute("select Futurecode from future")
code = conn.fetchall()
  
for COUNT in code:
    search_code = "".join(tuple(COUNT))
    print(search_code)
    model = generate_model(search_code)
    print(model)
    # store
    conn.execute("update future set M1=%s,M2=%s,C=%s where Futurecode='%s'" % (model[0], model[1], model[2], search_code))
    conn.connection.commit()
