# coding utf-8
import requests
from flask import Flask
import datetime
import jsonify
import dateutil.parser
from enum import Enum
class TempState(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3

LOW_TEMP = 22
HIGH_TEMP = 35
app = Flask(__name__)


@app.route('/check_temp', methods=['GET'])
def check_temp():
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

    (f_last_value_is_edge, previous_edge, edge_message) = last_value_is_edge(values)
    (f_wrong_range, wrong_range_begin, periodic_message) = wrong_range(values)
    if f_last_value_is_edge is True:
        if now - previous_edge > datetime.timedelta(hours=1) :
            return edge_message
    elif f_wrong_range is True:
        onehour = datetime.timedelta(hours=1)
        duration = now - wrong_range_begin
        if (duration % onehour) < datetime.timedelta(minutes=8):
            return periodic_message
    else:
        return None


# 不正な状態にどれだけ継続しているか？
#
def wrong_range(values):
    msg = ""
    return True, datetime.datetime.now(), msg

# 温度状態に関する標準関数軍
def low_temp(temp):
    return temp < LOW_TEMP
def high_temp(temp):
    return temp > HIGH_TEMP
def normal_temp(temp):
    return LOW_TEMP <= temp && temp <= HIGH_TEMP
def state_temp(temp)
    if temp < LOW_TEMP:
        return TempState.LOW
    elif temp > HIGH_TEMP
        return TempState.HIGH
    else:
        return TempState.NORMAL


# 最新のデータで状態が変化したか？
# 一個前の状態変化はいつか？
# 状態変化に対するメッセージ。
def last_value_is_edge(values):
    msg = None

    edge_time = []
    previous_temp = None
    for v in values:
        current_temp = float(v['value'])  # 今の温度
        if previous_temp is not None:
            p_state = state_temp(previous_temp)  # 前の状態
            c_state = state_temp(current_temp)   # 今の状態
            if p_state is not c_state:  # 前の状態と今の状態が違っていたら
                edge_time.append(dateutil.parser.parse(v['timestamp']))   # いつのだったのか記録
                if msg is None and c_state is TempState.NORMAL:
                    msg = "Return to Normal"
                elif msg is None and c_state is TempState.LOW:
                    msg = "Temperature is TOO LOW"
                elif msg is None and c_state is TempState.HIGH:
                    msg = "Temperature is TOO HIGH"
            else:
                pass
        previous_temp = current_temp

    flag = edge_time[0] is dateutil.parser.parse(values[1]['timestamp']) # 最新データがエッジか？
    previous_edge = datetime.date.min  # 一番古い時間。
    if flag is True:
        if len(edge_time) > 1:
            previous_edge = edge_time[1]

    return flag, previous_edge, msg


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8080)