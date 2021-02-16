import os
import json
import requests
import CONFIG
import time
import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import inquiry as IQ
import pyupbit
import threading

tickers = pyupbit.get_tickers(fiat="KRW")


def handle(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    response = msg['text']
    if response == '1':
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='금액차이(원)', callback_data='btn_1')],
                                                         [InlineKeyboardButton(text='금액차이(%)', callback_data='btn_2')]])
        bot.sendMessage(chat_id, '버튼을 선택하세요', reply_markup=keyboard)
    else:
        bot.sendMessage(chat_id, text=response)


def on_callback_query(msg):
    query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
    if query_data == 'btn_1':
        bot.answerCallbackQuery(query_id, IQ.price_gap)
    elif query_data == 'btn_2':
        bot.answerCallbackQuery(query_id, IQ.price_percentage)
    else:
        print('callback query', query_id, from_id, query_data)
        bot.answerCallbackQuery(query_id, text=query_data)


bot = telepot.Bot(CONFIG.TOKEN)

# MessageLoop(bot, {'chat': handle, 'callback_query': on_callback_query}).run_as_thread()

def TimerPerMinute():
    timer = threading.Timer(5, TimerPerMinute)
    timer.start()

    premium, Price_gap = IQ.get_premium()

    send_msg = ''

    ### premium이 빈값('')이면 조건에 안들어간거고,
    ### Price_gap은 초기화를 시켜서 0으로 올때도 있으므로 premium만으로 비교함
    ### Price_gap != 0을 넣게되면 실제 값이 0일 경우 확인이 안됨
    if premium != '':       ##price_gap 조건 제외
        send_msg += premium + ' / ' + Price_gap + '원'
        return send_msg


def TimerPer5Minute():
    # 하루에 333번 한달에 10,000번 가능
    # 24시간 기준 4.5분마다 보내야 연속해서 사용가능
    timer = threading.Timer(300, TimerPer5Minute)
    timer.start()

    dominance = IQ.GetDominance()

    send_msg = ''

    if (dominance != ''):
        send_msg += ' 도미넌스 : ' + str(dominance)
        return send_msg


def timer_test():
    timer = threading.Timer(1, timer_test)
    timer.start()
    print(time.localtime())


if __name__ == '__main__':
    send_msg = ''
    # tickers = pyupbit.get_tickers(fiat="KRW")
    # send_msg += '\n'.join(IQ.Filter(tickers))
    #TODO: 타이머는 계속 돌지만 메인에서 받아서 보내주는 부분이 없음 -> 타이머에 sendmessage를 넣는게 나을듯..
    send_msg += '\n' + TimerPerMinute()
    # send_msg += TimerPer5Minute()
    # timer_test()
    if send_msg != '':
        bot.sendMessage(chat_id=CONFIG.ID.LKJ, text=send_msg)
        bot.sendMessage(chat_id=CONFIG.ID.KBS, text=send_msg)
# while 1:
# bot.sendMessage(chat_id=CONFIG.ID.LKJ, text=IQ.GetDominance())
# bot.sendMessage(chat_id=CONFIG.ID.KBS, text=IQ.GetDominance())
#    time.sleep(2)

'''
for i in range(len(tickers)):
    if IQ.Filter(tickers[i]):
        bot.sendMessage(chat_id=CONFIG.ID.KBS, text=tickers[i]+" 필터통과")
    time.sleep(0.07)
'''

'''
    str_result = IQ.InquiryPriceByTicker(tickers[i])
    time.sleep(0.07)
    bot.sendMessage(chat_id=CONFIG.ID.KBS, text=str_result)
    bot.sendMessage(chat_id=CONFIG.ID.LKJ, text=str_result)
'''
