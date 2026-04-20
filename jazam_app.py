"""
JAZAM v2 — Juego de estrategia abstracta
7 niveles · 20 negras · 10 blancas · 3 azules
Streamlit app · 2 jugadores o vs IA · ES/EN
"""

import streamlit as st
import math
import time
import random

st.set_page_config(page_title="Jazam", page_icon="🔵", layout="centered",
                   initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:ital,wght@0,400;0,600;1,400&family=DM+Sans:wght@400;500&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif;}
.jazam-title{font-family:'Crimson Pro',serif;font-size:2.6rem;font-weight:600;color:#1C1A10;text-align:center;letter-spacing:0.08em;margin-bottom:0;}
.jazam-subtitle{font-family:'Crimson Pro',serif;font-style:italic;font-size:1rem;color:#BA7517;text-align:center;margin-bottom:1.2rem;}
.score-box{background:#F5F1E4;border-radius:12px;padding:10px 14px;text-align:center;border:1px solid #D3C8A0;}
.score-box.active{border:2px solid #BA7517;background:#FAEEDA;}
.score-box.active-ai{border:2px solid #185FA5;background:#E6F1FB;}
.score-name{font-size:0.75rem;color:#888;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:3px;}
.score-pts{font-size:1.8rem;font-weight:600;color:#1C1A10;line-height:1;}
.score-pts span{font-size:0.75rem;font-weight:400;color:#888;margin-left:3px;}
.status-bar{background:#F5F1E4;border-radius:8px;padding:10px 16px;text-align:center;font-size:0.88rem;color:#555;border:1px solid #D3C8A0;margin:8px 0;}
.status-bar b{color:#1C1A10;}
.status-bar.celestial{background:#C5E8FF;border-color:#185FA5;color:#0C447C;}
.status-bar.warning{background:#FCEBEB;border-color:#E24B4A;color:#A32D2D;}
.log-container{background:#F9F7F0;border:1px solid #D3C8A0;border-radius:10px;padding:10px 14px;max-height:180px;overflow-y:auto;font-size:0.78rem;}
.log-entry{padding:3px 0;border-bottom:1px solid #EDE8D5;}
.log-entry:last-child{border-bottom:none;}
.log-j1{color:#BA7517;font-weight:500;}
.log-j2{color:#185FA5;font-weight:500;}
.log-ai{color:#3B6D11;font-weight:500;}
.log-pts{color:#3B6D11;font-weight:600;}
.winner-box{background:#F5F1E4;border:2px solid #BA7517;border-radius:14px;padding:20px;text-align:center;margin-top:12px;}
.winner-title{font-family:'Crimson Pro',serif;font-size:1.9rem;font-weight:600;color:#1C1A10;margin-bottom:6px;}
.winner-scores{font-size:0.88rem;color:#666;}
.dot-row{display:flex;gap:3px;flex-wrap:wrap;margin-top:3px;justify-content:center;}
.dot{width:9px;height:9px;border-radius:50%;display:inline-block;}
.dot-black-on {background:#111110;border:1.5px solid #999990;}
.dot-black-off{background:#111110;border:1.5px solid #999990;opacity:0.15;}
.dot-white-on {background:#E8D44D;border:1.5px solid #B89A10;}
.dot-white-off{background:#E8D44D;border:1.5px solid #B89A10;opacity:0.15;}
.dot-blue-on  {background:#378ADD;border:1px solid #185FA5;}
.dot-blue-off {background:#378ADD;border:1px solid #185FA5;opacity:0.15;}
.rule-box{background:#F9F7F0;border-left:3px solid #BA7517;border-radius:0 8px 8px 0;padding:10px 14px;font-size:0.84rem;color:#444;margin-bottom:8px;}
.config-tag{font-size:11px;background:#EAF3DE;color:#27500A;border:0.5px solid #97C459;border-radius:10px;padding:2px 9px;margin-left:4px;}
@media(max-width:600px){
  .jazam-title{font-size:1.9rem!important;}
  .score-pts{font-size:1.4rem!important;}
  .dot{width:7px!important;height:7px!important;}
  .status-bar{font-size:0.78rem!important;padding:7px 10px!important;}
}
</style>
""", unsafe_allow_html=True)

# ── Constantes ────────────────────────────────────────────────────────────────
LEVELS = [64, 32, 16, 8, 4, 2, 1]   # 7 niveles, 127 espacios
INIT_PIECES = {"black": 20, "white": 10, "blue": 3}
MAXES = {"black": 20, "white": 10, "blue": 3}

# Puntos celestes: solo niveles 0-2 (niveles 1-3 del juego)
# Columnas: 12:00, 3:00, 6:00, 9:00
PTS_TABLE = [
    [12, 3, 6, 9],   # nivel 1
    [10, 2, 5, 7],   # nivel 2
    [8,  2, 4, 6],   # nivel 3
]

def is_celestial(li, si):
    if li >= 3: return False
    return si % (LEVELS[li] // 4) == 0

def space_pts(li, si):
    if li == 6: return 20
    if not is_celestial(li, si): return 0
    clock = si // (LEVELS[li] // 4)
    return PTS_TABLE[li][clock]

def aligned_next(li, si):
    next_n = LEVELS[li + 1]
    aligned = round(si * next_n / LEVELS[li]) % next_n
    return (aligned + 1) % next_n

def space_pos_svg(li, si, cx, cy, radii):
    if li == 6: return cx, cy
    a = -math.pi/2 + (si / LEVELS[li]) * math.pi * 2
    return cx + radii[li]*math.cos(a), cy + radii[li]*math.sin(a)

# ── Estado del juego ──────────────────────────────────────────────────────────
def init_game():
    return {
        "cp": 0, "scores": [0, 0],
        "pieces": [dict(INIT_PIECES), dict(INIT_PIECES)],
        "board": [[None]*n for n in LEVELS],
        "lv": 0, "next_si": 1,
        "to_place": 1, "placed_this_turn": 0,
        "last_color": None, "over": False,
        "log": [], "turn_count": 0,
        "winner": None, "win_reason": None,
    }

def valid_moves(G, cp=None):
    if cp is None: cp = G["cp"]
    pc = G["pieces"][cp]; lv = G["lv"]; si = G["next_si"]
    cel = is_celestial(lv, si); moves = []
    if pc["black"] > 0: moves.append("black")
    if pc["white"] > 0: moves.append("white")
    if pc["blue"] > 0 and lv < 3 and cel: moves.append("blue")
    return moves

def add_log(G, who, msg, pts=0):
    G["turn_count"] += 1
    G["log"].append({"turn": G["turn_count"], "who": who, "msg": msg, "pts": pts})

def adv_pointer(G, lv, si, cp, mode):
    all_filled = all(x is not None for x in G["board"][lv])
    if all_filled and lv < 6:
        G["scores"][cp] += 4
        who = "IA" if (mode == "ai" and cp == 1) else ("AI" if (mode == "ai" and cp == 1) else f"J{cp+1}")
        add_log(G, who, f"Nivel {lv+1} completo · Bono Arquitecto" if G.get("_es",True) else f"Level {lv+1} complete · Architect Bonus", 4)
        G["lv"] = lv + 1
        G["next_si"] = (round(si * LEVELS[lv+1] / LEVELS[lv]) + 1) % LEVELS[lv+1]
    else:
        G["next_si"] = (si + 1) % LEVELS[lv]

def do_play(G, piece_type, mode):
    if G["over"]: return
    cp = G["cp"]; pc = G["pieces"][cp]
    if piece_type == "black" and pc["black"] <= 0: return
    if piece_type == "white" and pc["white"] <= 0: return
    if piece_type == "blue" and (pc["blue"] <= 0 or G["lv"] >= 3 or not is_celestial(G["lv"], G["next_si"])): return

    lv = G["lv"]; si = G["next_si"]; cel = is_celestial(lv, si)
    pc[piece_type] -= 1
    G["board"][lv][si] = {"p": cp, "t": piece_type}
    G["last_color"] = piece_type
    G["placed_this_turn"] += 1

    pts = space_pts(lv, si)
    ES = G.get("_es", True)
    who = ("IA" if ES else "AI") if (mode == "ai" and cp == 1) else f"J{cp+1}"
    type_name = {"black": "negra" if ES else "black",
                 "white": "blanca" if ES else "white",
                 "blue":  "azul"   if ES else "blue"}[piece_type]
    clock_names = [" 12:00", " 3:00", " 6:00", " 9:00"]
    cel_note = f"{clock_names[si//(LEVELS[lv]//4)]} ({pts}pts)" if cel else ""

    if piece_type == "blue":
        G["scores"][cp] += pts
        if lv < 6: G["lv"] = lv + 1; G["next_si"] = aligned_next(lv, si)
        add_log(G, who, f"{type_name} Nv{lv+1}·esp{si+1}{cel_note} → Nv{G['lv']+1}", pts)
        G["placed_this_turn"] = 0; G["to_place"] = 1
        check_end(G, mode); return

    add_log(G, who, f"{type_name} Nv{lv+1}·esp{si+1}{cel_note}", 0)
    adv_pointer(G, lv, si, cp, mode)

    if G["placed_this_turn"] >= G["to_place"]:
        nxt = 2 if G["last_color"] == "white" else 1
        G["cp"] = 1 - cp; G["to_place"] = nxt; G["placed_this_turn"] = 0

    check_end(G, mode)

def check_end(G, mode):
    if G["lv"] == 6 and G["board"][6][0] is not None:
        who_idx = G["board"][6][0]["p"]
        G["scores"][who_idx] += 20
        ES = G.get("_es", True)
        who = ("IA" if ES else "AI") if (mode == "ai" and who_idx == 1) else f"J{who_idx+1}"
        add_log(G, who, "¡CENTRO ocupado!" if ES else "CENTER reached!", 20)
        G["over"] = True
        w = 0 if G["scores"][0] > G["scores"][1] else (1 if G["scores"][1] > G["scores"][0] else -1)
        G["winner"] = w; G["win_reason"] = "center"; return
    for p in range(2):
        pc = G["pieces"][p]
        if pc["black"] <= 0 and pc["white"] <= 0 and pc["blue"] <= 0:
            G["over"] = True; G["winner"] = 1 - p; G["win_reason"] = "nopcs"
            ES = G.get("_es", True)
            who = ("IA" if ES else "AI") if (mode == "ai" and p == 1) else f"J{p+1}"
            add_log(G, who, "sin piezas — pierde" if ES else "out of beads — loses", 0); return

# ── IA ────────────────────────────────────────────────────────────────────────
def ai_move(G, mode):
    moves = valid_moves(G, 1)
    if not moves: G["over"] = True; G["winner"] = 0; G["win_reason"] = "nopcs"; return
    lv = G["lv"]; si = G["next_si"]; cel = is_celestial(lv, si); pc = G["pieces"][1]
    choice = None
    if "blue" in moves and cel:
        pts = space_pts(lv, si)
        if pts >= 6: choice = "blue"
        elif pts >= 3 and random.random() > 0.45: choice = "blue"
    if not choice:
        use_white = "white" in moves and pc["white"] > 2 and (pc["black"]+pc["white"]) > 10 and random.random() > 0.5
        choice = "white" if use_white else ("black" if "black" in moves else moves[0])
    if choice not in moves: choice = moves[0]
    do_play(G, choice, mode)

# ── SVG del tablero ───────────────────────────────────────────────────────────
def render_board_svg(G):
    SIZE = 440
    cx = cy = SIZE // 2
    # 7 anillos — radios proporcionales
    radii = [int(cx * r) for r in [0.94, 0.80, 0.66, 0.52, 0.38, 0.25, 0.0]]

    lines = [f'<svg viewBox="0 0 {SIZE} {SIZE}" width="100%" style="max-width:{SIZE}px;display:block;margin:0 auto;" xmlns="http://www.w3.org/2000/svg">']

    # Fondo
    lines.append(f'<circle cx="{cx}" cy="{cy}" r="{cx-2}" fill="#F5F1E4" stroke="#D3C8A0" stroke-width="1.5"/>')

    # Pétalos mandala (primeros 3 niveles)
    for li in range(3):
        n = LEVELS[li]; rO = radii[li]+10; rI = radii[li+1]+10
        for k in range(8):
            si = k * n // 8
            a1 = -math.pi/2 + (si/n)*math.pi*2
            a2 = -math.pi/2 + ((si+n/8)/n)*math.pi*2
            x1i=cx+rI*math.cos(a1);y1i=cy+rI*math.sin(a1)
            x2o=cx+rO*math.cos(a1);y2o=cy+rO*math.sin(a1)
            x3o=cx+rO*math.cos(a2);y3o=cy+rO*math.sin(a2)
            x4i=cx+rI*math.cos(a2);y4i=cy+rI*math.sin(a2)
            lines.append(f'<path d="M{x1i:.1f},{y1i:.1f} L{x2o:.1f},{y2o:.1f} A{rO},{rO} 0 0,1 {x3o:.1f},{y3o:.1f} L{x4i:.1f},{y4i:.1f} A{rI},{rI} 0 0,0 {x1i:.1f},{y1i:.1f} Z" fill="rgba(120,90,40,0.07)"/>')

    # Anillos
    for li in range(6):
        r = radii[li] + 10
        lines.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="rgba(120,90,40,0.18)" stroke-width="0.8"/>')

    # Líneas radiales de reloj
    for i in range(4):
        a = -math.pi/2 + i*math.pi/2
        x1=cx+18*math.cos(a);y1=cy+18*math.sin(a)
        x2=cx+(cx-8)*math.cos(a);y2=cy+(cx-8)*math.sin(a)
        lines.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="rgba(120,90,40,0.13)" stroke-width="0.7" stroke-dasharray="2,5"/>')

    # Marcas de hora
    for i in range(12):
        a=-math.pi/2+i*math.pi/6; r1=cx-6; r2=r1-(5 if i%3==0 else 3)
        x1=cx+r1*math.cos(a);y1=cy+r1*math.sin(a)
        x2=cx+r2*math.cos(a);y2=cy+r2*math.sin(a)
        lines.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="rgba(120,90,40,0.25)" stroke-width="{1.5 if i%3==0 else 0.7}"/>')

    nlv = G["lv"]; nsi = G["next_si"]

    for li in range(7):
        n = LEVELS[li]
        for si in range(n):
            if li == 6:
                x, y = cx, cy; r_dot = 20
            else:
                a = -math.pi/2 + (si/n)*math.pi*2
                x = cx + radii[li]*math.cos(a)
                y = cy + radii[li]*math.sin(a)
                r_dot = 8 if li == 0 else 9 if li <= 2 else 9

            cel = is_celestial(li, si)
            is_next = (li == nlv and si == nsi and not G["over"])
            cell = G["board"][li][si]

            if li == 6:
                fill, stroke, sw = "#DDF0CC", "#3B6D11", 2
            elif is_next:
                fill, stroke, sw = "rgba(186,117,23,0.25)", "#BA7517", 2.5
            elif cel:
                fill, stroke, sw = "#C5E8FF", "#185FA5", 1.5
            else:
                fill, stroke, sw = "rgba(80,60,20,0.06)", "rgba(80,60,20,0.16)", 0.7

            lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r_dot}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

            if cel and cell is None and not is_next:
                pts = space_pts(li, si)
                fs = 7 if li == 0 else 8
                lines.append(f'<text x="{x:.1f}" y="{y+3:.1f}" text-anchor="middle" font-size="{fs}" fill="#0C447C" font-family="DM Sans,sans-serif">{pts}</text>')

            if li == 6 and cell is None:
                lines.append(f'<text x="{cx}" y="{cy+5}" text-anchor="middle" font-size="11" font-weight="600" fill="#27500A" font-family="DM Sans,sans-serif">20</text>')

            if cell:
                pr = r_dot - 2
                pf = {"black":"#111110","white":"#E8D44D","blue":"#378ADD"}[cell["t"]]
                ps = {"black":"#999990","white":"#B89A10","blue":"#185FA5"}[cell["t"]]
                lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{pr}" fill="{pf}" stroke="{ps}" stroke-width="1.5"/>')
                pd = "#BA7517" if cell["p"]==0 else "#185FA5"
                lines.append(f'<circle cx="{x:.1f}" cy="{y+pr-2:.1f}" r="1.8" fill="{pd}"/>')

    lines.append(f'<circle cx="{cx}" cy="{cy}" r="{cx-3}" fill="none" stroke="rgba(120,90,40,0.28)" stroke-width="1.5"/>')
    for i, lbl in enumerate(["12","3","6","9"]):
        a=-math.pi/2+i*math.pi/2
        lines.append(f'<text x="{cx+(cx+7)*math.cos(a):.1f}" y="{cy+(cx+7)*math.sin(a)+4:.1f}" text-anchor="middle" font-size="10" fill="rgba(90,65,30,0.5)" font-family="DM Sans,sans-serif">{lbl}</text>')

    lines.append("</svg>")
    return "\n".join(lines)

# ── Dots HTML ─────────────────────────────────────────────────────────────────
def render_dots(n, max_n, piece_type):
    dots = "".join(
        f'<span class="dot dot-{piece_type}-{"on" if i<n else "off"}"></span>'
        for i in range(max_n)
    )
    return f'<div class="dot-row">{dots}</div>'

def pieces_html(pc):
    rows = ""
    for t, max_n in [("black",20),("white",10),("blue",3)]:
        rows += f'<div style="margin-bottom:2px;">{render_dots(pc[t],max_n,t)} <small style="color:#888;">{pc[t]}</small></div>'
    return rows

# ── Inicialización ────────────────────────────────────────────────────────────
if "game" not in st.session_state: st.session_state.game = init_game()
if "mode" not in st.session_state: st.session_state.mode = "2p"
if "lang" not in st.session_state: st.session_state.lang = "ES"

G = st.session_state.game
mode = st.session_state.mode
G["_es"] = (st.session_state.lang == "ES")
ES = G["_es"]

# ── Header ────────────────────────────────────────────────────────────────────
col_title, col_lang = st.columns([3,1])
with col_title:
    st.markdown('<div class="jazam-title">JAZAM</div>', unsafe_allow_html=True)
with col_lang:
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    lang_sel = st.radio("", ["🇪🇸","🇬🇧"], horizontal=True, label_visibility="collapsed",
                        index=0 if ES else 1)
    st.session_state.lang = "ES" if lang_sel=="🇪🇸" else "EN"
    ES = G["_es"] = (st.session_state.lang == "ES")

st.markdown(f'<div class="jazam-subtitle">{"meditación competitiva" if ES else "competitive meditation"}</div>',
            unsafe_allow_html=True)

tab_game, tab_rules = st.tabs(["🎮 Juego" if ES else "🎮 Game",
                                "📖 Reglas" if ES else "📖 Rules"])

# ══════════════════════════════════════════════════════════════════════════════
# PESTAÑA REGLAS
# ══════════════════════════════════════════════════════════════════════════════
with tab_rules:
    st.divider()
    if ES:
        st.markdown("### ¿Qué es Jazam?")
        st.markdown('> *"Un mandala de decisiones donde cada pelotita puede cambiar tu destino."*')
        st.markdown("Jazam es un **juego de estrategia abstracta para 2 jugadores**. No se trata solo de llegar primero al centro — se trata de **llegar con más puntos**.")
        st.divider()
        st.markdown("### El tablero")
        st.markdown("Tablero circular con **7 niveles concéntricos** y **127 espacios**. Los espacios se recorren en orden **horario**, nivel por nivel, del exterior al centro.")
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("""
| Nivel | Espacios |
|-------|----------|
| 1 (exterior) | 64 |
| 2 | 32 |
| 3 | 16 |
| 4 | 8 |
| 5 | 4 |
| 6 | 2 |
| 7 — Centro | 1 |
""")
        with col_b:
            st.markdown("Los **espacios celestes** están en los niveles 1, 2 y 3, en las posiciones de **3:00, 6:00, 9:00 y 12:00**. Solo ahí se puede usar una pieza azul.")
        st.divider()
        st.markdown("### Piezas (por jugador)")
        c1,c2,c3 = st.columns(3)
        with c1: st.markdown('<div class="rule-box" style="text-align:center;"><span style="font-size:1.3rem;">⚫</span><br><b>20 Negras</b><br><small>El rival coloca 1 pieza en su próximo turno</small></div>', unsafe_allow_html=True)
        with c2: st.markdown('<div class="rule-box" style="text-align:center;"><span style="font-size:1.3rem;">🟡</span><br><b>10 Blancas</b><br><small>El rival coloca 2 piezas en su próximo turno</small></div>', unsafe_allow_html=True)
        with c3: st.markdown('<div class="rule-box" style="text-align:center;"><span style="font-size:1.3rem;">🔵</span><br><b>3 Azules</b><br><small>Solo en celeste → sube de nivel + repite turno</small></div>', unsafe_allow_html=True)
        st.divider()
        st.markdown("### Cómo jugar")
        st.markdown("En cada turno colocas piezas en el **siguiente espacio disponible** — siempre en la secuencia horaria, no puedes elegir.")
        st.markdown("""
| Última pieza del rival | Piezas que colocas |
|------------------------|-------------------|
| Negra o Azul | 1 pieza |
| Blanca | 2 piezas |

Si colocas 2, la **última** determina el efecto para el rival.
""")
        st.markdown('<div class="rule-box">🔵 <b>Azul</b> — solo en celeste (Nv 1–3). Ganas los puntos del celeste, subes al siguiente nivel, colocas en el espacio <b>siguiente al celeste alineado</b> del nuevo nivel, y <b>repites tu turno</b>.</div>', unsafe_allow_html=True)
        st.divider()
        st.markdown("### Puntuación")
        st.markdown("**Espacios celestes** — más lejos del inicio, más puntos:")
        st.markdown("""
| Nivel | 3:00 | 6:00 | 9:00 | 12:00 |
|-------|------|------|------|-------|
| 1 | 3 | 6 | 9 | **12** |
| 2 | 2 | 5 | 7 | **10** |
| 3 | 2 | 4 | 6 | **8** |
""")
        c1,c2 = st.columns(2)
        with c1: st.markdown('<div class="rule-box">🏛️ <b>Bono del Arquitecto (+4 pts)</b><br>El jugador que completa un nivel (1–6) recibe 4 puntos. No otorga turno extra.</div>', unsafe_allow_html=True)
        with c2: st.markdown('<div class="rule-box">🎯 <b>El Centro — Nivel 7 (+20 pts)</b><br>Colocar en el centro otorga 20 puntos y termina la partida inmediatamente.</div>', unsafe_allow_html=True)
        st.divider()
        st.markdown("### Fin del juego")
        st.markdown("""
- **Alguien ocupa el centro** → +20 pts · fin inmediato · gana quien tenga más puntos.
- **Un jugador se queda sin negras y blancas** → pierde automáticamente.
""")
        st.divider()
        st.markdown("### Estrategias")
        for tip, desc in [
            ("⚪ Presión con blancas","Cada blanca obliga al rival a colocar 2. Con 10 disponibles, úsalas en el momento correcto."),
            ("🔵 Guardar azules","Valen más en 12:00. Con 3 azules tienes más flexibilidad táctica."),
            ("🏛️ Bono del Arquitecto","Completar un nivel da +4 pts sin gastar azul. Hay 6 niveles para aprovechar este bono."),
            ("⚠️ Control de recursos","Sin negras ni blancas pierdes. El panel se pone en rojo cuando quedan ≤3 piezas."),
        ]:
            st.markdown(f'<div class="rule-box"><b>{tip}</b><br>{desc}</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;margin-top:2rem;font-style:italic;color:#BA7517;">"Jazam no es un juego… es una meditación competitiva."</div>', unsafe_allow_html=True)
    else:
        st.markdown("### What is Jazam?")
        st.markdown('> *"A mandala of decisions where every bead can change your fate."*')
        st.markdown("Jazam is an **abstract strategy game for 2 players**. It's not just about reaching the center first — it's about **getting there with more points**.")
        st.divider()
        st.markdown("### The Board")
        st.markdown("Circular board with **7 concentric levels** and **127 spaces**. Spaces are filled in **clockwise** order, level by level, from outside in.")
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("""
| Level | Spaces |
|-------|--------|
| 1 (outer) | 64 |
| 2 | 32 |
| 3 | 16 |
| 4 | 8 |
| 5 | 4 |
| 6 | 2 |
| 7 — Center | 1 |
""")
        with col_b:
            st.markdown("**Celestial spaces** are in levels 1, 2 and 3, at the **3:00, 6:00, 9:00 and 12:00** clock positions. Only blue beads can be placed there.")
        st.divider()
        st.markdown("### Beads (per player)")
        c1,c2,c3 = st.columns(3)
        with c1: st.markdown('<div class="rule-box" style="text-align:center;"><span style="font-size:1.3rem;">⚫</span><br><b>20 Black</b><br><small>Opponent places 1 bead next turn</small></div>', unsafe_allow_html=True)
        with c2: st.markdown('<div class="rule-box" style="text-align:center;"><span style="font-size:1.3rem;">🟡</span><br><b>10 White</b><br><small>Opponent places 2 beads next turn</small></div>', unsafe_allow_html=True)
        with c3: st.markdown('<div class="rule-box" style="text-align:center;"><span style="font-size:1.3rem;">🔵</span><br><b>3 Blue</b><br><small>Celestial only → advance level + repeat turn</small></div>', unsafe_allow_html=True)
        st.divider()
        st.markdown("### How to Play")
        st.markdown("Each turn you place beads in the **next available space** — always clockwise, no free choice.")
        st.markdown("""
| Opponent's last bead | Beads you place |
|----------------------|----------------|
| Black or Blue | 1 bead |
| White | 2 beads |

If you place 2, the **last** one determines the effect for your opponent.
""")
        st.markdown('<div class="rule-box">🔵 <b>Blue</b> — celestial only (Lv 1–3). Score the celestial points, advance one level, place on the space <b>after the aligned celestial</b> in the new level, and <b>take another turn</b>.</div>', unsafe_allow_html=True)
        st.divider()
        st.markdown("### Scoring")
        st.markdown("**Celestial spaces** — farther from start = more points:")
        st.markdown("""
| Level | 3:00 | 6:00 | 9:00 | 12:00 |
|-------|------|------|------|-------|
| 1 | 3 | 6 | 9 | **12** |
| 2 | 2 | 5 | 7 | **10** |
| 3 | 2 | 4 | 6 | **8** |
""")
        c1,c2 = st.columns(2)
        with c1: st.markdown('<div class="rule-box">🏛️ <b>Architect Bonus (+4 pts)</b><br>Player who completes a level (1–6) scores 4 bonus points. No extra turn.</div>', unsafe_allow_html=True)
        with c2: st.markdown('<div class="rule-box">🎯 <b>The Center — Level 7 (+20 pts)</b><br>Placing in the center scores 20 points and ends the game immediately.</div>', unsafe_allow_html=True)
        st.divider()
        st.markdown("### End of Game")
        st.markdown("""
- **Someone reaches the center** → +20 pts · immediate end · most points wins.
- **A player runs out of black and white beads** → automatic loss.
""")
        st.divider()
        st.markdown("### Strategies")
        for tip, desc in [
            ("⚪ White pressure","Each white forces your opponent to place 2. With 10 available, timing is everything."),
            ("🔵 Save your blues","Worth most at 12:00. With 3 blues you have more tactical flexibility."),
            ("🏛️ Architect Bonus","Completing a level gives +4 pts without spending a blue. 6 levels to exploit this."),
            ("⚠️ Resource control","No black or white = automatic loss. Panel turns red when ≤3 beads remain."),
        ]:
            st.markdown(f'<div class="rule-box"><b>{tip}</b><br>{desc}</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;margin-top:2rem;font-style:italic;color:#BA7517;">"Jazam is not a game… it\'s competitive meditation."</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PESTAÑA JUEGO
# ══════════════════════════════════════════════════════════════════════════════
with tab_game:
    # Modo + reset
    lbl_2p    = "👥 2 Jugadores"  if ES else "👥 2 Players"
    lbl_ai    = "🤖 vs IA"        if ES else "🤖 vs AI"
    lbl_reset = "↺ Nueva partida" if ES else "↺ New game"
    c1,c2,c3 = st.columns(3)
    with c1:
        if st.button(lbl_2p, use_container_width=True, type="primary" if mode=="2p" else "secondary"):
            st.session_state.mode="2p"; st.session_state.game=init_game(); st.rerun()
    with c2:
        if st.button(lbl_ai, use_container_width=True, type="primary" if mode=="ai" else "secondary"):
            st.session_state.mode="ai"; st.session_state.game=init_game(); st.rerun()
    with c3:
        if st.button(lbl_reset, use_container_width=True):
            st.session_state.game=init_game(); st.rerun()

    st.markdown(f'<div style="text-align:right;margin-top:-4px;"><span class="config-tag">7 {"niveles" if ES else "levels"} · 20⚫ · 10🟡 · 3🔵</span></div>', unsafe_allow_html=True)
    st.divider()

    # Paneles jugadores
    p1_name = "Jugador 1" if ES else "Player 1"
    p2_name = ("IA 🤖" if ES else "AI 🤖") if mode=="ai" else ("Jugador 2" if ES else "Player 2")
    p1_cls = "score-box active" if (G["cp"]==0 and not G["over"]) else "score-box"
    p2_cls = ("score-box active-ai" if mode=="ai" else "score-box active") if (G["cp"]==1 and not G["over"]) else "score-box"

    st.markdown(f"""
    <div style="display:flex;gap:10px;flex-wrap:wrap;">
      <div class="{p1_cls}" style="flex:1;min-width:110px;">
        <div class="score-name">{p1_name}</div>
        <div class="score-pts">{G['scores'][0]} <span>pts</span></div>
        <div>{pieces_html(G['pieces'][0])}</div>
      </div>
      <div class="{p2_cls}" style="flex:1;min-width:110px;">
        <div class="score-name">{p2_name}</div>
        <div class="score-pts">{G['scores'][1]} <span>pts</span></div>
        <div>{pieces_html(G['pieces'][1])}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Barra de estado
    if not G["over"]:
        cp=G["cp"]; lv=G["lv"]; si=G["next_si"]
        cel=is_celestial(lv,si); pts=space_pts(lv,si)
        rem=G["to_place"]-G["placed_this_turn"]
        total_left=G["pieces"][cp]["black"]+G["pieces"][cp]["white"]
        name=("IA" if ES else "AI") if (mode=="ai" and cp==1) else f"{'Jugador' if ES else 'Player'} {cp+1}"
        clock_labels=["12:00","3:00","6:00","9:00"]
        if total_left<=3:
            bar_cls="status-bar warning"
            txt=(f"⚠️ <b>{name}</b> — solo {total_left} piezas · Nv{lv+1} esp{si+1}"
                 if ES else f"⚠️ <b>{name}</b> — only {total_left} beads · Lv{lv+1} sp{si+1}")
        elif cel:
            clock=si//(LEVELS[lv]//4)
            bar_cls="status-bar celestial"
            txt=(f"★ <b>{name}</b> — coloca {rem} · Nv{lv+1} esp{si+1} · Celeste {clock_labels[clock]} = {pts}pts"
                 if ES else f"★ <b>{name}</b> — place {rem} · Lv{lv+1} sp{si+1} · Celestial {clock_labels[clock]} = {pts}pts")
        else:
            bar_cls="status-bar"
            txt=(f"<b>{name}</b> — coloca {rem} pieza{'s' if rem>1 else ''} · Nivel {lv+1} · espacio {si+1}"
                 if ES else f"<b>{name}</b> — place {rem} bead{'s' if rem>1 else ''} · Level {lv+1} · space {si+1}")
        st.markdown(f'<div class="{bar_cls}">{txt}</div>', unsafe_allow_html=True)

    # Tablero
    st.markdown(f'<div style="width:100%;max-width:440px;margin:8px auto;">{render_board_svg(G)}</div>',
                unsafe_allow_html=True)

    # Controles
    if not G["over"]:
        cp=G["cp"]; is_human=not(mode=="ai" and cp==1)
        moves=valid_moves(G); pc=G["pieces"][cp]
        if is_human:
            c1,c2,c3=st.columns(3)
            with c1:
                lbl=f"⚫ {'Negra' if ES else 'Black'} ({pc['black']})"
                if st.button(lbl,disabled="black" not in moves,use_container_width=True,key="btn_black"):
                    do_play(G,"black",mode); st.rerun()
            with c2:
                lbl=f"🟡 {'Blanca' if ES else 'White'} ({pc['white']})"
                if st.button(lbl,disabled="white" not in moves,use_container_width=True,key="btn_white"):
                    do_play(G,"white",mode); st.rerun()
            with c3:
                lbl=f"🔵 {'Azul' if ES else 'Blue'} ({pc['blue']})"
                if st.button(lbl,disabled="blue" not in moves,use_container_width=True,key="btn_blue"):
                    do_play(G,"blue",mode); st.rerun()
        else:
            st.info("🤖 La IA está pensando..." if ES else "🤖 AI is thinking...", icon="⏳")
            time.sleep(0.6); ai_move(G,mode); st.rerun()

    # Banner ganador
    if G["over"]:
        p2_label=("IA" if ES else "AI") if mode=="ai" else ("Jugador 2" if ES else "Player 2")
        winner=G.get("winner"); reason=G.get("win_reason")
        if winner==-1:
            title="¡Empate!" if ES else "It's a tie!"
            desc=f"J1: {G['scores'][0]}pts — {p2_label}: {G['scores'][1]}pts"
        elif winner==0:
            title=("¡Jugador 1 gana! 🎉" if ES else "Player 1 wins! 🎉")
            desc=f"J1: {G['scores'][0]}pts — {p2_label}: {G['scores'][1]}pts"
            if reason=="nopcs": desc+=f" · {p2_label} {'se quedó sin piezas' if ES else 'ran out of beads'}"
        else:
            title=(f"¡{p2_label} gana! 🎉" if ES else f"{p2_label} wins! 🎉")
            desc=f"J1: {G['scores'][0]}pts — {p2_label}: {G['scores'][1]}pts"
            if reason=="nopcs": desc+=(" · Jugador 1 se quedó sin piezas" if ES else " · Player 1 ran out of beads")
        st.markdown(f'<div class="winner-box"><div class="winner-title">{title}</div><div class="winner-scores">{desc}</div></div>',
                    unsafe_allow_html=True)

    # Historial
    if G["log"]:
        st.markdown("#### Historial de jugadas" if ES else "#### Game log")
        entries=""
        for e in reversed(G["log"]):
            who=e["who"]; wc="log-j1" if who in("J1","P1") else("log-ai" if who in("IA","AI") else "log-j2")
            pts_html=f' <span class="log-pts">+{e["pts"]}</span>' if e["pts"]>0 else ""
            entries+=f'<div class="log-entry"><span style="color:#aaa;">#{e["turn"]}</span> <span class="{wc}">{who}</span> {e["msg"]}{pts_html}</div>'
        st.markdown(f'<div class="log-container">{entries}</div>', unsafe_allow_html=True)
