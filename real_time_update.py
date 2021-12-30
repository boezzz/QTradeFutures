import requests


def update_live(future_code):
    url_str = ('http://stock2.finance.sina.com.cn/futures/api/json.php/IndexService.getInnerFuturesMiniKLine5m?symbol=' +
            future_code)
    # sina.finance
    # request
    r = requests.get(url_str)
    r_json = r.json()
    r_list = list(r_json)

    # seperate
    updatetime = r_list[0][0]
    open_price = float(r_list[0][1])
    high_price = float(r_list[0][2])
    low_price = float(r_list[0][3])
    close_price = float(r_list[0][4])
    volume = float(r_list[0][5])

    return[updatetime, open_price, high_price, low_price, close_price, volume]