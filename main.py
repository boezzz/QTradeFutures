import MySQLdb
import hashlib
import real_time_update
import re
import datetime
import time
import mobile
from apscheduler.schedulers.background import BackgroundScheduler


db = MySQLdb.connect(host='localhost', port=3306, user='root', passwd='619000ab', db='futures', charset='utf8')
sql = db.cursor()


def check_password(username, password):
    sql.execute("select Username from user")
    names = sql.fetchall()

    users = []
    for each in names:
       eachname = "".join(tuple(each))
       users.append(eachname)


    if username in users:
        sql.execute("select Password from user where Username='%s'" % username)
        hash = sql.fetchone()
        hash = "".join(hash)
        print(hash)
        sha256 = hashlib.sha256()
        sha256.update(password.encode('utf-8'))
        res = sha256.hexdigest()
        if hash == res:

            return True
        else:

            return False

    else:

        return False


def create_account(username, password, phonenumber):
    # create account and open a new row in user
    if not check_format(password):
        return False
    sql.execute("select * from user where Username='%s'" % username)
    check = sql.fetchall()
    if check == ():
        sha256 = hashlib.sha256()
        sha256.update(password.encode('utf-8'))
        hash_password = sha256.hexdigest()

        sql.execute("INSERT INTO user(Username,Password,Phonenumber)VALUES ('%s', '%s', %s)"% (username, hash_password, phonenumber))
        sql.connection.commit()

        return True
    else:

        return False
    # verify phone number


def forget_password(username, password, phonenumber):
    # reset password
    if not check_format(password):
        return False
    sql.execute("select Username from user")
    users = sql.fetchall()

    all = []
    for each in users:
        each = "".join("%s" % i for i in each)
        all.append(each)

    if str(username) in all:
        sql.execute("select Phonenumber from user where Username='%s'" % username)
        get = sql.fetchone()
        get = "".join("%s" % i for i in get)
        get = int(get)

        if get == int(phonenumber):
            sha256 = hashlib.sha256()
            sha256.update(password.encode('utf-8'))
            hash_password = sha256.hexdigest()
            sql.execute("update user set Password='%s' WHERE Username = '%s'" % (hash_password, username))
            sql.connection.commit()
            return True
        else:
            return False
    else:
        return False


def check_format(mystr):
    # check format of the password
    a = re.compile(r'[0-9a-zA-Z]{6,20}')
    if a.fullmatch(mystr) is None:
        return False
    return True


def name_to_code(user_name):
    sql.execute("select Usercode from user where Username='%s'"% user_name)
    id = sql.fetchone()
    id = "".join("%s" % i for i in id)
    id = int(id)

    return id


def get_all_futures():
    sql.execute("select Futurecode from future")
    all_futures = sql.fetchall()
    names = []
    for EACH in all_futures:
        EACH = "".join(EACH)
        names.append(EACH)

    return names


def display_future_name(code):
    sql.execute("select Futurename from future where Futurecode='%s'" % code)
    fcode = sql.fetchone()
    fcode = "".join(fcode)

    return fcode


def change_userinfo(userid, threshold, phonenumber):
    sql.execute("update user set Threshold=%s, Phonenumber=%s WHERE Usercode = %s" % (threshold, phonenumber, userid))
    sql.connection.commit()
    # need to verify phonenumber


def display_userinfo(userid):
    sql.execute("select Phonenumber, Threshold from user where Usercode=%s" % userid)
    info = sql.fetchall()
    info = info[0]

    pt = []
    for COUNT in info:
        pt.append(COUNT)
    return pt


def display_future(future_code, date):
    # return general information(diagram making)
    sql.execute("select open_price,high_price,low_price,close_price,volume from futurelive where Future_Futurecode='%s' and update_time<='%s' order by update_time desc limit 1 "
                % (future_code, date))
    prices = sql.fetchall()
    prices = prices[0]

    new_prices = []
    for COUNT in range(0, 4):
        price = float(prices[COUNT])
        new_prices.append(price)
    
    new_prices.append(prices[4])

    return new_prices


def generate_report(userid, futurecode):
    latest = display_future(futurecode, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    new_price = latest[3]

    now = datetime.datetime.now()
    yesterday = display_future(futurecode, (now - datetime.timedelta(hours=now.hour)).strftime('%Y-%m-%d %H:%M:%S'))
    last_price = yesterday[3]

    percentage = ((new_price - last_price) / last_price) * 100  # transfer into percentage
    # 3 digits
    percentage = round(percentage, 3)

    # generate daily report for each future
    sql.execute("select to_sell, to_buy, current_price from transaction where User_Usercode=%s and Future_Futurecode='%s'" % (userid, futurecode))
    transactions = sql.fetchall()
    #return empty information when there's no transaction
    if transactions == ():
        return [new_price, last_price, 0, percentage, 0, 0, 0]

    all_tran = []
    for trade in transactions:
        each_tran = []
        for peres in trade:
            each_tran.append(peres)
        all_tran.append(each_tran)

    total_rev = 0
    total_val = 0
    own_buy = 0
    own_sell = 0
    for each in all_tran:
        minus = new_price-each[2]
        buy = each[1]*minus
        sell = each[0]*(-minus)
        revenue = buy+sell
        total_rev += revenue

        own_buy += each[1]
        own_sell += each[0]

        total_val += new_price*(each[1]+each[0])


    return [new_price, last_price, total_rev, percentage, total_val, own_sell, own_buy]


def daily_report(userid):
    all_futures = get_all_futures()

    rev = 0
    val = 0
    for EACH in all_futures:
        report = generate_report(userid, EACH)
        rev += report[2]
        val += report[4]

    return [rev, val]


def generate_prediction(future_code):
    # make sure there's data more than 9 days
    # make use of regression line
    days = []
    for COUNT in range(1, 10):
        days.append((datetime.datetime.today()-datetime.timedelta(COUNT)).strftime('%Y-%m-%d %H:%M:%S'))

    all_prices = []
    for each_day in days:
        price = display_future(future_code, each_day)
        all_prices.append(price[3])

    total = 0
    for COUNT in range(0, 3):
        total += all_prices[COUNT]
    average_3 = total / 3

    total = 0
    for COUNT in range(0, 9):
        total += all_prices[COUNT]
    average_9 = total / 9

    sql.execute("select M1, M2, C from future where Futurecode='%s'" % future_code)
    peres = sql.fetchall()[0]

    all_peres = []
    for each in peres:
        each = float(each)
        all_peres.append(each)
    m1 = all_peres[0]
    m2 = all_peres[1]
    c = all_peres[2]
    pre_price = average_3*m1 + average_9*m2 + c

    return pre_price


def abnormal_check(userid, future_code):#加入更多策略
    sql.execute("select Threshold from user where Usercode=%s" % userid)
    thres = sql.fetchone()[0]
    if generate_report(userid, future_code)[3] > thres:
        return True
    else:
        return False


def trade(future_code, userid, quantity_sell, quantity_buy):
    currentP = display_future(future_code, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))[3]
    sql.execute("INSERT INTO transaction(User_usercode, Future_Futurecode, to_sell, to_buy, current_price, operation_time)VALUES (%s, '%s', %s, %s, %s, '%s')" % (
        userid, future_code, quantity_sell, quantity_buy, currentP, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    sql.connection.commit()


def update_data(future_code):
    # update live data and store in the database
    data = real_time_update.update_live(future_code)

    sql.execute("insert ignore into futurelive(update_time,Future_Futurecode,open_price,high_price,low_price,close_price,volume)\
                values('%s', '%s', %s, %s, %s, %s, %s) "\
                % (data[0], future_code, data[1], data[2], data[3], data[4], data[5]))
    sql.connection.commit()


def looping_update_check():
    print('check')

    sql.execute("select Usercode from user")
    all = sql.fetchall()
    all_users = []
    for each in all:
        each = "".join("%s" % i for i in each)
        each = int(each)
        all_users.append(each)

    all_futures = get_all_futures()

    for EACH in all_futures:
        update_data(EACH)

    for each_user in all_users:
        sql.execute("select Future_Futurecode from transaction where User_Usercode=%s" % (each_user))
        all = sql.fetchall()
        futures_own = []
        for each in all:
            each = "".join("%s" % i for i in each)
            futures_own.append(each)
        for each_future in futures_own:
            if abnormal_check(each_user, each_future):
                print('abnormal')
                mobile.send_warning(each_user, each_future)


def looping_report():
    print('report')
    sql.execute("select Usercode from user")
    all = sql.fetchall()
    all_users = []
    for each in all:
        each = "".join("%s" % i for i in each)
        each = int(each)
        all_users.append(each)
    print(all_users)
    for each in all_users:
        content = daily_report(each)
        print(content)
        mobile.send_report(each, content[0], content[1])


def looping_delete_data():
    print('delete')
    # delete expire data
    twoweeks = (datetime.datetime.today()-datetime.timedelta(14)).strftime('%Y-%m-%d %H:%M:%S')
    sql.execute("DELETE FROM futurelive WHERE update_time<'%s'" % twoweeks)
    sql.connection.commit()

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    # add task
    scheduler.add_job(looping_update_check, 'interval', minutes=2)
    scheduler.add_job(looping_report, 'interval', days=1)
    scheduler.add_job(looping_delete_data, 'interval', days=1)

    scheduler.start()

    while True:
        time.sleep(5)