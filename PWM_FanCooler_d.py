#!/usr/bin/python
# coding: utf-8

# モジュールをインポート
import RPi.GPIO as GPIO
import time
import sys

# daemon化に必要
import daemon
import daemon.pidfile
#from daemon.pidlockfile import PIDLockFile

# GPIOのピン番号を定義
PIN = 18

# 周波数を定義
Hz = 60

# Duty上限
top = 100.0
# Duty下限
bottom = 20.0
# 最高温度
height = 80.0
# 最低温度
low = 30.0

# =================
# CPUの温度を取得
# =================


def get_CPU_Temperature():
    temp = "0"

    f = open("/sys/class/thermal/thermal_zone0/temp", "r")
    for t in f:
        temp = t[:2] + "." + t[2:5]
    f.close()

    return float(temp)

# ==========
# Duty比算出
# ==========


def get_duty(tmp=low):
    rs = 5.0
    if(height < tmp):
        rs = top
    elif(tmp < low):
        rs = bottom
    else:
        rs = bottom + ((top - bottom) / (height - low)) * (tmp - low)
    return rs

# =========
# PWM実行
# =========


def exec_pwm():
    # GPIOピン番号の定義方法
    GPIO.setmode(GPIO.BCM)
    # 出力モードで初期化
    GPIO.setup(PIN, GPIO.OUT)
    # PWM初期化
    p = GPIO.PWM(PIN, Hz)

    try:
        # 100%の出力で、1秒間動かす
        # 最初の出力が小さすぎて、ファンが回らない場合の対策
        Duty = 100
        p.start(Duty)
        time.sleep(1)

        while True:
            # CPUの温度を取得
            CPU_Temp = get_CPU_Temperature()
            # CPUの温度によって出力を変更
            Duty = get_duty(CPU_Temp)
            # 出力を変更して、10秒間待機
            p.ChangeDutyCycle(Duty)
            time.sleep(10)

    except Exception as e:
        # 例外処理
        print("[例外発生] PWM_FanCooler_d.py を終了します。")
        print("Exception : " + str(e))
        print("     Type : " + str(type(e)))
        print("     Args : " + str(e.args))
        print("  Message : " + e.message)
    finally:
        # PWMを終了
        p.stop()

        # GPIO開放
        GPIO.cleanup()


if __name__ == "__main__":
    # PIDファイルの書き込みに失敗してデーモンが動かない事があるので、少し時間をずらす
    time.sleep(1)

    # /etc/init.d/PWM_FanCooler.sh のPIDファイルとは別名にする
    with daemon.DaemonContext(umask=0o002, pidfile=daemon.pidfile.PIDLockFile('/var/run/PWM_FanCooler_d.pid'), stdout=sys.stdout, stderr=sys.stderr):
        exec_pwm()
