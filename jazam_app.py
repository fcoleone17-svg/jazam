"""
JAZAM v5 — Dos punteros independientes por nivel
Negra  → avanza 1 espacio en la dirección elegida (↻ o ↺) · rival coloca 1
Blanca → avanza 1 espacio en la dirección elegida · rival coloca 2
         (primer espacio es zona de bloqueo — pieza pierde propiedades)
Azul   → solo en celeste · sube de nivel · repite turno
Primera jugada siempre en 12:00. Luego cada turno elige ↻ o ↺ independientemente.
"""

import streamlit as st
import math, time, random

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
.status-bar.blocking{background:#FFF3CD;border-color:#BA7517;color:#633806;}
.status-bar.first{background:#EAF3DE;border-color:#3B6D11;color:#27500A;}
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
  .status-bar{font-size:0.78rem!important;}
}
</style>
""", unsafe_allow_html=True)

# ── Constantes ────────────────────────────────────────────────────────────────
LEVELS = [32, 16, 8, 4, 2, 1]
INIT_PIECES = {"black": 14, "white": 8, "blue": 2}

# Celestes: índice base 0
# Nivel 1 (32): 3:00=idx8, 6:00=idx16, 9:00=idx24  → 6pts
# Nivel 2 (16): esp3=idx2, esp7=idx6, esp11=idx10, esp15=idx14 → 4pts
# Nivel 3 (8):  12:00=idx0, 3:00=idx2, 6:00=idx4, 9:00=idx6 → 2pts
CELESTIALS = {
    0: {8:6, 16:6, 24:6},
    1: {2:4, 6:4, 10:4, 14:4},
    2: {0:2, 2:2, 4:2, 6:2},
}

def is_celestial(li, si):
    return si in CELESTIALS.get(li, {})

def space_pts(li, si):
    if li == 5: return 16
    return CELESTIALS.get(li, {}).get(si, 0)

def aligned_si(li, si, new_li):
    return round(si * LEVELS[new_li] / LEVELS[li]) % LEVELS[new_li]

# ── Estado ────────────────────────────────────────────────────────────────────
def init_game():
    """
    Dos punteros independientes por nivel.
    ptr_cw:  próximo espacio libre yendo ↻ desde 12:00
    ptr_ccw: próximo espacio libre yendo ↺ desde 12:00
    Ambos parten en idx 0. Primera jugada fija en 12:00.
    Luego cada turno elige libremente ↻ o ↺.
    """
    return {
        "cp": 0, "scores": [0, 0],
        "pieces": [dict(INIT_PIECES), dict(INIT_PIECES)],
        "board": [[None]*n for n in LEVELS],
        "lv": 0,
        "ptr_cw": 1,       # next to fill clockwise (starts at idx 1 after 12:00 placed)
        "ptr_ccw": LEVELS[0]-1,  # next to fill ccw (last space)
        "started": False,  # primera pieza en 12:00 aún no colocada
        "to_place": 1,
        "placed_this_turn": 0,
        "blocking_space": False,
        "last_color": None,
        "over": False, "log": [], "turn_count": 0,
        "winner": None, "win_reason": None, "_es": True,
    }

def find_free_cw(G):
    """Próximo espacio libre yendo ↻"""
    lv = G["lv"]; n = LEVELS[lv]; board = G["board"][lv]
    si = G["ptr_cw"] % n
    for _ in range(n):
        if board[si] is None: return si
        si = (si + 1) % n
    return None

def find_free_ccw(G):
    """Próximo espacio libre yendo ↺"""
    lv = G["lv"]; n = LEVELS[lv]; board = G["board"][lv]
    si = G["ptr_ccw"] % n
    for _ in range(n):
        if board[si] is None: return si
        si = (si - 1) % n
    return None

def valid_moves(G):
    cp = G["cp"]; pc = G["pieces"][cp]; blocking = G["blocking_space"]
    lv = G["lv"]

    # Primera jugada: solo en 12:00 (idx 0)
    if not G["started"]:
        moves = []
        if pc["black"] > 0: moves.append(("black", "start"))
        if pc["white"] > 0: moves.append(("white", "start"))
        return moves

    t_cw  = find_free_cw(G)
    t_ccw = find_free_ccw(G)
    moves = []

    for d, tgt in [("cw", t_cw), ("ccw", t_ccw)]:
        if tgt is None: continue
        # If both pointers point to same space, only add once
        if d == "ccw" and tgt == t_cw: continue
        cel = is_celestial(lv, tgt) and not blocking
        if pc["black"] > 0: moves.append(("black", d))
        if pc["white"] > 0: moves.append(("white", d))
        if pc["blue"] > 0 and cel and lv < 5:
            moves.append(("blue", d))

    # Deduplicate
    seen = set(); unique = []
    for m in moves:
        if m not in seen: seen.add(m); unique.append(m)
    return unique

def add_log(G, who, msg, pts=0):
    G["turn_count"] += 1
    G["log"].append({"turn": G["turn_count"], "who": who, "msg": msg, "pts": pts})

def do_play(G, piece_type, direction, mode):
    if G["over"]: return
    cp = G["cp"]; pc = G["pieces"][cp]
    lv = G["lv"]; n = LEVELS[lv]; blocking = G["blocking_space"]
    ES = G.get("_es", True)
    who = ("IA" if ES else "AI") if (mode=="ai" and cp==1) else f"J{cp+1}"
    tn = {"black":"negra" if ES else "black",
          "white":"blanca" if ES else "white",
          "blue":"azul" if ES else "blue"}[piece_type]
    dn = {"cw":"↻","ccw":"↺","start":"12:00"}[direction]

    # Determine target space
    if direction == "start":
        target_si = 0
    elif direction == "cw":
        target_si = find_free_cw(G)
    else:
        target_si = find_free_ccw(G)

    if target_si is None: pc[piece_type] += 1; return

    # In blocking zone: piece is neutralized
    neutralized = blocking
    effective_type = "black" if neutralized else piece_type

    pc[piece_type] -= 1
    G["board"][lv][target_si] = {"p": cp, "t": piece_type, "neutralized": neutralized}
    G["last_color"] = effective_type
    G["placed_this_turn"] += 1

    # Update pointers
    if direction == "start":
        G["started"] = True
        G["ptr_cw"] = 1
        G["ptr_ccw"] = n - 1
    elif direction == "cw":
        G["ptr_cw"] = (target_si + 1) % n
    else:
        G["ptr_ccw"] = (target_si - 1) % n

    pts = 0
    note = " [bloqueo]" if neutralized else ""
    add_log(G, who, f"{tn} {dn} Nv{lv+1}·esp{target_si+1}{note}", pts)

    # Blue: score + go up
    if effective_type == "blue":
        pts = space_pts(lv, target_si)
        G["scores"][cp] += pts
        new_lv = lv + 1
        new_si = aligned_si(lv, target_si, new_lv)
        G["lv"] = new_lv
        n_new = LEVELS[new_lv]
        G["ptr_cw"] = (new_si + 1) % n_new
        G["ptr_ccw"] = (new_si - 1) % n_new
        G["board"][new_lv][new_si] = {"p": cp, "t": "blue", "neutralized": False}
        G["started"] = True
        add_log(G, who, f"azul sube Nv{new_lv+1}·esp{new_si+1}", pts)
        G["placed_this_turn"] = 0; G["to_place"] = 1; G["blocking_space"] = False
        check_end(G, mode); return

    # Bono arquitecto
    if all(x is not None for x in G["board"][lv]):
        G["scores"][cp] += 4
        add_log(G, who, f"Nv{lv+1} completo · +4" if ES else f"Lv{lv+1} complete · +4", 4)

    # Turn management
    done = G["placed_this_turn"] >= G["to_place"]
    if done:
        if effective_type == "white":
            G["to_place"] = 2
            G["blocking_space"] = True
        else:
            G["to_place"] = 1
            G["blocking_space"] = False
        G["cp"] = 1 - cp
        G["placed_this_turn"] = 0
    else:
        G["blocking_space"] = False  # second placement is normal

    check_end(G, mode)

def check_end(G, mode):
    if G["lv"] == 5 and any(x is not None for x in G["board"][5]):
        who_idx = next(x["p"] for x in G["board"][5] if x is not None)
        G["scores"][who_idx] += 16
        ES = G.get("_es", True)
        who = ("IA" if ES else "AI") if (mode=="ai" and who_idx==1) else f"J{who_idx+1}"
        add_log(G, who, "¡CENTRO! +16" if ES else "CENTER! +16", 16)
        G["over"] = True
        G["winner"] = 0 if G["scores"][0]>G["scores"][1] else (1 if G["scores"][1]>G["scores"][0] else -1)
        G["win_reason"] = "center"; return
    for p in range(2):
        pc = G["pieces"][p]
        if pc["black"]<=0 and pc["white"]<=0 and pc["blue"]<=0:
            G["over"] = True; G["winner"] = 1-p; G["win_reason"] = "nopcs"
            ES = G.get("_es", True)
            who = ("IA" if ES else "AI") if (mode=="ai" and p==1) else f"J{p+1}"
            add_log(G, who, "sin piezas" if ES else "out of beads", 0); return
    if not valid_moves(G):
        cp = G["cp"]; G["over"] = True; G["winner"] = 1-cp; G["win_reason"] = "trapped"

def ai_move(G, mode):
    moves = valid_moves(G)
    if not moves: G["over"]=True; G["winner"]=0; G["win_reason"]="nopcs"; return
    lv = G["lv"]; blocking = G["blocking_space"]; pc = G["pieces"][1]

    if blocking:
        black = [m for m in moves if m[0]=="black"]
        if black: do_play(G,"black",random.choice(black)[1],mode); return

    blue = [(t,d) for t,d in moves if t=="blue"]
    for t,d in blue:
        tgt = find_free_cw(G) if d=="cw" else find_free_ccw(G)
        if tgt is not None and space_pts(lv,tgt)>=4:
            do_play(G,t,d,mode); return

    black = [(t,d) for t,d in moves if t=="black"]
    if black:
        best=None; best_dist=999; n=LEVELS[lv]
        for t,d in black:
            tgt=find_free_cw(G) if d=="cw" else find_free_ccw(G)
            if tgt is None: continue
            for dist in range(1,n):
                cand=(tgt+dist)%n if d=="cw" else (tgt-dist)%n
                if is_celestial(lv,cand) and G["board"][lv][cand] is None:
                    if dist<best_dist: best_dist=dist; best=(t,d)
                    break
        if best: do_play(G,best[0],best[1],mode); return
        t,d=random.choice(black); do_play(G,t,d,mode); return

    white=[(t,d) for t,d in moves if t=="white"]
    if white: t,d=random.choice(white); do_play(G,t,d,mode); return
    t,d=random.choice(moves); do_play(G,t,d,mode)

# ── SVG ───────────────────────────────────────────────────────────────────────
def render_board_svg(G):
    SIZE=440; cx=cy=SIZE//2
    radii=[int(cx*r) for r in [0.91,0.74,0.57,0.41,0.26,0.0]]
    lines=[f'<svg viewBox="0 0 {SIZE} {SIZE}" width="100%" style="max-width:{SIZE}px;display:block;margin:0 auto;" xmlns="http://www.w3.org/2000/svg">']
    lines.append(f'<circle cx="{cx}" cy="{cy}" r="{cx-2}" fill="#F5F1E4" stroke="#D3C8A0" stroke-width="1.5"/>')

    for li in range(3):
        n=LEVELS[li]; rO=radii[li]+11; rI=radii[li+1]+11
        for k in range(8):
            s=k*n//8; a1=-math.pi/2+(s/n)*math.pi*2; a2=-math.pi/2+((s+n/8)/n)*math.pi*2
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

    nlv=G["lv"]; blocking=G["blocking_space"]
    t_cw=find_free_cw(G) if G["started"] else 0
    t_ccw=find_free_ccw(G) if G["started"] else 0
    first_space = (not G["started"])  # 12:00 is the target

    for li in range(6):
        n=LEVELS[li]
        for si in range(n):
            if li==5: x,y=cx,cy; r_dot=22
            else:
                a=-math.pi/2+(si/n)*math.pi*2; x=cx+radii[li]*math.cos(a); y=cy+radii[li]*math.sin(a); r_dot=10

            cel=is_celestial(li,si); cell=G["board"][li][si]
            is_cw_target = (li==nlv and si==t_cw and not G["over"] and cell is None and G["started"] and t_cw!=t_ccw)
            is_ccw_target = (li==nlv and si==t_ccw and not G["over"] and cell is None and G["started"] and t_cw!=t_ccw)
            is_first = (li==nlv and si==0 and first_space and not G["over"])
            is_blocking_target = blocking and (is_cw_target or is_ccw_target)

            if li==5: fill,stroke,sw="#DDF0CC","#3B6D11",2
            elif is_first: fill,stroke,sw="rgba(59,109,17,0.2)","#3B6D11",2.5
            elif is_blocking_target: fill,stroke,sw="rgba(230,100,30,0.25)","#D85A30",2.5
            elif is_cw_target or is_ccw_target: fill,stroke,sw="rgba(186,117,23,0.25)","#BA7517",2.5
            elif cel: fill,stroke,sw="#C5E8FF","#185FA5",1.5
            else: fill,stroke,sw="rgba(80,60,20,0.05)","rgba(80,60,20,0.15)",0.7

            lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r_dot}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

            if cel and not cell and not is_cw_target and not is_ccw_target and not is_first:
                pts=space_pts(li,si)
                lines.append(f'<text x="{x:.1f}" y="{y+3:.1f}" text-anchor="middle" font-size="{7 if li==0 else 8}" fill="#0C447C" font-family="DM Sans,sans-serif">{pts}</text>')
            if li==5 and not any(x2 is not None for x2 in G["board"][5]):
                lines.append(f'<text x="{cx}" y="{cy+5}" text-anchor="middle" font-size="12" font-weight="600" fill="#27500A" font-family="DM Sans,sans-serif">16</text>')

            if cell:
                t=cell["t"]; neu=cell.get("neutralized",False); pr=r_dot-2.5
                if neu or t=="black": pf,ps="#111110","#999990"
                elif t=="white": pf,ps="#E8D44D","#B89A10"
                else: pf,ps="#378ADD","#185FA5"
                lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{pr}" fill="{pf}" stroke="{ps}" stroke-width="1.5"/>')
                if neu and t!="black":
                    lines.append(f'<line x1="{x-3:.1f}" y1="{y-3:.1f}" x2="{x+3:.1f}" y2="{y+3:.1f}" stroke="#E24B4A" stroke-width="1.5"/>')
                    lines.append(f'<line x1="{x+3:.1f}" y1="{y-3:.1f}" x2="{x-3:.1f}" y2="{y+3:.1f}" stroke="#E24B4A" stroke-width="1.5"/>')
                pd="#BA7517" if cell["p"]==0 else "#185FA5"
                lines.append(f'<circle cx="{x:.1f}" cy="{y+pr-2:.1f}" r="1.8" fill="{pd}"/>')

    lines.append(f'<circle cx="{cx}" cy="{cy}" r="{cx-3}" fill="none" stroke="rgba(120,90,40,0.25)" stroke-width="1.5"/>')
    for i,lbl in enumerate(["12","3","6","9"]):
        a=-math.pi/2+i*math.pi/2
        lines.append(f'<text x="{cx+(cx+8)*math.cos(a):.1f}" y="{cy+(cx+8)*math.sin(a)+4:.1f}" text-anchor="middle" font-size="10" fill="rgba(90,65,30,0.5)" font-family="DM Sans,sans-serif">{lbl}</text>')
    lines.append("</svg>")
    return "\n".join(lines)

def render_dots(n,max_n,pt):
    return '<div class="dot-row">'+"".join(f'<span class="dot dot-{pt}-{"on" if i<n else "off"}"></span>' for i in range(max_n))+'</div>'

def pieces_html(pc):
    rows=""
    for t,mx in [("black",14),("white",8),("blue",2)]:
        rows+=f'<div style="margin-bottom:2px;">{render_dots(pc[t],mx,t)} <small style="color:#888;">{pc[t]}</small></div>'
    return rows

# ── App ───────────────────────────────────────────────────────────────────────
if "game" not in st.session_state: st.session_state.game=init_game()
if "mode" not in st.session_state: st.session_state.mode="2p"
if "lang" not in st.session_state: st.session_state.lang="ES"

G=st.session_state.game; mode=st.session_state.mode
G["_es"]=(st.session_state.lang=="ES"); ES=G["_es"]

col_title,col_lang=st.columns([3,1])
with col_title: st.markdown('<div class="jazam-title">JAZAM</div>',unsafe_allow_html=True)
with col_lang:
    st.markdown("<div style='height:12px'></div>",unsafe_allow_html=True)
    lang_sel=st.radio("",["🇪🇸","🇬🇧"],horizontal=True,label_visibility="collapsed",index=0 if ES else 1)
    st.session_state.lang="ES" if lang_sel=="🇪🇸" else "EN"
    ES=G["_es"]=(st.session_state.lang=="ES")

st.markdown(f'<div class="jazam-subtitle">{"meditación competitiva" if ES else "competitive meditation"}</div>',unsafe_allow_html=True)
tab_game,tab_rules=st.tabs(["🎮 Juego" if ES else "🎮 Game","📖 Reglas" if ES else "📖 Rules"])

with tab_rules:
    st.divider()
    if ES:
        st.markdown("### ¿Qué es Jazam?")
        st.markdown('> *"Un mandala de decisiones donde cada pelotita puede cambiar tu destino."*')
        st.markdown("Jazam es un **juego de estrategia abstracta para 2 jugadores**. Cada turno eliges en qué dirección avanzar, usa la zona de bloqueo a tu favor y llega al centro con más puntos.")
        st.divider()
        st.markdown("### El tablero")
        col_a,col_b=st.columns(2)
        with col_a:
            st.markdown("| Nivel | Espacios |\n|-------|----------|\n| 1 (exterior) | 32 |\n| 2 | 16 |\n| 3 | 8 |\n| 4 | 4 |\n| 5 | 2 |\n| 6 — Centro | 1 |")
        with col_b:
            st.markdown("El juego empieza en **12:00**. Desde ahí dos punteros independientes avanzan ↻ y ↺. Cada turno eliges libremente cuál dirección avanzar.\n\n**Celestes** (azul): dan puntos al usar azul.\n**Zona naranja**: zona de bloqueo — la pieza pierde sus propiedades.")
        st.divider()
        st.markdown("### Piezas (por jugador)")
        c1,c2,c3=st.columns(3)
        with c1: st.markdown('<div class="rule-box" style="text-align:center;"><b>⚫ 14 Negras</b><br><small>Avanza 1 espacio · rival coloca 1</small></div>',unsafe_allow_html=True)
        with c2: st.markdown('<div class="rule-box" style="text-align:center;"><b>🟡 8 Blancas</b><br><small>Avanza 1 espacio · rival coloca 2 (primero en zona de bloqueo)</small></div>',unsafe_allow_html=True)
        with c3: st.markdown('<div class="rule-box" style="text-align:center;"><b>🔵 2 Azules</b><br><small>Solo en celeste · sube de nivel · repite turno</small></div>',unsafe_allow_html=True)
        st.divider()
        st.markdown("### Zona de bloqueo")
        st.markdown('<div class="rule-box">⚠️ Cuando el rival juega <b>blanca</b>, colocas 2 piezas. El <b>primer espacio</b> es zona de bloqueo: cualquier pieza ahí pierde sus propiedades (azul no sube, blanca no fuerza 2). El segundo espacio es normal.</div>',unsafe_allow_html=True)
        st.divider()
        st.markdown("### Puntuación")
        st.markdown("| Nivel | Celestes | Puntos |\n|-------|----------|--------|\n| 1 | 3:00, 6:00, 9:00 | 6 pts |\n| 2 | esp 3, 7, 11, 15 | 4 pts |\n| 3 | 12:00, 3:00, 6:00, 9:00 | 2 pts |")
        c1,c2=st.columns(2)
        with c1: st.markdown('<div class="rule-box">🏛️ <b>Bono Arquitecto (+4)</b><br>Al completar todos los espacios de un nivel.</div>',unsafe_allow_html=True)
        with c2: st.markdown('<div class="rule-box">🎯 <b>Centro (+16)</b><br>Llegar al centro termina el juego. Gana quien tenga más puntos.</div>',unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;margin-top:2rem;font-style:italic;color:#BA7517;">"Jazam no es un juego… es una meditación competitiva."</div>',unsafe_allow_html=True)
    else:
        st.markdown("### What is Jazam?")
        st.markdown('> *"A mandala of decisions where every bead can change your fate."*')
        st.markdown("Jazam is an **abstract strategy game for 2 players**. Each turn choose which direction to advance, use the blocking zone strategically and reach the center with more points.")
        st.divider()
        st.markdown("### Beads (per player)")
        c1,c2,c3=st.columns(3)
        with c1: st.markdown('<div class="rule-box" style="text-align:center;"><b>⚫ 14 Black</b><br><small>Advance 1 space · opponent places 1</small></div>',unsafe_allow_html=True)
        with c2: st.markdown('<div class="rule-box" style="text-align:center;"><b>🟡 8 White</b><br><small>Advance 1 space · opponent places 2 (first in blocking zone)</small></div>',unsafe_allow_html=True)
        with c3: st.markdown('<div class="rule-box" style="text-align:center;"><b>🔵 2 Blue</b><br><small>Celestial only · go up one level · repeat turn</small></div>',unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;margin-top:2rem;font-style:italic;color:#BA7517;">"Jazam is not a game… it\'s competitive meditation."</div>',unsafe_allow_html=True)

with tab_game:
    lbl_2p="👥 2 Jugadores" if ES else "👥 2 Players"
    lbl_ai="🤖 vs IA" if ES else "🤖 vs AI"
    lbl_rst="↺ Nueva partida" if ES else "↺ New game"
    c1,c2,c3=st.columns(3)
    with c1:
        if st.button(lbl_2p,use_container_width=True,type="primary" if mode=="2p" else "secondary"):
            st.session_state.mode="2p"; st.session_state.game=init_game(); st.rerun()
    with c2:
        if st.button(lbl_ai,use_container_width=True,type="primary" if mode=="ai" else "secondary"):
            st.session_state.mode="ai"; st.session_state.game=init_game(); st.rerun()
    with c3:
        if st.button(lbl_rst,use_container_width=True):
            st.session_state.game=init_game(); st.rerun()

    st.markdown(f'<div style="text-align:right;margin-top:-4px;"><span style="font-size:11px;background:#EAF3DE;color:#27500A;border:0.5px solid #97C459;border-radius:10px;padding:2px 9px;">6 {"niveles" if ES else "levels"} · 14⚫ · 8🟡 · 2🔵</span></div>',unsafe_allow_html=True)
    st.divider()

    p1n="Jugador 1" if ES else "Player 1"
    p2n=("IA 🤖" if ES else "AI 🤖") if mode=="ai" else ("Jugador 2" if ES else "Player 2")
    p1c="score-box active" if (G["cp"]==0 and not G["over"]) else "score-box"
    p2c=("score-box active-ai" if mode=="ai" else "score-box active") if (G["cp"]==1 and not G["over"]) else "score-box"

    st.markdown(f"""<div style="display:flex;gap:10px;flex-wrap:wrap;">
      <div class="{p1c}" style="flex:1;min-width:110px;">
        <div class="score-name">{p1n}</div>
        <div class="score-pts">{G['scores'][0]} <span>pts</span></div>
        <div>{pieces_html(G['pieces'][0])}</div>
      </div>
      <div class="{p2c}" style="flex:1;min-width:110px;">
        <div class="score-name">{p2n}</div>
        <div class="score-pts">{G['scores'][1]} <span>pts</span></div>
        <div>{pieces_html(G['pieces'][1])}</div>
      </div></div>""",unsafe_allow_html=True)

    if not G["over"]:
        cp=G["cp"]; lv=G["lv"]; blocking=G["blocking_space"]
        moves=valid_moves(G)
        name=("IA" if ES else "AI") if (mode=="ai" and cp==1) else f"{'Jugador' if ES else 'Player'} {cp+1}"
        t_cw=find_free_cw(G) if G["started"] else 0
        t_ccw=find_free_ccw(G) if G["started"] else 0
        cw_cel=is_celestial(lv,t_cw) if t_cw is not None else False
        ccw_cel=is_celestial(lv,t_ccw) if t_ccw is not None else False

        if not G["started"]:
            bar_cls="status-bar first"
            txt=f"🟢 <b>{name}</b> — {'primera jugada: coloca en 12:00' if ES else 'first move: place at 12:00'}"
        elif blocking:
            bar_cls="status-bar blocking"
            txt=f"⚠️ <b>{name}</b> — {'zona de bloqueo · la pieza pierde sus propiedades' if ES else 'blocking zone · bead loses its properties'}"
        elif not moves:
            bar_cls="status-bar warning"
            txt=f"⚠️ <b>{name}</b> — {'sin movimientos' if ES else 'no moves'}"
        elif cw_cel or ccw_cel:
            bar_cls="status-bar celestial"
            txt=f"★ <b>{name}</b> — {'celeste disponible' if ES else 'celestial available'} · {'Nv' if ES else 'Lv'}{lv+1}"
        else:
            bar_cls="status-bar"
            cw_txt=f"↻ esp{t_cw+1}" if t_cw is not None else "↻ —"
            ccw_txt=f"↺ esp{t_ccw+1}" if t_ccw is not None else "↺ —"
            txt=f"<b>{name}</b> — {'Nv' if ES else 'Lv'}{lv+1} · {cw_txt} · {ccw_txt}"
        st.markdown(f'<div class="{bar_cls}">{txt}</div>',unsafe_allow_html=True)

    st.markdown(f'<div style="width:100%;max-width:440px;margin:8px auto;">{render_board_svg(G)}</div>',unsafe_allow_html=True)

    if not G["over"]:
        cp=G["cp"]; is_human=not(mode=="ai" and cp==1)
        moves=valid_moves(G); pc=G["pieces"][cp]

        if is_human and moves:
            can=lambda t,d:(t,d) in moves
            if not G["started"]:
                st.markdown(f"**{'Primera jugada — coloca en 12:00:' if ES else 'First move — place at 12:00:'}**")
                c1,c2=st.columns(2)
                with c1:
                    if st.button(f"⚫ {'Negra' if ES else 'Black'} 12:00 ({pc['black']})",disabled=not can("black","start"),use_container_width=True,key="bk_st"):
                        do_play(G,"black","start",mode); st.rerun()
                with c2:
                    if st.button(f"🟡 {'Blanca' if ES else 'White'} 12:00 ({pc['white']})",disabled=not can("white","start"),use_container_width=True,key="bw_st"):
                        do_play(G,"white","start",mode); st.rerun()
            else:
                st.markdown(f"**{'Elige tu jugada:' if ES else 'Choose your move:'}**")
                c1,c2=st.columns(2)
                with c1:
                    if st.button(f"⚫ ↻ {'Negra' if ES else 'Black'} ({pc['black']})",disabled=not can("black","cw"),use_container_width=True,key="bk_cw"):
                        do_play(G,"black","cw",mode); st.rerun()
                with c2:
                    if st.button(f"⚫ ↺ {'Negra' if ES else 'Black'} ({pc['black']})",disabled=not can("black","ccw"),use_container_width=True,key="bk_ccw"):
                        do_play(G,"black","ccw",mode); st.rerun()
                c1,c2=st.columns(2)
                with c1:
                    if st.button(f"🟡 ↻ {'Blanca' if ES else 'White'} ({pc['white']})",disabled=not can("white","cw"),use_container_width=True,key="bw_cw"):
                        do_play(G,"white","cw",mode); st.rerun()
                with c2:
                    if st.button(f"🟡 ↺ {'Blanca' if ES else 'White'} ({pc['white']})",disabled=not can("white","ccw"),use_container_width=True,key="bw_ccw"):
                        do_play(G,"white","ccw",mode); st.rerun()
                if can("blue","cw") or can("blue","ccw"):
                    c1,c2=st.columns(2)
                    with c1:
                        if st.button(f"🔵 ↻ {'Azul' if ES else 'Blue'} ({pc['blue']})",disabled=not can("blue","cw"),use_container_width=True,key="bb_cw"):
                            do_play(G,"blue","cw",mode); st.rerun()
                    with c2:
                        if st.button(f"🔵 ↺ {'Azul' if ES else 'Blue'} ({pc['blue']})",disabled=not can("blue","ccw"),use_container_width=True,key="bb_ccw"):
                            do_play(G,"blue","ccw",mode); st.rerun()
        elif is_human and not moves:
            st.warning("Sin movimientos posibles." if ES else "No moves available.")
        else:
            st.info("🤖 La IA está pensando..." if ES else "🤖 AI is thinking...",icon="⏳")
            time.sleep(0.7); ai_move(G,mode); st.rerun()

    if G["over"]:
        p2l=("IA" if ES else "AI") if mode=="ai" else ("Jugador 2" if ES else "Player 2")
        w=G.get("winner")
        if w==-1: title="¡Empate!" if ES else "It's a tie!"; desc=f"J1: {G['scores'][0]}pts — {p2l}: {G['scores'][1]}pts"
        elif w==0: title="¡Jugador 1 gana! 🎉" if ES else "Player 1 wins! 🎉"; desc=f"J1: {G['scores'][0]}pts — {p2l}: {G['scores'][1]}pts"
        else: title=f"¡{p2l} gana! 🎉" if ES else f"{p2l} wins! 🎉"; desc=f"J1: {G['scores'][0]}pts — {p2l}: {G['scores'][1]}pts"
        st.markdown(f'<div class="winner-box"><div class="winner-title">{title}</div><div class="winner-scores">{desc}</div></div>',unsafe_allow_html=True)

    if G["log"]:
        st.markdown("#### Historial" if ES else "#### Game log")
        entries=""
        for e in reversed(G["log"]):
            who=e["who"]; wc="log-j1" if who in("J1","P1") else("log-ai" if who in("IA","AI") else "log-j2")
            pts_html=f' <span class="log-pts">+{e["pts"]}</span>' if e["pts"]>0 else ""
            entries+=f'<div class="log-entry"><span style="color:#aaa;">#{e["turn"]}</span> <span class="{wc}">{who}</span> {e["msg"]}{pts_html}</div>'
        st.markdown(f'<div class="log-container">{entries}</div>',unsafe_allow_html=True)
