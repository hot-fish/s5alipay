from django.shortcuts import render, redirect, HttpResponse
from utils.pay import AliPay
import json
import paho.mqtt.client
from threading import Thread
mqtt = paho.mqtt.client
import time
from datetime import datetime
payinfo = {}

def get_ali_object():
    # 沙箱环境地址：https://openhome.alipay.com/platform/appDaily.htm?tab=info
    app_id = "2016092800618617"  #  APPID （沙箱应用）

    # 支付完成后，支付偷偷向这里地址发送一个post请求，识别公网IP,如果是 192.168.20.13局域网IP ,支付宝找不到，def page2() 接收不到这个请求
    # notify_url = "http://47.94.172.250:8804/page2/"
    notify_url = "http://127.0.0.1:8000/page2/"
    # notify_url = "http://127.0.0.1:8804/page2/"

    # 支付完成后，跳转的地址。
    return_url = "http://127.0.0.1:8000/page2/"

    merchant_private_key_path = "keys/app_private_2048.txt" # 应用私钥
    alipay_public_key_path = "keys/alipay_public_2048.txt"  # 支付宝公钥

    alipay = AliPay(
        appid=app_id,
        app_notify_url=notify_url,
        return_url=return_url,
        app_private_key_path=merchant_private_key_path,
        alipay_public_key_path=alipay_public_key_path,  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥
        debug=True,  # 默认False,
    )
    return alipay

def stop_pub():#断开与mq服务器的连接
    client.disconnect()
    client.loop_stop()
    print("已断开与服务器的连接")

def start_pub(ip="47.93.30.53",port=1883,username="public",pwd="123456"):#开始与服务器连接。在django启动时就调用，随web服务器
    dict = {"ip": ip, "port": port, "username": username, "pwd": pwd}
    print(dict)
    if ip != "" and port != "" and username != "" and pwd != "":
        print("服务器连接信息设置格式验证完毕，开始尝试连接...")
        start_connect(ip, port, username, pwd)
    else:
        print("订阅设置有误，请检查后重试！")

def thread_it(func, *args):#多线程函数
    t = Thread(target=func, args=args)
    t.setDaemon(True)
    t.start()
def start_connect(ip="47.93.30.53",port=1883,username="public",pwd="123456"):
    # client_id = "好咖啡" + time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    client_id = "好咖啡"+ time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    global client
    # ClientId不能重复，所以使用当前时间。连接方式参数为tcp也可以不写
    client = mqtt.Client(client_id, transport='tcp')
    # 初始化订阅用户和密码 必须设置，否则会返回「Connected with result code 4」
    client.username_pw_set(username, pwd)
    client.on_connect = on_connect  # 打印连接状态
    client.connect(ip, port, 60)  # 开始连接
    global xc1
    xc1 = Thread(target=client.loop_forever)  # 开启客户端阻塞线程
    xc1.setDaemon(True)
    xc1.start()  # 线程启动
def on_connect(client, userdata, flags, rc):  # 连接初始化函数。连接成功立即开始订阅并启动消息回调函数
    print("Connected with result code " + str(rc))  # 打印连接状态
    if rc == 0:
        print("已成功连接mqtt服务器!")
    else:
        print("连接失败，请检查服务器连接设置是否正确!")

def on_publish(topic, payload, qos):  # 发送函数
    """
    :param topic: 消息主题
    :param payload: 消息内容
    :param qos: 连接质量
    :return:
    """
    client.publish(topic, payload, qos)

def index(request):
    return render(request,'index.html')
def mq_index(request):
    return render(request,'mqtt.html')
def home(request):
    return render(request, 'home.html')
def page1(request):
    # 根据当前用户的配置，生成URL，并跳转。
    goods_dir = {"奶茶":3.00,"拿铁":12.00,"咖啡":9.80,"意式":12.00,"美式":12.00,"卡布奇诺":10.00,"热巧克力":9.80,"抹茶":9.80,"牛奶巧克力":9.80,"鸳鸯奶茶":9.80,"热牛奶":8.80,"双倍意式特浓":12.00,"热水":1.00,"玛奇朵":12.00}
    # money = float(request.POST.get('money'))
    goods = request.POST.get('choose goods')
    print(goods)
    if goods!="":
        money = goods_dir[goods]
        alipay = get_ali_object()
        subject = "已购商品: 一杯%s"%goods
        out_trade_no = "x2" + str(time.time())
        global payinfo
        payinfo = {"金额": money, "商品": subject,"订单号": out_trade_no,"商品名":goods}
        # 生成支付的url
        query_params = alipay.direct_pay(
            subject=subject,# 商品简单描述
            out_trade_no=out_trade_no,# 用户购买的商品订单号（每次不一样） 20180301073422891
            total_amount=money,# 交易金额(单位: 元 保留俩位小数)
        )
        pay_url = "https://openapi.alipaydev.com/gateway.do?{0}".format(query_params)  # 支付宝网关地址（沙箱应用）
        return redirect(pay_url)

def page1_1(request):
    # 根据当前用户的配置，生成URL，并跳转。
    money = float(request.POST.get('money'))
    alipay = get_ali_object()

    # 生成支付的url
    query_params = alipay.direct_pay(
        subject="自定义商品",  # 商品简单描述
        out_trade_no="x2" + str(time.time()),  # 用户购买的商品订单号（每次不一样） 20180301073422891
        total_amount=money,  # 交易金额(单位: 元 保留俩位小数)
    )

    pay_url = "https://openapi.alipaydev.com/gateway.do?{0}".format(query_params)  # 支付宝网关地址（沙箱应用）

    return redirect(pay_url)

def page2(request):
    alipay = get_ali_object()
    if request.method == "POST":
        # 检测是否支付成功
        # 去请求体中获取所有返回的数据：状态/订单号
        from urllib.parse import parse_qs
        # name&age=123....
        body_str = request.body.decode('utf-8')
        post_data = parse_qs(body_str)

        post_dict = {}
        for k, v in post_data.items():
            post_dict[k] = v[0]

        # post_dict有10key： 9 ，1
        sign = post_dict.pop('sign', None)
        status = alipay.verify(post_dict, sign)
        print('------------------开始------------------')
        print('POST验证', status)
        print(post_dict)
        out_trade_no = post_dict['out_trade_no']

        # 修改订单状态
        models.Order.objects.filter(trade_no=out_trade_no).update(status=2)
        print('------------------结束------------------')
        # 修改订单状态：获取订单号
        return HttpResponse('POST返回')

    else:
        params = request.GET.dict()
        sign = params.pop('sign', None)
        status = alipay.verify(params, sign)
        print('==================开始==================')
        print('GET验证', status)
        print('==================结束==================')
        # return HttpResponse('支付成功')
        seller = "爱思普芯科技有限公司"
        payway = "支付宝"
        i = datetime.now()
        trade_time = "{}年{}月{}日{}时{}分{}秒".format(i.year, i.month, i.day, i.hour, i.minute, i.second)
        # print(trade_time)
        global payinfo
        html = f'支付成功!付款信息如下:<br>\
        <table border="1">\
        <tr><td>商品名</td> <td>{payinfo["商品名"]}</td></tr>\
        <tr><td>商品详情</td> <td>{payinfo["商品"]}</td></tr>\
        <tr><td>订单号</td> <td>{payinfo["订单号"]}</td></tr>\
        <tr><td>付款金额</td> <td>{(payinfo["金额"])}元</td></tr>\
        <tr><td>收款方</td> <td>{seller}</td></tr>\
        <tr><td>交易时间</td> <td>{trade_time}</td></tr>\
        <tr><td>付款方式</td> <td>{payway}</td></tr>\
        </table>'
        #.format(payinfo["商品名"],payinfo["商品"],payinfo["订单号"],payinfo["金额"],seller,trade_time,payway)
        moneyinfo = str(payinfo["金额"])+"元"
        reinfodit = {"商品名":payinfo["商品名"],"商品":payinfo["商品"],"订单号":payinfo["订单号"],"金额":moneyinfo,"卖家":seller,"交易时间":trade_time,"付款方式":payway}
        reinfo=f'{reinfodit}'
        on_publish("public",reinfo,0)
        return HttpResponse(html)

start_pub()

