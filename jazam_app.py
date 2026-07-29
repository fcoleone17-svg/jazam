"""
JAZAM — dos variantes
  · Jazam       (classic) : 2 frentes desde 12:00, celestes cardinales, bono arquitecto
  · Jazam Duel  (dynamic) : frentes dinámicos, celestes en X, hasta 4 jugadores
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
.score-box{background:#F5F1E4;border-radius:12px;padding:8px 10px;text-align:center;border:1px solid #D3C8A0;}
.score-name{font-size:0.7rem;color:#888;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:2px;}
.score-pts{font-size:1.5rem;font-weight:600;color:#1C1A10;line-height:1;}
.score-pts span{font-size:0.7rem;font-weight:400;color:#888;margin-left:3px;}
.status-bar{background:#F5F1E4;border-radius:8px;padding:9px 14px;text-align:center;font-size:0.86rem;color:#555;border:1px solid #D3C8A0;margin:8px 0;}
.status-bar b{color:#1C1A10;}
.status-bar.celestial{background:#C5E8FF;border-color:#185FA5;color:#0C447C;}
.status-bar.warning{background:#FCEBEB;border-color:#E24B4A;color:#A32D2D;}
.status-bar.first{background:#EAF3DE;border-color:#3B6D11;color:#27500A;}
.log-container{background:#F9F7F0;border:1px solid #D3C8A0;border-radius:10px;padding:10px 14px;max-height:180px;overflow-y:auto;font-size:0.78rem;}
.log-entry{padding:3px 0;border-bottom:1px solid #EDE8D5;}
.log-entry:last-child{border-bottom:none;}
.log-pts{color:#3B6D11;font-weight:600;}
.winner-box{background:#F5F1E4;border:2px solid #BA7517;border-radius:14px;padding:20px;text-align:center;margin-top:12px;}
.winner-title{font-family:'Crimson Pro',serif;font-size:1.8rem;font-weight:600;color:#1C1A10;margin-bottom:6px;}
.winner-scores{font-size:0.86rem;color:#666;}
.dot-row{display:flex;gap:2px;flex-wrap:wrap;margin-top:2px;justify-content:center;}
.dot{width:7px;height:7px;border-radius:50%;display:inline-block;}
.rule-box{background:#F9F7F0;border-left:3px solid #BA7517;border-radius:0 8px 8px 0;padding:10px 14px;font-size:0.84rem;color:#444;margin-bottom:8px;}
@media(max-width:600px){
  .jazam-title{font-size:1.9rem!important;}
  .score-pts{font-size:1.2rem!important;}
  .dot{width:6px!important;height:6px!important;}
  .status-bar{font-size:0.76rem!important;}
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════ CONFIGURACIÓN ══════════════════════════
LEVELS = [32, 16, 8, 4, 2, 1]
CENTER_PTS = 12

CEL_CARD = {0:{0:9, 8:9, 16:9, 24:9},
            1:{0:6, 4:6, 8:6, 12:6},
            2:{0:3, 2:3, 4:3, 6:3}}
CEL_X    = {0:{4:9, 12:9, 20:9, 28:9},
            1:{2:6, 6:6, 10:6, 14:6},
            2:{1:3, 3:3, 5:3, 7:3}}

PCOLOR = ["#FF6B00", "#00C8FF", "#22A022", "#C044D0"]
PNAME  = ["12:00", "3:00", "6:00", "9:00"]

def cfg(G):
    if G["variant"] == "classic":
        return {"cel": CEL_CARD, "arch": True}
    return {"cel": CEL_X, "arch": False}

def is_cel(G, lv, si):  return si in cfg(G)["cel"].get(lv, {})
def space_pts(G, lv, si):
    if lv == 5: return CENTER_PTS
    return cfg(G)["cel"].get(lv, {}).get(si, 0)

def aligned_si(lo, si, ln):
    return round(si * LEVELS[ln] / LEVELS[lo]) % LEVELS[ln]

def entry_space(board, lo, si, ln):
    n = LEVELS[ln]; a = aligned_si(lo, si, ln)
    for off in range(n):
        c = (a + off) % n
        if board[ln][c] is None: return c
    return 0

def neighbors(lv, si):
    n = LEVELS[lv]
    if n == 1: return []
    if n == 2: return [1 - si]
    return [(si + 1) % n, (si - 1) % n]

def empty_neighbor(board, lv, si):
    for x in neighbors(lv, si):
        if board[lv][x] is None: return x
    return None

def frontier(board, lv):
    out = []
    for si in range(LEVELS[lv]):
        if board[lv][si] is not None: continue
        if any(board[lv][x] is not None for x in neighbors(lv, si)):
            out.append(si)
    return out

# ══════════════════════════ ESTADO ══════════════════════════
def init_game(variant="dynamic", np_=2, teams=False):
    if variant == "classic":
        pieces = [{"black":20,"white":6,"blue":2} for _ in range(2)]
        np_ = 2; teams = False
        origins = [0]
    elif np_ == 2:
        # komi: J1 recibe una negra extra por mover primero
        pieces = [{"black":21,"white":6,"blue":2},
                  {"black":20,"white":6,"blue":2}]
        origins = [0, 16]
    else:
        pieces = [{"black":10,"white":3,"blue":1} for _ in range(4)]
        origins = [0, 8, 16, 24]

    return {
        "variant": variant, "np": np_, "teams": teams,
        "origins": origins,
        "cp": 0, "scores": [0]*np_, "pieces": pieces,
        "board": [[None]*n for n in LEVELS],
        "lv": 0,
        # duel
        "ptr_cw": 1, "ptr_ccw": LEVELS[0]-1,
        "toll_cw": False, "toll_ccw": False,
        # jazam
        "toll_space": None, "seeded": [False]*np_,
        # comunes
        "toll_lv": None, "toll_pending": None,
        "forced_space": None, "started": False,
        "last_was_blue": False,
        "over": False, "winner": None, "win_reason": None,
        "log": [], "turn_count": 0, "_es": True,
    }

def find_free(G, direction):
    lv = G["lv"]; n = LEVELS[lv]; b = G["board"][lv]
    si = (G["ptr_cw"] if direction == "cw" else G["ptr_ccw"]) % n
    for _ in range(n):
        if b[si] is None: return si
        si = (si+1) % n if direction == "cw" else (si-1) % n
    return None

def add_log(G, who, msg, pts=0):
    G["turn_count"] += 1
    G["log"].append({"t":G["turn_count"], "who":who, "msg":msg, "pts":pts, "p":G["cp"]})

# ══════════════════════════ MOVIMIENTOS ══════════════════════════
def valid_moves(G):
    """Devuelve lista de (tipo, espacio, meta) donde meta guarda la dirección en Duel."""
    cp = G["cp"]; pc = G["pieces"][cp]; lv = G["lv"]
    if pc["black"] <= 0 and pc["white"] <= 0 and pc["blue"] <= 0: return []

    seed = False
    slots = []   # lista de (espacio, meta)

    if G["variant"] == "classic":
        if not G["started"]:
            slots = [(0, "start")]; seed = True
        elif G["forced_space"] is not None:
            slots = [(G["forced_space"], "forced")]
        elif G["toll_pending"] is not None:
            d = G["toll_pending"]
            t = find_free(G, d)
            if t is not None: slots = [(t, d)]
        else:
            seen = set()
            for d in ("cw", "ccw"):
                t = find_free(G, d)
                if t is None or t in seen: continue
                seen.add(t); slots.append((t, d))
    else:
        if lv == 0 and not G["seeded"][cp] and G["board"][0][G["origins"][cp]] is None:
            slots = [(G["origins"][cp], "seed")]; seed = True
        elif G["forced_space"] is not None:
            slots = [(G["forced_space"], "forced")]
        elif G["toll_pending"] is not None:
            slots = [(G["toll_pending"], "second")]
        else:
            f = frontier(G["board"], lv)
            if not f: f = [i for i, x in enumerate(G["board"][lv]) if x is None]
            slots = [(s, "free") for s in f]

    moves = []
    for s, meta in slots:
        on_toll = toll_here(G, s, meta)
        if pc["black"] > 0: moves.append(("black", s, meta))
        if pc["white"] > 0: moves.append(("white", s, meta))
        if (pc["blue"] > 0 and not G["last_was_blue"] and not on_toll and not seed):
            moves.append(("blue", s, meta))
    return moves

def toll_here(G, space, meta):
    """¿Esta colocación es la 1ª pieza de un peaje (sin propiedades)?"""
    if G["toll_pending"] is not None: return False
    if G["toll_lv"] != G["lv"]: return False
    if G["variant"] == "classic":
        if meta == "cw":  return G["toll_cw"]
        if meta == "ccw": return G["toll_ccw"]
        return False
    return G["toll_space"] == space

# ══════════════════════════ JUGADA ══════════════════════════
def advance_level(G, from_si):
    """Sube un nivel dejando el espacio de entrada alineado."""
    lv = G["lv"]
    if lv >= 5: return None
    e = entry_space(G["board"], lv, from_si, lv+1)
    G["lv"] = lv + 1
    G["toll_cw"] = G["toll_ccw"] = False
    G["toll_space"] = None; G["toll_lv"] = None
    if G["variant"] == "classic":
        n = LEVELS[G["lv"]]
        G["ptr_cw"] = (e+1) % n; G["ptr_ccw"] = (e-1) % n
    return e

def do_play(G, ptype, space, meta, mode):
    if G["over"]: return
    cp = G["cp"]; pc = G["pieces"][cp]; lv = G["lv"]; ES = G["_es"]
    who = player_label(G, cp, mode)
    tn = {"black":"negra" if ES else "black",
          "white":"blanca" if ES else "white",
          "blue":"azul" if ES else "blue"}[ptype]

    paying = toll_here(G, space, meta)
    second = (meta == "second") or (G["variant"] == "classic" and G["toll_pending"] is not None)

    pc[ptype] -= 1

    # ─────────── AZUL con propiedades ───────────
    if ptype == "blue" and not paying:
        cel = is_cel(G, lv, space)
        pts = space_pts(G, lv, space) if cel else 0
        G["scores"][cp] += pts
        G["board"][lv][space] = {"p":cp, "t":"blue", "neu":False}
        G["toll_pending"] = None; G["forced_space"] = None
        if G["variant"] == "classic" and meta in ("cw","ccw"):
            n = LEVELS[lv]
            if meta == "cw": G["ptr_cw"] = (space+1) % n
            else: G["ptr_ccw"] = (space-1) % n
        if cel and lv < 5:
            add_log(G, who, f"{tn} esp{space+1} +{pts} → Nv{lv+2}", pts)
            G["forced_space"] = advance_level(G, space)
            G["last_was_blue"] = True
            check_end(G, mode); return                 # repite turno
        add_log(G, who, f"{tn} esp{space+1}" + (f" +{pts}" if pts else ""), pts)
        G["last_was_blue"] = False
        after_place(G, space, mode, pass_turn=True); return

    # ─────────── Pieza normal (o azul neutralizada) ───────────
    eff = "black" if paying else ptype
    G["board"][lv][space] = {"p":cp, "t":ptype, "neu":paying}
    G["last_was_blue"] = False
    note = " ·peaje" if paying else ""
    add_log(G, who, f"{tn} esp{space+1}{note}", 0)

    if G["variant"] == "classic":
        n = LEVELS[lv]
        if meta == "start":
            G["started"] = True; G["ptr_cw"] = 1; G["ptr_ccw"] = n-1
            G["toll_cw"] = G["toll_ccw"] = False; G["toll_lv"] = None
        elif meta == "forced":
            G["forced_space"] = None
            G["ptr_cw"] = (space+1) % n; G["ptr_ccw"] = (space-1) % n
        elif meta in ("cw", "ccw"):
            if meta == "cw": G["ptr_cw"] = (space+1) % n
            else: G["ptr_ccw"] = (space-1) % n
    else:
        if meta == "seed": G["seeded"][cp] = True; G["started"] = True
        elif meta == "forced": G["forced_space"] = None

    # ── 1ª pieza del peaje: mismo jugador coloca la 2ª ──
    if paying:
        if G["variant"] == "classic":
            if meta == "cw": G["toll_cw"] = False
            else: G["toll_ccw"] = False
            nxt = meta
        else:
            G["toll_space"] = None
            nxt = empty_neighbor(G["board"], lv, space)
        if all(x is not None for x in G["board"][lv]):
            e = level_bonus_and_advance(G, cp, space, who, ES)
            G["toll_pending"] = e if e is not None else None
            if e is None: G["cp"] = (cp+1) % G["np"]
            check_end(G, mode); return
        G["toll_pending"] = nxt
        if nxt is None: G["cp"] = (cp+1) % G["np"]
        check_end(G, mode); return

    # ── 2ª pieza del peaje (con propiedades) ──
    if second:
        G["toll_pending"] = None

    if eff == "white":
        if G["variant"] == "classic":
            if meta in ("cw", "ccw"):
                if meta == "cw": G["toll_cw"] = True
                else: G["toll_ccw"] = True
                G["toll_lv"] = lv
            else:
                G["toll_cw"] = G["toll_ccw"] = True; G["toll_lv"] = lv
        else:
            nb = empty_neighbor(G["board"], lv, space)
            if nb is not None:
                G["toll_space"] = nb; G["toll_lv"] = lv

    after_place(G, space, mode, pass_turn=True)

def level_bonus_and_advance(G, cp, space, who, ES):
    """Aplica bono (si la variante lo tiene) y sube de nivel. Devuelve espacio de entrada."""
    lv = G["lv"]
    if cfg(G)["arch"] and lv <= 2:
        G["scores"][cp] += 4
        add_log(G, who, f"Nv{lv+1} completo +4" if ES else f"Lv{lv+1} complete +4", 4)
    return advance_level(G, space)

def after_place(G, space, mode, pass_turn):
    cp = G["cp"]; ES = G["_es"]; who = player_label(G, cp, mode)
    if all(x is not None for x in G["board"][G["lv"]]):
        e = level_bonus_and_advance(G, cp, space, who, ES)
        if e is not None: G["forced_space"] = e
    if pass_turn: G["cp"] = (cp+1) % G["np"]
    check_end(G, mode)

def check_end(G, mode):
    ES = G["_es"]
    # centro
    if G["board"][5][0] is not None:
        w = G["board"][5][0]["p"]
        G["scores"][w] += CENTER_PTS
        G["board"][5][0]["scored"] = True
        add_log(G, player_label(G, w, mode), "¡CENTRO! +12" if ES else "CENTER! +12", CENTER_PTS)
        G["over"] = True; G["win_reason"] = "center"
        G["winner"] = w if not G["teams"] else (w % 2)
        return
    # sin piezas en su turno
    cp = G["cp"]; pc = G["pieces"][cp]
    if pc["black"] <= 0 and pc["white"] <= 0 and pc["blue"] <= 0:
        G["over"] = True; G["win_reason"] = "nopcs"
        add_log(G, player_label(G, cp, mode), "sin piezas" if ES else "out of beads", 0)
        G["winner"] = resolve_on_exhaustion(G, cp)
        return
    if not valid_moves(G):
        G["over"] = True; G["win_reason"] = "nopcs"
        G["winner"] = resolve_on_exhaustion(G, cp)

def resolve_on_exhaustion(G, loser):
    """Quien se queda sin piezas pierde. Entre el resto, gana el de más puntos."""
    if G["teams"]:
        return 1 - (loser % 2)
    others = [p for p in range(G["np"]) if p != loser]
    best = max(G["scores"][p] for p in others)
    tied = [p for p in others if G["scores"][p] == best]
    return tied[0] if len(tied) == 1 else -1

# ══════════════════════════ IA ══════════════════════════
def ai_move(G, mode):
    moves = valid_moves(G)
    if not moves: return
    lv = G["lv"]; cels = cfg(G)["cel"].get(lv, {})
    b = G["board"]

    # 1. tomar celeste con azul
    take = [m for m in moves if m[0] == "blue" and m[1] in cels]
    if take:
        m = random.choice(take); do_play(G, m[0], m[1], m[2], mode); return
    # 2. tapar celeste con negra
    block = [m for m in moves if m[0] == "black" and m[1] in cels]
    if block:
        m = random.choice(block); do_play(G, m[0], m[1], m[2], mode); return
    # 3. blanca junto a celeste libre (envenenar el acceso)
    poison = []
    for m in moves:
        if m[0] != "white": continue
        nb = empty_neighbor(b, lv, m[1])
        if nb is not None and nb in cels: poison.append(m)
    if poison:
        m = random.choice(poison); do_play(G, m[0], m[1], m[2], mode); return
    # 4. negra hacia el celeste libre más cercano
    blacks = [m for m in moves if m[0] == "black"]
    if blacks:
        free_cels = [c for c in cels if b[lv][c] is None]
        if free_cels:
            n = LEVELS[lv]
            def dist(m):
                return min(min((m[1]-c) % n, (c-m[1]) % n) for c in free_cels)
            blacks.sort(key=dist)
            m = blacks[0]
        else:
            m = random.choice(blacks)
        do_play(G, m[0], m[1], m[2], mode); return
    m = random.choice(moves); do_play(G, m[0], m[1], m[2], mode)

# ══════════════════════════ TABLERO ══════════════════════════
def render_board_svg(G, options=None, chosen=None):
    options = options or []
    SIZE = 440; cx = cy = SIZE // 2
    radii = [int(cx*r) for r in [0.91, 0.74, 0.57, 0.41, 0.26, 0.0]]
    L = [f'<svg viewBox="0 0 {SIZE} {SIZE}" width="100%" style="max-width:{SIZE}px;display:block;margin:0 auto;" xmlns="http://www.w3.org/2000/svg">']
    L.append(f'<circle cx="{cx}" cy="{cy}" r="{cx-2}" fill="#F5F1E4" stroke="#D3C8A0" stroke-width="1.5"/>')
    for li in range(3):
        n = LEVELS[li]; rO = radii[li]+11; rI = radii[li+1]+11
        for k in range(8):
            s = k*n//8
            a1 = -math.pi/2 + (s/n)*math.pi*2
            a2 = -math.pi/2 + ((s+n/8)/n)*math.pi*2
            x1i=cx+rI*math.cos(a1); y1i=cy+rI*math.sin(a1)
            x2o=cx+rO*math.cos(a1); y2o=cy+rO*math.sin(a1)
            x3o=cx+rO*math.cos(a2); y3o=cy+rO*math.sin(a2)
            x4i=cx+rI*math.cos(a2); y4i=cy+rI*math.sin(a2)
            L.append(f'<path d="M{x1i:.1f},{y1i:.1f} L{x2o:.1f},{y2o:.1f} A{rO},{rO} 0 0,1 {x3o:.1f},{y3o:.1f} L{x4i:.1f},{y4i:.1f} A{rI},{rI} 0 0,0 {x1i:.1f},{y1i:.1f} Z" fill="rgba(120,90,40,0.07)"/>')
    for li in range(5):
        L.append(f'<circle cx="{cx}" cy="{cy}" r="{radii[li]+11}" fill="none" stroke="rgba(120,90,40,0.18)" stroke-width="0.8"/>')
    # ejes: cardinales en Duel, X en Jazam
    axis = [0,1,2,3] if G["variant"]=="classic" else [0.5,1.5,2.5,3.5]
    for i in axis:
        a = -math.pi/2 + i*math.pi/2
        x1=cx+18*math.cos(a); y1=cy+18*math.sin(a)
        x2=cx+(cx-8)*math.cos(a); y2=cy+(cx-8)*math.sin(a)
        L.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="rgba(120,90,40,0.14)" stroke-width="0.8" stroke-dasharray="2,5"/>')
    for i in range(12):
        a = -math.pi/2 + i*math.pi/6; r1 = cx-6; r2 = r1-(5 if i%3==0 else 3)
        L.append(f'<line x1="{cx+r1*math.cos(a):.1f}" y1="{cy+r1*math.sin(a):.1f}" x2="{cx+r2*math.cos(a):.1f}" y2="{cy+r2*math.sin(a):.1f}" stroke="rgba(120,90,40,0.22)" stroke-width="{1.5 if i%3==0 else 0.7}"/>')

    nlv = G["lv"]; forced = G.get("forced_space")
    for li in range(6):
        n = LEVELS[li]
        r_dot = 22 if li == 5 else 10
        for si in range(n):
            if li == 5: x, y = cx, cy
            else:
                a = -math.pi/2 + (si/n)*math.pi*2
                x = cx + radii[li]*math.cos(a); y = cy + radii[li]*math.sin(a)
            cel = is_cel(G, li, si); cell = G["board"][li][si]
            is_opt = (li == nlv and si in options and cell is None)
            is_sel = (li == nlv and chosen == si and cell is None)
            is_forced = (li == nlv and forced is not None and si == forced and cell is None and not G["over"])

            if li == 5:      fill,stroke,sw = "#DDF0CC","#3B6D11",2
            elif is_sel:     fill,stroke,sw = "rgba(34,160,34,0.45)","#22A022",3.5
            elif is_forced:  fill,stroke,sw = "rgba(59,109,17,0.30)","#3B6D11",3
            elif is_opt:     fill,stroke,sw = "rgba(255,107,0,0.22)","#FF6B00",2.5
            elif cel:        fill,stroke,sw = "#C5E8FF","#185FA5",1.5
            else:            fill,stroke,sw = "rgba(80,60,20,0.05)","rgba(80,60,20,0.15)",0.7
            L.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r_dot}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

            if is_opt or is_sel:
                L.append(f'<text x="{x:.1f}" y="{y+3:.1f}" text-anchor="middle" font-size="9" font-weight="600" fill="#7A3B00" font-family="DM Sans,sans-serif">{si+1}</text>')
            elif cel and not cell and not is_forced:
                L.append(f'<text x="{x:.1f}" y="{y+3:.1f}" text-anchor="middle" font-size="{7 if li==0 else 8}" fill="#0C447C" font-family="DM Sans,sans-serif">{space_pts(G,li,si)}</text>')
            if li == 5 and G["board"][5][0] is None:
                L.append(f'<text x="{cx}" y="{cy+5}" text-anchor="middle" font-size="12" font-weight="600" fill="#27500A" font-family="DM Sans,sans-serif">{CENTER_PTS}</text>')

            if cell:
                t = cell["t"]; neu = cell.get("neu", False); pr = r_dot-2.5
                if neu or t == "black": pf, ps = "#111110", "#999990"
                elif t == "white":      pf, ps = "#E8D44D", "#B89A10"
                else:                   pf, ps = "#378ADD", "#185FA5"
                L.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{pr}" fill="{pf}" stroke="{ps}" stroke-width="1.5"/>')
                L.append(f'<circle cx="{x:.1f}" cy="{y+pr-2:.1f}" r="2.0" fill="{PCOLOR[cell["p"]]}"/>')

    L.append(f'<circle cx="{cx}" cy="{cy}" r="{cx-3}" fill="none" stroke="rgba(120,90,40,0.25)" stroke-width="1.5"/>')
    for i, lbl in enumerate(["12","3","6","9"]):
        a = -math.pi/2 + i*math.pi/2
        L.append(f'<text x="{cx+(cx+8)*math.cos(a):.1f}" y="{cy+(cx+8)*math.sin(a)+4:.1f}" text-anchor="middle" font-size="10" fill="rgba(90,65,30,0.5)" font-family="DM Sans,sans-serif">{lbl}</text>')
    L.append("</svg>")
    return "\n".join(L)

def dots(n, mx, color):
    return ('<div class="dot-row">' + "".join(
        f'<span class="dot" style="background:{color};opacity:{1 if i<n else 0.15};"></span>'
        for i in range(mx)) + '</div>')

def pieces_html(G, p):
    pc = G["pieces"][p]
    mx = {"black":21 if G["variant"]!="classic" and G["np"]==2 else (20 if G["np"]==2 else 10),
          "white":6 if G["np"]==2 else 3,
          "blue":2 if G["np"]==2 else 1}
    rows = ""
    for t, col in [("black","#111110"), ("white","#E8D44D"), ("blue","#378ADD")]:
        rows += f'<div>{dots(pc[t], mx[t], col)}<small style="color:#888;font-size:0.65rem;">{pc[t]}</small></div>'
    return rows

def player_label(G, p, mode):
    ES = G["_es"]
    if mode == "ai" and p > 0: return ("IA" if ES else "AI") + (f"{p}" if G["np"] > 2 else "")
    return f"J{p+1}"

# ══════════════════════════ APP ══════════════════════════
if "game" not in st.session_state:
    st.session_state.game = init_game("dynamic", 2)
    st.session_state.mode = "2p"
if "lang" not in st.session_state: st.session_state.lang = "ES"

G = st.session_state.game
mode = st.session_state.mode
G["_es"] = (st.session_state.lang == "ES")
ES = G["_es"]

ct, cl = st.columns([3,1])
with ct: st.markdown('<div class="jazam-title">JAZAM</div>', unsafe_allow_html=True)
with cl:
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    sel = st.radio("", ["🇪🇸","🇬🇧"], horizontal=True, label_visibility="collapsed",
                   index=0 if ES else 1)
    st.session_state.lang = "ES" if sel == "🇪🇸" else "EN"
    ES = G["_es"] = (st.session_state.lang == "ES")

if G["variant"] == "classic":
    vname = "clásico" if ES else "classic"
elif G["teams"]:
    vname = "Duel · parejas" if ES else "Duel · teams"
elif G["np"] > 2:
    vname = f"Duel · {G['np']} " + ("jugadores" if ES else "players")
else:
    vname = "Duel · 2"
st.markdown(f'<div class="jazam-subtitle">{"meditación competitiva" if ES else "competitive meditation"} · {vname}</div>',
            unsafe_allow_html=True)

tab_game, tab_rules = st.tabs(["🎮 " + ("Juego" if ES else "Game"),
                               "📖 " + ("Reglas" if ES else "Rules")])

# ─────────────────────────── REGLAS ───────────────────────────
with tab_rules:
    st.divider()
    if ES:
        st.markdown("### Dos juegos, un tablero")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="rule-box"><b>🔵 Jazam</b><br><small>Dos frentes desde 12:00 · celestes en 12/3/6/9 · bono del arquitecto. Lento, de construcción. 2 jugadores.</small></div>', unsafe_allow_html=True)
        with c2:
            st.markdown('<div class="rule-box"><b>⚔️ Jazam Duel</b><br><small>Frentes dinámicos · celestes en X · hasta 4 jugadores, solos o en parejas. Rápido, carrera hacia el centro.</small></div>', unsafe_allow_html=True)
        st.divider()
        st.markdown("### El tablero")
        ca, cb = st.columns(2)
        with ca:
            st.markdown("| Nivel | Espacios |\n|---|---|\n| 1 (exterior) | 32 |\n| 2 | 16 |\n| 3 | 8 |\n| 4 | 4 |\n| 5 | 2 |\n| 6 — Centro | 1 |")
        with cb:
            st.markdown("**Duel:** cada jugador siembra su primera pelota en su origen (12:00, 3:00, 6:00 o 9:00). Después puedes jugar en **cualquier espacio vacío que toque una pelota ya puesta**. A medida que los arcos se unen, las opciones se cierran solas.\n\n**Jazam (clásico):** dos frentes avanzan ↻ y ↺ desde 12:00.")
        st.divider()
        st.markdown("### Las pelotas")
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown('<div class="rule-box" style="text-align:center;"><b>⚫ Negra</b><br><small>Ocupa un espacio. Nada más.</small></div>', unsafe_allow_html=True)
        with c2: st.markdown('<div class="rule-box" style="text-align:center;"><b>🟡 Blanca</b><br><small>Deja un peaje en el espacio siguiente.</small></div>', unsafe_allow_html=True)
        with c3: st.markdown('<div class="rule-box" style="text-align:center;"><b>🔵 Azul</b><br><small>Va en cualquier espacio · solo en celeste puntúa, sube de nivel y repite turno.</small></div>', unsafe_allow_html=True)
        st.markdown('<div class="rule-box">🟡 <b>El peaje:</b> después de una blanca, el próximo que juegue en el espacio marcado pone 2 pelotas. Ojo: la primera no cuenta — solo ocupa el espacio. La segunda es la que realmente juega.<br><br><b>Ejemplo:</b> la blanca queda justo antes de un celeste. El siguiente jugador pone su primera pelota ahí — pero no tiene efecto (aunque sea azul, no sube de nivel). La segunda es la que juega normalmente.</div>', unsafe_allow_html=True)
        st.markdown("*No se pueden jugar dos azules seguidas.*")
        st.divider()
        st.markdown("### Puntuación")
        st.markdown("| Nivel | Celeste | Puntos |\n|---|---|---|\n| 1 | los cuatro | 9 |\n| 2 | los cuatro | 6 |\n| 3 | los cuatro | 3 |\n| 6 | centro | 12 |")
        st.markdown('<div class="rule-box">🏛️ <b>Bono del Arquitecto (+4)</b> — solo en <b>Jazam</b> (clásico): completar un nivel del 1 al 3.</div>', unsafe_allow_html=True)
        st.divider()
        st.markdown("### Fin del juego")
        st.markdown('<div class="rule-box">Termina cuando alguien llega al centro (+12) o cuando un jugador <b>no tiene pelotas para colocar en su turno</b> — ese jugador pierde. Entre el resto, gana quien tenga más puntos.<br><br>En <b>parejas</b>, si un jugador se queda sin pelotas, pierde su equipo.</div>', unsafe_allow_html=True)
        st.markdown('<div class="rule-box"><b>Compensación:</b> en el duelo de 2, el jugador que abre recibe una negra extra — mover primero significa agotarse primero.</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;margin-top:2rem;font-style:italic;color:#BA7517;">"Jazam no es un juego… es una meditación competitiva."</div>', unsafe_allow_html=True)
    else:
        st.markdown("### Two games, one board")
        c1, c2 = st.columns(2)
        with c1: st.markdown('<div class="rule-box"><b>🔵 Jazam</b><br><small>Two fronts from 12:00 · celestials at 12/3/6/9 · architect bonus. Slow, constructive. 2 players.</small></div>', unsafe_allow_html=True)
        with c2: st.markdown('<div class="rule-box"><b>⚔️ Jazam Duel</b><br><small>Dynamic fronts · X celestials · up to 4 players, solo or in teams. Fast, a race inward.</small></div>', unsafe_allow_html=True)
        st.divider()
        st.markdown("### The board")
        ca, cb = st.columns(2)
        with ca:
            st.markdown("| Level | Spaces |\n|---|---|\n| 1 (outer) | 32 |\n| 2 | 16 |\n| 3 | 8 |\n| 4 | 4 |\n| 5 | 2 |\n| 6 — Center | 1 |")
        with cb:
            st.markdown("**Duel:** each player seeds their first bead at their origin (12:00, 3:00, 6:00 or 9:00). After that you may play on **any empty space touching a placed bead**. As the arcs merge, options close by themselves.\n\n**Jazam (classic):** two fronts advance ↻ and ↺ from 12:00.")
        st.divider()
        st.markdown("### The beads")
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown('<div class="rule-box" style="text-align:center;"><b>⚫ Black</b><br><small>Fills a space. Nothing else.</small></div>', unsafe_allow_html=True)
        with c2: st.markdown('<div class="rule-box" style="text-align:center;"><b>🟡 White</b><br><small>Leaves a toll on the next space.</small></div>', unsafe_allow_html=True)
        with c3: st.markdown('<div class="rule-box" style="text-align:center;"><b>🔵 Blue</b><br><small>Any space · only on a celestial does it score, ascend and repeat turn.</small></div>', unsafe_allow_html=True)
        st.markdown('<div class="rule-box">🟡 <b>The toll:</b> after a white, the next player to use the marked space places 2 beads. The first one doesn\'t count — it just fills the space. The second one is the one that really plays.</div>', unsafe_allow_html=True)
        st.markdown("*Two blues cannot be played in a row.*")
        st.divider()
        st.markdown("### Scoring")
        st.markdown("| Level | Celestials | Points |\n|---|---|---|\n| 1 | all four | 9 |\n| 2 | all four | 6 |\n| 3 | all four | 3 |\n| 6 | center | 12 |")
        st.markdown('<div class="rule-box">🏛️ <b>Architect Bonus (+4)</b> — <b>Jazam</b> (classic) only: complete a level from 1 to 3.</div>', unsafe_allow_html=True)
        st.divider()
        st.markdown("### End of game")
        st.markdown('<div class="rule-box">Ends when someone reaches the center (+12) or a player <b>has no beads to place on their turn</b> — that player loses. Among the rest, most points wins.</div>', unsafe_allow_html=True)

# ─────────────────────────── JUEGO ───────────────────────────
with tab_game:
    opts = ["⚔️ Duel · 2 vs IA", "⚔️ Duel · 2", "⚔️ Duel · 4",
            "⚔️ Duel · parejas", "🔵 Jazam · 2", "🔵 Jazam · vs IA"]
    pick = st.selectbox("Modo" if ES else "Mode", opts,
                        index=opts.index(st.session_state.get("pick", opts[1])),
                        label_visibility="collapsed")
    if pick != st.session_state.get("pick"):
        st.session_state.pick = pick
        if pick == opts[0]: st.session_state.game = init_game("dynamic", 2); st.session_state.mode = "ai"
        elif pick == opts[1]: st.session_state.game = init_game("dynamic", 2); st.session_state.mode = "2p"
        elif pick == opts[2]: st.session_state.game = init_game("dynamic", 4); st.session_state.mode = "2p"
        elif pick == opts[3]: st.session_state.game = init_game("dynamic", 4, True); st.session_state.mode = "2p"
        elif pick == opts[4]: st.session_state.game = init_game("classic", 2); st.session_state.mode = "2p"
        else: st.session_state.game = init_game("classic", 2); st.session_state.mode = "ai"
        st.session_state.pop("sel_space", None)
        st.rerun()

    if st.button("↺ " + ("Nueva partida" if ES else "New game"), use_container_width=True):
        v = G["variant"]; n = G["np"]; t = G["teams"]
        st.session_state.game = init_game(v, n, t)
        st.session_state.pop("sel_space", None); st.rerun()

    G = st.session_state.game; mode = st.session_state.mode
    G["_es"] = ES
    st.divider()

    # marcadores
    cols = st.columns(G["np"])
    for p in range(G["np"]):
        with cols[p]:
            act = (G["cp"] == p and not G["over"])
            bord = f"border:2px solid {PCOLOR[p]};" if act else ""
            nm = player_label(G, p, mode)
            if G["np"] == 4:
                nm += f" · {PNAME[p]}"
                if G["teams"]: nm += " · " + ("A" if p % 2 == 0 else "B")
            st.markdown(f"""<div class="score-box" style="{bord}">
              <div class="score-name" style="color:{PCOLOR[p]};">{nm}</div>
              <div class="score-pts">{G['scores'][p]}<span>pts</span></div>
              <div>{pieces_html(G, p)}</div></div>""", unsafe_allow_html=True)

    if G["teams"] and not G["over"]:
        A = G["scores"][0] + G["scores"][2]; B = G["scores"][1] + G["scores"][3]
        st.markdown(f'<div class="status-bar">{"Equipo" if ES else "Team"} A <b>{A}</b> — <b>{B}</b> B</div>',
                    unsafe_allow_html=True)

    # estado + opciones
    moves = valid_moves(G) if not G["over"] else []
    spaces = sorted({m[1] for m in moves})
    sel_space = st.session_state.get("sel_space")
    if sel_space is not None and sel_space not in spaces:
        sel_space = None; st.session_state.pop("sel_space", None)

    if not G["over"]:
        cp = G["cp"]; nm = player_label(G, cp, mode)
        col = PCOLOR[cp]
        if G["variant"] != "classic" and G["lv"] == 0 and not G["seeded"][cp]:
            cls, txt = "status-bar first", f"🟢 <b>{nm}</b> — {'siembra en' if ES else 'seed at'} {PNAME[cp]}"
        elif G["forced_space"] is not None:
            cls, txt = "status-bar first", f"🟢 <b>{nm}</b> — {'entra al Nv' if ES else 'enters Lv'}{G['lv']+1} · esp{G['forced_space']+1}"
        elif G["toll_pending"] is not None:
            cls, txt = "status-bar", f"<b>{nm}</b> — {'2ª pelota del peaje' if ES else '2nd toll bead'}"
        elif not moves:
            cls, txt = "status-bar warning", f"⚠️ <b>{nm}</b> — {'sin movimientos' if ES else 'no moves'}"
        elif any(is_cel(G, G["lv"], s) for s in spaces):
            cls, txt = "status-bar celestial", f"★ <b>{nm}</b> — {'celeste disponible' if ES else 'celestial available'} · Nv{G['lv']+1}"
        else:
            cls, txt = "status-bar", f"<b style='color:{col}'>{nm}</b> — Nv{G['lv']+1} · {len(spaces)} {'opciones' if ES else 'options'}"
        st.markdown(f'<div class="{cls}">{txt}</div>', unsafe_allow_html=True)

    st.markdown(f'<div style="width:100%;max-width:440px;margin:6px auto;">{render_board_svg(G, spaces, sel_space)}</div>',
                unsafe_allow_html=True)

    # controles
    if not G["over"]:
        cp = G["cp"]
        human = not (mode == "ai" and cp > 0)
        if human and moves:
            pc = G["pieces"][cp]
            if sel_space is None:
                if len(spaces) == 1:
                    st.session_state.sel_space = spaces[0]; st.rerun()
                st.markdown(f"**{'1 · Elige espacio:' if ES else '1 · Choose space:'}**")
                per_row = 4
                for i in range(0, len(spaces), per_row):
                    row = spaces[i:i+per_row]
                    cc = st.columns(per_row)
                    for j, s in enumerate(row):
                        with cc[j]:
                            star = "★" if is_cel(G, G["lv"], s) else ""
                            if st.button(f"{star}{s+1}", key=f"sp{s}", use_container_width=True):
                                st.session_state.sel_space = s; st.rerun()
            else:
                s = sel_space
                star = " ★" if is_cel(G, G["lv"], s) else ""
                st.markdown(f"**{'2 · Espacio' if ES else '2 · Space'} {s+1}{star} — {'elige color:' if ES else 'choose colour:'}**")
                avail = [m for m in moves if m[1] == s]
                types = list(dict.fromkeys(m[0] for m in avail))
                lab = {"black":f"⚫ {pc['black']}", "white":f"🟡 {pc['white']}", "blue":f"🔵 {pc['blue']}"}
                cc = st.columns(len(types) + (0 if len(spaces) == 1 else 1))
                for i, t in enumerate(types):
                    with cc[i]:
                        if st.button(lab[t], key=f"c{t}", use_container_width=True):
                            m = next(x for x in avail if x[0] == t)
                            do_play(G, m[0], m[1], m[2], mode)
                            st.session_state.pop("sel_space", None); st.rerun()
                if len(spaces) > 1:
                    with cc[-1]:
                        if st.button("✕", key="cancel", use_container_width=True):
                            st.session_state.pop("sel_space", None); st.rerun()
        elif human and not moves:
            st.warning("Sin movimientos." if ES else "No moves.")
        else:
            st.info("🤖 " + ("La IA está pensando…" if ES else "AI thinking…"), icon="⏳")
            time.sleep(0.6); ai_move(G, mode)
            st.session_state.pop("sel_space", None); st.rerun()

    # resultado
    if G["over"]:
        w = G["winner"]; rz = G["win_reason"]
        rtxt = (" · " + ("llegó al centro" if ES else "reached the center")) if rz == "center" \
               else (" · " + ("sin pelotas" if ES else "out of beads"))
        if G["teams"]:
            A = G["scores"][0] + G["scores"][2]; B = G["scores"][1] + G["scores"][3]
            title = ("¡Gana el equipo " if ES else "Team ") + ("A!" if w == 0 else "B!") + " 🎉"
            desc = f"A: {A} — B: {B}{rtxt}"
        elif w == -1:
            title = "¡Empate!" if ES else "Tie!"
            desc = " · ".join(f"{player_label(G,p,mode)}: {G['scores'][p]}" for p in range(G["np"])) + rtxt
        else:
            title = f"¡{player_label(G, w, mode)} " + ("gana!" if ES else "wins!") + " 🎉"
            desc = " · ".join(f"{player_label(G,p,mode)}: {G['scores'][p]}" for p in range(G["np"])) + rtxt
        st.markdown(f'<div class="winner-box"><div class="winner-title">{title}</div><div class="winner-scores">{desc}</div></div>',
                    unsafe_allow_html=True)

    if G["log"]:
        st.markdown("#### " + ("Historial" if ES else "Game log"))
        ent = ""
        for e in reversed(G["log"][-40:]):
            c = PCOLOR[e.get("p", 0)]
            pts = f' <span class="log-pts">+{e["pts"]}</span>' if e["pts"] else ""
            ent += f'<div class="log-entry"><span style="color:#bbb;">#{e["t"]}</span> <b style="color:{c};">{e["who"]}</b> {e["msg"]}{pts}</div>'
        st.markdown(f'<div class="log-container">{ent}</div>', unsafe_allow_html=True)
