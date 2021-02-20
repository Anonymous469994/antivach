import logging
logging.basicConfig(filename='logfile', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

import requests
import json
from time import sleep
import datetime
from random import randint
from telebot.types import InputMediaDocument
import telegram as tg

BUFFER = 25
MIN_TIMEOUT = 0.5
MIN_TIMEOUT_TG = 1
BOARD = 'b' 

def prepare_resp_thread(num, body):    
    metadata_msg = """
УБИТЫЙ ТРЕД!
№{num}
Дата: {date}
Тема: {subject}
Постов: {posts_count}
Файлов: {files_count}""".format(num=num, subject=body['subject'], date=body['date'], posts_count=body['posts_count'], 
                            files_count=body['files_count'])
    comment_msg = 'Комментарий: '+ body['comment'][:800]
    if len(body['media']):
        media_msgs = [x['names'] + ' : ' + x['refs'] for x in body['media']]
    else:
        media_msgs = None
    return metadata_msg, comment_msg, media_msgs

def prepare_resp_message(num_thrd, body, num_msg):    
    metadata_msg = """
ВЫРЕЗАННОЕ СООБЩЕНИЕ!
№{num_thrd}
Тема: {subject}
Постов: {posts_count}
Файлов: {files_count}
Дата: {date}""".format(num_thrd=num_thrd, subject=body['subject'], date=body['coms'][num_msg]['date'], 
                            posts_count=body['posts_count'], files_count=body['files_count'])
    comment_msg = 'Комментарий: '+ body['coms'][num_msg]['comment'][:800]
    media = body['coms'][num_msg]['media']
    if len(media):
        media_msgs = [x['names'] + ' : ' + x['refs'] for x in media]
    else:
        media_msgs = None
    return metadata_msg, comment_msg, media_msgs

if __name__ == "__main__":
    thrds_dict = dict()
    top_threads = []
    logging.info('Restart the app')
        
    while True:
        try:
            res = requests.get('https://2ch.hk/{}/catalog.json'.format(BOARD))
#             print('A', res)
            thrds = json.loads(res.text)['threads']
        except:
            logging.error('Can`t connect...')
            sleep(60 + randint(0,10))
            continue

        new_top_threads = []
        new_thrds_dict = dict()
        for it, t in enumerate(thrds):
            body = {
            'subject' : t['subject'],
            'comment' : t['comment'],
            'date' : t['date'],
            'posts_count' : t['posts_count'],
            'files_count' : t['files_count'],
            'media' : 
                [{'refs' : 'https://2ch.hk' + x['path'], 'names' : x['displayname']} for x in t['files']]
            }
            num_thread = int(t['num'])
            body['coms'] = dict()
           
            if it > len(thrds) - BUFFER:
                new_thrds_dict[num_thread] = body
                new_top_threads.append(num_thread)
                continue
                
            try:
                ref = 'https://2ch.hk/makaba/mobile.fcgi?task=get_thread&board={}&thread={}&post=0'.format(BOARD, num_thread)
                res = requests.get(ref)
#                 print('B', res)
                coms = json.loads(res.text)
                if 'Error' in coms[0].keys():
                    raise
            except:
                logging.error('Can`t connect to thread №' + str(num_thread))
                if num_thread in set(thrds_dict.keys()):
                    body['coms'] = thrds_dict[num_thread]['coms']
                new_thrds_dict[num_thread] = body
                new_top_threads.append(num_thread)
                sleep(MIN_TIMEOUT)
                continue
            
            for c in coms:
                com_body = {
                'date' : c['date'],
                'comment' : c['comment'],
                }
                try:
                    com_body['media'] = [
                        {'refs' : 'https://2ch.hk' + x['path'], 'names' : x['displayname']} for x in c['files']
                    ]
                except:
                    pass
                body['coms'][int(c['num'])] = com_body
                
            if num_thread in set(top_threads):
                anomalies = set(thrds_dict[num_thread]['coms'].keys()) - set(body['coms'].keys())
                if anomalies:
                    logging.warning('Anomalies!')
                    for a in anomalies:
                        logging.info(str(thrds_dict[num_thread]['subject']) + ':\t' + str(thrds_dict[num_thread]['coms'][a]))
                        msgs = prepare_resp_message(num_thread, thrds_dict[num_thread], a)
                        tg.send_text_message(msgs[0])
                        sleep(MIN_TIMEOUT_TG)
                        if msgs[1] != '':
                            print(len(msgs[1]))
                            tg.send_text_message(msgs[1])
                        sleep(MIN_TIMEOUT_TG)
                        if msgs[2] is not None:
                            for media_msg in msgs[2]:
                                tg.send_text_message(media_msg)
                                sleep(MIN_TIMEOUT_TG)
            new_thrds_dict[num_thread] = body
            new_top_threads.append(num_thread)
            sleep(MIN_TIMEOUT)

        anomalies = set(top_threads) - set(new_thrds_dict.keys())
        top_threads = new_top_threads[:-BUFFER]
#         print(len(anomalies), len(thrds_dict), len(new_thrds_dict))
        if anomalies:
            logging.warning('Anomalies!')
            for a in anomalies:
                logging.info(str(a) + ' : ' + str(thrds_dict[a]['subject']))
                msgs = prepare_resp_thread(a, thrds_dict[a])
                tg.send_text_message(msgs[0])
                sleep(MIN_TIMEOUT_TG)
                if msgs[1] != '':
                    print(len(msgs[1]))
                    tg.send_text_message(msgs[1])
                sleep(MIN_TIMEOUT_TG)
                if msgs[2] is not None:
                    for media_msg in msgs[2]:
                        tg.send_text_message(media_msg)
                        sleep(MIN_TIMEOUT_TG)
        thrds_dict = new_thrds_dict
        sleep(MIN_TIMEOUT)
#         sleep(randint(0,5))
        
        t = datetime.datetime.now()
        if t.hour == 0:
            open('logfile', 'w').close()
            logging.info('logfile cleanup')
            
