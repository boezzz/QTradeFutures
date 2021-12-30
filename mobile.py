import MySQLdb
import string
import random
import requests


db = MySQLdb.connect(host='localhost', port=3306, user='root', passwd='619000ab', db='futures', charset='utf8')
sql = db.cursor()

def send_mobile(phone_number, text):
    # external api
    apikey = "a7f38398b04886e1377b44e6be14455d"
    params = {"apikey": apikey, "text": text, "mobile": str(phone_number)}
    # send
    requests.post("https://sms.yunpian.com/v2/sms/single_send.json", params)

def send_veri(phone_number):
    # generate verification code
    seeds = string.digits
    random_str = random.choices(seeds, k=4)
    code = "".join(random_str)
    sql.execute("INSERT INTO verification(phonenumber,code)VALUES (%s, %s) on duplicate key update code= %s"
                % (phone_number, code, code))
    sql.connection.commit()

    # format
    text = "【天昇环保】您的验证码是%s. Your verification code is %s." % (code, code)
    send_mobile(phone_number, text)

def check_mobile(phone_number, code):
    # check if the codes match
    sql.execute("select phonenumber from verification")
    allnum = sql.fetchall()
    numbers = []
    for each in allnum:
        each = "".join("%s" % i for i in each)
        each = int(each)
        numbers.append(each)


    if int(phone_number) in numbers:

        sql.execute("select code from verification where phonenumber=%s" % phone_number)
        cor_code = sql.fetchone()[0]

        if cor_code == int(code):
            # refresh code
            sql.execute("delete from verification where phonenumber=%s" % phone_number)
            sql.connection.commit()
            return True
        else:
            return False
    else:

        return False


def send_report(userid, rev, val):
    sql.execute("select Username, Phonenumber from user where Usercode=%s" % userid)
    getall = sql.fetchall()[0]

    name = getall[0]
    phone_number = getall[1]

    text = "【天昇环保】用户%s，您的累计增加值为%s，累计持有额金为%s。User %s,Your revenue is %s,total value hold is %s." % (name, rev, val, name, rev, val)

    send_mobile(phone_number, text)

def send_warning(userid, future_code):
    sql.execute("select Futurename from future where Futurecode='%s'" % future_code)
    name = sql.fetchone()
    name = "".join(name)

    sql.execute("select Phonenumber from user where Usercode=%s" % userid)
    phone_number = sql.fetchone()[0]

    text = "【天昇环保】%s价格波动异常,请检查。We detected a fluctuation in prices of %s,please check." % (name, name)
           
    send_mobile(phone_number, text)