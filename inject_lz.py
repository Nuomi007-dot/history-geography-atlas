# -*- coding: utf-8 -*-
"""稳健注入《龙族》原文到 index.html 标记的 quote 字段。
策略：按 title 行定位标记块，找到该块闭合 `},`，删除块内旧 quote 行，
在闭合前插入一行新 quote，并确保前一行带尾逗号。不重建整个对象。
"""
import io

HTML = 'index.html'
SQ = chr(39)   # '
BS = chr(92)   # \


def load_text(path):
    with io.open(path, 'r', encoding='utf-8') as f:
        return f.read()


def jvesc(t):
    """转义为合法的 JS 单引号字符串字面量。"""
    t = t.replace(BS, BS + BS)             # 反斜杠
    t = t.replace(SQ, BS + SQ)             # 单引号（含 '夔门' 等）
    t = t.replace(chr(13), '').replace(chr(10), BS + 'n')  # 换行 -> \n
    return t.strip()


def inject(title, raw_text, lines):
    # 1. 定位 title 行（仅匹配 title: 开头，避免命中 note 里的同名）
    ti = None
    for i, ln in enumerate(lines):
        if ln.strip().startswith('title:') and title in ln:
            ti = i
            break
    if ti is None:
        raise SystemExit('title not found: ' + title)

    # 2. 找到该块闭合行（其后第一个 strip 后恰为 '},' 的行）
    ci = None
    for j in range(ti + 1, len(lines)):
        if lines[j].strip() == '},':
            ci = j
            break
    if ci is None:
        raise SystemExit('close }, not found: ' + title)

    # 3. 收集块内原有行，剔除旧 quote 行
    inner = []
    for k in range(ti + 1, ci):
        if lines[k].strip().startswith('quote:'):
            continue
        inner.append(lines[k])

    # 4. 确保 inner 最后一行以逗号结尾（原块末属性常无逗号）
    if inner:
        last = inner[-1].rstrip('\n')
        if not last.rstrip().endswith(','):
            inner[-1] = last + ',\n'
        else:
            inner[-1] = last + '\n'

    # 5. 构造插入行（4 空格缩进，与属性对齐，末属性带逗号）
    quote_line = "    quote: '" + jvesc(raw_text) + "',\n"

    # 6. 重组：title 行 + 原内部行(已补逗号) + 新 quote 行 + 闭合行及之后
    return lines[:ti + 1] + inner + [quote_line] + lines[ci:]


# ---- 准备三段原文 ----
# 白帝城：取最后一个“序章 白帝城”之后的正文（跳过目录与章节标题行）
baidi = load_text('LZ_BaiDi.txt')
i = baidi.rfind('序章 白帝城（Bai Di Cheng）')
baidi = baidi[i:]
nl = baidi.find('\n')
baidi = baidi[nl + 1:].strip()

# 卡塞尔：整封邀请信 + 路明非反应
cassell = load_text('LZ_Cassell.txt').strip()

# 三峡：只取前半段夔门/青铜城场景，截断在“夜深人静”（后面是芝加哥宿舍场景）
bronze = load_text('LZ_Bronze.txt')
cut = bronze.find('夜深人静')
bronze = bronze[:cut].strip()

# ---- 注入 ----
with io.open(HTML, 'r', encoding='utf-8') as f:
    lines = f.readlines()

lines = inject('白帝城 · 青铜城入口 (龙族Ⅰ)', baidi, lines)
lines = inject('卡塞尔学院 (龙族系列)', cassell, lines)
lines = inject('三峡大坝 · 青铜城遗迹 (龙族Ⅰ)', bronze, lines)

with io.open(HTML, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('injected. baidi=%d cassell=%d bronze=%d chars'
      % (len(baidi), len(cassell), len(bronze)))
