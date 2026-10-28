"""とうひょうくん（ヒョウ柄の投票箱ロボ）の絵を作る。2026-10-28 先生がB案（口をガーッと開ける）で採用。
viewBox は 0 0 64 84。体は y=22〜68。投票用紙は斜めに投票口へ刺さり、縦1行に「〇〇〇」。
"""
import math
import random

INK = "#1d2321"     # 線の色
BASE = "#ecd08c"    # ヒョウ柄の地（写真より明るめ）
RING = "#3b2412"    # 斑点のふち
CORE = "#b07a3c"    # 斑点の中

PINK = "#e8807e"
RED = "#7a2a24"
MOUTHS = {
    # 口を閉じているが目立つ：太い笑い口と口角
    "close": f'<path d="M24.5 55 Q32 62.5 39.5 55" fill="none" stroke="{INK}" stroke-width="2.8" stroke-linecap="round"/><path d="M23.6 53.6 L25.2 56" stroke="{INK}" stroke-width="2" stroke-linecap="round"/><path d="M40.4 53.6 L38.8 56" stroke="{INK}" stroke-width="2" stroke-linecap="round"/>',
    # 口をガーッと開ける：大きく開いた口と舌
    "open": f'<path d="M23.5 53 Q32 52 40.5 53 Q40 64 32 64.5 Q24 64 23.5 53Z" fill="{RED}" stroke="{INK}" stroke-width="2" stroke-linejoin="round"/><path d="M26.5 61 Q32 57 37.5 61 Q35 64 32 64.2 Q29 64 26.5 61Z" fill="{PINK}"/><path d="M24.5 53.6 L39.5 53.6" stroke="#fff" stroke-width="1.6" stroke-linecap="round"/>',
    # ネコ科の口：小さな鼻、ωの口、舌をぺろっと
    "cat": f'<path d="M30.2 52 L33.8 52 L32 54 Z" fill="{INK}" stroke="{INK}" stroke-width="1" stroke-linejoin="round"/><path d="M32 54 V55.6" stroke="{INK}" stroke-width="1.6" stroke-linecap="round"/><path d="M26.5 55 Q29.2 58.6 32 55.6 Q34.8 58.6 37.5 55" fill="none" stroke="{INK}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M30.3 57.2 Q30.2 61.6 32.8 61.4 Q35 61 34 57.2" fill="{PINK}" stroke="{INK}" stroke-width="1.2" stroke-linejoin="round"/><path d="M32.2 58 V60" stroke="#c45f5d" stroke-width="0.8" stroke-linecap="round"/>',
}


def rosette(x, y, r, rnd):
    """ヒョウの斑点：中が茶色、まわりが途切れた濃いふち。"""
    out = [f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{r*0.75:.1f}" ry="{r*0.6:.1f}" fill="{CORE}" transform="rotate({rnd.uniform(-40,40):.0f} {x:.1f} {y:.1f})"/>']
    n = rnd.choice([3, 4, 4, 5])
    start = rnd.uniform(0, 360)
    for i in range(n):
        a0 = start + i * 360 / n
        a1 = a0 + 360 / n * rnd.uniform(0.45, 0.75)
        p = []
        for a in (a0, (a0 + a1) / 2, a1):
            rr = r * rnd.uniform(1.0, 1.25)
            p.append((x + rr * math.cos(math.radians(a)), y + rr * 0.85 * math.sin(math.radians(a))))
        out.append(f'<path d="M{p[0][0]:.1f} {p[0][1]:.1f} Q{p[1][0]:.1f} {p[1][1]:.1f} {p[2][0]:.1f} {p[2][1]:.1f}" fill="none" stroke="{RING}" stroke-width="{rnd.uniform(1.1,1.6):.1f}" stroke-linecap="round"/>')
    return "".join(out)


def robot(uid="t", mouth="open"):
    rnd = random.Random(7)
    spots = []
    # 体の範囲に、目とメガネの部分を少しよけて斑点を敷きつめる
    for gy in range(0, 6):
        for gx in range(0, 6):
            x = 10 + gx * 8.6 + rnd.uniform(-2, 2) + (4 if gy % 2 else 0)
            y = 26 + gy * 8.2 + rnd.uniform(-1.5, 1.5)
            spots.append(rosette(x, y, rnd.uniform(2.0, 2.9), rnd))
    clip = f"clip-{uid}"
    return f'''<defs><clipPath id="{clip}"><rect x="8" y="22" width="48" height="46" rx="7"/></clipPath></defs>
<g stroke-linecap="round">
<path d="M8 42 L2 34" stroke="{INK}" stroke-width="3"/><circle cx="2" cy="33" r="3" fill="#fff" stroke="{INK}" stroke-width="1.5"/>
<path d="M56 42 L62 50" stroke="{INK}" stroke-width="3"/><circle cx="62" cy="51" r="3" fill="#fff" stroke="{INK}" stroke-width="1.5"/>
<path d="M22 68 L20 80" stroke="{INK}" stroke-width="3"/><path d="M42 68 L44 80" stroke="{INK}" stroke-width="3"/>
</g>
<ellipse cx="18" cy="81" rx="5" ry="2.6" fill="{INK}"/><ellipse cx="46" cy="81" rx="5" ry="2.6" fill="{INK}"/>
<rect x="8" y="22" width="48" height="46" rx="7" fill="{BASE}"/>
<g clip-path="url(#{clip})">{"".join(spots)}</g>
<rect x="8" y="22" width="48" height="46" rx="7" fill="none" stroke="{INK}" stroke-width="1.5"/>
<rect x="18" y="24.5" width="28" height="5" rx="2.5" fill="{INK}"/>
<clipPath id="{clip}-p"><rect x="0" y="0" width="64" height="27.6"/></clipPath>
<g clip-path="url(#{clip}-p)"><g transform="rotate(-16 32 27.5)">
<rect x="27.6" y="3" width="8.8" height="26" rx="0.8" fill="#fff" stroke="{INK}" stroke-width="1.3"/>
<g fill="none" stroke="{INK}" stroke-width="1"><circle cx="32" cy="8" r="1.8"/><circle cx="32" cy="13" r="1.8"/><circle cx="32" cy="18" r="1.8"/></g>
</g></g>
<circle cx="23" cy="41" r="7.6" fill="#fff" stroke="{INK}" stroke-width="2.4"/><circle cx="41" cy="41" r="7.6" fill="#fff" stroke="{INK}" stroke-width="2.4"/>
<path d="M30.6 40 Q32 38.4 33.4 40" fill="none" stroke="{INK}" stroke-width="2"/>
<path d="M15.4 39.5 L9 37.5" stroke="{INK}" stroke-width="2"/><path d="M48.6 39.5 L55 37.5" stroke="{INK}" stroke-width="2"/>
<circle cx="24" cy="42" r="3" fill="{INK}"/><circle cx="42" cy="42" r="3" fill="{INK}"/>
<circle cx="25" cy="40.8" r="0.9" fill="#fff"/><circle cx="43" cy="40.8" r="0.9" fill="#fff"/>

{MOUTHS[mouth]}'''


if __name__ == "__main__":
    print(robot())
