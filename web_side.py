from flask import Flask, request, render_template, redirect, url_for, flash, session
import main
import datetime

app = Flask(__name__)
app.secret_key = '123456'


@app.route('/', methods=['GET', 'POST'])
def login():
    error = ''
    if request.method == 'POST':
        th = request.form["login"]
        if th == "Log in":
            if main.check_password(request.form["username"], request.form["password"]):
                # store username
                session["username"] = request.form["username"]
                return redirect(url_for("home"))
            else:
                error = 'incorrect username or password！'

        if th == "Create account":
            # store destination
            session['veri_from'] = "login"
            session['veri_require'] = "create_account"
            return redirect(url_for("verification"), code=302)
            # mobile verification

        if th == "Forget password":
            # store destination
            session['veri_from'] = "login"
            session['veri_require'] = "forget_password"
            return redirect(url_for("verification"), code=302)
            # mobile verification

    return render_template('login_page.html', error=error)

@app.route('/create', methods=['GET', 'POST'])
def create_account():
    error = ''
    if request.method == 'POST':
        click = request.form['create']
        if click == 'return to login':
            return redirect(url_for('login'))



        if click == 'create account':
            p1 = request.form['password']
            p2 = request.form['password_repeat']
            if p1 == p2:
                username = request.form['username']
                number = session.get('correct_mobile')
                invit = request.form['invite_code']
                if invit == '2021CSIA':
                   if main.create_account(username, p2, number):
                       return redirect(url_for('login'))
                   else:
                       error = 'unaviliable username or password'
                else:
                    error = 'wrong invitation code'
            else:
                error = 'please make sure you are entering the same password for two times!'

    return render_template('create_account.html', error=error)

@app.route('/reset', methods=['GET', 'POST'])
def forget_password():
    error = ''
    if request.method == 'POST':
        click = request.form['reset']
        if click == 'return to login':
            return redirect(url_for('login'))

        if click == 'Confirm':
            p1 = request.form['password']
            p2 = request.form['password_repeat']
            if p1 == p2:
                username = request.form['username']
                number = session['correct_mobile']
                if main.forget_password(username, p2, number): # notify success
                    return redirect(url_for('login'))
                else:
                    error = 'incorrect username or phone number, please try again'
            else:
                error = 'please make sure you are entering the same password for two times!'

    return render_template('password_reset.html', error=error)

@app.route('/verify', methods=['GET', 'POST'])
def verification():
    default = None
    error = ''
    if request.method == 'POST':
        phonenumber = request.form["phonenumber"]
        click = request.form["verify"]

        if click == "return to last page":
            return redirect(url_for(session['veri_from']))

        if click == "Send":
            main.mobile.send_veri(phonenumber)
            default = phonenumber
            error = 'successfully send'

        if click == "Confirm":
            veri_code = request.form["veri_code"]
            print(phonenumber, veri_code)
            if main.mobile.check_mobile(phonenumber, veri_code):
                session['correct_mobile'] = phonenumber
                return redirect(url_for(session['veri_require']))
            else:
                default = phonenumber
                error = 'incorrect verification code, please try again'

    return render_template('veri_code.html', error=error, dnumber=default)

@app.route('/home', methods=['GET', 'POST'])
def home():
    username = session['username']
    userid = main.name_to_code(username)

    user_info = [username]

    names = main.get_all_futures()

    # for each future
    futures_info = []
    for EACH in names:
        report = main.generate_report(userid, EACH)

        # add total quantity hold
        total_hold = report[5]+report[6]
        report.append(total_hold)
        # add code
        report.append(EACH)
        # add chinese name
        name = main.display_future_name(EACH)
        report.append(name)
        futures_info.append(report)

    # for each day
    daily = main.daily_report(userid)
    user_info.append(daily[0])
    user_info.append(daily[1])

    print(futures_info)
    print(user_info)

    # futures_info=[[new_price, last_price, total_rev, percentage, total_val, own_sell, own_buy, total_hold, future_code, future_name],[],[]]
    # user_info=[username, total_rev, total_val]


    return render_template('home_page.html', mainpage_info=user_info, futures_info=futures_info)


@app.route('/home/<future>', methods=['GET', 'POST'])
def detail(future):
    username = session['username']
    userid = main.name_to_code(username)

    name = main.display_future_name(future)
    future_detail = [future, name]

    # get historical data
    days = []
    all_prices = []
    # last 14 days
    for COUNT in range(13, -1, -1):
        each_day = (datetime.datetime.today() - datetime.timedelta(COUNT)).strftime("%Y-%m-%d 23:00:00")
        price = main.display_future(future, each_day)
        all_prices.append(price[3])
        days.append(each_day[:10])

    future_report = main.display_future(future, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    future_detail.append(future_report)     # get the newest price

    prediction = main.generate_prediction(future)
    future_detail.append(prediction) # add prediction value

    personal_report = main.generate_report(userid, future)
    future_detail.append(personal_report) # individual information

    #futured=[future,name,[open_price,high_price,low_price,close_price], prediction, [new_price, last_price, total_rev, percentage, total_val, own_sell, own_buy]]

    if request.method == 'POST':
        click = request.form['detail']
        if click == 'Trade':
            return redirect(url_for('trade', future=future))
        if click == 'return to home page':
            return redirect(url_for('home'))

    return render_template('detail_page.html', futured=future_detail, x_data=days, y_data=all_prices)


@app.route('/home/<future>/trade', methods=['GET', 'POST'])
def trade(future):
    note = ''
    username = session['username']
    userid = main.name_to_code(username)
    # display information
    name = main.display_future_name(future)
    trade_prices = [name]

    info = main.generate_report(userid, future)
    trade_prices.append(info)    # individual information

    if request.method == 'POST':
        click = request.form['trade']
        sell = request.form['selling']
        buy = request.form['buying']
        # record
        if click == 'record transaction':
            print("record")
            main.trade(future, userid, int(sell), int(buy))
            return redirect(url_for('trade', future=future))

        if click == 'return to home page':
            return redirect(url_for('home'))

        if click == 'back to detail':
            return redirect(url_for('detail', future=future))

    return render_template('trading_page.html', trade=trade_prices, statue=note)


@app.route('/home/settings', methods=['GET', 'POST'])
def setting():
    error = ''
    username = session['username']
    userid = main.name_to_code(username)

    raw = main.display_userinfo(userid) # raw data

    if request.method == 'POST':
        click = request.form['settings']
        threshold = request.form['thres']
        phonenumber = request.form['phonenumber']
        # return home
        if click == 'return to home page':
            print("return")
            return redirect(url_for('home'))
        # confirm change
        if click == 'Confirm':
            print("confirm")
            main.change_userinfo(userid, int(threshold), int(phonenumber))
            # add verification
            error = 'success'
            return redirect(url_for('setting'))

    return render_template('settings_page.html', default=raw, error=error)


if __name__ =="__main__":
    app.run(debug=True, port=8080)
