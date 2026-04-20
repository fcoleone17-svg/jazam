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
.dot-black-on  { background: #2C2C2A; border: 1px solid #888; }
.dot-black-off { background: #2C2C2A; border: 1px solid #888; opacity: 0.15; }
.dot-white-on  { background: #F5F5F0; border: 1px solid #aaa; }
.dot-white-off { background: #F5F5F0; border: 1px solid #aaa; opacity: 0.15; }
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
</style>
""", unsafe_allow_html=True)

# ── Constantes del juego ──────────────────────────────────────────────────────
LEVELS = [32, 16, 8, 4, 2, 1]   # espacios por nivel
INIT_PIECES = {"black": 12, "white": 6, "blue": 2}

PTS_TABLE = [
    [12, 9, 6, 3],   # nivel 1: 12:00, 3:00, 6:00, 9:00 (índice 0,n/4,n/2,3n/4)
    [8,  6, 4, 2],   # nivel 2
    [4,  3, 2, 1],   # nivel 3
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

    lines = [f'<svg width="{SIZE}" height="{SIZE}" xmlns="http://www.w3.org/2000/svg">']

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
                pr = r_dot - 2.5
                pf = {"black": "#2C2C2A", "white": "#F5F5F0", "blue": "#378ADD"}[t]
                ps = {"black": "#888", "white": "#aaa", "blue": "#185FA5"}[t]
                lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{pr}" fill="{pf}" stroke="{ps}" stroke-width="1.5"/>')
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

# ── Sidebar: reglas ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📖 Reglas rápidas")
    for rule in [
        "Coloca piezas en orden horario, nivel por nivel.",
        "**Negra/Azul** del rival → colocas 1. **Blanca** del rival → colocas 2.",
        "**Azul**: solo en espacio celeste (Nv 1-3) → sube de nivel + repite turno.",
        "**Celestes** otorgan puntos: 12:00=12/8/4, 9:00=9/6/3, 6:00=6/4/2, 3:00=3/2/1.",
        "**Bono Arquitecto**: +4pts al completar un nivel.",
        "**Centro**: +16pts y fin inmediato.",
        "Sin negras ni blancas → pierde automáticamente.",
    ]:
        st.markdown(f'<div class="rule-box">{rule}</div>', unsafe_allow_html=True)
    st.caption("Configuración: 12N · 6B · 2A por jugador")

# ── Inicialización del estado ─────────────────────────────────────────────────
if "game" not in st.session_state:
    st.session_state.game = init_game()
if "mode" not in st.session_state:
    st.session_state.mode = "2p"
if "ai_turn" not in st.session_state:
    st.session_state.ai_turn = False

G = st.session_state.game
mode = st.session_state.mode

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<div class="jazam-title">JAZAM</div>', unsafe_allow_html=True)
st.markdown('<div class="jazam-subtitle">meditación competitiva</div>', unsafe_allow_html=True)

# ── Selector de modo + reset ──────────────────────────────────────────────────
col_m1, col_m2, col_m3 = st.columns([1, 1, 1])
with col_m1:
    if st.button("👥 2 Jugadores", use_container_width=True,
                 type="primary" if mode == "2p" else "secondary"):
        st.session_state.mode = "2p"
        st.session_state.game = init_game()
        st.session_state.ai_turn = False
        st.rerun()
with col_m2:
    if st.button("🤖 vs IA", use_container_width=True,
                 type="primary" if mode == "ai" else "secondary"):
        st.session_state.mode = "ai"
        st.session_state.game = init_game()
        st.session_state.ai_turn = False
        st.rerun()
with col_m3:
    if st.button("↺ Nueva partida", use_container_width=True):
        st.session_state.game = init_game()
        st.session_state.ai_turn = False
        st.rerun()

st.divider()

# ── Paneles de jugadores ──────────────────────────────────────────────────────
p1_active = G["cp"] == 0 and not G["over"]
p2_active = G["cp"] == 1 and not G["over"]
p2_name = "IA 🤖" if mode == "ai" else "Jugador 2"

col1, col2 = st.columns(2)

with col1:
    cls = "score-box active" if p1_active else "score-box"
    dots_html = pieces_html(G["pieces"][0], mode, 0)
    st.markdown(f"""
    <div class="{cls}">
        <div class="score-name">Jugador 1</div>
        <div class="score-pts">{G['scores'][0]} <span>pts</span></div>
        <div class="pieces-row">{dots_html}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    cls = "score-box active-ai" if (p2_active and mode == "ai") else ("score-box active" if p2_active else "score-box")
    dots_html = pieces_html(G["pieces"][1], mode, 1)
    st.markdown(f"""
    <div class="{cls}">
        <div class="score-name">{p2_name}</div>
        <div class="score-pts">{G['scores'][1]} <span>pts</span></div>
        <div class="pieces-row">{dots_html}</div>
    </div>
    """, unsafe_allow_html=True)

# ── Barra de estado ───────────────────────────────────────────────────────────
if not G["over"]:
    cp = G["cp"]
    lv, si = G["lv"], G["next_si"]
    cel = is_celestial(lv, si)
    pts = space_pts(lv, si)
    rem = G["to_place"] - G["placed_this_turn"]
    total_left = G["pieces"][cp]["black"] + G["pieces"][cp]["white"]
    name = ("IA" if mode == "ai" and cp == 1 else f"Jugador {cp+1}")

    if total_left <= 3:
        bar_cls = "status-bar warning"
        txt = f"⚠️ <b>{name}</b> — solo {total_left} piezas restantes · Nv{lv+1} esp{si+1}"
    elif cel:
        clock_labels = ["12:00", "3:00", "6:00", "9:00"]
        clock = si // (LEVELS[lv] // 4)
        bar_cls = "status-bar celestial"
        txt = f"★ <b>{name}</b> — coloca {rem} · Nv{lv+1} esp{si+1} · Celeste {clock_labels[clock]} = {pts}pts"
    else:
        bar_cls = "status-bar"
        txt = f"<b>{name}</b> — coloca {rem} pieza{'s' if rem > 1 else ''} · Nivel {lv+1} · espacio {si+1}"

    st.markdown(f'<div class="{bar_cls}">{txt}</div>', unsafe_allow_html=True)

# ── Tablero SVG ───────────────────────────────────────────────────────────────
svg = render_board_svg(G)
st.markdown(
    f'<div style="display:flex;justify-content:center;margin:8px 0;">{svg}</div>',
    unsafe_allow_html=True
)

# ── Controles de juego ────────────────────────────────────────────────────────
if not G["over"]:
    cp = G["cp"]
    is_human = not (mode == "ai" and cp == 1)
    moves = valid_moves(G)
    pc = G["pieces"][cp]

    if is_human:
        lv, si = G["lv"], G["next_si"]
        cel = is_celestial(lv, si)

        c1, c2, c3 = st.columns(3)
        with c1:
            disabled = "black" not in moves
            label = f"⚫ Negra ({pc['black']})"
            if st.button(label, disabled=disabled, use_container_width=True, key="btn_black"):
                do_play(G, "black", mode)
                if mode == "ai" and not G["over"] and G["cp"] == 1:
                    st.session_state.ai_turn = True
                st.rerun()
        with c2:
            disabled = "white" not in moves
            label = f"⚪ Blanca ({pc['white']})"
            if st.button(label, disabled=disabled, use_container_width=True, key="btn_white"):
                do_play(G, "white", mode)
                if mode == "ai" and not G["over"] and G["cp"] == 1:
                    st.session_state.ai_turn = True
                st.rerun()
        with c3:
            disabled = "blue" not in moves
            label = f"🔵 Azul ({pc['blue']})"
            if st.button(label, disabled=disabled, use_container_width=True, key="btn_blue"):
                do_play(G, "blue", mode)
                if mode == "ai" and not G["over"] and G["cp"] == 1:
                    st.session_state.ai_turn = True
                st.rerun()
    else:
        # Turno de la IA
        st.info("🤖 La IA está pensando...", icon="⏳")
        time.sleep(0.6)
        ai_move(G, mode)
        st.rerun()

# ── Banner de ganador ─────────────────────────────────────────────────────────
if G["over"]:
    p2_label = "IA" if mode == "ai" else "Jugador 2"
    winner = G.get("winner")
    reason = G.get("win_reason")

    if winner == -1:
        title = "¡Empate!"
        desc = f"J1: {G['scores'][0]}pts — {p2_label}: {G['scores'][1]}pts"
    elif winner == 0:
        title = "¡Jugador 1 gana! 🎉"
        desc = f"J1: {G['scores'][0]}pts — {p2_label}: {G['scores'][1]}pts"
        if reason == "nopcs":
            desc += f" · {p2_label} se quedó sin piezas"
    else:
        title = f"¡{p2_label} gana! 🎉"
        desc = f"J1: {G['scores'][0]}pts — {p2_label}: {G['scores'][1]}pts"
        if reason == "nopcs":
            desc += " · Jugador 1 se quedó sin piezas"

    st.markdown(f"""
    <div class="winner-box">
        <div class="winner-title">{title}</div>
        <div class="winner-scores">{desc}</div>
    </div>
    """, unsafe_allow_html=True)

# ── Historial de jugadas ──────────────────────────────────────────────────────
if G["log"]:
    st.markdown("#### Historial de jugadas")
    entries = ""
    for e in reversed(G["log"]):
        who = e["who"]
        cls = "log-j1" if who == "J1" else ("log-ai" if who == "IA" else "log-j2")
        pts_html = f' <span class="log-pts">+{e["pts"]}</span>' if e["pts"] > 0 else ""
        entries += f'<div class="log-entry"><span style="color:#aaa;">#{e["turn"]}</span> <span class="{cls}">{who}</span> {e["msg"]}{pts_html}</div>'
    st.markdown(f'<div class="log-container">{entries}</div>', unsafe_allow_html=True)
