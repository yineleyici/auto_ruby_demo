# -*- coding: utf-8 -*-
from pywebio.input import *
from pywebio.output import *
from pywebio.platform.flask import webio_view
from pywebio import start_server, STATIC_PATH
from pywebio.session import hold
from flask import Flask, send_from_directory
from autoruby import AutoRuby
import argparse
import os


def index():
    put_markdown('# 自動ルビ挿入デモ\n* ふりがなの無いテキストファイルに、自動でふりがなを付与する試みです。\n* ファイルは保存しないので、私に内容を知られることはありません。\n* 自動なのでわりと間違えます。自己責任でお使いください。')
    main()


def main():
    # 検索画像を入力
    inputFile = file_upload(accept=['.txt'],
                           max_size='3M',
                           placeholder='テキストファイルをアップロード',
                           required=True)
    text = inputFile['content'].decode(encoding='utf-8')

    # ルビ挿入
    r = AutoRuby()
    r.jouyouBlock = False
    r.mode = 'html'
    text = r.TextToRuby(text)
    text = f'<p>{text}</p>'.replace('\n', '<br>\n')

    # 出力
    put_html(text).style('font-size: 1em; line-height: 2.2em; height: 38em; overflow: auto; margin: 30px 2%; width: 86%; padding: 30px 0; float: left; writing-mode: tb-rl; writing-mode: vertical-rl; /writing-mode: tb-rl; _writing-mode: tb-rl; -ms-writing-mode: tb-rl; -moz-writing-mode: vertical-rl; -webkit-writing-mode: vertical-rl; -o-writing-mode: vertical-rl;')
    scroll_to(position='bottom')

    hold()


app = Flask(__name__)

### ローカルサーバー起動用
#if __name__ == '__main__':
#    index()

#app.run(host='localhost', port=8000)



### デプロイ用
app.add_url_rule('/schedule', 'webio_view', webio_view(index),
                 methods=['GET', 'POST', 'OPTIONS'])

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', type=int,
                        default=int(os.environ.get('PORT', 8000)), help='port')
    parser.add_argument('--host', default='0.0.0.0', help='host')
    args = parser.parse_args()

    start_server(index, port=args.port)
