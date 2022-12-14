import time
from datetime import date

from flask import Flask, request, render_template, g, redirect, Response, session
import db

app = Flask(__name__)
engine = db.getEngine()
app.secret_key = 'BROADWAY_SECRET_KEY'


@app.route('/')
def index():
    discounts = []
    cursor = g.conn.execute("SELECT * FROM Discounts")
    for entry in cursor:
        discount = dict()
        discount['code'] = entry[0]
        discount['amount'] = int(float(entry[2]))
        discount['type'] = entry[1]
        discounts.append(discount)
    session['discounts'] = discounts
    return render_template("index.html", name="Yaochen Shen")


@app.route('/submitAvailabilityRequestByName', methods=['POST'])
def submitAvailabilityRequestByName():
    name = request.form.get('byName')
    # cursor = g.conn.execute(
    #     "SELECT name, row, seat, section, theatre_name as Theatre, cdate as Date, ctime as Time, price, temp1.location_id, temp2.sid, temp1.ccid FROM (AvailableOn a inner join (Select cid as ccid, cdate, ctime From Calendars) cal ON a.cid = cal.ccid) temp1 inner join (Select location_id, theatre_name, l.row_id as row, l.seat_id as seat, l.section, name, s.sid From Locations l Left join (SELECT * FROM shows WHERE name ='{name1}') s on l.sid = s.sid) temp2 ON temp1.location_id = temp2.location_id WHERE order_number is Null and temp2.name ='{name1}'".format(
    #         name1=name))
    cursor = g.conn.execute(
        "SELECT name, row, seat, section, theatre_name as Theatre, cdate as Date, ctime as Time, price, temp1.location_id, temp2.sid, temp1.ccid FROM (AvailableOn a inner join (Select cid as ccid, cdate, ctime From Calendars) cal ON a.cid = cal.ccid) temp1 inner join (Select location_id, theatre_name, l.row_id as row, l.seat_id as seat, l.section, name, s.sid From Locations l Left join (SELECT * FROM shows WHERE name =%s) s on l.sid = s.sid) temp2 ON temp1.location_id = temp2.location_id WHERE order_number is Null and temp2.name =%s",
        name, name)
    shows = []
    for entry in cursor:
        # print(entry)

        show = dict()
        show['name'] = entry[0]
        show['row'] = entry[1]
        show['seat'] = entry[2]
        show['section'] = entry[3]
        show['theatre'] = entry[4]
        show['date'] = entry[5]
        show['time'] = entry[6]
        show['price'] = entry[7]

        show['id'] = str(entry[8]) + "," + str(entry[9]) + "," + str(entry[10]) + "," + str(entry[7])

        shows.append(show)

    cursor.close()
    context = dict(shows=shows)
    return render_template("find-tickets-process/availability.html", **context)
    # return str(shows)


@app.route('/submitAvailabilityRequestByDate', methods=['POST'])
def submitAvailabilityRequestByDate():
    if request.method == "POST":
        from_date = request.form.get('fromDate')
        to_date = request.form.get('toDate')
        shows = []
        cursor = g.conn.execute(
            "Select name as Show, row, seat, section, theatre_name as Theatre, cdate as Date, ctime as Time, price,  temp1.location_id, temp2.sid, temp1.ccid From (AvailableOn a inner join (Select cid as ccid, cdate, ctime From Calendars c Where c.cdate between CAST(%s AS DATE) and CAST(%s AS DATE)) cal on a.cid = cal.ccid) temp1 Left join (Select location_id, theatre_name, l.row_id as row, l.seat_id as seat, l.section, name, s.sid From Locations l Left join Shows s on l.sid = s.sid) temp2 on temp1.location_id = temp2.location_id Where order_number is Null",
            from_date, to_date)
        for entry in cursor:
            # print(entry)

            show = dict()
            show['name'] = entry[0]
            show['row'] = entry[1]
            show['seat'] = entry[2]
            show['section'] = entry[3]
            show['theatre'] = entry[4]
            show['date'] = entry[5]
            show['time'] = entry[6]
            show['price'] = entry[7]

            show['id'] = str(entry[8]) + "," + str(entry[9]) + "," + str(entry[10]) + "," + str(entry[7])

            shows.append(show)

        cursor.close()
        context = dict(shows=shows)
        return render_template("find-tickets-process/availability.html", **context)


@app.route('/fillPaymentInfo', methods=['POST'])
def fillPaymentInfo():
    chkbox_values = request.form.getlist('chkbox')
    coupon = request.form.get("coupon")
    print(chkbox_values)
    print(coupon)
    session['chkbox_values'] = chkbox_values
    session['coupon'] = coupon
    return render_template("find-tickets-process/paymentInfo.html")


@app.route('/completeOrder', methods=['POST'])
def completeOrder():
    chkbox_values = session['chkbox_values']
    coupon = session['coupon'].upper()
    session.pop('chkbox_values', default=None)
    session.pop('coupon', default=None)
    c_name = request.form.get('cName')
    c_email = request.form.get('cEmail')
    c_phone = request.form.get('cPhone')
    c_date = date.today()
    t = time.localtime()
    c_time = time.strftime("%H:%M:%S", t)
    c_payment = request.form.getlist('paymentM')

    c_info = []
    c_info_dict = dict()
    c_info_dict['name'] = c_name
    c_info_dict['email'] = c_email
    c_info_dict['phone'] = c_phone
    c_info.append(c_info_dict)

    # print(chkbox_values)
    # print(c_name)
    # print(c_email)
    # print(c_phone)
    # print(c_date)
    # print(c_time)
    # print(c_discount)
    # if c_payment != []:
    #     print(c_payment[0])
    # get customer id (identify by email + phone) -> create an order --> get order id --> create an suborder
    # cursor = g.conn.execute("SELECT customerId FROM customers WHERE email ='{c_email}' and phone ='{c_phone}'".format(c_email=c_email, c_phone=c_phone))
    cursor = g.conn.execute(
        "SELECT customerId FROM customers WHERE email =%s and phone =%s", c_email, c_phone)
    if cursor.rowcount == 0:
        # g.conn.execute("INSERT INTO customers(name, email, phone) VALUES ('{c_name}', '{c_email}', '{c_phone}')".format(c_name=c_name, c_email=c_email, c_phone=c_phone))
        g.conn.execute("INSERT INTO customers(name, email, phone) VALUES (%s, %s, %s)",
                       c_name, c_email, c_phone)
    cursorN = g.conn.execute(f"SELECT * FROM customers WHERE email = '{c_email}' and phone = '{c_phone}'")
    customerId = -1
    for entry in cursorN:
        customerId = entry[0]

    # check if invalid coupon
    coupon_stat = []
    cursor = g.conn.execute(f"SELECT * FROM Discounts WHERE discount_code = '{coupon}'")
    # print(cursor.fetchone())
    if cursor.rowcount == 0:
        g.conn.execute(
            "INSERT INTO Orders(customerId, order_date, order_time, payment_method) VALUES (%s, %s, %s, %s)",
            customerId, c_date, c_time, c_payment[0])
    else:
        coupon_stat = cursor.fetchone()
        g.conn.execute(
            "INSERT INTO Orders(customerId, discount_code, order_date, order_time, payment_method) VALUES (%s, %s, %s, %s, %s)",
            customerId, coupon_stat[0], c_date, c_time, c_payment[0])


    # if c_payment != [] and c_discount != '':
    #     # g.conn.execute("INSERT INTO Orders(customerId, discount_code, order_date, order_time, payment_method) VALUES ('{customerId}', '{discount_code}', '{order_date}', '{order_time}', '{payment_method}')".format(customerId=customerId,discount_code=c_discount,order_date=c_date, order_time=c_time, payment_method = c_payment[0]))
    #     g.conn.execute(
    #         "INSERT INTO Orders(customerId, discount_code, order_date, order_time, payment_method) VALUES (%s, %s, %s, %s, %s)",
    #         customerId, c_discount, c_date, c_time, c_payment[0])
    # elif c_payment != [] and c_discount == '':
    #     g.conn.execute(
    #         "INSERT INTO Orders(customerId, order_date, order_time, payment_method) VALUES (%s, %s, %s, %s)",
    #         customerId, c_date, c_time, c_payment[0])
    #     # g.conn.execute("INSERT INTO Orders(customerId, order_date, order_time, payment_method) VALUES ('{customerId}', '{order_date}', '{order_time}', '{payment_method}')".format(customerId=customerId,order_date=c_date, order_time=c_time, payment_method = c_payment[0]))
    # elif c_payment == [] and c_discount != '':
    #     g.conn.execute(
    #         "INSERT INTO Orders(customerId, discount_code, order_date, order_time) VALUES (%s, %s, %s, %s)",
    #         customerId, c_discount, c_date, c_time)
    #     # g.conn.execute("INSERT INTO Orders(customerId, discount_code, order_date, order_time) VALUES ('{customerId}', '{discount_code}', '{order_date}', '{order_time}')".format(customerId=customerId, discount_code=c_discount, order_date=c_date, order_time=c_time))
    # else:
    #     g.conn.execute(
    #         "INSERT INTO Orders(customerId, order_date, order_time) VALUES (%s, %s, %s)",
    #         customerId, c_date, c_time)
    #     # g.conn.execute("INSERT INTO Orders(customerId, order_date, order_time) VALUES ('{customerId}', '{order_date}', '{order_time}')".format(customerId=customerId, order_date=c_date, order_time=c_time))

    cursorO = g.conn.execute(
        "SELECT order_number FROM Orders WHERE customerId =%s and order_date =%s and order_time =%s",
        customerId, c_date, c_time)
    order_number = cursorO.fetchone()[0]
    # for entry in cursorO:
    #     order_number = entry[0]
    # print(order_number)
    price_list = []
    for v in chkbox_values:
        v_list = [int(item) if item.isdigit() else item for item in v.split(',')]
        price_list.append(int(float(v_list[3])))
        cid = v_list[2]
        location_id = v_list[0]
        # g.conn.execute("INSERT INTO SubOrders(order_number, cid, location_id) VALUES ('{order_number}', '{cid}', '{location_id}')".format(order_number=order_number, cid=cid, location_id=location_id))
        g.conn.execute(
            "INSERT INTO SubOrders(order_number, cid, location_id) VALUES (%s, %s, %s)",
            order_number, cid, location_id)

    # cursorTest = g.conn.execute("SELECT * FROM SubOrders")
    # for entry in cursorTest:
    #     print(entry[0])
    origin_price = sum(price_list)
    final_price = sum(price_list)
    if len(coupon_stat) != 0:
        if coupon_stat[1] == 'DiscountPercent':
            final_price = final_price * (100-int(float(coupon_stat[2])))/100
        else:
            final_price = final_price - len(price_list) * int(float(coupon_stat[2]))

    c_info_dict['order_id'] = order_number
    c_info_dict['origin_price'] = origin_price
    c_info_dict['final_price'] = final_price
    context = dict(customers=c_info)
    return render_template("find-tickets-process/orderComplete.html", **context)


@app.route('/allShows', methods=['GET'])
def allShows():
    cursor = g.conn.execute("SELECT * FROM shows")
    shows = []
    for entry in cursor:
        show = dict()
        show['name'] = entry[1]
        show['description'] = entry[2]
        shows.append(show)

    cursor.close()
    context = dict(shows=shows)
    return render_template("all-shows-info/showInfoResults.html", **context)


@app.route('/prevOrders', methods=['GET'])
def prevOrders():
    return render_template("find-previous-orders/preOrderSearch.html")


@app.route('/findByOrderNumber', methods=['POST'])
def findByOrderNumber():
    order_number = request.form.get('ByOrderNumber')
    # cursor = g.conn.execute(
    #     f"SELECT order_date, order_time, row_id, seat_id, theatre_name, section, cdate, ctime, name, Onum FROM (((SELECT *, o.order_number as Onum FROM orders o LEFT JOIN SubOrders so on o.order_number = so.order_number WHERE o.order_number = {order_number}) AS temp1 INNER JOIN Locations l on temp1.location_id = l.location_id) temp2 INNER JOIN Calendars c on temp2.cid = c.cid) temp3 INNER JOIN Shows s on temp3.sid = s.sid")
    cursor = g.conn.execute(
        "SELECT order_date, order_time, row_id, seat_id, theatre_name, section, cdate, ctime, name, Onum FROM (((SELECT *, o.order_number as Onum FROM orders o LEFT JOIN SubOrders so on o.order_number = so.order_number WHERE o.order_number =%s) AS temp1 INNER JOIN Locations l on temp1.location_id = l.location_id) temp2 INNER JOIN Calendars c on temp2.cid = c.cid) temp3 INNER JOIN Shows s on temp3.sid = s.sid",
        order_number)
    orders = []
    for entry in cursor:
        order = dict()
        order['o_date'] = entry[0]
        order['o_time'] = entry[1]
        order['row'] = entry[2]
        order['seat'] = entry[3]
        order['theatre'] = entry[4]
        order['section'] = entry[5]
        order['s_date'] = entry[6]
        order['s_time'] = entry[7]
        order['show'] = entry[8]
        order['order_number'] = entry[9]
        orders.append(order)
    cursor.close()
    context = dict(orders=orders)
    return render_template("find-previous-orders/preOrderResults.html", **context)


@app.route('/findByEmail', methods=['POST'])
def findByByEmail():
    email = request.form.get('ByEmail')
    # cursor = g.conn.execute(
    #     f"SELECT order_date, order_time, row_id, seat_id, theatre_name, section, cdate, ctime, s.name, Onum FROM (SELECT *, Orders.order_number as Onum FROM Orders LEFT JOIN SubOrders on Orders.order_number = SubOrders.order_number) AS TEMP1 INNER JOIN (SELECT * FROM Customers WHERE Customers.email = '{email}') Cust on TEMP1.customerid = Cust.customerid INNER JOIN Locations l on TEMP1.location_id = l.location_id INNER JOIN Calendars c on TEMP1.cid = c.cid LEFT JOIN Shows s on l.sid = s.sid")
    cursor = g.conn.execute(
        "SELECT order_date, order_time, row_id, seat_id, theatre_name, section, cdate, ctime, s.name, Onum FROM (SELECT *, Orders.order_number as Onum FROM Orders LEFT JOIN SubOrders on Orders.order_number = SubOrders.order_number) AS TEMP1 INNER JOIN (SELECT * FROM Customers WHERE Customers.email =%s) Cust on TEMP1.customerid = Cust.customerid INNER JOIN Locations l on TEMP1.location_id = l.location_id INNER JOIN Calendars c on TEMP1.cid = c.cid LEFT JOIN Shows s on l.sid = s.sid",
        email)
    orders = []
    for entry in cursor:
        order = dict()
        order['o_date'] = entry[0]
        order['o_time'] = entry[1]
        order['row'] = entry[2]
        order['seat'] = entry[3]
        order['theatre'] = entry[4]
        order['section'] = entry[5]
        order['s_date'] = entry[6]
        order['s_time'] = entry[7]
        order['show'] = entry[8]
        order['order_number'] = entry[9]
        orders.append(order)
    cursor.close()
    context = dict(orders=orders)
    return render_template("find-previous-orders/preOrderResults.html", **context)


# test purpose function
@app.route('/database')
def db():
    cursor = g.conn.execute("SELECT * FROM customers")
    users = []
    for entry in cursor:
        user = dict()
        user['name'] = entry[1]
        user['email'] = entry[2]
        user['number'] = entry[3]
        users.append(user)
    cursor.close()
    context = dict(users=users)
    return render_template("random/users.html", **context)


@app.before_request
def before_request():
    try:
        g.conn = engine.connect()
    except:
        print("uh oh, problem connecting to database")
        g.conn = None


@app.teardown_request
def teardown_request(exception):
    try:
        g.conn.close()
    except:
        pass


if __name__ == "__main__":
    import click


    @click.command()
    @click.option('--debug', is_flag=True)
    @click.option('--threaded', is_flag=True)
    @click.argument('HOST', default='0.0.0.0')
    @click.argument('PORT', default=8111, type=int)
    def run(debug, threaded, host, port):
        """
    This function handles command line parameters.
    Run the server using
        python server.py
    Show the help text using
        python server.py --help
    """

        HOST, PORT = host, port
        print("running on %s:%d" % (HOST, PORT))
        app.run(host=HOST, port=PORT, debug=True, threaded=threaded)


    run()
