"""
JAZAM — Juego de estrategia abstracta
Streamlit app · 2 jugadores o vs IA
Configuración: 12 negras · 6 blancas · 2 azules
"""

import streamlit as st
import math
import time
import random

# ── Configuración de página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Jazam",
    page_icon="🔵",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── CSS personalizado ─────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:ital,wght@0,400;0,600;1,400&family=DM+Sans:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

.jazam-title {
    font-family: 'Crimson Pro', serif;
    font-size: 2.8rem;
    font-weight: 600;
    color: #1C1A10;
    text-align: center;
    letter-spacing: 0.08em;
    margin-bottom: 0;
}
.jazam-subtitle {
    font-family: 'Crimson Pro', serif;
    font-style: italic;
    font-size: 1rem;
    color: #BA7517;
    text-align: center;
    margin-bottom: 1.5rem;
}
.score-box {
    background: #F5F1E4;
    border-radius: 12px;
    padding: 14px 18px;
    text-align: center;
    border: 1px solid #D3C8A0;
}
.score-box.active {
    border: 2px solid #BA7517;
    background: #FAEEDA;
}
.score-box.active-ai {
    border: 2px solid #185FA5;
    background: #E6F1FB;
}
.score-name {
    font-size: 0.8rem;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 4px;
}
.score-pts {
    font-size: 2rem;
    font-weight: 600;
    color: #1C1A10;
    line-height: 1;
}
.score-pts span { font-size: 0.8rem; font-weight: 400; color: #888; margin-left: 4px; }
.pieces-row { font-size: 0.8rem; color: #555; margin-top: 6px; line-height: 1.6; }
.status-bar {
    background: #F5F1E4;
    border-radius: 8px;
    padding: 10px 16px;
    text-align: center;
    font-size: 0.9rem;
    color: #555;
    border: 1px solid #D3C8A0;
    margin: 8px 0;
}
.status-bar b { color: #1C1A10; }
.status-bar.celestial { background: #C5E8FF; border-color: #185FA5; color: #0C447C; }
.status-bar.warning { background: #FCEBEB; border-color: #E24B4A; color: #A32D2D; }
.log-container {
    background: #F9F7F0;
    border: 1px solid #D3C8A0;
    border-radius: 10px;
    padding: 10px 14px;
    max-height: 200px;
    overflow-y: auto;
    font-size: 0.8rem;
}
.log-entry { padding: 3px 0; border-bottom: 1px solid #EDE8D5; }
.log-entry:last-child { border-bottom: none; }
.log-j1 { color: #BA7517; font-weight: 500; }
.log-j2 { color: #185FA5; font-weight: 500; }
.log-ai { color: #3B6D11; font-weight: 500; }
.log-pts { color: #3B6D11; font-weight: 600; }
.winner-box {
    background: #F5F1E4;
    border: 2px solid #BA7517;
    border-radius: 14px;
    padding: 24px;
    text-align: center;
    margin-top: 12px;
}
.winner-title {
    font-family: 'Crimson Pro', serif;
    font-size: 2rem;
    font-weight: 600;
    color: #1C1A10;
    margin-bottom: 6px;
}
.winner-scores { font-size: 0.9rem; color: #666; }
.dot-row { display: flex; gap: 4px; flex-wrap: wrap; margin-top: 4px; justify-content: center; }
.dot { width: 11px; height: 11px; border-radius: 50%; display: inline-block; }
.dot-black-on  { background: #111110; border: 1.5px solid #999990; }
.dot-black-off { background: #111110; border: 1.5px solid #999990; opacity: 0.15; }
.dot-white-on  { background: #E8D44D; border: 1.5px solid #B89A10; }
.dot-white-off { background: #E8D44D; border: 1.5px solid #B89A10; opacity: 0.15; }
.dot-blue-on   { background: #378ADD; border: 1px solid #185FA5; }
.dot-blue-off  { background: #378ADD; border: 1px solid #185FA5; opacity: 0.15; }
.stButton button {
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
}
.rule-box {
    background: #F9F7F0;
    border-left: 3px solid #BA7517;
    border-radius: 0 8px 8px 0;
    padding: 10px 14px;
    font-size: 0.85rem;
    color: #444;
    margin-bottom: 8px;
}
/* Responsive móvil */
@media (max-width: 600px) {
    .jazam-title { font-size: 2rem !important; }
    .jazam-subtitle { font-size: 0.9rem !important; }
    .score-box { padding: 8px 10px !important; }
    .score-pts { font-size: 1.5rem !important; }
    .score-name { font-size: 0.7rem !important; }
    .pdot, .dot { width: 8px !important; height: 8px !important; }
    .status-bar { font-size: 0.8rem !important; padding: 8px 10px !important; }
    .log-container { font-size: 0.75rem !important; }
}
</style>
""", unsafe_allow_html=True)

# ── Constantes del juego ──────────────────────────────────────────────────────
LEVELS = [32, 16, 8, 4, 2, 1]   # espacios por nivel
INIT_PIECES = {"black": 12, "white": 6, "blue": 2}

PTS_TABLE = [
    [12, 3, 6, 9],   # nivel 1: idx0=12:00, idx1=3:00, idx2=6:00, idx3=9:00
    [8,  2, 4, 6],   # nivel 2
    [4,  1, 2, 3],   # nivel 3
]

def is_celestial(li, si):
    if li >= 3:
        return False
    n = LEVELS[li]
    return si % (n // 4) == 0

def space_pts(li, si):
    if li == 5:
        return 16
    if not is_celestial(li, si):
        return 0
    n = LEVELS[li]
    clock = si // (n // 4)
    return PTS_TABLE[li][clock]

def aligned_next(li, si):
    next_n = LEVELS[li + 1]
    aligned = round(si * next_n / LEVELS[li]) % next_n
    return (aligned + 1) % next_n

def space_angle(li, si):
    n = LEVELS[li]
    return -math.pi / 2 + (si / n) * math.pi * 2

def space_xy(li, si, cx, cy, radii):
    if li == 5:
        return cx, cy
    a = space_angle(li, si)
    r = radii[li]
    return cx + r * math.cos(a), cy + r * math.sin(a)

# ── Estado del juego ──────────────────────────────────────────────────────────
def init_game():
    return {
        "cp": 0,
        "scores": [0, 0],
        "pieces": [dict(INIT_PIECES), dict(INIT_PIECES)],
        "board": [[None] * n for n in LEVELS],
        "lv": 0,
        "next_si": 1,
        "to_place": 1,
        "placed_this_turn": 0,
        "last_color": None,
        "over": False,
        "log": [],
        "turn_count": 0,
        "winner": None,
        "win_reason": None,
    }

def valid_moves(G, cp=None):
    if cp is None:
        cp = G["cp"]
    pc = G["pieces"][cp]
    lv, si = G["lv"], G["next_si"]
    cel = is_celestial(lv, si)
    moves = []
    if pc["black"] > 0:
        moves.append("black")
    if pc["white"] > 0:
        moves.append("white")
    if pc["blue"] > 0 and lv < 3 and cel:
        moves.append("blue")
    return moves

def add_log(G, who, msg, pts=0):
    G["turn_count"] += 1
    G["log"].append({"turn": G["turn_count"], "who": who, "msg": msg, "pts": pts})

def adv_pointer(G, lv, si, cp, mode):
    board = G["board"]
    all_filled = all(x is not None for x in board[lv])
    if all_filled and lv < 5:
        G["scores"][cp] += 4
        who = "IA" if (mode == "ai" and cp == 1) else f"J{cp+1}"
        add_log(G, who, f"¡Nivel {lv+1} completo! Bono Arquitecto", 4)
        G["lv"] = lv + 1
        G["next_si"] = (round(si * LEVELS[lv+1] / LEVELS[lv]) + 1) % LEVELS[lv+1]
    else:
        G["next_si"] = (si + 1) % LEVELS[lv]

def do_play(G, piece_type, mode):
    if G["over"]:
        return
    cp = G["cp"]
    pc = G["pieces"][cp]
    lv, si = G["lv"], G["next_si"]
    cel = is_celestial(lv, si)

    # Validar
    if piece_type == "black" and pc["black"] <= 0:
        return
    if piece_type == "white" and pc["white"] <= 0:
        return
    if piece_type == "blue" and (pc["blue"] <= 0 or lv >= 3 or not cel):
        return

    pc[piece_type] -= 1
    G["board"][lv][si] = {"p": cp, "t": piece_type}
    G["last_color"] = piece_type
    G["placed_this_turn"] += 1

    pts = space_pts(lv, si)
    who = "IA" if (mode == "ai" and cp == 1) else f"J{cp+1}"
    type_name = {"black": "negra", "white": "blanca", "blue": "azul"}[piece_type]
    clock_names = [" 12:00", " 3:00", " 6:00", " 9:00"]
    cel_note = ""
    if cel:
        clock = si // (LEVELS[lv] // 4)
        cel_note = f"{clock_names[clock]} ({pts}pts)"

    if piece_type == "blue":
        G["scores"][cp] += pts
        if lv < 5:
            G["lv"] = lv + 1
            G["next_si"] = aligned_next(lv, si)
        add_log(G, who, f"{type_name} Nv{lv+1}·esp{si+1}{cel_note} → Nv{G['lv']+1}", pts)
        G["placed_this_turn"] = 0
        G["to_place"] = 1
        check_end(G, mode)
        return

    add_log(G, who, f"{type_name} Nv{lv+1}·esp{si+1}{cel_note}", 0)
    adv_pointer(G, lv, si, cp, mode)

    if G["placed_this_turn"] >= G["to_place"]:
        nxt = 2 if G["last_color"] == "white" else 1
        G["cp"] = 1 - cp
        G["to_place"] = nxt
        G["placed_this_turn"] = 0

    check_end(G, mode)

def check_end(G, mode):
    # Centro ocupado
    if G["lv"] == 5 and G["board"][5][0] is not None:
        who_idx = G["board"][5][0]["p"]
        G["scores"][who_idx] += 16
        who = "IA" if (mode == "ai" and who_idx == 1) else f"J{who_idx+1}"
        add_log(G, who, "¡CENTRO ocupado!", 16)
        G["over"] = True
        G["win_reason"] = "center"
        w = 0 if G["scores"][0] > G["scores"][1] else (1 if G["scores"][1] > G["scores"][0] else -1)
        G["winner"] = w
        return
    # Sin piezas
    for p in range(2):
        pc = G["pieces"][p]
        if pc["black"] <= 0 and pc["white"] <= 0 and pc["blue"] <= 0:
            G["over"] = True
            G["win_reason"] = "nopcs"
            G["winner"] = 1 - p
            who = "IA" if (mode == "ai" and p == 1) else f"J{p+1}"
            add_log(G, who, "sin piezas — pierde", 0)
            return

# ── IA ────────────────────────────────────────────────────────────────────────
def ai_move(G, mode):
    moves = valid_moves(G, 1)
    if not moves:
        G["over"] = True
        G["winner"] = 0
        G["win_reason"] = "nopcs"
        return
    lv, si = G["lv"], G["next_si"]
    cel = is_celestial(lv, si)
    pc = G["pieces"][1]
    choice = None

    if "blue" in moves and cel:
        pts = space_pts(lv, si)
        if pts >= 6:
            choice = "blue"
        elif pts >= 3 and random.random() > 0.45:
            choice = "blue"

    if not choice:
        use_white = (
            "white" in moves and
            pc["white"] > 1 and
            (pc["black"] + pc["white"]) > 6 and
            random.random() > 0.5
        )
        if use_white:
            choice = "white"
        elif "black" in moves:
            choice = "black"
        else:
            choice = moves[0]

    if choice not in moves:
        choice = moves[0]

    do_play(G, choice, mode)

# ── Dibujo del tablero con SVG ────────────────────────────────────────────────
def render_board_svg(G):
    SIZE = 420
    cx = cy = SIZE // 2
    radii = [int(cx * r) for r in [0.92, 0.74, 0.57, 0.40, 0.26, 0.0]]

    lines = [f'<svg viewBox="0 0 {SIZE} {SIZE}" width="100%" style="max-width:{SIZE}px;display:block;margin:0 auto;" xmlns="http://www.w3.org/2000/svg">']

    # Fondo
    lines.append(f'<circle cx="{cx}" cy="{cy}" r="{cx-2}" fill="#F5F1E4" stroke="#D3C8A0" stroke-width="2"/>')

    # Pétalos mandala
    for li in range(3):
        n = LEVELS[li]
        rO = radii[li] + 11
        rI = radii[li+1] + 11
        for k in range(8):
            si = k * n // 8
            a1 = -math.pi/2 + (si/n)*math.pi*2
            a2 = -math.pi/2 + ((si + n/8)/n)*math.pi*2
            x1i = cx + rI*math.cos(a1); y1i = cy + rI*math.sin(a1)
            x2o = cx + rO*math.cos(a1); y2o = cy + rO*math.sin(a1)
            x3o = cx + rO*math.cos(a2); y3o = cy + rO*math.sin(a2)
            x4i = cx + rI*math.cos(a2); y4i = cy + rI*math.sin(a2)
            lines.append(
                f'<path d="M{x1i:.1f},{y1i:.1f} L{x2o:.1f},{y2o:.1f} '
                f'A{rO},{rO} 0 0,1 {x3o:.1f},{y3o:.1f} '
                f'L{x4i:.1f},{y4i:.1f} '
                f'A{rI},{rI} 0 0,0 {x1i:.1f},{y1i:.1f} Z" '
                f'fill="rgba(120,90,40,0.07)"/>'
            )

    # Anillos
    for li in range(5):
        r = radii[li] + 11
        lines.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="rgba(120,90,40,0.2)" stroke-width="1"/>')

    # Líneas radiales de reloj
    for i in range(4):
        a = -math.pi/2 + i*math.pi/2
        x1 = cx + 18*math.cos(a); y1 = cy + 18*math.sin(a)
        x2 = cx + (cx-8)*math.cos(a); y2 = cy + (cx-8)*math.sin(a)
        lines.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="rgba(120,90,40,0.15)" stroke-width="0.8" stroke-dasharray="2,5"/>')

    # Marcas de hora
    for i in range(12):
        a = -math.pi/2 + i*math.pi/6
        r1 = cx - 6
        r2 = r1 - (5 if i % 3 == 0 else 3)
        x1 = cx+r1*math.cos(a); y1 = cy+r1*math.sin(a)
        x2 = cx+r2*math.cos(a); y2 = cy+r2*math.sin(a)
        w = 1.5 if i % 3 == 0 else 0.8
        lines.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="rgba(120,90,40,0.3)" stroke-width="{w}"/>')

    nlv = G["lv"]
    nsi = G["next_si"]

    # Espacios
    for li in range(6):
        n = LEVELS[li]
        for si in range(n):
            if li == 5:
                x, y = cx, cy
                r_dot = 20
            else:
                a = -math.pi/2 + (si/n)*math.pi*2
                r_ring = radii[li]
                x = cx + r_ring*math.cos(a)
                y = cy + r_ring*math.sin(a)
                r_dot = 9

            cel = is_celestial(li, si)
            is_next = (li == nlv and si == nsi and not G["over"])
            cell = G["board"][li][si]

            # Fondo del espacio
            if li == 5:
                fill, stroke, sw = "#DDF0CC", "#3B6D11", 2
            elif is_next:
                fill, stroke, sw = "rgba(186,117,23,0.25)", "#BA7517", 2.5
            elif cel:
                fill, stroke, sw = "#C5E8FF", "#185FA5", 1.5
            else:
                fill, stroke, sw = "rgba(80,60,20,0.06)", "rgba(80,60,20,0.18)", 0.8

            lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r_dot}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

            # Puntos en celestes vacíos
            if cel and cell is None and not is_next and li < 3:
                pts = space_pts(li, si)
                fs = 7 if li == 0 else 8
                lines.append(f'<text x="{x:.1f}" y="{y+3:.1f}" text-anchor="middle" font-size="{fs}" fill="#0C447C" font-family="DM Sans, sans-serif">{pts}</text>')

            # Label centro vacío
            if li == 5 and cell is None:
                lines.append(f'<text x="{cx}" y="{cy+5}" text-anchor="middle" font-size="11" font-weight="600" fill="#27500A" font-family="DM Sans, sans-serif">16</text>')

            # Pieza colocada
            if cell is not None:
                t = cell["t"]
                p = cell["p"]
                pr = r_dot - 2
                # Negra: negro carbón con borde plateado
                # Blanca: amarillo cálido con borde dorado — completamente distinto al negro y al fondo
                # Azul: azul vibrante
                pf = {"black": "#111110", "white": "#E8D44D", "blue": "#378ADD"}[t]
                ps = {"black": "#999990", "white": "#B89A10", "blue": "#185FA5"}[t]
                sw = {"black": 1.5, "white": 2, "blue": 1.5}[t]
                lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{pr}" fill="{pf}" stroke="{ps}" stroke-width="{sw}"/>')
                # Dot de jugador
                pd_color = "#BA7517" if p == 0 else "#185FA5"
                dy = pr - 2.5
                lines.append(f'<circle cx="{x:.1f}" cy="{y+dy:.1f}" r="2" fill="{pd_color}"/>')

    # Borde exterior
    lines.append(f'<circle cx="{cx}" cy="{cy}" r="{cx-3}" fill="none" stroke="rgba(120,90,40,0.3)" stroke-width="1.5"/>')

    # Etiquetas de reloj
    for i, lbl in enumerate(["12", "3", "6", "9"]):
        a = -math.pi/2 + i*math.pi/2
        lx = cx + (cx+6)*math.cos(a)
        ly = cy + (cx+6)*math.sin(a)
        lines.append(f'<text x="{lx:.1f}" y="{ly+4:.1f}" text-anchor="middle" font-size="10" fill="rgba(90,65,30,0.55)" font-family="DM Sans, sans-serif">{lbl}</text>')

    lines.append("</svg>")
    return "\n".join(lines)

# ── Renderizar piezas como dots HTML ─────────────────────────────────────────
def render_dots(n, max_n, piece_type):
    cls_on  = f"dot dot-{piece_type}-on"
    cls_off = f"dot dot-{piece_type}-off"
    dots = "".join(
        f'<span class="{cls_on if i < n else cls_off}"></span>'
        for i in range(max_n)
    )
    return f'<div class="dot-row">{dots}</div>'

def pieces_html(pc, mode, player_idx):
    maxes = {"black": 12, "white": 6, "blue": 2}
    label = "IA" if (mode == "ai" and player_idx == 1) else f"Jugador {player_idx+1}"
    rows = ""
    for t, emoji, max_n in [("black", "⚫", 12), ("white", "⚪", 6), ("blue", "🔵", 2)]:
        n = pc[t]
        rows += f'<div style="margin-bottom:3px;">{render_dots(n, max_n, t)} <small style="color:#888;">{n}</small></div>'
    return rows

# ── sidebar vacío ─────────────────────────────────────────────────────────────

# ── Inicialización del estado ─────────────────────────────────────────────────
if "game" not in st.session_state:
    st.session_state.game = init_game()
if "mode" not in st.session_state:
    st.session_state.mode = "2p"
if "ai_turn" not in st.session_state:
    st.session_state.ai_turn = False
if "lang" not in st.session_state:
    st.session_state.lang = "ES"

G = st.session_state.game
mode = st.session_state.mode

# ── Header + selector de idioma ───────────────────────────────────────────────
col_title, col_lang = st.columns([3, 1])
with col_title:
    st.markdown('<div class="jazam-title">JAZAM</div>', unsafe_allow_html=True)
with col_lang:
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    lang_sel = st.radio("", ["🇪🇸", "🇬🇧"], horizontal=True,
                        label_visibility="collapsed",
                        index=0 if st.session_state.lang == "ES" else 1)
    st.session_state.lang = "ES" if lang_sel == "🇪🇸" else "EN"

ES = st.session_state.lang == "ES"

subtitle = "meditación competitiva" if ES else "competitive meditation"
st.markdown(f'<div class="jazam-subtitle">{subtitle}</div>', unsafe_allow_html=True)

# ── Pestañas ──────────────────────────────────────────────────────────────────
tab_label_game  = "🎮 Juego"  if ES else "🎮 Game"
tab_label_rules = "📖 Reglas" if ES else "📖 Rules"
tab_game, tab_rules = st.tabs([tab_label_game, tab_label_rules])

# ══════════════════════════════════════════════════════════════════════════════
# PESTAÑA: REGLAS
# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
# PESTAÑA: REGLAS
# ══════════════════════════════════════════════════════════════════════════════
with tab_rules:
    st.divider()

    if ES:
        st.markdown("### ¿Qué es Jazam?")
        st.markdown("""
Jazam es un **juego de estrategia abstracta para 2 jugadores** donde cada movimiento cuenta.
No se trata solo de llegar primero al centro — se trata de **llegar con más puntos**.

> *"Un mandala de decisiones donde cada pelotita puede cambiar tu destino."*
""")
        st.divider()
        st.markdown("### El tablero")
        st.markdown("El tablero es circular con **6 niveles concéntricos** y **63 espacios** en total. Los espacios se recorren en orden **horario**, nivel por nivel, del exterior al centro.")
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("""
| Nivel | Espacios |
|-------|----------|
| 1 (exterior) | 32 |
| 2 | 16 |
| 3 | 8 |
| 4 | 4 |
| 5 | 2 |
| 6 — Centro | 1 |
""")
        with col_b:
            st.markdown("""
Los **espacios celestes** están en los niveles 1, 2 y 3, en las posiciones equivalentes a las **3:00, 6:00, 9:00 y 12:00** de un reloj.

Son los únicos espacios donde se puede colocar una pieza azul, y otorgan puntos al jugador que las usa.
""")
        st.divider()
        st.markdown("### Piezas (por jugador)")
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            st.markdown('<div class="rule-box" style="text-align:center;"><span style="font-size:1.4rem;">⚫</span><br><b>12 Negras</b><br><small>El rival coloca 1 pieza en su próximo turno</small></div>', unsafe_allow_html=True)
        with col_p2:
            st.markdown('<div class="rule-box" style="text-align:center;"><span style="font-size:1.4rem;">🟡</span><br><b>6 Blancas</b><br><small>El rival coloca 2 piezas en su próximo turno</small></div>', unsafe_allow_html=True)
        with col_p3:
            st.markdown('<div class="rule-box" style="text-align:center;"><span style="font-size:1.4rem;">🔵</span><br><b>2 Azules</b><br><small>Solo en celeste → sube de nivel + repite turno</small></div>', unsafe_allow_html=True)
        st.divider()
        st.markdown("### Cómo jugar")
        st.markdown("En cada turno, el jugador activo coloca piezas en el **siguiente espacio disponible** — no se puede elegir, siempre es el siguiente en la secuencia horaria.")
        st.markdown("**¿Cuántas piezas se colocan?**")
        st.markdown("""
| Última pieza del rival | Piezas que debes colocar |
|------------------------|--------------------------|
| Negra o Azul | 1 pieza |
| Blanca | 2 piezas |

Si colocas 2 piezas, es la **última** de las dos la que determina el efecto para el rival.
""")
        st.markdown('<div class="rule-box">🔵 <b>La pieza azul</b> — solo en espacio celeste (Nv 1–3). Al usarla: ganas los puntos del celeste, subes al siguiente nivel, colocas en el espacio <b>siguiente al celeste alineado</b> del nuevo nivel, y <b>repites tu turno</b>.</div>', unsafe_allow_html=True)
        st.divider()
        st.markdown("### Puntuación")
        st.markdown("**Espacios celestes:**")
        st.markdown("""
| Nivel | 3:00 | 6:00 | 9:00 | 12:00 |
|-------|------|------|------|-------|
| 1 | 3 | 6 | 9 | **12** |
| 2 | 2 | 4 | 6 | **8** |
| 3 | 1 | 2 | 3 | **4** |
""")
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            st.markdown('<div class="rule-box">🏛️ <b>Bono del Arquitecto (+4 pts)</b><br>El jugador que completa un nivel (1–5) recibe 4 puntos. No otorga turno extra.</div>', unsafe_allow_html=True)
        with col_b2:
            st.markdown('<div class="rule-box">🎯 <b>El Centro — Nivel 6 (+16 pts)</b><br>Colocar en el centro otorga 16 puntos y termina la partida inmediatamente.</div>', unsafe_allow_html=True)
        st.divider()
        st.markdown("### Fin del juego")
        st.markdown("""
- **Alguien ocupa el centro** → +16 pts · fin inmediato · gana quien tenga más puntos.
- **Un jugador se queda sin negras y sin blancas** → pierde automáticamente.
""")
        st.divider()
        st.markdown("### Estrategias")
        for tip, desc in [
            ("⚪ Presión con blancas", "Jugar blancas obliga al rival a colocar 2 piezas. Con solo 6 disponibles, cada blanca es una decisión de peso."),
            ("🔵 Guardar azules", "Las azules valen más en los espacios de 12:00. Guardarlas para ese momento puede ser decisivo."),
            ("🏛️ Bono del Arquitecto", "Completar un nivel da +4 pts sin gastar azul. Calcular cuándo completar es parte clave de la táctica."),
            ("⚠️ Control de recursos", "Sin negras ni blancas se pierde automáticamente. El panel se pone en rojo cuando quedan ≤3 piezas."),
        ]:
            st.markdown(f'<div class="rule-box"><b>{tip}</b><br>{desc}</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;margin-top:2rem;font-style:italic;color:#BA7517;font-size:1.05rem;">"Jazam no es un juego… es una meditación competitiva."</div>', unsafe_allow_html=True)

    else:
        st.markdown("### What is Jazam?")
        st.markdown("""
Jazam is an **abstract strategy game for 2 players** where every move counts.
It's not just about reaching the center first — it's about **getting there with more points**.

> *"A mandala of decisions where every bead can change your fate."*
""")
        st.divider()
        st.markdown("### The Board")
        st.markdown("The board is circular with **6 concentric levels** and **63 spaces** in total. Spaces are filled in **clockwise** order, level by level, from the outside in.")
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("""
| Level | Spaces |
|-------|--------|
| 1 (outer) | 32 |
| 2 | 16 |
| 3 | 8 |
| 4 | 4 |
| 5 | 2 |
| 6 — Center | 1 |
""")
        with col_b:
            st.markdown("""
**Celestial spaces** (light blue) are found in levels 1, 2 and 3, at positions equivalent to **3:00, 6:00, 9:00 and 12:00** on a clock.

They are the only spaces where a blue bead can be placed, and they award points to the player who uses them.
""")
        st.divider()
        st.markdown("### Beads (per player)")
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            st.markdown('<div class="rule-box" style="text-align:center;"><span style="font-size:1.4rem;">⚫</span><br><b>12 Black</b><br><small>Opponent places 1 bead on their next turn</small></div>', unsafe_allow_html=True)
        with col_p2:
            st.markdown('<div class="rule-box" style="text-align:center;"><span style="font-size:1.4rem;">🟡</span><br><b>6 White</b><br><small>Opponent places 2 beads on their next turn</small></div>', unsafe_allow_html=True)
        with col_p3:
            st.markdown('<div class="rule-box" style="text-align:center;"><span style="font-size:1.4rem;">🔵</span><br><b>2 Blue</b><br><small>Celestial only → advance a level + take another turn</small></div>', unsafe_allow_html=True)
        st.divider()
        st.markdown("### How to Play")
        st.markdown("On each turn, the active player places beads in the **next available space** — you cannot choose freely, it is always the next space in clockwise sequence.")
        st.markdown("**How many beads do you place?**")
        st.markdown("""
| Opponent's last bead | Beads you must place |
|----------------------|----------------------|
| Black or Blue | 1 bead |
| White | 2 beads |

If you place 2 beads, it is the **last** one that determines the effect for your opponent.
""")
        st.markdown('<div class="rule-box">🔵 <b>The blue bead</b> — only on a celestial space (Levels 1–3). When used: you score that space\'s points, advance to the next level, place on the space <b>immediately after the aligned celestial</b> in the new level, and <b>take another turn</b>.</div>', unsafe_allow_html=True)
        st.divider()
        st.markdown("### Scoring")
        st.markdown("**Celestial spaces:**")
        st.markdown("""
| Level | 3:00 | 6:00 | 9:00 | 12:00 |
|-------|------|------|------|-------|
| 1 | 3 | 6 | 9 | **12** |
| 2 | 2 | 4 | 6 | **8** |
| 3 | 1 | 2 | 3 | **4** |
""")
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            st.markdown('<div class="rule-box">🏛️ <b>Architect Bonus (+4 pts)</b><br>The player who places the last bead completing a level (1–5) scores 4 bonus points. No extra turn awarded.</div>', unsafe_allow_html=True)
        with col_b2:
            st.markdown('<div class="rule-box">🎯 <b>The Center — Level 6 (+16 pts)</b><br>Placing a bead in the center scores 16 points and ends the game immediately.</div>', unsafe_allow_html=True)
        st.divider()
        st.markdown("### End of Game")
        st.markdown("""
- **Someone occupies the center** → +16 pts · immediate end · player with most points wins.
- **A player runs out of black and white beads** → they lose automatically.
""")
        st.divider()
        st.markdown("### Strategies")
        for tip, desc in [
            ("⚪ White pressure", "Playing white forces your opponent to place 2 beads. With only 6 available, each white is a weighty decision."),
            ("🔵 Save your blues", "Blue beads score more at 12:00 positions. Saving them for the right moment can be decisive."),
            ("🏛️ Architect Bonus", "Completing a level gives +4 pts without spending a blue. Timing this is a key tactical element."),
            ("⚠️ Resource management", "Running out of black and white beads means an automatic loss. The panel turns red when ≤3 beads remain."),
        ]:
            st.markdown(f'<div class="rule-box"><b>{tip}</b><br>{desc}</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;margin-top:2rem;font-style:italic;color:#BA7517;font-size:1.05rem;">"Jazam is not a game… it\'s competitive meditation."</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PESTAÑA: JUEGO
# ══════════════════════════════════════════════════════════════════════════════
with tab_game:

    # ── Selector de modo + reset ──────────────────────────────────────────────
    lbl_2p    = "👥 2 Jugadores"  if ES else "👥 2 Players"
    lbl_ai    = "🤖 vs IA"        if ES else "🤖 vs AI"
    lbl_reset = "↺ Nueva partida" if ES else "↺ New game"

    col_m1, col_m2, col_m3 = st.columns([1, 1, 1])
    with col_m1:
        if st.button(lbl_2p, use_container_width=True,
                     type="primary" if mode == "2p" else "secondary"):
            st.session_state.mode = "2p"
            st.session_state.game = init_game()
            st.session_state.ai_turn = False
            st.rerun()
    with col_m2:
        if st.button(lbl_ai, use_container_width=True,
                     type="primary" if mode == "ai" else "secondary"):
            st.session_state.mode = "ai"
            st.session_state.game = init_game()
            st.session_state.ai_turn = False
            st.rerun()
    with col_m3:
        if st.button(lbl_reset, use_container_width=True):
            st.session_state.game = init_game()
            st.session_state.ai_turn = False
            st.rerun()

    st.divider()

    # ── Paneles de jugadores ──────────────────────────────────────────────────
    p1_active = G["cp"] == 0 and not G["over"]
    p2_active = G["cp"] == 1 and not G["over"]
    p1_name = "Player 1" if not ES else "Jugador 1"
    p2_name = ("AI 🤖" if not ES else "IA 🤖") if mode == "ai" else ("Player 2" if not ES else "Jugador 2")

    p1_cls = "score-box active" if p1_active else "score-box"
    p2_cls = "score-box active-ai" if (p2_active and mode == "ai") else ("score-box active" if p2_active else "score-box")
    dots_p1 = pieces_html(G["pieces"][0], mode, 0)
    dots_p2 = pieces_html(G["pieces"][1], mode, 1)

    st.markdown(f"""
    <div style="display:flex;gap:12px;flex-wrap:wrap;">
      <div class="{p1_cls}" style="flex:1;min-width:120px;">
        <div class="score-name">{p1_name}</div>
        <div class="score-pts">{G['scores'][0]} <span>pts</span></div>
        <div class="pieces-row">{dots_p1}</div>
      </div>
      <div class="{p2_cls}" style="flex:1;min-width:120px;">
        <div class="score-name">{p2_name}</div>
        <div class="score-pts">{G['scores'][1]} <span>pts</span></div>
        <div class="pieces-row">{dots_p2}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Barra de estado ───────────────────────────────────────────────────────
    if not G["over"]:
        cp = G["cp"]
        lv, si = G["lv"], G["next_si"]
        cel = is_celestial(lv, si)
        pts = space_pts(lv, si)
        rem = G["to_place"] - G["placed_this_turn"]
        total_left = G["pieces"][cp]["black"] + G["pieces"][cp]["white"]
        if ES:
            name = "IA" if mode == "ai" and cp == 1 else f"Jugador {cp+1}"
        else:
            name = "AI" if mode == "ai" and cp == 1 else f"Player {cp+1}"

        if total_left <= 3:
            bar_cls = "status-bar warning"
            txt = (f"⚠️ <b>{name}</b> — solo {total_left} piezas restantes · Nv{lv+1} esp{si+1}"
                   if ES else
                   f"⚠️ <b>{name}</b> — only {total_left} beads left · Lv{lv+1} sp{si+1}")
        elif cel:
            clock_labels = ["12:00", "3:00", "6:00", "9:00"]
            clock = si // (LEVELS[lv] // 4)
            bar_cls = "status-bar celestial"
            txt = (f"★ <b>{name}</b> — coloca {rem} · Nv{lv+1} esp{si+1} · Celeste {clock_labels[clock]} = {pts}pts"
                   if ES else
                   f"★ <b>{name}</b> — place {rem} · Lv{lv+1} sp{si+1} · Celestial {clock_labels[clock]} = {pts}pts")
        else:
            bar_cls = "status-bar"
            txt = (f"<b>{name}</b> — coloca {rem} pieza{'s' if rem > 1 else ''} · Nivel {lv+1} · espacio {si+1}"
                   if ES else
                   f"<b>{name}</b> — place {rem} bead{'s' if rem > 1 else ''} · Level {lv+1} · space {si+1}")

        st.markdown(f'<div class="{bar_cls}">{txt}</div>', unsafe_allow_html=True)

    # ── Tablero SVG ───────────────────────────────────────────────────────────
    svg = render_board_svg(G)
    st.markdown(
        f'<div style="width:100%;max-width:420px;margin:8px auto;">{svg}</div>',
        unsafe_allow_html=True
    )

    # ── Controles de juego ────────────────────────────────────────────────────
    if not G["over"]:
        cp = G["cp"]
        is_human = not (mode == "ai" and cp == 1)
        moves = valid_moves(G)
        pc = G["pieces"][cp]

        if is_human:
            lv, si = G["lv"], G["next_si"]
            c1, c2, c3 = st.columns(3)
            with c1:
                lbl = f"⚫ {'Negra' if ES else 'Black'} ({pc['black']})"
                if st.button(lbl, disabled="black" not in moves, use_container_width=True, key="btn_black"):
                    do_play(G, "black", mode)
                    if mode == "ai" and not G["over"] and G["cp"] == 1:
                        st.session_state.ai_turn = True
                    st.rerun()
            with c2:
                lbl = f"🟡 {'Blanca' if ES else 'White'} ({pc['white']})"
                if st.button(lbl, disabled="white" not in moves, use_container_width=True, key="btn_white"):
                    do_play(G, "white", mode)
                    if mode == "ai" and not G["over"] and G["cp"] == 1:
                        st.session_state.ai_turn = True
                    st.rerun()
            with c3:
                lbl = f"🔵 {'Azul' if ES else 'Blue'} ({pc['blue']})"
                if st.button(lbl, disabled="blue" not in moves, use_container_width=True, key="btn_blue"):
                    do_play(G, "blue", mode)
                    if mode == "ai" and not G["over"] and G["cp"] == 1:
                        st.session_state.ai_turn = True
                    st.rerun()
        else:
            msg = "🤖 La IA está pensando..." if ES else "🤖 AI is thinking..."
            st.info(msg, icon="⏳")
            time.sleep(0.6)
            ai_move(G, mode)
            st.rerun()

    # ── Banner de ganador ─────────────────────────────────────────────────────
    if G["over"]:
        p2_label = ("IA" if ES else "AI") if mode == "ai" else ("Jugador 2" if ES else "Player 2")
        winner = G.get("winner")
        reason = G.get("win_reason")

        if winner == -1:
            title = "¡Empate!" if ES else "It's a tie!"
            desc = f"J1: {G['scores'][0]}pts — {p2_label}: {G['scores'][1]}pts"
        elif winner == 0:
            title = "¡Jugador 1 gana! 🎉" if ES else "Player 1 wins! 🎉"
            desc = f"J1: {G['scores'][0]}pts — {p2_label}: {G['scores'][1]}pts"
            if reason == "nopcs":
                desc += (f" · {p2_label} se quedó sin piezas" if ES else f" · {p2_label} ran out of beads")
        else:
            title = (f"¡{p2_label} gana! 🎉" if ES else f"{p2_label} wins! 🎉")
            desc = f"J1: {G['scores'][0]}pts — {p2_label}: {G['scores'][1]}pts"
            if reason == "nopcs":
                desc += (" · Jugador 1 se quedó sin piezas" if ES else " · Player 1 ran out of beads")

        st.markdown(f"""
        <div class="winner-box">
            <div class="winner-title">{title}</div>
            <div class="winner-scores">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Historial de jugadas ──────────────────────────────────────────────────
    if G["log"]:
        st.markdown("#### Historial de jugadas" if ES else "#### Game log")
        entries = ""
        for e in reversed(G["log"]):
            who = e["who"]
            cls = "log-j1" if who in ("J1","P1") else ("log-ai" if who in ("IA","AI") else "log-j2")
            pts_html = f' <span class="log-pts">+{e["pts"]}</span>' if e["pts"] > 0 else ""
            entries += f'<div class="log-entry"><span style="color:#aaa;">#{e["turn"]}</span> <span class="{cls}">{who}</span> {e["msg"]}{pts_html}</div>'
        st.markdown(f'<div class="log-container">{entries}</div>', unsafe_allow_html=True)
