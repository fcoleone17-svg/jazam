"""
JAZAM v5 — Mecánica correcta de la blanca
Negra  → llena 1 espacio · siguiente jugador coloca 1
Blanca → llena 1 espacio · activa "peaje" en ese extremo:
         el próximo que avance por ese extremo coloca 2 piezas,
         la primera sin propiedades (solo rellena), la segunda normal
Azul   → solo en celeste (niveles 1-3) · sube de nivel · repite turno
         (en turno repetido debe colocar primero en espacio alineado)
"""

import streamlit as st
import streamlit.components.v1 as components
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
.score-box.active{border:2px solid #FF6B00;background:#FFF0E6;}
.score-box.active-ai{border:2px solid #00C8FF;background:#E6FAFF;}
.score-name{font-size:0.75rem;color:#888;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:3px;}
.score-pts{font-size:1.8rem;font-weight:600;color:#1C1A10;line-height:1;}
.score-pts span{font-size:0.75rem;font-weight:400;color:#888;margin-left:3px;}
.status-bar{background:#F5F1E4;border-radius:8px;padding:10px 16px;text-align:center;font-size:0.88rem;color:#555;border:1px solid #D3C8A0;margin:8px 0;}
.status-bar b{color:#1C1A10;}
.status-bar.celestial{background:#C5E8FF;border-color:#185FA5;color:#0C447C;}
.status-bar.warning{background:#FCEBEB;border-color:#E24B4A;color:#A32D2D;}
.status-bar.toll{background:#FFF3CD;border-color:#BA7517;color:#633806;}
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

LEVELS = [32, 16, 8, 4, 2, 1]
INIT_PIECES = {"black": 20, "white": 6, "blue": 2}
CELESTIALS = {
    0: {0:9, 8:9, 16:9, 24:9},   # Nv1: 12:00, 3:00, 6:00, 9:00 → 9pts
    1: {0:6, 4:6, 8:6, 12:6},    # Nv2: 12:00, 3:00, 6:00, 9:00 → 6pts
    2: {0:3, 2:3, 4:3, 6:3},     # Nv3: 12:00, 3:00, 6:00, 9:00 → 3pts
}

def is_celestial(li, si): return si in CELESTIALS.get(li, {})
def space_pts(li, si):
    if li == 5: return 12
    return CELESTIALS.get(li, {}).get(si, 0)
def aligned_si(li, si, new_li):
    return round(si * LEVELS[new_li] / LEVELS[li]) % LEVELS[new_li]

def init_game():
    n0 = LEVELS[0]
    return {
        "cp": 0, "scores": [0, 0],
        "pieces": [dict(INIT_PIECES), dict(INIT_PIECES)],
        "board": [[None]*n for n in LEVELS],
        "lv": 0,
        "ptr_cw": 1,
        "ptr_ccw": n0 - 1,
        "toll_cw": False,     # peaje activo en extremo ↻
        "toll_ccw": False,    # peaje activo en extremo ↺
        "toll_lv": None,      # nivel donde está activo el peaje
        "toll_placing": None,
        "started": False,
        "forced_space": None,
        "last_was_blue": False,
        "over": False, "log": [], "turn_count": 0,
        "winner": None, "win_reason": None, "_es": True,
    }

def find_free_cw(G):
    lv=G["lv"]; n=LEVELS[lv]; board=G["board"][lv]
    si=G["ptr_cw"]%n
    for _ in range(n):
        if board[si] is None: return si
        si=(si+1)%n
    return None

def find_free_ccw(G):
    lv=G["lv"]; n=LEVELS[lv]; board=G["board"][lv]
    si=G["ptr_ccw"]%n
    for _ in range(n):
        if board[si] is None: return si
        si=(si-1)%n
    return None

def any_free(G):
    """Returns True if there's any free space in current level"""
    lv=G["lv"]
    return any(x is None for x in G["board"][lv])

def toll_active_cw(G):
    """Peaje ↻ activo solo si estamos en el mismo nivel donde se activó"""
    return G["toll_cw"] and G.get("toll_lv") == G["lv"]

def toll_active_ccw(G):
    """Peaje ↺ activo solo si estamos en el mismo nivel donde se activó"""
    return G["toll_ccw"] and G.get("toll_lv") == G["lv"]

def set_toll(G, direction):
    if direction=="cw": G["toll_cw"]=True
    else: G["toll_ccw"]=True
    G["toll_lv"]=G["lv"]

def clear_tolls(G):
    G["toll_cw"]=False; G["toll_ccw"]=False; G["toll_lv"]=None

def valid_moves(G):
    cp=G["cp"]; pc=G["pieces"][cp]; lv=G["lv"]

    # First move
    if not G["started"]:
        moves=[]
        if pc["black"]>0: moves.append(("black","start"))
        if pc["white"]>0: moves.append(("white","start"))
        return moves

    # Forced space after blue jump
    if G["forced_space"] is not None:
        moves=[]
        if pc["black"]>0: moves.append(("black","forced"))
        if pc["white"]>0: moves.append(("white","forced"))
        return moves

    # Paying toll: must place 2nd piece (this one has properties)
    if G["toll_placing"] is not None:
        d=G["toll_placing"]
        moves=[]
        tgt=find_free_cw(G) if d=="cw" else find_free_ccw(G)
        if tgt is None: return []
        cel=is_celestial(lv,tgt)
        if pc["black"]>0: moves.append(("black",d))
        if pc["white"]>0: moves.append(("white",d))
        if pc["blue"]>0 and lv<=2 and not G.get("last_was_blue",False): moves.append(("blue",d))
        return moves

    t_cw=find_free_cw(G); t_ccw=find_free_ccw(G)

    # Si los punteros no encuentran espacio pero hay espacios libres,
    # resetearlos al primer espacio libre disponible
    if t_cw is None or t_ccw is None:
        lv2=G["lv"]; n2=LEVELS[lv2]
        free=[i for i,x in enumerate(G["board"][lv2]) if x is None]
        if free:
            if t_cw is None: G["ptr_cw"]=free[0]; t_cw=free[0]
            if t_ccw is None: G["ptr_ccw"]=free[-1]; t_ccw=free[-1]

    moves=[]
    for d,tgt in [("cw",t_cw),("ccw",t_ccw)]:
        if tgt is None: continue
        if d=="ccw" and tgt==t_cw: continue
        toll_on_this=(d=="cw" and toll_active_cw(G)) or (d=="ccw" and toll_active_ccw(G))
        cel=is_celestial(lv,tgt) and not toll_on_this
        if pc["black"]>0: moves.append(("black",d))
        if pc["white"]>0: moves.append(("white",d))
        if pc["blue"]>0 and lv<=2 and not G.get("last_was_blue",False) and not toll_on_this: moves.append(("blue",d))
    seen=set(); unique=[]
    for m in moves:
        if m not in seen: seen.add(m); unique.append(m)
    return unique

def add_log(G, who, msg, pts=0):
    G["turn_count"]+=1
    G["log"].append({"turn":G["turn_count"],"who":who,"msg":msg,"pts":pts})

def do_play(G, piece_type, direction, mode):
    if G["over"]: return
    cp=G["cp"]; pc=G["pieces"][cp]; lv=G["lv"]; n=LEVELS[lv]
    ES=G.get("_es",True)
    who=("IA" if ES else "AI") if (mode=="ai" and cp==1) else f"J{cp+1}"
    tn={"black":"negra" if ES else "black","white":"blanca" if ES else "white","blue":"azul" if ES else "blue"}[piece_type]
    dn={"cw":"↻","ccw":"↺","start":"12:00","forced":"↑"}[direction]

    # ── BLUE: solo válida si NO hay peaje activo en esa dirección ──
    is_toll_first = (G["toll_placing"] is None and direction in ("cw","ccw") and
                     ((direction=="cw" and toll_active_cw(G)) or
                      (direction=="ccw" and toll_active_ccw(G))))

    if piece_type=="blue" and G["toll_placing"] is None and G["forced_space"] is None and not is_toll_first:
        tgt=find_free_cw(G) if direction=="cw" else find_free_ccw(G)
        if tgt is None: return
        pc["blue"]-=1
        cel=is_celestial(lv,tgt)
        pts=space_pts(lv,tgt) if cel else 0
        G["scores"][cp]+=pts
        G["board"][lv][tgt]={"p":cp,"t":"blue","neu":False}
        if direction=="cw": G["ptr_cw"]=(tgt+1)%n
        else: G["ptr_ccw"]=(tgt-1)%n
        if cel and lv<5:
            # Celeste: sube de nivel y repite turno
            add_log(G,who,f"azul {dn} Nv{lv+1}·esp{tgt+1} +{pts}pts → Nv{lv+2}",pts)
            new_lv=lv+1
            if new_lv>5: check_end(G,mode); return
            new_n=LEVELS[new_lv]
            aligned=aligned_si(lv,tgt,new_lv)
            G["lv"]=new_lv
            G["ptr_cw"]=aligned; G["ptr_ccw"]=aligned
            clear_tolls(G)
            G["forced_space"]=aligned
            G["started"]=True
            G["last_was_blue"]=True
        else:
            # No celeste: ocupa el espacio como negra, pasa turno
            add_log(G,who,f"azul {dn} Nv{lv+1}·esp{tgt+1} (sin efecto)",0)
            G["last_was_blue"]=False
            # Check level complete
            if all(x is not None for x in G["board"][lv]):
                if lv<=2:
                    G["scores"][cp]+=4
                    add_log(G,who,f"Nv{lv+1} completo · +4" if ES else f"Lv{lv+1} complete · +4",4)
                if lv<5:
                    G["lv"]=lv+1; new_n=LEVELS[lv+1]
                    G["ptr_cw"]=0; G["ptr_ccw"]=new_n-1; clear_tolls(G)
            G["cp"]=1-cp
        check_end(G,mode); return

    # ── Determine target space ──
    if direction=="start":       target=0
    elif direction=="forced":    target=G["forced_space"]
    elif direction=="cw":        target=find_free_cw(G)
    else:                        target=find_free_ccw(G)
    if target is None: return

    # ── Is this piece neutralized? ──
    # Neutralized if: paying toll first piece OR forced space (after blue jump)
    paying_toll_first = (G["toll_placing"] is None and direction in ("cw","ccw") and
                         ((direction=="cw" and toll_active_cw(G)) or
                          (direction=="ccw" and toll_active_ccw(G))))
    is_forced_space = (G["forced_space"] is not None and direction=="forced")
    neutralized = paying_toll_first  # forced space piece has full properties

    effective = "black" if neutralized else piece_type
    pc[piece_type]-=1
    G["board"][lv][target]={"p":cp,"t":piece_type,"neu":neutralized}
    G["last_was_blue"]=False  # reset — siguiente turno puede usar azul si aplica
    note=" [peaje]" if neutralized else (" [forzado]" if is_forced_space else "")
    add_log(G,who,f"{tn} {dn} Nv{lv+1}·esp{target+1}{note}",0)

    # Update pointers
    if direction=="start":
        G["started"]=True; G["ptr_cw"]=1; G["ptr_ccw"]=(n-1)%n
        clear_tolls(G)
    elif direction=="forced":
        G["forced_space"]=None
        G["ptr_cw"]=(target+1)%n; G["ptr_ccw"]=(target-1)%n
        clear_tolls(G)
    elif direction=="cw":
        G["ptr_cw"]=(target+1)%n
    else:
        G["ptr_ccw"]=(target-1)%n

    # ── Handle toll logic ──
    if paying_toll_first:
        # Clear the toll on this direction since we're paying it
        if direction=="cw": G["toll_cw"]=False
        else: G["toll_ccw"]=False
        G["toll_placing"]=direction
        # Check level complete even on first toll piece
        if all(x is not None for x in G["board"][lv]):
            if lv<=2:
                G["scores"][cp]+=4
                add_log(G,who,f"Nv{lv+1} completo · +4" if ES else f"Lv{lv+1} complete · +4",4)
            if lv<5:
                G["lv"]=lv+1; new_n=LEVELS[lv+1]
                G["ptr_cw"]=0; G["ptr_ccw"]=new_n-1
                clear_tolls(G)
                G["toll_placing"]=None  # cancel toll — level done
                G["cp"]=1-cp
                check_end(G,mode); return
        check_end(G,mode); return

    if G["toll_placing"] is not None:
        # Just placed the 2nd toll piece (with properties) — now apply white effect if needed
        G["toll_placing"]=None
        if effective=="white":
            d=direction
            set_toll(G, d)
        elif effective=="blue":
            pts2=space_pts(lv,target)
            G["scores"][cp]+=pts2
            new_lv=lv+1
            if new_lv<=5:
                new_n=LEVELS[new_lv]; aligned=aligned_si(lv,target,new_lv)
                G["lv"]=new_lv; G["ptr_cw"]=aligned; G["ptr_ccw"]=aligned
                clear_tolls(G)
                G["forced_space"]=aligned; G["started"]=True
            check_end(G,mode); return
        # Check level complete after 2nd toll piece
        if all(x is not None for x in G["board"][lv]):
            if lv<=2:
                G["scores"][cp]+=4
                add_log(G,who,f"Nv{lv+1} completo · +4" if ES else f"Lv{lv+1} complete · +4",4)
            if lv<5:
                G["lv"]=lv+1; new_n=LEVELS[lv+1]
                G["ptr_cw"]=0; G["ptr_ccw"]=new_n-1
                clear_tolls(G)
        G["cp"]=1-cp
        check_end(G,mode); return

    # ── Normal piece effects ──
    if effective=="white":
        if direction in ("cw","ccw"):
            set_toll(G, direction)
        elif direction=="forced":
            # Blanca en espacio forzado activa peaje en ambas direcciones
            G["toll_cw"]=True; G["toll_ccw"]=True
            G["toll_lv"]=G["lv"]

    # Architect bonus (levels 1-3 only) + level advance
    if all(x is not None for x in G["board"][lv]):
        if lv<=2:
            G["scores"][cp]+=4
            add_log(G,who,f"Nv{lv+1} completo · +4" if ES else f"Lv{lv+1} complete · +4",4)
        if lv<5:
            G["lv"]=lv+1; new_n=LEVELS[lv+1]
            G["ptr_cw"]=0; G["ptr_ccw"]=new_n-1
            clear_tolls(G)

    G["cp"]=1-cp
    check_end(G,mode)

def check_end(G, mode):
    if G["lv"]==5 and any(x is not None for x in G["board"][5]):
        who_idx=next(x["p"] for x in G["board"][5] if x is not None)
        G["scores"][who_idx]+=12
        ES=G.get("_es",True)
        who=("IA" if ES else "AI") if (mode=="ai" and who_idx==1) else f"J{who_idx+1}"
        add_log(G,who,"¡CENTRO! +12" if ES else "CENTER! +12",12)
        G["over"]=True
        G["winner"]=0 if G["scores"][0]>G["scores"][1] else (1 if G["scores"][1]>G["scores"][0] else -1)
        G["win_reason"]="center"; return
    # Sin piezas en su turno = pierde automáticamente
    cp=G["cp"]; pc=G["pieces"][cp]
    if pc["black"]<=0 and pc["white"]<=0 and pc["blue"]<=0:
        G["over"]=True
        G["winner"]=1-cp  # pierde quien se quedó sin piezas
        G["win_reason"]="nopcs"
        ES=G.get("_es",True)
        who=("IA" if ES else "AI") if (mode=="ai" and cp==1) else f"J{cp+1}"
        add_log(G,who,"sin piezas — pierde" if ES else "out of beads — loses",0); return
    if not valid_moves(G):
        G["over"]=True
        G["winner"]=1-cp
        G["win_reason"]="nopcs"

def ai_move(G, mode):
    moves=valid_moves(G)
    if not moves: return
    lv=G["lv"]; pc=G["pieces"][1]
    my_score=G["scores"][1]; rival_score=G["scores"][0]
    losing=(my_score < rival_score); gap=abs(my_score-rival_score)

    # ── Forced space after blue jump ──
    if G["forced_space"] is not None:
        # Place white if ahead (pressure), black if behind (speed)
        if pc["white"]>0 and not losing and random.random()>0.4:
            do_play(G,"white","forced",mode); return
        t="black" if pc["black"]>0 else "white"
        do_play(G,t,"forced",mode); return

    # ── Second toll piece ──
    if G["toll_placing"] is not None:
        d=G["toll_placing"]
        tgt=find_free_cw(G) if d=="cw" else find_free_ccw(G)
        cel=is_celestial(lv,tgt) if tgt is not None else False
        if pc["blue"]>0 and cel and lv<=2 and space_pts(lv,tgt)>=4:
            do_play(G,"blue",d,mode); return
        if pc["white"]>0 and not losing and random.random()>0.4:
            do_play(G,"white",d,mode); return
        t="black" if pc["black"]>0 else "white"
        do_play(G,t,d,mode); return

    t_cw=find_free_cw(G); t_ccw=find_free_ccw(G)
    n=LEVELS[lv]

    def score_move(t, d):
        tgt=t_cw if d=="cw" else t_ccw
        if tgt is None: return -999
        val=0

        if t=="blue":
            val+=space_pts(lv,tgt)*2  # azul vale doble (puntos + sube nivel)
            return val

        if t=="white":
            # Buscar si la blanca queda justo antes de un celeste
            next1=(tgt+1)%n if d=="cw" else (tgt-1)%n
            next2=(next1+1)%n if d=="cw" else (next1-1)%n
            if is_celestial(lv,next1) and G["board"][lv][next1] is None: val+=8
            elif is_celestial(lv,next2) and G["board"][lv][next2] is None: val+=4
            if losing and gap>6: val-=5  # si voy perdiendo, no desperdiciar blancas
            return val

        # Negra: evaluar cercanía al próximo celeste
        for dist in range(1, min(10, n)):
            cand=(tgt+dist)%n if d=="cw" else (tgt-dist)%n
            if G["board"][lv][cand] is None and is_celestial(lv,cand):
                val+=max(0, space_pts(lv,cand)-dist+2)
                break
        # Bonus si el nivel está casi completo
        free_in_lv=sum(1 for x in G["board"][lv] if x is None)
        if free_in_lv<=3 and lv<5: val+=4
        return val

    # Priorizar azul en celeste valioso
    for d in ["cw","ccw"]:
        if ("blue",d) in moves:
            tgt=t_cw if d=="cw" else t_ccw
            if tgt is not None and space_pts(lv,tgt)>=4:
                do_play(G,"blue",d,mode); return

    # Evaluar y elegir mejor movimiento (con algo de aleatoriedad)
    scored=[(score_move(t,d),t,d) for t,d in moves if t!="blue"]
    if not scored:
        t,d=random.choice(moves); do_play(G,t,d,mode); return

    scored.sort(key=lambda x:-x[0])
    # Elegir entre top 2 con probabilidad 75/25
    top=scored[:min(2,len(scored))]
    weights=[3,1][:len(top)]
    _,t,d=random.choices(top,weights=weights,k=1)[0]
    do_play(G,t,d,mode)


def render_board_svg(G):
    SIZE=440; cx=cy=SIZE//2
    radii=[int(cx*r) for r in [0.91,0.74,0.57,0.41,0.26,0.0]]
    # Colores de jugadores: J1=naranja, J2=cian
    P_COLOR=["#FF6B00","#00C8FF"]
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

    nlv=G["lv"]; forced=G.get("forced_space")
    toll_placing=G.get("toll_placing")
    t_cw=find_free_cw(G) if G["started"] and forced is None and toll_placing is None else None
    t_ccw=find_free_ccw(G) if G["started"] and forced is None and toll_placing is None else None

    # Highlight para 2ª pieza del peaje
    t_toll=None
    if toll_placing is not None and not G["over"]:
        t_toll=find_free_cw(G) if toll_placing=="cw" else find_free_ccw(G)

    for li in range(6):
        n=LEVELS[li]
        if li==5: x,y=cx,cy; r_dot=22
        else:
            r_dot=10

        for si in range(n):
            if li==5: x,y=cx,cy
            else:
                a=-math.pi/2+(si/n)*math.pi*2; x=cx+radii[li]*math.cos(a); y=cy+radii[li]*math.sin(a)

            cel=is_celestial(li,si); cell=G["board"][li][si]
            is_forced=(li==nlv and forced is not None and si==forced and cell is None and not G["over"])
            is_toll=(li==nlv and t_toll is not None and si==t_toll and cell is None)
            is_cw=(li==nlv and t_cw is not None and si==t_cw and cell is None and t_cw!=t_ccw)
            is_ccw=(li==nlv and t_ccw is not None and si==t_ccw and cell is None and t_cw!=t_ccw)
            is_first=(li==nlv and si==0 and not G["started"] and not G["over"])

            if li==5: fill,stroke,sw="#DDF0CC","#3B6D11",2
            elif is_forced: fill,stroke,sw="rgba(59,109,17,0.3)","#3B6D11",3
            elif is_first: fill,stroke,sw="rgba(59,109,17,0.2)","#3B6D11",2.5
            elif is_toll: fill,stroke,sw="rgba(255,107,0,0.25)","#FF6B00",2.5
            elif is_cw:  fill,stroke,sw="rgba(34,139,34,0.25)","#22A022",2.5   # verde para ↻
            elif is_ccw: fill,stroke,sw="rgba(255,107,0,0.25)","#FF6B00",2.5   # naranja para ↺
            elif cel: fill,stroke,sw="#C5E8FF","#185FA5",1.5
            else: fill,stroke,sw="rgba(80,60,20,0.05)","rgba(80,60,20,0.15)",0.7
            lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r_dot}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

            if cel and not cell and not is_cw and not is_ccw and not is_forced and not is_first:
                pts=space_pts(li,si)
                lines.append(f'<text x="{x:.1f}" y="{y+3:.1f}" text-anchor="middle" font-size="{7 if li==0 else 8}" fill="#0C447C" font-family="DM Sans,sans-serif">{pts}</text>')
            if li==5 and not any(x2 is not None for x2 in G["board"][5]):
                lines.append(f'<text x="{cx}" y="{cy+5}" text-anchor="middle" font-size="12" font-weight="600" fill="#27500A" font-family="DM Sans,sans-serif">12</text>')

            if cell:
                t2=cell["t"]; neu=cell.get("neu",False); pr=r_dot-2
                # Colores de pelota: negras=blanco hueso (visible en oscuro), blanca=dorado, azul=azul
                if neu or t2=="black": pf,ps="#111110","#999990"
                elif t2=="white": pf,ps="#E8D44D","#B89A10"
                else: pf,ps="#378ADD","#185FA5"
                lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{pr}" fill="{pf}" stroke="{ps}" stroke-width="2"/>')
                pd=P_COLOR[cell["p"]]
                lines.append(f'<circle cx="{x:.1f}" cy="{y+pr-2:.1f}" r="2.0" fill="{pd}"/>')

    lines.append(f'<circle cx="{cx}" cy="{cy}" r="{cx-3}" fill="none" stroke="rgba(120,90,40,0.25)" stroke-width="1.5"/>')
    for i,lbl in enumerate(["12","3","6","9"]):
        a=-math.pi/2+i*math.pi/2
        lines.append(f'<text x="{cx+(cx+8)*math.cos(a):.1f}" y="{cy+(cx+8)*math.sin(a)+4:.1f}" text-anchor="middle" font-size="10" fill="rgba(90,65,30,0.5)" font-family="DM Sans,sans-serif">{lbl}</text>')
    lines.append("</svg>")
    return "\n".join(lines)

def render_clickable_board(G, clickable_spaces):
    SIZE=440; cx=cy=SIZE//2
    radii=[int(cx*r) for r in [0.91,0.74,0.57,0.41,0.26,0.0]]
    click_svg_extra=""
    for li,si in clickable_spaces:
        if li==5: x,y=cx,cy; r=26
        else:
            a=-math.pi/2+(si/LEVELS[li])*math.pi*2
            x=cx+radii[li]*math.cos(a); y=cy+radii[li]*math.sin(a); r=16
        click_svg_extra+=f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="rgba(255,107,0,0.0)" stroke="rgba(255,107,0,0.7)" stroke-width="3.5" stroke-dasharray="4,3" style="cursor:pointer;" onclick="sendClick({li},{si})"/>'
    svg=render_board_svg(G)
    svg_with_clicks=svg.replace("</svg>", click_svg_extra+"</svg>")
    html=f"""<!DOCTYPE html>
<html><body style="margin:0;padding:0;background:transparent;">
<div style="width:100%;max-width:440px;margin:0 auto;">
{svg_with_clicks}
</div>
<script>
function sendClick(li, si) {{
    const url = new URL(window.parent.location.href);
    url.searchParams.set('jazam_click', li + '_' + si);
    window.parent.location.href = url.toString();
}}
</script>
</body></html>"""
    components.html(html, height=450)


def render_dots(n,max_n,pt):
    return '<div class="dot-row">'+"".join(f'<span class="dot dot-{pt}-{"on" if i<n else "off"}"></span>' for i in range(max_n))+'</div>'

def pieces_html(pc):
    rows=""
    for t,mx in [("black",20),("white",6),("blue",2)]:
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
        st.markdown("Jazam es un **juego de estrategia abstracta para 2 jugadores**. Cada turno eliges dirección, usa tus piezas con sabiduría y llega al centro con más puntos.")
        st.divider()
        st.markdown("### El tablero")
        col_a,col_b=st.columns(2)
        with col_a:
            st.markdown("| Nivel | Espacios |\n|-------|----------|\n| 1 (exterior) | 32 |\n| 2 | 16 |\n| 3 | 8 |\n| 4 | 4 |\n| 5 | 2 |\n| 6 — Centro | 1 |")
        with col_b:
            st.markdown("El juego empieza en **12:00**. Dos punteros independientes avanzan ↻ y ↺ — en cada turno eliges libremente cuál dirección.\n\n**Celestes** (azul): dan puntos al usar azul.")
        st.divider()
        st.markdown("### Piezas (por jugador)")
        c1,c2,c3=st.columns(3)
        with c1: st.markdown('<div class="rule-box" style="text-align:center;"><b>⚫ 14 Negras</b><br><small>Llena 1 espacio · siguiente coloca 1</small></div>',unsafe_allow_html=True)
        with c2: st.markdown('<div class="rule-box" style="text-align:center;"><b>🟡 8 Blancas</b><br><small>Llena 1 espacio · activa peaje en ese extremo: próximo que avance por ahí coloca 2 (primera sin propiedades)</small></div>',unsafe_allow_html=True)
        with c3: st.markdown('<div class="rule-box" style="text-align:center;"><b>🔵 2 Azules</b><br><small>Se puede poner en cualquier espacio · solo en celeste gana puntos y sube de nivel · repite turno</small></div>',unsafe_allow_html=True)
        st.divider()
        st.markdown("### El peaje de la Blanca")
        st.markdown('<div class="rule-box">🟡 Después de una <b>blanca</b>, el próximo que avance por ese lado pone 2 pelotas. Ojo: la primera no cuenta — solo ocupa el espacio. La segunda es la que realmente juega.<br><br><b>Ejemplo:</b> la blanca queda justo antes de un espacio celeste. El siguiente jugador pone su primera pelota ahí — pero no tiene efecto (aunque sea azul, no sube de nivel). La segunda pelota es la que juega normalmente.</div>',unsafe_allow_html=True)
        st.divider()
        st.markdown("### Puntuación")
        st.markdown("| Nivel | Celestes | Puntos |\n|-------|----------|--------|\n| 1 | 12:00, 3:00, 6:00, 9:00 | 9 pts |\n| 2 | 12:00, 3:00, 6:00, 9:00 | 6 pts |\n| 3 | 12:00, 3:00, 6:00, 9:00 | 3 pts |")
        c1,c2=st.columns(2)
        with c1: st.markdown('<div class="rule-box">🏛️ <b>Bono Arquitecto (+4)</b><br>Solo en niveles 1, 2 y 3 · al completar todos los espacios.</div>',unsafe_allow_html=True)
        with c2: st.markdown('<div class="rule-box">🎯 <b>Centro (+12)</b><br>Llegar al centro termina el juego. Gana quien tenga más puntos.</div>',unsafe_allow_html=True)
        st.divider()
        st.markdown("### Fin del juego")
        st.markdown('<div class="rule-box">El juego termina cuando alguien llega al centro (+12 pts) o cuando un jugador <b>no tiene pelotas para colocar en su turno</b> — ese jugador pierde automáticamente.</div>',unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;margin-top:2rem;font-style:italic;color:#BA7517;">"Jazam no es un juego… es una meditación competitiva."</div>',unsafe_allow_html=True)
    else:
        st.markdown("### What is Jazam?")
        st.markdown('> *"A mandala of decisions where every bead can change your fate."*')
        st.markdown("Jazam is an **abstract strategy game for 2 players**. Each turn choose a direction, use your beads wisely and reach the center with more points.")
        st.divider()
        st.markdown("### The Board")
        col_a,col_b=st.columns(2)
        with col_a:
            st.markdown("| Level | Spaces |\n|-------|--------|\n| 1 (outer) | 32 |\n| 2 | 16 |\n| 3 | 8 |\n| 4 | 4 |\n| 5 | 2 |\n| 6 — Center | 1 |")
        with col_b:
            st.markdown("The game starts at **12:00**. Two independent pointers advance ↻ and ↺ — each turn you freely choose which direction.\n\n**Celestial spaces** (blue): score points when using a blue bead.")
        st.divider()
        st.markdown("### Beads (per player)")
        c1,c2,c3=st.columns(3)
        with c1: st.markdown('<div class="rule-box" style="text-align:center;"><b>⚫ 14 Black</b><br><small>Fills 1 space · next player places 1</small></div>',unsafe_allow_html=True)
        with c2: st.markdown('<div class="rule-box" style="text-align:center;"><b>🟡 8 White</b><br><small>Fills 1 space · next player advancing that way places 2 — only the second one counts</small></div>',unsafe_allow_html=True)
        with c3: st.markdown('<div class="rule-box" style="text-align:center;"><b>🔵 2 Blue</b><br><small>Can go on any space · only on celestial scores points and goes up a level · repeat turn</small></div>',unsafe_allow_html=True)
        st.divider()
        st.markdown("### The White")
        st.markdown('<div class="rule-box">🟡 After a <b>white</b> bead, the next player advancing that way must place 2 beads. Note: the first one doesn\'t count — it just fills the space. The second one is the one that really plays.<br><br><b>Example:</b> the white lands just before a celestial space. The next player places their first bead there — but it has no effect (even if it\'s a blue, it won\'t go up a level). The second bead is the one that plays normally.</div>',unsafe_allow_html=True)
        st.divider()
        st.markdown("### Scoring")
        st.markdown("| Level | Celestials | Points |\n|-------|------------|--------|\n| 1 | 12:00, 3:00, 6:00, 9:00 | 9 pts |\n| 2 | 12:00, 3:00, 6:00, 9:00 | 6 pts |\n| 3 | 12:00, 3:00, 6:00, 9:00 | 3 pts |")
        c1,c2=st.columns(2)
        with c1: st.markdown('<div class="rule-box">🏛️ <b>Architect Bonus (+4)</b><br>Only levels 1, 2 and 3 · when all spaces are filled.</div>',unsafe_allow_html=True)
        with c2: st.markdown('<div class="rule-box">🎯 <b>Center (+12)</b><br>Reaching center ends the game. Most points wins.</div>',unsafe_allow_html=True)
        st.divider()
        st.markdown("### End of Game")
        st.markdown('<div class="rule-box">The game ends when someone reaches the center (+12 pts) or when a player <b>has no beads left to place on their turn</b> — that player loses automatically.</div>',unsafe_allow_html=True)
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

    st.markdown(f'<div style="text-align:right;margin-top:-4px;"><span style="font-size:11px;background:#EAF3DE;color:#27500A;border:0.5px solid #97C459;border-radius:10px;padding:2px 9px;">6 {"niveles" if ES else "levels"} · 20⚫ · 6🟡 · 2🔵</span></div>',unsafe_allow_html=True)
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
        cp=G["cp"]; lv=G["lv"]
        moves=valid_moves(G)
        forced=G.get("forced_space"); toll_placing=G.get("toll_placing")
        name=("IA" if ES else "AI") if (mode=="ai" and cp==1) else f"{'Jugador' if ES else 'Player'} {cp+1}"
        t_cw=find_free_cw(G) if G["started"] and not forced and not toll_placing else None
        t_ccw=find_free_ccw(G) if G["started"] and not forced and not toll_placing else None
        cw_cel=is_celestial(lv,t_cw) if t_cw is not None else False
        ccw_cel=is_celestial(lv,t_ccw) if t_ccw is not None else False

        if not G["started"]:
            bar_cls="status-bar first"
            txt=f"🟢 <b>{name}</b> — {'primera jugada: 12:00' if ES else 'first move: 12:00'}"
        elif forced is not None:
            bar_cls="status-bar first"
            txt=f"🟢 <b>{name}</b> — {'subió · coloca en esp' if ES else 'went up · place at sp'}{forced+1} · {'Nv' if ES else 'Lv'}{lv+1}"
        elif toll_placing is not None:
            d_sym="↻" if toll_placing=="cw" else "↺"
            bar_cls="status-bar"
            txt=f"<b>{name}</b> — {'2ª pieza' if ES else '2nd bead'} {d_sym} · {'Nv' if ES else 'Lv'}{lv+1}"
        elif not moves:
            bar_cls="status-bar warning"
            txt=f"⚠️ <b>{name}</b> — {'sin movimientos' if ES else 'no moves'}"
        elif cw_cel or ccw_cel:
            bar_cls="status-bar celestial"
            txt=f"★ <b>{name}</b> — {'celeste disponible' if ES else 'celestial available'} · {'Nv' if ES else 'Lv'}{lv+1}"
        else:
            bar_cls="status-bar"
            cw_t=f"↻ esp{t_cw+1}" if t_cw is not None else "↻ —"
            ccw_t=f"↺ esp{t_ccw+1}" if t_ccw is not None else "↺ —"
            txt=f"<b>{name}</b> — {'Nv' if ES else 'Lv'}{lv+1} · {cw_t} · {ccw_t}"
        st.markdown(f'<div class="{bar_cls}">{txt}</div>',unsafe_allow_html=True)

    st.markdown(f'<div style="width:100%;max-width:440px;margin:8px auto;">{render_board_svg(G)}</div>',unsafe_allow_html=True)

    if not G["over"]:
        cp=G["cp"]; is_human=not(mode=="ai" and cp==1)
        moves=valid_moves(G); pc=G["pieces"][cp]
        forced=G.get("forced_space"); toll_placing=G.get("toll_placing")

        if is_human and moves:
            can=lambda t,d:(t,d) in moves

            # ── Primera jugada ──
            if not G["started"]:
                st.markdown(f"**{'Primera jugada — 12:00:' if ES else 'First move — 12:00:'}**")
                c1,c2=st.columns(2)
                with c1:
                    if st.button(f"⚫ ({pc['black']})",disabled=not can("black","start"),use_container_width=True,key="bk_st"):
                        do_play(G,"black","start",mode); st.session_state.pop("selected_color",None); st.rerun()
                with c2:
                    if st.button(f"🟡 ({pc['white']})",disabled=not can("white","start"),use_container_width=True,key="bw_st"):
                        do_play(G,"white","start",mode); st.session_state.pop("selected_color",None); st.rerun()

            # ── Espacio forzado ──
            elif forced is not None:
                lv2=G["lv"]
                st.markdown(f"**{'Elige color para esp' if ES else 'Choose color for sp'}{forced+1} · {'Nv' if ES else 'Lv'}{lv2+1}:**")
                c1,c2=st.columns(2)
                with c1:
                    if st.button(f"⚫ ({pc['black']})",disabled=not can("black","forced"),use_container_width=True,key="bk_f"):
                        do_play(G,"black","forced",mode); st.session_state.pop("selected_color",None); st.rerun()
                with c2:
                    if st.button(f"🟡 ({pc['white']})",disabled=not can("white","forced"),use_container_width=True,key="bw_f"):
                        do_play(G,"white","forced",mode); st.session_state.pop("selected_color",None); st.rerun()

            # ── Segunda pieza del peaje ──
            elif toll_placing is not None:
                d_sym="↻" if toll_placing=="cw" else "↺"
                st.markdown(f"**{'2ª pieza' if ES else '2nd bead'} {d_sym} — {'elige color:' if ES else 'choose color:'}**")
                cols=st.columns(3)
                with cols[0]:
                    if st.button(f"⚫ ({pc['black']})",disabled=not can("black",toll_placing),use_container_width=True,key="bk_t"):
                        do_play(G,"black",toll_placing,mode); st.session_state.pop("selected_color",None); st.rerun()
                with cols[1]:
                    if st.button(f"🟡 ({pc['white']})",disabled=not can("white",toll_placing),use_container_width=True,key="bw_t"):
                        do_play(G,"white",toll_placing,mode); st.session_state.pop("selected_color",None); st.rerun()
                with cols[2]:
                    if st.button(f"🔵 ({pc['blue']})",disabled=not can("blue",toll_placing),use_container_width=True,key="bb_t"):
                        do_play(G,"blue",toll_placing,mode); st.session_state.pop("selected_color",None); st.rerun()

            # ── Turno normal: primero dirección, luego color ──
            else:
                t_cw2=find_free_cw(G); t_ccw2=find_free_ccw(G)
                two_options=(t_cw2 is not None and t_ccw2 is not None and t_cw2!=t_ccw2)
                selected_dir=st.session_state.get("selected_dir",None)

                # Paso 1: elegir dirección
                if selected_dir is None:
                    if two_options:
                        st.markdown(f"**{'Elige sentido:' if ES else 'Choose direction:'}**")
                        c1,_,c2=st.columns([5,1,5])
                        with c1:
                            if st.button("↻", key="pick_cw", use_container_width=True):
                                st.session_state["selected_dir"]="cw"; st.rerun()
                        with c2:
                            if st.button("↺", key="pick_ccw", use_container_width=True):
                                st.session_state["selected_dir"]="ccw"; st.rerun()
                        st.markdown("""<style>
button[kind="secondary"][data-testid="baseButton-secondary"] { border: 2px solid #ccc; }
div:has(> div > div > div > button[data-testid="baseButton-secondary"]:nth-of-type(1)) button { border:2.5px solid #22A022!important;color:#22A022!important; }
</style>""", unsafe_allow_html=True)
                        # JS directo sobre los botones por texto
                        components.html("""<script>
(function() {
  function styleButtons() {
    const btns = window.parent.document.querySelectorAll('button');
    btns.forEach(b => {
      if (b.innerText.trim() === '↻') {
        b.style.border = '2.5px solid #22A022';
        b.style.color = '#22A022';
        b.style.fontSize = '1.4rem';
      }
      if (b.innerText.trim() === '↺') {
        b.style.border = '2.5px solid #FF6B00';
        b.style.color = '#FF6B00';
        b.style.fontSize = '1.4rem';
      }
    });
  }
  styleButtons();
  setTimeout(styleButtons, 100);
  setTimeout(styleButtons, 400);
})();
</script>""", height=0)
                    else:
                        # Solo una dirección — ir directo a elegir color
                        d="cw" if t_cw2 is not None else "ccw"
                        st.session_state["selected_dir"]=d; st.rerun()

                # Paso 2: elegir color
                else:
                    d=selected_dir
                    d_sym="↻" if d=="cw" else "↺"
                    d_col="#22A022" if d=="cw" else "#FF6B00"
                    st.markdown(
                        f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">'
                        f'<span style="font-size:1.4rem;color:{d_col};">{d_sym}</span>'
                        f'<strong>{"Elige color:" if ES else "Choose color:"}</strong>'
                        f'</div>', unsafe_allow_html=True)
                    types_avail=list(dict.fromkeys(t for t,dd in moves if dd==d))
                    labels={"black":f"⚫ ({pc['black']})","white":f"🟡 ({pc['white']})","blue":f"🔵 ({pc['blue']})"}
                    cols=st.columns(len(types_avail)+1)
                    for i,t in enumerate(types_avail):
                        with cols[i]:
                            if st.button(labels[t],use_container_width=True,key=f"col_{t}",type="secondary"):
                                do_play(G,t,d,mode)
                                st.session_state.pop("selected_dir",None)
                                st.session_state.pop("selected_color",None)
                                st.rerun()
                    with cols[-1]:
                        if st.button("✕",use_container_width=True,key="cancel_dir"):
                            st.session_state.pop("selected_dir",None); st.rerun()

        elif is_human and not moves:
            st.warning("Sin movimientos posibles." if ES else "No moves available.")
        else:
            st.info("🤖 La IA está pensando..." if ES else "🤖 AI is thinking...",icon="⏳")
            time.sleep(0.7); ai_move(G,mode)
            st.session_state.pop("selected_color",None); st.rerun()

    if G["over"]:
        p2l=("IA" if ES else "AI") if mode=="ai" else ("Jugador 2" if ES else "Player 2")
        w=G.get("winner"); reason=G.get("win_reason","")
        reason_txt=""
        if reason=="nopcs": reason_txt=f" · {'sin piezas' if ES else 'out of beads'}"
        elif reason=="center": reason_txt=f" · {'llegó al centro' if ES else 'reached center'}"
        if w==-1: title="¡Empate!" if ES else "It's a tie!"; desc=f"J1: {G['scores'][0]}pts — {p2l}: {G['scores'][1]}pts{reason_txt}"
        elif w==0: title="¡Jugador 1 gana! 🎉" if ES else "Player 1 wins! 🎉"; desc=f"J1: {G['scores'][0]}pts — {p2l}: {G['scores'][1]}pts{reason_txt}"
        else: title=f"¡{p2l} gana! 🎉" if ES else f"{p2l} wins! 🎉"; desc=f"J1: {G['scores'][0]}pts — {p2l}: {G['scores'][1]}pts{reason_txt}"
        st.markdown(f'<div class="winner-box"><div class="winner-title">{title}</div><div class="winner-scores">{desc}</div></div>',unsafe_allow_html=True)

    if G["log"]:
        st.markdown("#### Historial" if ES else "#### Game log")
        entries=""
        for e in reversed(G["log"]):
            who=e["who"]; wc="log-j1" if who in("J1","P1") else("log-ai" if who in("IA","AI") else "log-j2")
            pts_html=f' <span class="log-pts">+{e["pts"]}</span>' if e["pts"]>0 else ""
            entries+=f'<div class="log-entry"><span style="color:#aaa;">#{e["turn"]}</span> <span class="{wc}">{who}</span> {e["msg"]}{pts_html}</div>'
        st.markdown(f'<div class="log-container">{entries}</div>',unsafe_allow_html=True)
