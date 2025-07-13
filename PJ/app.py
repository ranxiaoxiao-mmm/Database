from flask import Flask, render_template, request, redirect, session
import pymysql
import datetime
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key'

#查询电影数据
def get_featured_movies():
    # 连接数据库
    conn = pymysql.connect(host='localhost', port=3306, user='root', password='20050306', charset='utf8', db='cinema_ticket')
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    # 查询所有电影信息
    cursor.execute("SELECT id, title, state, poster FROM movie ")
    featured_movies = cursor.fetchall()
    cursor.close()
    conn.close()
    return featured_movies

#网站首页
@app.route('/cinema_ticket/home')
def home():
    featured_movies = get_featured_movies()  # 获取电影数据
    # 渲染模板并传递电影信息
    return render_template('home.html', featured_movies=featured_movies)

#电影总览
@app.route('/cinema_ticket/movies')
def movies():
    featured_movies = get_featured_movies()  # 获取电影数据
    # 将 featured_movies 转换为列表并逆序
    featured_movies = list(reversed(featured_movies))
    # 渲染模板并传递电影信息
    return render_template('movies.html', featured_movies=featured_movies)


#个人中心
@app.route('/cinema_ticket/vip')
def vip():
    user_id = session.get('user_id')
    if not user_id:
        return "请登录或注册会员账户"

    # 连接数据库
    conn = pymysql.connect(host='localhost', port=3306, user='root', password='20050306', charset='utf8', db='cinema_ticket')
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    # 获取用户信息
    cursor.execute("SELECT name, phone, email FROM users WHERE id = %s", (user_id,))
    user_info = cursor.fetchone()
    # 获取订单信息
    cursor.execute("SELECT * FROM `order` WHERE user_id = %s", (user_id,))
    orders = cursor.fetchall()

    watchlist = []
    orderlist = []
    for order in orders:
        screen_id = order['screen_id']
        state = order['state']
        total_amount = order['total_amount']
        seat_id = order['seat_id']
        employee_id = order['employee_id']
        order_id = order['id']
        cursor.execute("SELECT movie_id, start_time, hall_id FROM screening WHERE id = %s", (screen_id,))
        screening_info = cursor.fetchone()
        cursor.execute("SELECT name FROM employee WHERE id = %s", (employee_id,))
        employee_info = cursor.fetchone()

        # 新增：处理座位名称
        seat_name = ""
        if seat_id:
            seat_names = []
            # 支持seat_id为字符串或列表（如json数组）
            import json
            try:
                seat_id_list = json.loads(seat_id) if isinstance(seat_id, str) and seat_id.startswith("[") else [seat_id]
            except Exception:
                seat_id_list = [seat_id]
            for sid in seat_id_list:
                cursor.execute("SELECT `row`, `column` FROM seat WHERE id = %s", (sid,))
                seat_info = cursor.fetchone()
                if seat_info:
                    seat_names.append(f"{seat_info['row']}排{seat_info['column']}座")
            seat_name = "、".join(seat_names)
        else:
            seat_name = ""

        if screening_info:
            movie_id = screening_info['movie_id']
            start_time = screening_info['start_time']
            hall_id = screening_info['hall_id']
            cursor.execute("SELECT name FROM movie_hall WHERE id = %s", (hall_id,))
            hall_info = cursor.fetchone()
            cursor.execute("SELECT title, poster FROM movie WHERE id = %s", (movie_id,))
            movie_info = cursor.fetchone()
            if movie_info and state == '已支付':
                watchlist.append({
                    'title': movie_info['title'],
                    'poster': movie_info['poster'],
                    'start_time': start_time
                })
            orderlist.append({
                    'title': movie_info['title'],
                    'start_time': start_time,
                    'hall_name': hall_info['name'],
                    'seat_id': seat_id,
                    'total_amount': total_amount,
                    'employee_name': employee_info['name'],
                    'state': state,
                    'screen_id': screen_id,
                    'order_id': order_id,
                    'seat_name': seat_name
            })

    cursor.close()
    conn.close()

    return render_template('vip.html', user_info=user_info, watchlist=watchlist, orderlist = orderlist, order_num=len(orders), watchlist_num = len(watchlist))


#关于我们
@app.route('/cinema_ticket/about')
def about():
    return render_template('about.html')


#搜索电影
@app.route('/cinema_ticket/search')
def search_movie():
    title = request.args.get('title')
    if not title:
        return "请输入电影名称"
    # 连接数据库
    conn = pymysql.connect(host='localhost', port=3306, user='root', password='20050306', charset='utf8', db='cinema_ticket')
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    cursor.execute("SELECT id FROM movie WHERE title = %s", (title,))
    movie = cursor.fetchone()
    cursor.close()
    conn.close()
    if movie:
        return redirect(f"/cinema_ticket/movie_single?id={movie['id']}")
    else:
        return "未找到该电影，请检查名称是否正确。"

#用户注册
@app.route('/cinema_ticket/register', methods=['GET','POST'])
def cinema_register():
    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        phone = request.form.get('phone')
        email = request.form.get('email')

        # 检查两次密码是否一致
        if password != password_confirm:
            return "两次输入的密码不一致，请重新输入！"
        # 如果 email 未填写，设置为 None
        if not email:
            email = None
        # 检查必填项目
        if not name or not password or not phone:
            return "请填写所有必填项！"
        # 检查手机号格式
        if len(phone) != 11 or not phone.isdigit():
            return "手机号格式不正确，请重新输入！"

# 连接mysql
        conn = pymysql.connect(host = 'localhost', port = 3306, user = 'root', password = '20050306', charset = 'utf8', db = 'cinema_ticket')
        cursor = conn.cursor(cursor = pymysql.cursors.DictCursor)
        sql = "insert into users(name, password,phone,email) values(%s, %s, %s, %s)"
        cursor.execute(sql, (name,password,phone,email) )
        conn.commit()
        cursor.close()
        conn.close()
    
    return render_template('register.html')

#用户登录
@app.route('/cinema_ticket/login')
def cinema_login():
    return render_template('login.html')

@app.context_processor
def inject_user():
    return dict(username=session.get('username'))

#用户名登录
@app.route('/cinema_ticket/login_pwd', methods=['GET','POST'])
def login_pwd():
    if request.method == 'POST':
        name = request.form.get('username')
        password = request.form.get('password')

        # 检查必填项目
        if not name or not password:
            return "请填写所有必填项！"

        # 连接mysql
        conn = pymysql.connect(host = 'localhost', port = 3306, user = 'root', password = '20050306', charset = 'utf8', db = 'cinema_ticket')
        cursor = conn.cursor(cursor = pymysql.cursors.DictCursor)
        sql = "select * from users where name=%s and password=%s"
        cursor.execute(sql, (name,password) )
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if result:
            username = result['name']
            user_id = result['id']  # 获取用户id
            session['username'] = username  # 保存用户名到 session
            session['user_id'] = user_id    # 保存用户id到 session
            featured_movies = get_featured_movies()  # 获取电影数据
            return render_template('home.html', username=username, featured_movies=featured_movies) # 将用户名传递到模板
        else:
            return "用户名或密码错误，请重新输入！"
    
    return render_template('login_pwd.html')

#手机号登录
@app.route('/cinema_ticket/login_phone', methods=['GET','POST'])
def login_phone():
    if request.method == 'POST':
        phone = request.form.get('phone')
        code = request.form.get('code')

        # 检查必填项目
        if not phone or not code:
            return "请填写所有必填项！"

        # 连接mysql
        conn = pymysql.connect(host = 'localhost', port = 3306, user = 'root', password = '20050306', charset = 'utf8', db = 'cinema_ticket')
        cursor = conn.cursor(cursor = pymysql.cursors.DictCursor)
        sql = "select * from users where phone=%s"
        cursor.execute(sql, (phone) )
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if result:
            username = result['name']
            user_id = result['id']  # 获取用户id
            session['username'] = username  # 保存用户名到 session
            session['user_id'] = user_id    # 保存用户id到 session
            featured_movies = get_featured_movies()  # 获取电影数据
            return render_template('home.html', username=username, featured_movies=featured_movies) # 将用户名传递到模板
        else:
            return "手机号或密码错误，请重新输入！"
    
    return render_template('login_phone.html')

#邮箱登录
@app.route('/cinema_ticket/login_email', methods=['GET','POST'])
def login_email():
    if request.method == 'POST':
        email = request.form.get('email')
        code = request.form.get('code')

        # 检查必填项目
        if not email or not code:
            return "请填写所有必填项！"

        # 连接mysql
        conn = pymysql.connect(host = 'localhost', port = 3306, user = 'root', password = '20050306', charset = 'utf8', db = 'cinema_ticket')
        cursor = conn.cursor(cursor = pymysql.cursors.DictCursor)
        sql = "select * from users where email=%s"
        cursor.execute(sql, (email) )
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if result:
            username = result['name']
            user_id = result['id']  # 获取用户id
            session['username'] = username  # 保存用户名到 session
            session['user_id'] = user_id    # 保存用户id到 session
            featured_movies = get_featured_movies()  # 获取电影数据
            return render_template('home.html', username=username, featured_movies=featured_movies) # 将用户名传递到模板
        else:
            return "邮箱号或密码错误，请重新输入！"
    
    return render_template('login_email.html')

#退出登录
@app.route('/cinema_ticket/logout')
def logout():
    session.pop('username', None)  # 清除 session 中的用户名
    return redirect('/cinema_ticket/home')  # 重定向到首页

#电影详情页
@app.route('/cinema_ticket/movie_single')
def movie_single():
    movie_id = request.args.get('id', type=int)
    if not movie_id:
        return "该电影不在本影院上映噢"
    # 查询数据库获取电影详情
    conn = pymysql.connect(host='localhost', port=3306, user='root', password='20050306', charset='utf8', db='cinema_ticket')
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM movie WHERE id = %s", (movie_id,))
    movie = cursor.fetchone()
    if not movie:
        cursor.close()
        conn.close()
        return "该电影不在本影院上映哦"

    screenings = []
    screenings_msg = ""
    if movie['state'] == '未上映':
        screenings_msg = "即将上映，敬请期待。"
    elif movie['state'] == '下映':
        screenings_msg = "遗憾下映，暂无排场。"
    else:
        # 查询数据库获取场次信息
        cursor.execute("""
            SELECT s.id, s.start_time, s.end_time, s.price, s.state, h.name AS hall_name
            FROM screening s
            JOIN movie_hall h ON s.hall_id = h.id
            WHERE s.movie_id = %s
            ORDER BY s.start_time
        """, (movie_id,))
        screenings = cursor.fetchall()
        # 拆分日期和时间
        for s in screenings:
            s['date'] = s['start_time'].strftime('%Y-%m-%d')
            s['start_time_only'] = s['start_time'].strftime('%H:%M')
            s['end_time_only'] = s['end_time'].strftime('%H:%M')

    cursor.close()
    conn.close()
    return render_template('movie_single.html', movie=movie, screenings=screenings, screenings_msg=screenings_msg)


#选座
@app.route('/cinema_ticket/choose_seat')
def choose_seat():
    # 获取前端传递的screening -> id参数
    screen_id = request.args.get('screen_id', type=int)

    # 连接数据库
    conn = pymysql.connect(host='localhost', port=3306, user='root', password='20050306', charset='utf8', db='cinema_ticket')
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)

    # 查询影厅编号、电影编号、场次信息
    cursor.execute("""
        SELECT movie_id, hall_id, price AS movie_price, start_time, employee_id
        FROM screening s
        WHERE s.id = %s and state = '可订座'
    """, (screen_id,))
    info = cursor.fetchone()
    hall_id = info['hall_id'] if info else ''
    movie_id = info['movie_id'] if info else ''
    movie_price = info['movie_price'] if info else ''
    start_time = info['start_time'] if info else ''
    employee_id = info['employee_id'] if info else ''

    # 查询影厅信息
    cursor.execute("""
        SELECT name AS hall_name, `row` AS hall_row, `column` AS hall_column
        FROM movie_hall
        WHERE id = %s
    """, (hall_id,))
    info = cursor.fetchone()
    hall_name = info['hall_name'] if info else ''
    hall_row = info['hall_row'] if info else ''
    hall_column = info['hall_column'] if info else ''

    # 查询电影信息
    cursor.execute(""" 
        SELECT title, poster
        FROM movie
        WHERE id = %s
    """, (movie_id,))
    info = cursor.fetchone()
    title = info['title'] if info else ''
    poster = info['poster'] if info else ''

    # 查询所有属于该影厅的座位
    cursor.execute("""
        SELECT id AS seat_id, `row` AS seat_row, `column` AS seat_column, state AS state_use, price
        FROM seat
        WHERE hall_id = %s
    """, (hall_id,))
    seats = cursor.fetchall()

    # 查询该场次下所有座位的售卖状态
    cursor.execute("""
        SELECT seat_id, state AS state_buy
        FROM seat_state
        WHERE screen_id = %s
    """, (screen_id,))
    seat_states = cursor.fetchall()
    seat_state_map = {s['seat_id']: s['state_buy'] for s in seat_states}

    # 整合座位信息，生成前端需要的数据结构
    seat_list = []
    for seat in seats:
        state = seat_state_map.get(seat['seat_id'], '可订')
        seat_list.append({
            'seat_id': seat['seat_id'],
            'row': seat['seat_row'],
            'col': seat['seat_column'],
            'price': float(seat['price']),
            'seat_state': state
        })

    cursor.close()
    conn.close()

    return render_template(
        'seat_choose.html',
        seats=seat_list,
        row_count=hall_row,
        col_count=hall_column,
        hall_name=hall_name,
        movie_name=title,
        movie_poster=poster,
        movie_price=movie_price,
        showtime=start_time,
        employee_id=employee_id,
        screen_id=screen_id,
    )


# 支付页面
@app.route('/cinema_ticket/seat_pay', methods=['GET'])
def seat_pay():
    # 从 seat_choose 页面通过 GET 方式传递所有参数
    movie_name = request.args.get('movie_name')
    movie_poster = request.args.get('movie_poster')
    showtime = request.args.get('showtime')
    hall_name = request.args.get('hall_name')
    select_seats = request.args.get('select_seats')
    total_price = request.args.get('total_price')
    eact_id = request.args.get('eact_id')
    user_id = session.get('user_id')
    screen_id = request.args.get('screen_id')
    seat_ids = request.args.get('seat_ids')  # 新增

    # 查询售票员（随机）
    conn = pymysql.connect(host='localhost', port=3306, user='root', password='20050306', charset='utf8', db='cinema_ticket')
    cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
    cursor.execute("SELECT id, name FROM employee WHERE job='售票员' ORDER BY RAND() LIMIT 1")
    esold = cursor.fetchone()
    esold_name = esold['name'] if esold else '未知'
    esold_id = esold['id'] if esold else None
    # 查询放映员
    cursor.execute("SELECT name FROM employee WHERE id=%s", (eact_id,))
    eact = cursor.fetchone()
    eact_name = eact['name'] if eact else '未知'

    cursor.close()
    conn.close()

    return render_template(
        'seat_pay.html',
        movie_name=movie_name,
        movie_poster=movie_poster,
        showtime=showtime,
        hall_name=hall_name,
        select_seats=select_seats,
        total_price=total_price,
        esold_name=esold_name,
        esold_id=esold_id,
        eact_name=eact_name,
        eact_id=eact_id,
        user_id=user_id,
        screen_id=screen_id,
        seat_ids=seat_ids  # 新增
    )

# 订单支付/取消处理
@app.route('/cinema_ticket/pay_order', methods=['POST'])
def pay_order():
    import json
    data = request.get_json()
    user_id = data.get('user_id')
    screen_id = data.get('screen_id')
    seat_id_str = data.get('seat_id')  # 逗号分隔
    total_amount = data.get('total_amount')
    state = data.get('state')  # '已支付' 或 '已取消'
    employee_id = data.get('employee_id')

    seat_ids = [int(s) for s in seat_id_str.split(',') if s]
    # 将 seat_ids 转换为 JSON 字符串
    seat_ids_json = json.dumps(seat_ids)

    conn = pymysql.connect(host='localhost', port=3306, user='root', password='20050306', charset='utf8', db='cinema_ticket')
    cursor = conn.cursor()

    try:
        # 插入订单
        cursor.execute(
            "INSERT INTO `order` (user_id, screen_id, seat_id, total_amount, state, employee_id) VALUES (%s, %s, %s, %s, %s, %s)",
            (user_id, screen_id, seat_ids_json, total_amount, state, employee_id)
        )
        for seat_id in seat_ids:
            # 修改座位状态
            if state == '已支付':
                cursor.execute(
                    "UPDATE seat_state SET state='已售' WHERE screen_id=%s AND seat_id=%s",
                    (screen_id, seat_id)
                )
        conn.commit()
        cursor.close()
        conn.close()
        return {"success": True}
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return {"success": False, "msg": str(e)}

@app.route('/cinema_ticket/refund_order', methods=['POST'])
def refund_order():
    """
    订单退款接口：前端应直接传递 order_id、screen_id、seat_id(JSON数组字符串)。
    将订单状态改为“已退款”,并释放对应座位(seat_state.state 改为“可订”)。
    """
    data = request.get_json()
    order_id = data.get('order_id')
    screen_id = data.get('screen_id')
    seat_id_str = data.get('seat_id')
    user_id = session.get('user_id')
    if user_id is None:
        return {"success": False, "msg": "用户未登录"}
    print(f"order_id: {order_id}, screen_id: {screen_id}, seat_id_str: {seat_id_str}")

    import json
# seat_id 解析并强制转为 int
    try:
    # 先解析一次
        seat_ids_raw = json.loads(seat_id_str)
    # 如果还是字符串，再解析一次
        if isinstance(seat_ids_raw, str):
            seat_ids_raw = json.loads(seat_ids_raw)
        seat_ids = [int(s) for s in seat_ids_raw]
    except Exception:
        seat_ids = [int(seat_id_str)] if seat_id_str else []

    print(f"seat_ids: {seat_ids}, screen_id: {screen_id}, seat_id_str: {seat_id_str}")

    conn = pymysql.connect(host='localhost', port=3306, user='root', password='20050306', charset='utf8', db='cinema_ticket')
    cursor = conn.cursor()
    try:
        # 1. 更新订单状态为“已退款”
        cursor.execute("UPDATE `order` SET state=%s WHERE id=%s", ('已退款', order_id))
        # 2. 遍历座位，释放 seat_state
        for seat_id in seat_ids:

            cursor.execute(
                "UPDATE seat_state SET state=%s WHERE screen_id=%s AND seat_id=%s",
                ('可订', int(screen_id), int(seat_id))
            )
            print(f"UPDATE seat_state affected rows: {cursor.rowcount}, seat_id: {seat_id}, screen_id: {screen_id}")
        conn.commit()
        cursor.close()
        conn.close()
        return {"success": True, "msg": "订单已成功退款，座位已释放"}
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return {"success": False, "msg": f"退款失败：{str(e)}"}

if __name__ == '__main__':
    app.run()