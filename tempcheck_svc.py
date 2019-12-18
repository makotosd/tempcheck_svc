# coding utf-8
import requests
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


@app.route('/check_temp', methods=['POST'])
def check_temp():
    # テストデータの受取
    response_json = request.get_json()

    if response_json is None:
        # 温度履歴を取得
        response = requests.get(
            # 'http://m2x:8080/m2x_temperature'
            'http://192.168.1.100:8081/m2x_temperature'
        )
        response_json = response.json()

    values = response_json['values']

    # 温度履歴をもとに、メッセージを作成
    message = message_gen(values)
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

    msg = None

    if preStatus is None:
        preStatus is c_status
        preStatusStart = datetime.datetime.now()
        preMsgTime = datetime.datetime.now()
        msg = "ぴよ！げんき？"

    elif preStatus is not c_status:  # 状態遷移あり
        msg = get_msg(c_status, c_temp)
        preStatus = c_status
        preStatusStart = datetime.datetime.now()
        preMsgTime = None

    else:  # 状態遷移なし
        now = datetime.datetime.now()
        if now - preStatusStart > datetime.timedelta(hours=1.0):
            if now - preMsgTime > datetime.deltatime(hours=1.0):
                preMsgTime = now
                msg = get_msg(c_status, c_temp)
            else:
                pass
        else:
            pass

    preStatus = c_status

    return msg


def get_msg(state, temp):
    if state is TempState.HIGH:
        msg = MSG_HIGH + ' {:.2f}C'.format(temp)
    elif state is TempState.LOW:
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
        if p_state is TempState.LOW:
            if t < LOW_TEMP + DELTA_TEMP:
                return TempState.LOW
            else:
                return TempState.NORMAL
        if p_state is TempState.NORMAL:
            if t < LOW_TEMP:
                return TempState.LOW
            elif t > HIGH_TEMP:
                return TempState.HIGH
            else:
                return TempState.NORMAL
        if p_state is TempState.HIGH:
            if t > HIGH_TEMP - DELTA_TEMP:
                return TempState.HIGH
            else:
                return TempState.NORMAL


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8080)
