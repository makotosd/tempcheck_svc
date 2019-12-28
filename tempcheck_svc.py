# coding utf-8
import requests
import logging
import logging.handlers
from flask import Flask, jsonify, request
import datetime
from enum import Enum


class TempState(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3


LOW_TEMP = 20.0
HIGH_TEMP = 35.0
DELTA_TEMP = 1.0
MSG_LOW = "じぇじぇじぇ、ちょっとすずしいなぁー. "
MSG_HIGH = "じぇ、あちっちー. "
MSG_NOM = "ふぅ、かいてきかいてき。ぴよ。"
preStatus = None
preStatusStart = None
preMsgTime = None

app = Flask(__name__)


if app.config['ENV'] == "development":
    M2X_SVC = 'http://192.168.1.100:8081/m2x_temperature'
else:
    M2X_SVC = 'http://m2x:8080/m2x_temperature'


# Add RotatingFileHandler to Flask Logger
handler = logging.handlers.RotatingFileHandler("tempcheck.log", "a+", maxBytes=30000, backupCount=5)
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s'))
app.logger.addHandler(handler)
# 下の行がないお、RotatingFileHandlerがWARNING以上しか出してくれなかった。
app.logger.setLevel(logging.DEBUG)


@app.route('/check_temp', methods=['POST'])
def check_temp():
    app.logger.info("check_temp called. --------------------------------------------")

    # テストデータの受取
    response_json = request.get_json()

    if response_json is None:
        try:
            # 温度履歴を取得
            response = requests.get(
                url=M2X_SVC,
                timeout=(10, 30)
            )

        except requests.exceptions.ConnectTimeout:
            app.logger.error('Timeout for M2X server')
            return jsonify({'message': None})

        else:
            response_json = response.json()
    else:
        pass

    values = response_json['values']

    # 温度履歴をもとに、メッセージを作成
    message = message_gen(values)
    app.logger.info("message is %s", message)
    ret = {
        'message': message
    }
    return jsonify(ret)


# 温度履歴をもとに、メッセージを返す
def message_gen(values):
    global preMsgTime
    global preStatus
    global preStatusStart

    c_temp = float(values[0]['value'])
    c_status = state_temp2(c_temp, preStatus)

    if preStatus is not None:
        app.logger.debug("preStatus is %s", preStatus.name)
        app.logger.debug("preStatus starts %s", preStatusStart.strftime("%d/%m/%Y %H:%M:%S"))
        app.logger.debug("preMsgTime is %s", preMsgTime.strftime("%d/%m/%Y %H:%M:%S"))
        app.logger.debug("temperature is {}".format(c_temp))
        app.logger.debug("c_status is " + c_status.name)

    msg = None
    now = datetime.datetime.now()

    if preStatus is None:
        preStatus = c_status
        preStatusStart = now
        preMsgTime = now
        msg = "ぴよ！げんき？"

    elif preStatus != c_status:  # 状態遷移あり
        msg = get_msg(c_status, c_temp)
        preStatus = c_status
        preStatusStart = now
        preMsgTime = now
        app.logger.debug("state changed")

    else:  # 状態遷移なし
        app.logger.debug("no state change")

        if c_status != TempState.NORMAL:  # NORMAL以外の場合
            if now - preStatusStart > datetime.timedelta(hours=1.0):
                app.logger.debug("one hour passed from previous state change.")
                if now - preMsgTime > datetime.timedelta(hours=1.0):
                    app.logger.debug("one hour passed from previous message.")
                    preMsgTime = now
                    msg = get_msg(c_status, c_temp)
                else:
                    pass  # 前の通知から1H今んなので、何もしない
            else:
                pass      # 状態遷移から1H未満なので、何もしない
        else:
            pass          # NORMALなので何もしない

    preStatus = c_status

    return msg


def get_msg(state, temp):
    if state == TempState.HIGH:
        msg = MSG_HIGH + ' {:.2f}C'.format(temp)
    elif state == TempState.LOW:
        msg = MSG_LOW + ' {:.2f}C'.format(temp)
    else:
        msg = MSG_NOM + ' {:.2f}C'.format(temp)
    return msg


# 温度状態に関する標準関数軍
def state_temp2(t, p_state):
    if p_state is None:
        if t < LOW_TEMP:
            return TempState.LOW
        elif t > HIGH_TEMP:
            return TempState.HIGH
        else:
            return TempState.NORMAL
    else:
        if p_state == TempState.LOW:
            if t < LOW_TEMP + DELTA_TEMP:
                return TempState.LOW
            else:
                return TempState.NORMAL
        if p_state == TempState.NORMAL:
            if t < LOW_TEMP:
                return TempState.LOW
            elif t > HIGH_TEMP:
                return TempState.HIGH
            else:
                return TempState.NORMAL
        if p_state == TempState.HIGH:
            if t > HIGH_TEMP - DELTA_TEMP:
                return TempState.HIGH
            else:
                return TempState.NORMAL


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
