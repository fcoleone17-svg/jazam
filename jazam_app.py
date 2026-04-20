"""
JAZAM v4 — Dos frentes activos por nivel
6 niveles · 14 negras · 8 blancas · 2 azules

Cada nivel tiene DOS frentes (extremo horario y extremo antihorario).
En cada turno el jugador elige desde cuál extremo avanzar.
Negra: avanza 1 espacio desde el extremo elegido
Blanca: cierra permanentemente el extremo elegido (nadie puede avanzar por ahí)
Azul: desde celeste en cualquier extremo activo, sube o baja de nivel + repite turno
El nivel se completa cuando los dos frentes se encuentran (sin espacio entre ellos)
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
.log-j1{color:#BA7517;font-weight:500;}.log-j2{color:#185FA5;font-weight:500;}.log-ai{color:#3B6D11;font-weight:500;}
.log-pts{color:#3B6D11;font-weight:600;}
.winner-box{background:#F5F1E4;border:2px solid #BA7517;border-radius:14px;padding:20px;text-align:center;margin-top:12px;}
.winner-title{font-family:'Crimson Pro',serif;font-size:1.9rem;font-weight:600;color:#1C1A10;margin-bottom:6px;}
.winner-scores{font-size:0.88rem;color:#666;}
.dot-row{display:flex;gap:3px;flex-wrap:wrap;margin-top:3px;justify-content:center;}
.dot{width:9px;height:9px;border-radius:50%;display:inline-block;}
.dot-black-on{background:#111110;border:1.5px solid #999990;}
.dot-black-off{background:#111110;border:1.5px solid #999990;opacity:0.15;}
.dot-white-on{background:#E8D44D;border:1.5px solid #B89A10;}
.dot-white-off{background:#E8D44D;border:1.5px solid #B89A10;opacity:0.15;}
.dot-blue-on{background:#378ADD;border:1px solid #185FA5;}
.dot-blue-off{background:#378ADD;border:1px solid #185FA5;opacity:0.15;}
.rule-box{background:#F9F7F0;border-left:3px solid #BA7517;border-radius:0 8px 8px 0;padding:10px 14px;font-size:0.84rem;color:#444;margin-bottom:8px;}
@media(max-width:600px){
  .jazam-title{font-size:1.9rem!important;}
  .score-pts{font-size:1.4rem!important;}
  .dot{width:7px!important;height:7px!important;}
  .status-bar{font-size:0.78rem!important;padding:7px 10px!important;}
}
</style>
""", unsafe_allow_html=True)

LEVELS = [32, 16, 8, 4, 2, 1]
INIT_PIECES = {"black": 18, "white": 4, "blue": 2}

# Puntos fijos por nivel — todos los celestes del mismo nivel valen igual
CEL_PTS_BY_LEVEL = {0: 6, 1: 4, 2: 2}
PTS_TABLE = [[12,3,6,9],[8,2,4,6],[4,1,2,3]]

# Celestes fijos por nivel (índices base 0)
CELESTIALS = {
    0: {4, 12, 20, 28},   # Nivel 1: esp 5,13,21,29
    1: {0, 4, 8, 12},     # Nivel 2: esp 1,5,9,13
    2: {1, 3, 5, 7},      # Nivel 3: esp 2,4,6,8
}

def is_celestial(li, si):
    return si in CELESTIALS.get(li, set())

def space_pts(li, si):
    if li == 5: return 16
    return CEL_PTS_BY_LEVEL.get(li, 0) if is_celestial(li, si) else 0

def init_game():
    """
    Each level has two active fronts:
    - front_cw[li]: the leading edge of the clockwise front (starts at index 0, grows clockwise)
    - front_ccw[li]: the leading edge of the counter-clockwise front (starts at index n-1, grows ccw)
    - closed_cw[li]: True if clockwise front is permanently blocked
    - closed_ccw[li]: True if counter-clockwise front is permanently blocked
    The level starts with space 0 = CW start, space n-1 = CCW start.
    Both fronts advance inward toward each other.
    """
    levels_data = []
    for li, n in enumerate(LEVELS):
        levels_data.append({
            "front_cw": 0,
            "front_ccw": n - 1,
            "closed_cw": False,
            "closed_ccw": False,
            "filled": set(),
            "blocked": set(),
        })
    return {
        "cp": 0, "scores": [0, 0],
        "pieces": [dict(INIT_PIECES), dict(INIT_PIECES)],
        "levels": levels_data,
        "cur_lv": 0,
        "turn": 0,          # global turn counter (0=J1 first, 1=J2 first)
        "j1_placed": False, # J1 has placed first bead at 12:00
        "j2_chose": False,  # J2 has chosen their starting direction
        "over": False, "log": [], "turn_count": 0,
        "winner": None, "win_reason": None, "_es": True,
    }

def fronts_meet(lv_data, li):
    """Level is complete when no free space remains between the two fronts."""
    n = LEVELS[li]
    occupied = lv_data["filled"] | lv_data["blocked"]

    # Both fronts closed by white
    if lv_data["closed_cw"] and lv_data["closed_ccw"]:
        return True

    # Simply check: are all spaces occupied or blocked?
    if len(occupied) >= n:
        return True

    # If one front is closed, check if the remaining front has nowhere to go
    if lv_data["closed_cw"] and lv_data["closed_ccw"]:
        return True

    # Find next free space in each active direction
    def next_free_cw(start):
        si = start % n
        for _ in range(n):
            if si not in occupied: return si
            si = (si + 1) % n
        return None

    def next_free_ccw(start):
        si = start % n
        for _ in range(n):
            if si not in occupied: return si
            si = (si - 1) % n
        return None

    # Count free spaces between the two active fronts
    # CW front advances clockwise, CCW front advances counter-clockwise
    # They meet when the space the CW front would fill == space CCW would fill
    cw_next = next_free_cw(lv_data["front_cw"]) if not lv_data["closed_cw"] else None
    ccw_next = next_free_ccw(lv_data["front_ccw"]) if not lv_data["closed_ccw"] else None

    if cw_next is None and ccw_next is None:
        return True
    if cw_next is not None and ccw_next is not None and cw_next == ccw_next:
        # Only one space left — fronts have met
        return False  # Still that one space to fill
    # Count total free spaces
    free = n - len(occupied)
    return free == 0

def get_moves(G):
    cp = G["cp"]; pc = G["pieces"][cp]
    li = G["cur_lv"]; lv = G["levels"][li]
    moves = []; n = LEVELS[li]
    occupied = lv["filled"] | lv["blocked"]

    # ── Primer turno J1: solo puede poner negra en esp 0 (12:00) ↻
    if not G["j1_placed"]:
        return [("black", "cw")]

    # ── Primer turno J2: elige sentido (↻ o ↺) con negra
    if G["j1_placed"] and not G["j2_chose"]:
        moves = []
        if pc["black"] > 0:
            if 1 not in occupied: moves.append(("black", "cw"))    # esp 2 (↻)
            if n-1 not in occupied: moves.append(("black", "ccw")) # esp n (↺)
        return moves

    def next_free_cw(start):
        si = start % n
        for _ in range(n):
            if si not in occupied: return si
            si = (si + 1) % n
        return None

    def next_free_ccw(start):
        si = start % n
        for _ in range(n):
            if si not in occupied: return si
            si = (si - 1) % n
        return None

    # Black moves
    if pc["black"] > 0:
        if not lv["closed_cw"] and next_free_cw(lv["front_cw"]) is not None:
            moves.append(("black", "cw"))
        if not lv["closed_ccw"] and next_free_ccw(lv["front_ccw"]) is not None:
            moves.append(("black", "ccw"))

    # White moves
    if pc["white"] > 0:
        if not lv["closed_cw"]: moves.append(("white", "cw"))
        if not lv["closed_ccw"]: moves.append(("white", "ccw"))

    # Blue moves: from celestial on an active front
    if pc["blue"] > 0:
        fcw = lv["front_cw"]
        fccw = lv["front_ccw"]
        cw_is_cel = is_celestial(li, fcw) and not lv["closed_cw"] and fcw not in lv["filled"]
        ccw_is_cel = is_celestial(li, fccw) and not lv["closed_ccw"] and fccw not in lv["filled"]
        if (cw_is_cel or ccw_is_cel) and li in CELESTIALS:
            if li < 5: moves.append(("blue", "up"))
            if li > 0: moves.append(("blue", "down"))

    return moves

def get_next_front_space(lv_data, li, front):
    n = LEVELS[li]; occupied = lv_data["filled"] | lv_data["blocked"]
    if front == "cw":
        si = lv_data["front_cw"] % n
        for _ in range(n):
            if si not in occupied: return si
            si = (si + 1) % n
    else:
        si = lv_data["front_ccw"] % n
        for _ in range(n):
            if si not in occupied: return si
            si = (si - 1) % n
    return None

def add_log(G, who, msg, pts=0):
    G["turn_count"] += 1
    G["log"].append({"turn": G["turn_count"], "who": who, "msg": msg, "pts": pts})

def do_play(G, t, d, mode):
    if G["over"]: return
    cp = G["cp"]; pc = G["pieces"][cp]
    li = G["cur_lv"]; lv = G["levels"][li]
    ES = G.get("_es", True)
    who = ("IA" if ES else "AI") if (mode == "ai" and cp == 1) else f"J{cp+1}"
    tn = {"black": "negra" if ES else "black",
          "white": "blanca" if ES else "white",
          "blue":  "azul"   if ES else "blue"}[t]
    dn = {"cw": "↻", "ccw": "↺", "up": "↑", "down": "↓"}[d]

    pc[t] -= 1
    n = LEVELS[li]

    if t == "black":
        # First turn J1: place at index 0 (12:00), only CW front active
        if not G["j1_placed"]:
            si = 0
            lv["filled"].add(si)
            lv["front_cw"] = 1          # CW front advances from esp 2
            lv["closed_ccw"] = True     # CCW front locked until J2 chooses
            lv["blocked"].discard(n-1)  # clear any accidental block
            G["j1_placed"] = True
            add_log(G, who, f"{tn} 12:00 Nv{li+1}·esp1", 0)
            G["cp"] = 1 - cp

        # First turn J2: choose direction, second piece placed
        elif not G["j2_chose"]:
            if d == "cw":
                si = 1  # esp 2, just after J1's piece
                lv["filled"].add(si)
                lv["front_cw"] = 2
                lv["closed_ccw"] = False          # now unlock CCW front
                lv["front_ccw"] = n - 1           # CCW starts from last space
            else:
                si = n - 1  # last space going CCW
                lv["filled"].add(si)
                lv["front_ccw"] = n - 2
                lv["closed_ccw"] = False
            G["j2_chose"] = True
            add_log(G, who, f"{tn} {dn} Nv{li+1}·esp{si+1}", 0)
            G["cp"] = 1 - cp

        # Normal turns
        else:
            si = get_next_front_space(lv, li, d)
            if si is None: pc[t] += 1; return
            lv["filled"].add(si)
            if d == "cw": lv["front_cw"] = (si + 1) % n
            else: lv["front_ccw"] = (si - 1) % n
            add_log(G, who, f"{tn} {dn} Nv{li+1}·esp{si+1}", 0)
            if fronts_meet(lv, li):
                G["scores"][cp] += 4
                add_log(G, who, f"Nv{li+1} completo · +4" if ES else f"Lv{li+1} complete · +4", 4)
                if li < 5: G["cur_lv"] = li + 1
            G["cp"] = 1 - cp

    elif t == "white":
        if d == "cw":
            lv["closed_cw"] = True
            si = lv["front_cw"]
            lv["blocked"].add(si)
        else:
            lv["closed_ccw"] = True
            si = lv["front_ccw"]
            lv["blocked"].add(si)
        add_log(G, who, f"{tn} cierra {dn} Nv{li+1}·esp{si+1}" if ES else f"{tn} closes {dn} Lv{li+1}·sp{si+1}", 0)
        if fronts_meet(lv, li):
            G["scores"][cp] += 4
            add_log(G, who, f"Nv{li+1} completo · +4" if ES else f"Lv{li+1} complete · +4", 4)
            if li < 5: G["cur_lv"] = li + 1
        G["cp"] = 1 - cp

    elif t == "blue":
        lv_data = G["levels"][li]
        fcw_si = lv_data["front_cw"]
        fccw_si = lv_data["front_ccw"]
        cel_si = None
        if is_celestial(li, fcw_si) and not lv_data["closed_cw"]:
            cel_si = fcw_si
        elif is_celestial(li, fccw_si) and not lv_data["closed_ccw"]:
            cel_si = fccw_si
        pts = space_pts(li, cel_si) if cel_si is not None else 0
        G["scores"][cp] += pts
        new_li = li + 1 if d == "up" else li - 1
        # Land exactly on the radially aligned space in the new level
        new_si = round(cel_si * LEVELS[new_li] / LEVELS[li]) % LEVELS[new_li]
        G["cur_lv"] = new_li
        # Both fronts start AT the aligned space so player expands from there
        # front_cw = new_si means CW front is ready to advance from new_si
        # front_ccw = new_si means CCW front is ready to advance from new_si
        # But they must NOT be equal or fronts_meet() will trigger immediately
        # Solution: mark new_si as filled (the landing spot) and set fronts around it
        new_lv = G["levels"][new_li]
        new_n = LEVELS[new_li]
        new_lv["filled"].add(new_si)
        new_lv["front_cw"] = (new_si + 1) % new_n
        new_lv["front_ccw"] = (new_si - 1) % new_n
        add_log(G, who, f"{tn} {dn} Nv{new_li+1}·esp{new_si+1}", pts)
        # repeat turn — no cp switch

    check_end(G, mode)

def check_end(G, mode):
    li = G["cur_lv"]
    ES = G.get("_es", True)
    # Center reached (level 5 = index 5, 1 space)
    if li == 5:
        lv = G["levels"][5]
        if lv["filled"]:
            # find who placed it
            cp = G["cp"]
            G["scores"][cp] += 16
            who = ("IA" if ES else "AI") if (mode == "ai" and cp == 1) else f"J{cp+1}"
            add_log(G, who, "¡CENTRO! +16" if ES else "CENTER! +16", 16)
            G["over"] = True
            G["winner"] = 0 if G["scores"][0] > G["scores"][1] else (1 if G["scores"][1] > G["scores"][0] else -1)
            G["win_reason"] = "center"; return
    # Out of pieces
    for p in range(2):
        pc = G["pieces"][p]
        if pc["black"] <= 0 and pc["white"] <= 0 and pc["blue"] <= 0:
            G["over"] = True; G["winner"] = 1 - p; G["win_reason"] = "nopcs"
            who = ("IA" if ES else "AI") if (mode == "ai" and p == 1) else f"J{p+1}"
            add_log(G, who, "sin piezas" if ES else "out of beads", 0); return
    # No moves
    if not get_moves(G):
        cp = G["cp"]; G["over"] = True; G["winner"] = 1 - cp; G["win_reason"] = "trapped"
        who = ("IA" if ES else "AI") if (mode == "ai" and cp == 1) else f"J{cp+1}"
        add_log(G, who, "sin movimientos" if ES else "no moves", 0)

def ai_move(G, mode):
    moves = get_moves(G)
    if not moves: G["over"] = True; G["winner"] = 0; G["win_reason"] = "trapped"; return
    li = G["cur_lv"]; lv = G["levels"][li]

    # Blue up on celestial
    if ("blue", "up") in moves:
        fcw = lv["front_cw"]; fccw = lv["front_ccw"]
        if is_celestial(li, fcw) and space_pts(li, fcw) >= 6:
            do_play(G, "blue", "up", mode); return
        if is_celestial(li, fccw) and space_pts(li, fccw) >= 6:
            do_play(G, "blue", "up", mode); return
        if random.random() > 0.5:
            do_play(G, "blue", "up", mode); return

    # Prefer black toward next celestial
    black_moves = [(t, d) for t, d in moves if t == "black"]
    if black_moves:
        n = LEVELS[li]; best = None; best_pts = -1
        for t, d in black_moves:
            si = get_next_front_space(lv, li, d)
            if si is not None and is_celestial(li, si):
                pts = space_pts(li, si)
                if pts > best_pts: best_pts = pts; best = (t, d)
        if best: do_play(G, best[0], best[1], mode); return
        t, d = random.choice(black_moves); do_play(G, t, d, mode); return

    # White: close less valuable front
    white_moves = [(t, d) for t, d in moves if t == "white"]
    if white_moves:
        t, d = random.choice(white_moves); do_play(G, t, d, mode); return

    t, d = random.choice(moves); do_play(G, t, d, mode)

def render_board_svg(G):
    SIZE = 440; cx = cy = SIZE // 2
    radii = [int(cx * r) for r in [0.91, 0.74, 0.57, 0.41, 0.26, 0.0]]
    lines = [f'<svg viewBox="0 0 {SIZE} {SIZE}" width="100%" style="max-width:{SIZE}px;display:block;margin:0 auto;" xmlns="http://www.w3.org/2000/svg">']
    lines.append(f'<circle cx="{cx}" cy="{cy}" r="{cx-2}" fill="#F5F1E4" stroke="#D3C8A0" stroke-width="1.5"/>')

    # Mandala petals
    for li in range(3):
        n = LEVELS[li]; rO = radii[li]+11; rI = radii[li+1]+11
        for k in range(8):
            s = k*n//8; a1 = -math.pi/2+(s/n)*math.pi*2; a2 = -math.pi/2+((s+n/8)/n)*math.pi*2
            x1i=cx+rI*math.cos(a1);y1i=cy+rI*math.sin(a1);x2o=cx+rO*math.cos(a1);y2o=cy+rO*math.sin(a1)
            x3o=cx+rO*math.cos(a2);y3o=cy+rO*math.sin(a2);x4i=cx+rI*math.cos(a2);y4i=cy+rI*math.sin(a2)
            lines.append(f'<path d="M{x1i:.1f},{y1i:.1f} L{x2o:.1f},{y2o:.1f} A{rO},{rO} 0 0,1 {x3o:.1f},{y3o:.1f} L{x4i:.1f},{y4i:.1f} A{rI},{rI} 0 0,0 {x1i:.1f},{y1i:.1f} Z" fill="rgba(120,90,40,0.07)"/>')

    for li in range(5):
        lines.append(f'<circle cx="{cx}" cy="{cy}" r="{radii[li]+11}" fill="none" stroke="rgba(120,90,40,0.18)" stroke-width="0.8"/>')
    for i in range(4):
        a=-math.pi/2+i*math.pi/2; x1=cx+18*math.cos(a);y1=cy+18*math.sin(a);x2=cx+(cx-8)*math.cos(a);y2=cy+(cx-8)*math.sin(a)
        lines.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="rgba(120,90,40,0.12)" stroke-width="0.7" stroke-dasharray="2,5"/>')
    for i in range(12):
        a=-math.pi/2+i*math.pi/6; r1=cx-6; r2=r1-(5 if i%3==0 else 3)
        x1=cx+r1*math.cos(a);y1=cy+r1*math.sin(a);x2=cx+r2*math.cos(a);y2=cy+r2*math.sin(a)
        lines.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="rgba(120,90,40,0.22)" stroke-width="{1.5 if i%3==0 else 0.7}"/>')

    cur_li = G["cur_lv"]

    for li in range(6):
        n = LEVELS[li]; lv = G["levels"][li]
        filled = lv["filled"]; blocked = lv["blocked"]
        fcw = lv["front_cw"]; fccw = lv["front_ccw"]
        closed_cw = lv["closed_cw"]; closed_ccw = lv["closed_ccw"]

        for si in range(n):
            if li == 5: x, y = cx, cy; r_dot = 22
            else:
                a = -math.pi/2+(si/n)*math.pi*2; x = cx+radii[li]*math.cos(a); y = cy+radii[li]*math.sin(a); r_dot = 10

            cel = is_celestial(li, si)
            is_filled = si in filled
            is_blocked = si in blocked
            is_front_cw = (li == cur_li and si == fcw and not closed_cw and si not in filled)
            is_front_ccw = (li == cur_li and si == fccw and not closed_ccw and si not in filled)

            if li == 5:
                fill, stroke, sw = "#DDF0CC", "#3B6D11", 2
            elif is_front_cw or is_front_ccw:
                fill, stroke, sw = "rgba(186,117,23,0.3)", "#BA7517", 3
            elif is_blocked:
                fill, stroke, sw = "#FCEBEB", "#E24B4A", 2
            elif cel:
                fill, stroke, sw = "#C5E8FF", "#185FA5", 1.5
            else:
                fill, stroke, sw = "rgba(80,60,20,0.05)", "rgba(80,60,20,0.15)", 0.7

            lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r_dot}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

            if is_blocked:
                lines.append(f'<text x="{x:.1f}" y="{y+3:.1f}" text-anchor="middle" font-size="{8 if li==0 else 9}" fill="#A32D2D" font-weight="bold" font-family="DM Sans,sans-serif">✕</text>')
            elif is_filled:
                pr = r_dot - 2.5
                lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{pr}" fill="#111110" stroke="#999990" stroke-width="1.5"/>')
            elif cel and not is_front_cw and not is_front_ccw:
                pts = space_pts(li, si)
                lines.append(f'<text x="{x:.1f}" y="{y+3:.1f}" text-anchor="middle" font-size="{7 if li==0 else 8}" fill="#0C447C" font-family="DM Sans,sans-serif">{pts}</text>')

            if li == 5 and not filled:
                lines.append(f'<text x="{cx}" y="{cy+5}" text-anchor="middle" font-size="12" font-weight="600" fill="#27500A" font-family="DM Sans,sans-serif">16</text>')

    lines.append(f'<circle cx="{cx}" cy="{cy}" r="{cx-3}" fill="none" stroke="rgba(120,90,40,0.25)" stroke-width="1.5"/>')
    for i, lbl in enumerate(["12","3","6","9"]):
        a=-math.pi/2+i*math.pi/2
        lines.append(f'<text x="{cx+(cx+8)*math.cos(a):.1f}" y="{cy+(cx+8)*math.sin(a)+4:.1f}" text-anchor="middle" font-size="10" fill="rgba(90,65,30,0.5)" font-family="DM Sans,sans-serif">{lbl}</text>')
    lines.append("</svg>")
    return "\n".join(lines)

def render_dots(n, max_n, pt):
    return '<div class="dot-row">' + "".join(f'<span class="dot dot-{pt}-{"on" if i<n else "off"}"></span>' for i in range(max_n)) + '</div>'

def pieces_html(pc):
    rows = ""
    for t, mx in [("black",18),("white",4),("blue",2)]:
        rows += f'<div style="margin-bottom:2px;">{render_dots(pc[t],mx,t)} <small style="color:#888;">{pc[t]}</small></div>'
    return rows

if "game" not in st.session_state: st.session_state.game = init_game()
if "mode" not in st.session_state: st.session_state.mode = "2p"
if "lang" not in st.session_state: st.session_state.lang = "ES"

G = st.session_state.game; mode = st.session_state.mode
G["_es"] = (st.session_state.lang == "ES"); ES = G["_es"]

col_title, col_lang = st.columns([3,1])
with col_title: st.markdown('<div class="jazam-title">JAZAM</div>', unsafe_allow_html=True)
with col_lang:
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    lang_sel = st.radio("", ["🇪🇸","🇬🇧"], horizontal=True, label_visibility="collapsed", index=0 if ES else 1)
    st.session_state.lang = "ES" if lang_sel == "🇪🇸" else "EN"
    ES = G["_es"] = (st.session_state.lang == "ES")

st.markdown(f'<div class="jazam-subtitle">{"meditación competitiva" if ES else "competitive meditation"}</div>', unsafe_allow_html=True)
tab_game, tab_rules = st.tabs(["🎮 Juego" if ES else "🎮 Game", "📖 Reglas" if ES else "📖 Rules"])

with tab_rules:
    st.divider()
    if ES:
        st.markdown("### ¿Qué es Jazam?")
        st.markdown('> *"Un mandala de decisiones donde cada pelotita puede cambiar tu destino."*')
        st.markdown("Jazam es un **juego de estrategia abstracta para 2 jugadores**. Cada nivel se llena desde dos extremos — elige cuál frente avanzar y cuándo bloquear al rival.")
        st.divider()
        st.markdown("### El tablero")
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("| Nivel | Espacios |\n|-------|----------|\n| 1 (exterior) | 32 |\n| 2 | 16 |\n| 3 | 8 |\n| 4 | 4 |\n| 5 | 2 |\n| 6 — Centro | 1 |")
        with col_b:
            st.markdown("Cada nivel tiene **dos frentes activos** — uno en cada extremo del anillo. Los frentes avanzan hacia el interior del nivel (uno horario, uno antihorario) hasta encontrarse.\n\nLos **espacios celestes** (azul) están en los niveles 1–3, en las posiciones 3:00, 6:00, 9:00 y 12:00.")
        st.divider()
        st.markdown("### Piezas (por jugador)")
        c1,c2,c3 = st.columns(3)
        with c1: st.markdown('<div class="rule-box" style="text-align:center;"><b>⚫ 18 Negras</b><br><small>Avanza 1 espacio desde el frente elegido (→ o ←)</small></div>', unsafe_allow_html=True)
        with c2: st.markdown('<div class="rule-box" style="text-align:center;"><b>🟡 4 Blancas</b><br><small>Cierra permanentemente el frente elegido — nadie puede seguir por ahí</small></div>', unsafe_allow_html=True)
        with c3: st.markdown('<div class="rule-box" style="text-align:center;"><b>🔵 2 Azules</b><br><small>Desde frente celeste → sube o baja de nivel + repite turno</small></div>', unsafe_allow_html=True)
        st.divider()
        st.markdown("### Turno")
        st.markdown("Cada turno colocas **1 pieza** y eliges **desde qué frente** actuar (→ extremo horario o ← extremo antihorario).")
        for tip, desc in [
            ("⚫ Negra → avanza un frente", "El frente elegido avanza 1 espacio hacia el interior del nivel."),
            ("🟡 Blanca → cierra un frente", "El frente elegido queda cerrado permanentemente. El otro frente puede seguir avanzando."),
            ("🔵 Azul → salta de nivel", "Solo si el frente activo está en un espacio celeste. Eliges ↑ subir o ↓ bajar. Ganas los puntos del celeste y repites turno."),
        ]:
            st.markdown(f'<div class="rule-box"><b>{tip}</b><br>{desc}</div>', unsafe_allow_html=True)
        st.divider()
        st.markdown("### Puntuación")
        st.markdown("**Espacios celestes** (solo con azul):\n\n| Nivel | 3:00 | 6:00 | 9:00 | 12:00 |\n|-------|------|------|------|-------|\n| 1 | 3 | 6 | 9 | **12** |\n| 2 | 2 | 4 | 6 | **8** |\n| 3 | 1 | 2 | 3 | **4** |")
        c1,c2 = st.columns(2)
        with c1: st.markdown('<div class="rule-box">🏛️ <b>Bono Arquitecto (+4)</b><br>Cuando los dos frentes se encuentran y el nivel queda completo.</div>', unsafe_allow_html=True)
        with c2: st.markdown('<div class="rule-box">🎯 <b>Centro (+16)</b><br>Llegar al centro termina el juego. Gana quien tenga más puntos.</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;margin-top:2rem;font-style:italic;color:#BA7517;">"Jazam no es un juego… es una meditación competitiva."</div>', unsafe_allow_html=True)
    else:
        st.markdown("### What is Jazam?")
        st.markdown('> *"A mandala of decisions where every bead can change your fate."*')
        st.markdown("Jazam is an **abstract strategy game for 2 players**. Each level fills from two ends — choose which front to advance and when to block your opponent.")
        st.divider()
        st.markdown("### The Board")
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("| Level | Spaces |\n|-------|--------|\n| 1 (outer) | 32 |\n| 2 | 16 |\n| 3 | 8 |\n| 4 | 4 |\n| 5 | 2 |\n| 6 — Center | 1 |")
        with col_b:
            st.markdown("Each level has **two active fronts** — one at each end of the ring. Fronts advance inward until they meet.\n\n**Celestial spaces** (blue) are in levels 1–3 at 3:00, 6:00, 9:00 and 12:00.")
        st.divider()
        st.markdown("### Beads (per player)")
        c1,c2,c3 = st.columns(3)
        with c1: st.markdown('<div class="rule-box" style="text-align:center;"><b>⚫ 18 Black</b><br><small>Advance 1 space from chosen front (→ or ←)</small></div>', unsafe_allow_html=True)
        with c2: st.markdown('<div class="rule-box" style="text-align:center;"><b>🟡 4 White</b><br><small>Permanently close the chosen front — nobody can advance there</small></div>', unsafe_allow_html=True)
        with c3: st.markdown('<div class="rule-box" style="text-align:center;"><b>🔵 2 Blue</b><br><small>From celestial front → go up or down a level + repeat turn</small></div>', unsafe_allow_html=True)
        st.divider()
        st.markdown("### Turn")
        st.markdown("Each turn place **1 bead** and choose **which front** to act from (→ clockwise end or ← counter-clockwise end).")
        for tip, desc in [
            ("⚫ Black → advance a front", "The chosen front advances 1 space inward."),
            ("🟡 White → close a front", "The chosen front is permanently closed. The other front can still advance."),
            ("🔵 Blue → jump levels", "Only if the active front is on a celestial space. Choose ↑ up or ↓ down. Score celestial points and take another turn."),
        ]:
            st.markdown(f'<div class="rule-box"><b>{tip}</b><br>{desc}</div>', unsafe_allow_html=True)
        st.divider()
        st.markdown("### Scoring")
        st.markdown("**Celestial spaces** (blue bead only):\n\n| Level | 3:00 | 6:00 | 9:00 | 12:00 |\n|-------|------|------|------|-------|\n| 1 | 3 | 6 | 9 | **12** |\n| 2 | 2 | 4 | 6 | **8** |\n| 3 | 1 | 2 | 3 | **4** |")
        c1,c2 = st.columns(2)
        with c1: st.markdown('<div class="rule-box">🏛️ <b>Architect Bonus (+4)</b><br>When the two fronts meet and the level is complete.</div>', unsafe_allow_html=True)
        with c2: st.markdown('<div class="rule-box">🎯 <b>Center (+16)</b><br>Reaching the center ends the game. Most points wins.</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;margin-top:2rem;font-style:italic;color:#BA7517;">"Jazam is not a game… it\'s competitive meditation."</div>', unsafe_allow_html=True)

with tab_game:
    lbl_2p = "👥 2 Jugadores" if ES else "👥 2 Players"
    lbl_ai  = "🤖 vs IA"       if ES else "🤖 vs AI"
    lbl_rst = "↺ Nueva partida" if ES else "↺ New game"
    c1,c2,c3 = st.columns(3)
    with c1:
        if st.button(lbl_2p, use_container_width=True, type="primary" if mode=="2p" else "secondary"):
            st.session_state.mode="2p"; st.session_state.game=init_game(); st.rerun()
    with c2:
        if st.button(lbl_ai, use_container_width=True, type="primary" if mode=="ai" else "secondary"):
            st.session_state.mode="ai"; st.session_state.game=init_game(); st.rerun()
    with c3:
        if st.button(lbl_rst, use_container_width=True):
            st.session_state.game=init_game(); st.rerun()

    st.markdown(f'<div style="text-align:right;margin-top:-4px;"><span style="font-size:11px;background:#EAF3DE;color:#27500A;border:0.5px solid #97C459;border-radius:10px;padding:2px 9px;">6 {"niveles" if ES else "levels"} · 18⚫ · 4🟡 · 2🔵</span></div>', unsafe_allow_html=True)
    st.divider()

    p1n = "Jugador 1" if ES else "Player 1"
    p2n = ("IA 🤖" if ES else "AI 🤖") if mode=="ai" else ("Jugador 2" if ES else "Player 2")
    p1c = "score-box active" if (G["cp"]==0 and not G["over"]) else "score-box"
    p2c = ("score-box active-ai" if mode=="ai" else "score-box active") if (G["cp"]==1 and not G["over"]) else "score-box"

    st.markdown(f"""
    <div style="display:flex;gap:10px;flex-wrap:wrap;">
      <div class="{p1c}" style="flex:1;min-width:110px;">
        <div class="score-name">{p1n}</div>
        <div class="score-pts">{G['scores'][0]} <span>pts</span></div>
        <div>{pieces_html(G['pieces'][0])}</div>
      </div>
      <div class="{p2c}" style="flex:1;min-width:110px;">
        <div class="score-name">{p2n}</div>
        <div class="score-pts">{G['scores'][1]} <span>pts</span></div>
        <div>{pieces_html(G['pieces'][1])}</div>
      </div>
    </div>""", unsafe_allow_html=True)

    if not G["over"]:
        cp=G["cp"]; li=G["cur_lv"]; lv=G["levels"][li]
        moves=get_moves(G)
        name=("IA" if ES else "AI") if (mode=="ai" and cp==1) else f"{'Jugador' if ES else 'Player'} {cp+1}"
        fcw=lv["front_cw"]; fccw=lv["front_ccw"]
        fcw_cel=is_celestial(li,fcw) and not lv["closed_cw"]
        fccw_cel=is_celestial(li,fccw) and not lv["closed_ccw"]

        if not G["j1_placed"]:
            bar_cls="status-bar celestial"
            txt=f"★ <b>{name}</b> — {'primera jugada: coloca en 12:00' if ES else 'first move: place at 12:00'}"
        elif not G["j2_chose"]:
            bar_cls="status-bar celestial"
            txt=f"★ <b>{name}</b> — {'elige tu sentido: ↻ o ↺' if ES else 'choose your direction: ↻ or ↺'}"
        elif not moves:
            bar_cls="status-bar warning"
            txt=f"⚠️ <b>{name}</b> — {'sin movimientos' if ES else 'no moves available'}"
        elif fcw_cel or fccw_cel:
            cel_si=fcw if fcw_cel else fccw
            pts=space_pts(li,cel_si)
            bar_cls="status-bar celestial"
            txt=f"★ <b>{name}</b> — {'Frente celeste' if ES else 'Celestial front'} · {pts}pts · {'Nv' if ES else 'Lv'}{li+1}"
        else:
            cw_info=f"↻ esp{fcw+1}" if not lv['closed_cw'] else "↻ ✕"
            ccw_info=f"↺ esp{fccw+1}" if not lv['closed_ccw'] else "↺ ✕"
            bar_cls="status-bar"
            txt=f"<b>{name}</b> — {'Nv' if ES else 'Lv'}{li+1} · {cw_info} · {ccw_info}"
        st.markdown(f'<div class="{bar_cls}">{txt}</div>', unsafe_allow_html=True)

    st.markdown(f'<div style="width:100%;max-width:440px;margin:8px auto;">{render_board_svg(G)}</div>', unsafe_allow_html=True)

    if not G["over"]:
        cp=G["cp"]; is_human=not(mode=="ai" and cp==1)
        moves=get_moves(G); pc=G["pieces"][cp]

        if is_human and moves:
            li=G["cur_lv"]; lv=G["levels"][li]
            can=lambda t,d:(t,d) in moves
            st.markdown(f"**{'Elige tu jugada:' if ES else 'Choose your move:'}**")
            c1,c2 = st.columns(2)
            with c1:
                lbl=f"⚫ ↻ {'Avanzar frente' if ES else 'Advance front'} ({pc['black']})"
                if st.button(lbl, disabled=not can("black","cw"), use_container_width=True, key="bk_cw"):
                    do_play(G,"black","cw",mode); st.rerun()
            with c2:
                lbl=f"⚫ ↺ {'Avanzar frente' if ES else 'Advance front'} ({pc['black']})"
                if st.button(lbl, disabled=not can("black","ccw"), use_container_width=True, key="bk_ccw"):
                    do_play(G,"black","ccw",mode); st.rerun()
            c1,c2 = st.columns(2)
            with c1:
                lbl=f"🟡 ↻ {'Cerrar frente' if ES else 'Close front'} ({pc['white']})"
                if st.button(lbl, disabled=not can("white","cw"), use_container_width=True, key="bw_cw"):
                    do_play(G,"white","cw",mode); st.rerun()
            with c2:
                lbl=f"🟡 ↺ {'Cerrar frente' if ES else 'Close front'} ({pc['white']})"
                if st.button(lbl, disabled=not can("white","ccw"), use_container_width=True, key="bw_ccw"):
                    do_play(G,"white","ccw",mode); st.rerun()
            if can("blue","up") or can("blue","down"):
                c1,c2 = st.columns(2)
                with c1:
                    lbl=f"🔵 ↑ {'Subir nivel' if ES else 'Go up'} ({pc['blue']})"
                    if st.button(lbl, disabled=not can("blue","up"), use_container_width=True, key="bb_up"):
                        do_play(G,"blue","up",mode); st.rerun()
                with c2:
                    lbl=f"🔵 ↓ {'Bajar nivel' if ES else 'Go down'} ({pc['blue']})"
                    if st.button(lbl, disabled=not can("blue","down"), use_container_width=True, key="bb_dn"):
                        do_play(G,"blue","down",mode); st.rerun()
        elif is_human and not moves:
            st.warning("Sin movimientos posibles." if ES else "No moves available.")
        else:
            st.info("🤖 La IA está pensando..." if ES else "🤖 AI is thinking...", icon="⏳")
            time.sleep(0.7); ai_move(G,mode); st.rerun()

    if G["over"]:
        p2l=("IA" if ES else "AI") if mode=="ai" else ("Jugador 2" if ES else "Player 2")
        w=G.get("winner")
        if w==-1: title="¡Empate!" if ES else "It's a tie!"; desc=f"J1: {G['scores'][0]}pts — {p2l}: {G['scores'][1]}pts"
        elif w==0: title="¡Jugador 1 gana! 🎉" if ES else "Player 1 wins! 🎉"; desc=f"J1: {G['scores'][0]}pts — {p2l}: {G['scores'][1]}pts"
        else: title=f"¡{p2l} gana! 🎉" if ES else f"{p2l} wins! 🎉"; desc=f"J1: {G['scores'][0]}pts — {p2l}: {G['scores'][1]}pts"
        st.markdown(f'<div class="winner-box"><div class="winner-title">{title}</div><div class="winner-scores">{desc}</div></div>', unsafe_allow_html=True)

    if G["log"]:
        st.markdown("#### Historial" if ES else "#### Game log")
        entries=""
        for e in reversed(G["log"]):
            who=e["who"]; wc="log-j1" if who in("J1","P1") else("log-ai" if who in("IA","AI") else "log-j2")
            pts_html=f' <span class="log-pts">+{e["pts"]}</span>' if e["pts"]>0 else ""
            entries+=f'<div class="log-entry"><span style="color:#aaa;">#{e["turn"]}</span> <span class="{wc}">{who}</span> {e["msg"]}{pts_html}</div>'
        st.markdown(f'<div class="log-container">{entries}</div>', unsafe_allow_html=True)
