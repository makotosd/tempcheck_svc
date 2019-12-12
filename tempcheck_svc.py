# coding utf-8
import requests
from flask import Flask, jsonify, request
import datetime
import dateutil.parser
from enum import Enum
class TempState(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3

LOW_TEMP = 22
HIGH_TEMP = 35
MSG_LOW = "Temperature is too LOW. "
MSG_HIGH = "Temperature is too HIGH. "
MSG_NOM = "Temperature return to NORMAL. "

app = Flask(__name__)


@app.route('/check_temp', methods=['GET'])
def check_temp():
    # テストデータの受取
    response_json = request.get_json()

    if response_json is None:
        # 温度履歴を取得
        response = requests.get(
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
    now = datetime.datetime.now()

    (f_last_value_is_edge, edge_message) = last_value_is_edge(values)
    c_state = state_temp(float(values[0]['value']))
    if f_last_value_is_edge is True:  # 状態遷移があった場合
        edge_list = gen_edge_list(values)
        edge_duration = dateutil.parser(edge_list[0]['timestamp']) - dateutil.parser(edge_list[1]['timestamp'])
        if edge_duration > datetime.timedelta(hours=1) : # 前回の状態遷移から1時間以上空いていた場合
            return edge_message
    elif c_state is not TempState.NORMAL:       # 異常状態にいる場合
        duration = wrong_range_duration(values)
        onehour = datetime.timedelta(hours=1)
        if (duration % onehour) < datetime.timedelta(minutes=8):
            if c_state is TempState.LOW:
                return MSG_LOW + "{%.2f}C".float(values[0]['value'])
            elif c_state is TempState.HIGH:
                return MSG_HIGH + "{%.2f}C".float(values[0]['value'])
            else:
                return "ERROR: 2000"
    else:
        return None

# 不正な状態にどれだけ継続しているか？
#
def wrong_range_duration(values):
    now = datetime.datetime.now()
    for v in values:
        state = state_temp(float(v['value']))
        if state is TempState.NORMAL:
            return now - dateutil.parser(v['timestamp'])

# 温度状態に関する標準関数軍
def low_temp(temp):
    return temp < LOW_TEMP
def high_temp(temp):
    return temp > HIGH_TEMP
def normal_temp(temp):
    return LOW_TEMP <= temp and temp <= HIGH_TEMP
def state_temp(temp):
    if temp < LOW_TEMP:
        return TempState.LOW
    elif temp > HIGH_TEMP:
        return TempState.HIGH
    else:
        return TempState.NORMAL


# 最新のデータで状態が変化したか？
# 一個前の状態変化はいつか？
# 状態変化に対するメッセージ。
def last_value_is_edge(values):
    c_state = state_temp(values[0]['value'])
    p_state = state_temp(values[1]['value'])

    if c_state is p_state:
        return False, None
    else:
        if c_state is TempState.HIGH:
            return True, MSG_HIGH + "{%.2f}C".float(values[0]['value'])
        elif c_state is TempState.LOW:
            return True, MSG_LOW + "{%.2f}C".float(values[0]['value'])
        else:
            return True, MSG_NOM + "{%.2f}C".float(values[0]['value'])

def gen_edge_list(values):
    edge_list = []
    previous_temp = None
    for v in values:
        current_temp = float(v['value'])  # 今の温度
        if previous_temp is not None:
            p_state = state_temp(previous_temp)  # 前の状態
            c_state = state_temp(current_temp)   # 今の状態
            if p_state is not c_state:  # 前の状態と今の状態が違っていたら
                edge_list.append(v)   # いつのだったのか記録
            else:
                pass
        previous_temp = current_temp

    return edge_list


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8080)