"""
JAZAM v3 — Nueva mecánica: navegación y bloqueo
6 niveles · 14 negras · 8 blancas · 2 azules
Negra: avanza el marcador 1 espacio (horario o antihorario)
Blanca: bloquea el espacio siguiente en esa dirección (máx 1 por nivel)
Azul: desde celeste, sube o baja de nivel, repite turno
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
.status-bar.blocked{background:#FAEEDA;border-color:#BA7517;color:#633806;}
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
@media(max-width:600px){
  .jazam-title{font-size:1.9rem!important;}
  .score-pts{font-size:1.4rem!important;}
  .dot{width:7px!important;height:7px!important;}
  .status-bar{font-size:0.78rem!important;padding:7px 10px!important;}
}
</style>
""", unsafe_allow_html=True)

LEVELS = [32, 16, 8, 4, 2, 1]
INIT_PIECES = {"black": 14, "white": 8, "blue": 2}

PTS_TABLE = [[12,3,6,9],[8,2,4,6],[4,1,2,3]]

def is_celestial(li, si):
    if li >= 3: return False
    return si % (LEVELS[li] // 4) == 0

def space_pts(li, si):
    if li == 5: return 16
    if not is_celestial(li, si): return 0
    return PTS_TABLE[li][si // (LEVELS[li] // 4)]

def nxt(li, si, d):
    n = LEVELS[li]
    return (si+1)%n if d=="cw" else (si-1)%n

def aligned_si(li, si, new_li):
    return round(si * LEVELS[new_li] / LEVELS[li]) % LEVELS[new_li]

def init_game():
    return {
        "cp":0, "scores":[0,0],
        "pieces":[dict(INIT_PIECES), dict(INIT_PIECES)],
        "board":[[None]*n for n in LEVELS],
        "blocks":[[] for _ in LEVELS],
        "whites_lv":[0]*6,
        "lv":0, "si":0,
        "over":False, "log":[], "turn_count":0,
        "winner":None, "win_reason":None, "_es":True,
    }

def get_moves(G):
    cp=G["cp"]; pc=G["pieces"][cp]; lv=G["lv"]; si=G["si"]; moves=[]
    if pc["black"]>0:
        for d in ["cw","ccw"]:
            ns=nxt(lv,si,d)
            if ns not in G["blocks"][lv] and G["board"][lv][ns] is None:
                moves.append(("black",d))
    if pc["white"]>0 and G["whites_lv"][lv]==0:
        for d in ["cw","ccw"]:
            ns=nxt(lv,si,d)
            if ns not in G["blocks"][lv] and G["board"][lv][ns] is None:
                moves.append(("white",d))
    if pc["blue"]>0 and is_celestial(lv,si):
        if lv<5: moves.append(("blue","up"))
        if lv>0: moves.append(("blue","down"))
    return moves

def add_log(G, who, msg, pts=0):
    G["turn_count"]+=1
    G["log"].append({"turn":G["turn_count"],"who":who,"msg":msg,"pts":pts})

def do_play(G, t, d, mode):
    if G["over"]: return
    cp=G["cp"]; pc=G["pieces"][cp]; lv=G["lv"]; si=G["si"]
    ES=G.get("_es",True)
    who=("IA" if ES else "AI") if (mode=="ai" and cp==1) else f"J{cp+1}"
    tn={"black":"negra" if ES else "black","white":"blanca" if ES else "white","blue":"azul" if ES else "blue"}[t]
    dn={"cw":"→","ccw":"←","up":"↑","down":"↓"}[d]
    pc[t]-=1

    if t=="black":
        ns=nxt(lv,si,d)
        G["board"][lv][ns]={"p":cp,"t":"black"}
        G["si"]=ns
        add_log(G,who,f"{tn} {dn} Nv{lv+1}·esp{ns+1}",0)
        filled=sum(1 for x in G["board"][lv] if x is not None)
        if filled+len(G["blocks"][lv])==LEVELS[lv]:
            G["scores"][cp]+=4
            add_log(G,who,"Nivel completo · +4" if ES else "Level complete · +4",4)
        G["cp"]=1-cp

    elif t=="white":
        ns=nxt(lv,si,d)
        G["blocks"][lv].append(ns)
        G["whites_lv"][lv]+=1
        G["board"][lv][ns]={"p":cp,"t":"white"}
        add_log(G,who,f"{tn} bloquea {dn} Nv{lv+1}·esp{ns+1}" if ES else f"{tn} blocks {dn} Lv{lv+1}·sp{ns+1}",0)
        G["cp"]=1-cp

    elif t=="blue":
        pts=space_pts(lv,si)
        G["scores"][cp]+=pts
        new_lv=lv+1 if d=="up" else lv-1
        new_si=aligned_si(lv,si,new_lv)
        G["lv"]=new_lv; G["si"]=new_si
        add_log(G,who,f"{tn} {dn} → Nv{new_lv+1}·esp{new_si+1}",pts)
        # repeat turn — no cp switch

    check_end(G,mode)

def check_end(G,mode):
    if G["lv"]==5 and G["board"][5][0] is not None:
        wi=G["board"][5][0]["p"]; G["scores"][wi]+=16
        ES=G.get("_es",True)
        who=("IA" if ES else "AI") if (mode=="ai" and wi==1) else f"J{wi+1}"
        add_log(G,who,"¡CENTRO! +16" if ES else "CENTER! +16",16)
        G["over"]=True
        G["winner"]=0 if G["scores"][0]>G["scores"][1] else (1 if G["scores"][1]>G["scores"][0] else -1)
        G["win_reason"]="center"; return
    for p in range(2):
        pc=G["pieces"][p]
        if pc["black"]<=0 and pc["white"]<=0 and pc["blue"]<=0:
            G["over"]=True; G["winner"]=1-p; G["win_reason"]="nopcs"
            ES=G.get("_es",True)
            who=("IA" if ES else "AI") if (mode=="ai" and p==1) else f"J{p+1}"
            add_log(G,who,"sin piezas" if ES else "out of beads",0); return
    if not get_moves(G):
        cp=G["cp"]; G["over"]=True; G["winner"]=1-cp; G["win_reason"]="trapped"
        ES=G.get("_es",True)
        who=("IA" if ES else "AI") if (mode=="ai" and cp==1) else f"J{cp+1}"
        add_log(G,who,"sin movimientos" if ES else "no moves",0)

def ai_move(G,mode):
    moves=get_moves(G)
    if not moves: G["over"]=True; G["winner"]=0; G["win_reason"]="trapped"; return
    lv=G["lv"]; si=G["si"]
    # Blue up on high value
    if ("blue","up") in moves and space_pts(lv,si)>=6:
        do_play(G,"blue","up",mode); return
    if ("blue","up") in moves and random.random()>0.4:
        do_play(G,"blue","up",mode); return
    # Black toward nearest celestial
    black_moves=[(t,d) for t,d in moves if t=="black"]
    if black_moves:
        best=None; best_dist=999; n=LEVELS[lv]
        for t,d in black_moves:
            ns=nxt(lv,si,d)
            for dist in range(1,n):
                c=(ns+dist)%n if d=="cw" else (ns-dist)%n
                if is_celestial(lv,c) and c not in G["blocks"][lv]:
                    if dist<best_dist: best_dist=dist; best=(t,d)
                    break
        if best: do_play(G,best[0],best[1],mode); return
        t,d=black_moves[0]; do_play(G,t,d,mode); return
    # White block
    white_moves=[(t,d) for t,d in moves if t=="white"]
    if white_moves: do_play(G,white_moves[0][0],white_moves[0][1],mode); return
    t,d=random.choice(moves); do_play(G,t,d,mode)

def render_board_svg(G):
    SIZE=440; cx=cy=SIZE//2
    radii=[int(cx*r) for r in [0.91,0.74,0.57,0.41,0.26,0.0]]
    lines=[f'<svg viewBox="0 0 {SIZE} {SIZE}" width="100%" style="max-width:{SIZE}px;display:block;margin:0 auto;" xmlns="http://www.w3.org/2000/svg">']
    lines.append(f'<circle cx="{cx}" cy="{cy}" r="{cx-2}" fill="#F5F1E4" stroke="#D3C8A0" stroke-width="1.5"/>')
    for li in range(3):
        n=LEVELS[li]; rO=radii[li]+11; rI=radii[li+1]+11
        for k in range(8):
            s=k*n//8
            a1=-math.pi/2+(s/n)*math.pi*2; a2=-math.pi/2+((s+n/8)/n)*math.pi*2
            x1i=cx+rI*math.cos(a1);y1i=cy+rI*math.sin(a1)
            x2o=cx+rO*math.cos(a1);y2o=cy+rO*math.sin(a1)
            x3o=cx+rO*math.cos(a2);y3o=cy+rO*math.sin(a2)
            x4i=cx+rI*math.cos(a2);y4i=cy+rI*math.sin(a2)
            lines.append(f'<path d="M{x1i:.1f},{y1i:.1f} L{x2o:.1f},{y2o:.1f} A{rO},{rO} 0 0,1 {x3o:.1f},{y3o:.1f} L{x4i:.1f},{y4i:.1f} A{rI},{rI} 0 0,0 {x1i:.1f},{y1i:.1f} Z" fill="rgba(120,90,40,0.07)"/>')
    for li in range(5):
        r=radii[li]+11
        lines.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="rgba(120,90,40,0.18)" stroke-width="0.8"/>')
    for i in range(4):
        a=-math.pi/2+i*math.pi/2
        x1=cx+18*math.cos(a);y1=cy+18*math.sin(a)
        x2=cx+(cx-8)*math.cos(a);y2=cy+(cx-8)*math.sin(a)
        lines.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="rgba(120,90,40,0.12)" stroke-width="0.7" stroke-dasharray="2,5"/>')
    for i in range(12):
        a=-math.pi/2+i*math.pi/6; r1=cx-6; r2=r1-(5 if i%3==0 else 3)
        x1=cx+r1*math.cos(a);y1=cy+r1*math.sin(a)
        x2=cx+r2*math.cos(a);y2=cy+r2*math.sin(a)
        lines.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="rgba(120,90,40,0.22)" stroke-width="{1.5 if i%3==0 else 0.7}"/>')

    nlv=G["lv"]; nsi=G["si"]
    for li in range(6):
        n=LEVELS[li]
        for si in range(n):
            if li==5: x,y=cx,cy; r_dot=22
            else:
                a=-math.pi/2+(si/n)*math.pi*2
                x=cx+radii[li]*math.cos(a); y=cy+radii[li]*math.sin(a); r_dot=10
            cel=is_celestial(li,si)
            is_cur=(li==nlv and si==nsi)
            is_blk=si in G["blocks"][li]
            cell=G["board"][li][si]
            if li==5: fill,stroke,sw="#DDF0CC","#3B6D11",2
            elif is_cur and not G["over"]: fill,stroke,sw="rgba(186,117,23,0.3)","#BA7517",3
            elif is_blk: fill,stroke,sw="#FCEBEB","#E24B4A",2
            elif cel: fill,stroke,sw="#C5E8FF","#185FA5",1.5
            else: fill,stroke,sw="rgba(80,60,20,0.05)","rgba(80,60,20,0.15)",0.7
            lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r_dot}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
            if is_blk and cell and cell["t"]=="white":
                lines.append(f'<text x="{x:.1f}" y="{y+3:.1f}" text-anchor="middle" font-size="{8 if li==0 else 9}" fill="#A32D2D" font-weight="bold" font-family="DM Sans,sans-serif">✕</text>')
            elif cel and not cell and not is_cur:
                pts=space_pts(li,si)
                lines.append(f'<text x="{x:.1f}" y="{y+3:.1f}" text-anchor="middle" font-size="{7 if li==0 else 8}" fill="#0C447C" font-family="DM Sans,sans-serif">{pts}</text>')
            if li==5 and not cell:
                lines.append(f'<text x="{cx}" y="{cy+5}" text-anchor="middle" font-size="12" font-weight="600" fill="#27500A" font-family="DM Sans,sans-serif">16</text>')
            if cell and cell["t"] in ("black","blue"):
                pr=r_dot-2.5
                pf="#111110" if cell["t"]=="black" else "#378ADD"
                ps="#999990" if cell["t"]=="black" else "#185FA5"
                lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{pr}" fill="{pf}" stroke="{ps}" stroke-width="1.5"/>')
                pd="#BA7517" if cell["p"]==0 else "#185FA5"
                lines.append(f'<circle cx="{x:.1f}" cy="{y+pr-2:.1f}" r="2" fill="{pd}"/>')

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
        st.markdown("Jazam es un **juego de estrategia abstracta para 2 jugadores**. Navega el tablero, bloquea a tu rival y llega al centro con más puntos.")
        st.divider()
        st.markdown("### El tablero")
        col_a,col_b=st.columns(2)
        with col_a:
            st.markdown("| Nivel | Espacios |\n|-------|----------|\n| 1 (exterior) | 32 |\n| 2 | 16 |\n| 3 | 8 |\n| 4 | 4 |\n| 5 | 2 |\n| 6 — Centro | 1 |")
        with col_b:
            st.markdown("El marcador puede moverse **en cualquier dirección** — horario o antihorario dentro del nivel.\n\nLos **espacios celestes** (azul) solo existen en los niveles 1–3, en las posiciones de reloj 3:00, 6:00, 9:00 y 12:00.\n\nLos **espacios bloqueados** (✕ rojo) no se pueden atravesar.")
        st.divider()
        st.markdown("### Piezas (por jugador)")
        c1,c2,c3=st.columns(3)
        with c1: st.markdown('<div class="rule-box" style="text-align:center;"><b>⚫ 14 Negras</b><br><small>Avanza el marcador 1 espacio en la dirección elegida</small></div>',unsafe_allow_html=True)
        with c2: st.markdown('<div class="rule-box" style="text-align:center;"><b>🟡 8 Blancas</b><br><small>Bloquea el espacio siguiente en la dirección elegida (máx. 1 por nivel)</small></div>',unsafe_allow_html=True)
        with c3: st.markdown('<div class="rule-box" style="text-align:center;"><b>🔵 2 Azules</b><br><small>Solo desde celeste → sube o baja de nivel + repite turno</small></div>',unsafe_allow_html=True)
        st.divider()
        st.markdown("### Turno")
        st.markdown("Cada turno colocas **1 pieza** y eliges **dirección** (→ horario o ← antihorario).")
        for tip,desc in [
            ("⚫ Negra → avanza","El marcador se mueve 1 espacio. Ese espacio queda ocupado."),
            ("🟡 Blanca → bloquea","El espacio siguiente en esa dirección queda bloqueado permanentemente. Solo 1 blanca por nivel."),
            ("🔵 Azul → salta de nivel","Solo desde celeste. Eliges ↑ subir (hacia centro) o ↓ bajar (hacia exterior). Ganas los puntos del celeste y repites turno."),
        ]:
            st.markdown(f'<div class="rule-box"><b>{tip}</b><br>{desc}</div>',unsafe_allow_html=True)
        st.divider()
        st.markdown("### Puntuación")
        st.markdown("| Nivel | 3:00 | 6:00 | 9:00 | 12:00 |\n|-------|------|------|------|-------|\n| 1 | 3 | 6 | 9 | **12** |\n| 2 | 2 | 4 | 6 | **8** |\n| 3 | 1 | 2 | 3 | **4** |")
        c1,c2=st.columns(2)
        with c1: st.markdown('<div class="rule-box">🏛️ <b>Bono Arquitecto (+4)</b><br>Al completar un nivel (todos sus espacios ocupados o bloqueados).</div>',unsafe_allow_html=True)
        with c2: st.markdown('<div class="rule-box">🎯 <b>Centro (+16)</b><br>Llegar al centro termina el juego. Gana quien tenga más puntos.</div>',unsafe_allow_html=True)
        st.divider()
        st.markdown("### Fin del juego")
        st.markdown("- **Alguien llega al centro** → +16 pts · fin · gana quien tenga más puntos.\n- **Sin piezas o sin movimientos** → pierde automáticamente.")
        st.markdown('<div style="text-align:center;margin-top:2rem;font-style:italic;color:#BA7517;">"Jazam no es un juego… es una meditación competitiva."</div>',unsafe_allow_html=True)
    else:
        st.markdown("### What is Jazam?")
        st.markdown('> *"A mandala of decisions where every bead can change your fate."*')
        st.markdown("Jazam is an **abstract strategy game for 2 players**. Navigate the board, block your opponent, and reach the center with more points.")
        st.divider()
        st.markdown("### The Board")
        col_a,col_b=st.columns(2)
        with col_a:
            st.markdown("| Level | Spaces |\n|-------|--------|\n| 1 (outer) | 32 |\n| 2 | 16 |\n| 3 | 8 |\n| 4 | 4 |\n| 5 | 2 |\n| 6 — Center | 1 |")
        with col_b:
            st.markdown("The marker can move in **any direction** — clockwise or counter-clockwise within a level.\n\n**Celestial spaces** (blue) exist only in levels 1–3, at 3:00, 6:00, 9:00 and 12:00.\n\n**Blocked spaces** (✕ red) cannot be passed through.")
        st.divider()
        st.markdown("### Beads (per player)")
        c1,c2,c3=st.columns(3)
        with c1: st.markdown('<div class="rule-box" style="text-align:center;"><b>⚫ 14 Black</b><br><small>Advance marker 1 space in chosen direction</small></div>',unsafe_allow_html=True)
        with c2: st.markdown('<div class="rule-box" style="text-align:center;"><b>🟡 8 White</b><br><small>Block next space in chosen direction (max 1 per level)</small></div>',unsafe_allow_html=True)
        with c3: st.markdown('<div class="rule-box" style="text-align:center;"><b>🔵 2 Blue</b><br><small>Celestial only → go up or down a level + repeat turn</small></div>',unsafe_allow_html=True)
        st.divider()
        st.markdown("### Turn")
        st.markdown("Each turn place **1 bead** and choose **direction** (→ clockwise or ← counter-clockwise).")
        for tip,desc in [
            ("⚫ Black → advance","The marker moves 1 space. That space becomes occupied."),
            ("🟡 White → block","The next space in that direction is permanently blocked. Max 1 white per level."),
            ("🔵 Blue → jump levels","Only from a celestial space. Choose ↑ up (center) or ↓ down (outer). Score celestial points and take another turn."),
        ]:
            st.markdown(f'<div class="rule-box"><b>{tip}</b><br>{desc}</div>',unsafe_allow_html=True)
        st.divider()
        st.markdown("### Scoring")
        st.markdown("| Level | 3:00 | 6:00 | 9:00 | 12:00 |\n|-------|------|------|------|-------|\n| 1 | 3 | 6 | 9 | **12** |\n| 2 | 2 | 4 | 6 | **8** |\n| 3 | 1 | 2 | 3 | **4** |")
        c1,c2=st.columns(2)
        with c1: st.markdown('<div class="rule-box">🏛️ <b>Architect Bonus (+4)</b><br>When a level is fully occupied or blocked.</div>',unsafe_allow_html=True)
        with c2: st.markdown('<div class="rule-box">🎯 <b>Center (+16)</b><br>Reaching the center ends the game. Most points wins.</div>',unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;margin-top:2rem;font-style:italic;color:#BA7517;">"Jazam is not a game… it\'s competitive meditation."</div>',unsafe_allow_html=True)

with tab_game:
    lbl_2p="👥 2 Jugadores" if ES else "👥 2 Players"
    lbl_ai="🤖 vs IA" if ES else "🤖 vs AI"
    lbl_reset="↺ Nueva partida" if ES else "↺ New game"
    c1,c2,c3=st.columns(3)
    with c1:
        if st.button(lbl_2p,use_container_width=True,type="primary" if mode=="2p" else "secondary"):
            st.session_state.mode="2p"; st.session_state.game=init_game(); st.rerun()
    with c2:
        if st.button(lbl_ai,use_container_width=True,type="primary" if mode=="ai" else "secondary"):
            st.session_state.mode="ai"; st.session_state.game=init_game(); st.rerun()
    with c3:
        if st.button(lbl_reset,use_container_width=True):
            st.session_state.game=init_game(); st.rerun()

    st.markdown(f'<div style="text-align:right;margin-top:-4px;"><span style="font-size:11px;background:#EAF3DE;color:#27500A;border:0.5px solid #97C459;border-radius:10px;padding:2px 9px;">6 {"niveles" if ES else "levels"} · 14⚫ · 8🟡 · 2🔵</span></div>',unsafe_allow_html=True)
    st.divider()

    p1n="Jugador 1" if ES else "Player 1"
    p2n=("IA 🤖" if ES else "AI 🤖") if mode=="ai" else ("Jugador 2" if ES else "Player 2")
    p1c="score-box active" if (G["cp"]==0 and not G["over"]) else "score-box"
    p2c=("score-box active-ai" if mode=="ai" else "score-box active") if (G["cp"]==1 and not G["over"]) else "score-box"

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
    </div>""",unsafe_allow_html=True)

    if not G["over"]:
        cp=G["cp"]; lv=G["lv"]; si=G["si"]
        cel=is_celestial(lv,si); moves=get_moves(G)
        name=("IA" if ES else "AI") if (mode=="ai" and cp==1) else f"{'Jugador' if ES else 'Player'} {cp+1}"
        cw_blk=nxt(lv,si,"cw") in G["blocks"][lv]
        ccw_blk=nxt(lv,si,"ccw") in G["blocks"][lv]
        if not moves:
            bar_cls="status-bar warning"
            txt=f"⚠️ <b>{name}</b> — {'sin movimientos' if ES else 'no moves available'}"
        elif cel:
            pts=space_pts(lv,si); cl=["12:00","3:00","6:00","9:00"][si//(LEVELS[lv]//4)]
            bar_cls="status-bar celestial"
            txt=f"★ <b>{name}</b> — {'Celeste' if ES else 'Celestial'} {cl} · {pts}pts · {'Nv' if ES else 'Lv'}{lv+1}"
        elif cw_blk or ccw_blk:
            bar_cls="status-bar blocked"
            info=("→ bloqueada " if cw_blk else "")+("← bloqueada" if ccw_blk else "") if ES else ("→ blocked " if cw_blk else "")+("← blocked" if ccw_blk else "")
            txt=f"⚡ <b>{name}</b> — {info} · {'Nv' if ES else 'Lv'}{lv+1} {'esp' if ES else 'sp'}{si+1}"
        else:
            bar_cls="status-bar"
            txt=f"<b>{name}</b> — {'Nivel' if ES else 'Level'} {lv+1} · {'espacio' if ES else 'space'} {si+1}"
        st.markdown(f'<div class="{bar_cls}">{txt}</div>',unsafe_allow_html=True)

    st.markdown(f'<div style="width:100%;max-width:440px;margin:8px auto;">{render_board_svg(G)}</div>',unsafe_allow_html=True)

    if not G["over"]:
        cp=G["cp"]; is_human=not(mode=="ai" and cp==1)
        moves=get_moves(G); pc=G["pieces"][cp]
        if is_human and moves:
            lv=G["lv"]; si=G["si"]
            can=lambda t,d:(t,d) in moves
            st.markdown(f"**{'Elige tu jugada:' if ES else 'Choose your move:'}**")
            c1,c2=st.columns(2)
            with c1:
                if st.button(f"⚫ {'Negra' if ES else 'Black'} → ({pc['black']})",disabled=not can("black","cw"),use_container_width=True,key="bk_cw"):
                    do_play(G,"black","cw",mode); st.rerun()
            with c2:
                if st.button(f"← ⚫ {'Negra' if ES else 'Black'} ({pc['black']})",disabled=not can("black","ccw"),use_container_width=True,key="bk_ccw"):
                    do_play(G,"black","ccw",mode); st.rerun()
            c1,c2=st.columns(2)
            with c1:
                if st.button(f"🟡 {'Bloquear' if ES else 'Block'} → ({pc['white']})",disabled=not can("white","cw"),use_container_width=True,key="bw_cw"):
                    do_play(G,"white","cw",mode); st.rerun()
            with c2:
                if st.button(f"← 🟡 {'Bloquear' if ES else 'Block'} ({pc['white']})",disabled=not can("white","ccw"),use_container_width=True,key="bw_ccw"):
                    do_play(G,"white","ccw",mode); st.rerun()
            if can("blue","up") or can("blue","down"):
                c1,c2=st.columns(2)
                with c1:
                    if st.button(f"🔵 ↑ {'Subir nivel' if ES else 'Go up'} ({pc['blue']})",disabled=not can("blue","up"),use_container_width=True,key="bb_up"):
                        do_play(G,"blue","up",mode); st.rerun()
                with c2:
                    if st.button(f"🔵 ↓ {'Bajar nivel' if ES else 'Go down'} ({pc['blue']})",disabled=not can("blue","down"),use_container_width=True,key="bb_down"):
                        do_play(G,"blue","down",mode); st.rerun()
        elif is_human and not moves:
            st.warning("Sin movimientos posibles." if ES else "No moves available.")
        else:
            st.info("🤖 La IA está pensando..." if ES else "🤖 AI is thinking...",icon="⏳")
            time.sleep(0.7); ai_move(G,mode); st.rerun()

    if G["over"]:
        p2l=("IA" if ES else "AI") if mode=="ai" else ("Jugador 2" if ES else "Player 2")
        w=G.get("winner"); r=G.get("win_reason")
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
