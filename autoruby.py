from janome.tokenizer import Tokenizer
import regex as re
import jaconv
import json

class AutoRuby:
    def __init__(self):
        self.t = Tokenizer()

        self.NGList = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '〇']
        self.kataList = ['ぺーじ', 'こーひー', 'びーる', 'きりすと', 'きりしたん', 'がす', 'めりやす', 'くらぶ', 'がらす', 'あじあ']
        self.p = re.compile('\p{Script=Han}+')
        self.jouyouBlock = False
        self.duplicationBlock = True
        self.mode = 'aozora'

        # 常用漢字表
        with open('./re_han_jouyou.txt', encoding='utf-8') as f:
            self.j = re.compile(f.read())

        # Unicode音訓辞書
        with open('Unihan-KJapaneseOnKun.json', encoding='utf-8') as f:
            self.hanDic = json.load(f)


    def TokenizerSet(self, path):
        self.t = Tokenizer(path)


    def UnihanOnKun(self, han, reading):
        try:
            for r in self.hanDic[han]['reading']:
                if r in reading:  # 音読みが一致したら
                    return r
            for r in self.hanDic[han]['phonetic']:
                if r in reading:  # 訓読みが一致したら
                    return r
            return ''
        except KeyError:
            return ''


    def ToBaseForm(self, text):
        result = []
        for token in self.t.tokenize(text):
            result.append(token.base_form)
        return result


    def RubyFomet(self,rs,rr):
        if self.mode == 'aozora':
            return f'｜{rs}《{rr}》'
        if self.mode == 'html':
            return f'<ruby>{rs}<rp>（</rp><rt>{rr}</rt><rp>）</rp></ruby>'
        if self.mode == 'pixiv':
            return f'[[rb:{rs} > {rr}]]'


    def TokenToRuby(self, token):
        surface = token.surface
        reading = jaconv.kata2hira(token.reading)

        if (not self.p.search(surface)) or reading == '*':  # 漢字でないもの、読みが無いもの
            return surface


        s = ''
        for m in self.p.finditer(surface):  # 漢字だけにする
            s = s + m.group()

        if self.jouyouBlock:
            if self.j.fullmatch(s):  # 漢字部分がすべて常用漢字だったらはじく
                return surface

        if s in self.NGList:  # NGリストにあったらはじく
            return surface

        if self.duplicationBlock:
            self.NGList.append(s)  # NGリスト追加

        if self.p.fullmatch(surface):  # すべて漢字の場合
            if reading in self.kataList:  # カタカナにする場合
                reading = jaconv.hira2kata(reading)
            return self.RubyFomet(surface,reading)

        else:  # かな混じりの場合

            # '天丼マン太郎' -> ['', '', '天丼マン', '太郎']
            surfaceFix = ','
            for v in surface:
                if self.p.fullmatch(v) and not self.p.fullmatch(
                        surfaceFix[-1]):
                    surfaceFix = f'{surfaceFix},{v}'
                else:
                    surfaceFix = f'{surfaceFix}{v}'
            sList = surfaceFix.split(",")

            result = ''
            for s in sList:

                if s == '':  # 何もない場合
                    continue

                if not self.p.match(s):  # 漢字でない、またはNGにある場合
                    result = result + s
                    continue

                if len(s) == 1:  # このトークンが一文字の場合
                    rp = self.UnihanOnKun(s, reading)
                    if rp:
                        result = result + self.RubyFomet(s,rp)
                        continue

                # Janomeで解決する
                rp = ''
                for st in self.t.tokenize(s):
                    rp = rp + jaconv.kata2hira(st.reading)
                rp = rp.replace('*', '')

                if rp:
                    rs = self.p.match(s).group()
                    ra = s[len(rs) :]
                    if ra:
                        rr = rp[: -1 * len(ra)]
                    else:
                        rr = rp

                    if rr:
                        result = result + self.RubyFomet(rs,rr) + ra
                        continue

                # UnihanOnKunで解決する
                bfr = ''
                for bf in self.t.tokenize(self.ToBaseForm(s)[0]):
                    bfr = bfr + jaconv.kata2hira(bf.reading)


                hl = ''
                for v in self.p.finditer(s):
                    for i in v.group():
                        hl = hl + i

                rr = ''
                for h in hl:
                    rt = self.UnihanOnKun(h, bfr)
                    if not rt:
                        rt = self.UnihanOnKun(h, reading)

                    rr = rr + rt

                ra = s[len(self.p.match(s).group()):]

                if ra:
                    rr = rr[: -1 * len(ra)]

                if rr:
                    result = result + self.RubyFomet(hl,rr) + ra
                    continue

                print(f'error: notfound {s}, {rp}')
                result = result + s

            return result


    def TextToRuby(self, text):
        result = ''
        for token in self.t.tokenize(text):
            result = result + self.TokenToRuby(token)

        return result


    def FileToRuby(self, inputPath, outputPath):
        with open(inputPath, encoding='utf-8') as f:
            text = f.read()

        result = self.TextToRuby(text)

        with open(outputPath, mode='w', encoding='utf-8') as f:
            f.write(result)


def main():
    ### 説明

    # まずはインスタンスをつくるよ
    r = AutoRuby()


    ### 設定

    # Janome辞書のパスを指定できるよ。指定しなければJanome既定の辞書が使用されるよ。詳しくはJanomeの仕様を見てね。
    # r.TokenizerSet('./NEologd_dic')

    # ルビを振らない単語を指定できるよ。
    # r.NGList = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '〇']

    # ルビをカタカナに変える単語を指定できるよ。
    # r.kataList = ['ぺーじ', 'こーひー', 'びーる', 'きりすと', 'きりしたん', 'がす', 'めりやす', 'くらぶ', 'がらす', 'あじあ']

    # 常用漢字にはルビを振らないようにできるよ。既定はFalseだよ。
    # r.jouyouBlock = True

    # いちどルビを振った単語にはふたたび振らないようにできるよ。既定はTrueだよ。
    # r.duplicationBlock = False

    # ルビの形式を指定できるよ。aozora, pixiv, html を用意してあるよ。既定はaozoraだよ。
    # r.mode = 'pixiv'


    ### ルビ生成

    # テキストを放り込めばルビありテキストをつくれるよ。
    print(r.TextToRuby('白露に風の吹きしく秋の野はつらぬき留めぬ玉ぞ散りける　『後撰集』秋・308'))

    # テキストファイルを指定すればルビありファイルを出力できるよ。
    # r.FileToRuby('wesuto_minsuta_jiin_fix.txt', 'result.txt')

    print('Done.')


if __name__ == "__main__":
    main()