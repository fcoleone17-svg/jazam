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

# Colores: todos contra todos vs parejas (bandos por familia de color)
COL_FFA  = ["#FF6B00", "#00C8FF", "#22A022", "#C044D0"]
COL_TEAM = ["#FF6B00", "#0A84FF", "#FFB000", "#00C8FF"]   # A: naranjas · B: azules
PNAME    = ["12:00", "3:00", "6:00", "9:00"]

def pcolor(G, p):
    return (COL_TEAM if G["teams"] else COL_FFA)[p]

def team_of(p): return p % 2

def cfg(G):
    if G["variant"] == "classic":
        return {"cel": CEL_CARD, "arch": True, "open": False}
    return {"cel": CEL_X, "arch": False, "open": True}

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
    return None

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
        np_ = 2; teams = False
        pieces = [{"black":20,"white":6,"blue":2} for _ in range(2)]
        origins = [0]
    elif np_ == 2:
        pieces = [{"black":24,"white":6,"blue":2} for _ in range(2)]
        origins = [0, 16]
    else:
        pieces = [{"black":12,"white":3,"blue":1} for _ in range(4)]
        origins = [0, 8, 16, 24]
    return {
        "variant": variant, "np": np_, "teams": teams, "origins": origins,
        "cp": 0, "scores": [0]*np_, "pieces": pieces,
        "board": [[None]*n for n in LEVELS],
        "lv": 0,          # classic: nivel activo · dynamic: nivel más alto abierto
        "ptr_cw": 1, "ptr_ccw": LEVELS[0]-1,          # classic
        "toll_cw": False, "toll_ccw": False, "toll_lv": None,
        "toll_at": set(),                              # dynamic: {(lv, si), ...}
        "toll_pending": None,                          # 2ª pelota: dir (classic) o (lv,si)
        "forced": None,                                # (lv, si)
        "seeded": [False]*np_, "started": False,
        "out": [False]*np_,
        "last_was_blue": False,
        "over": False, "winner": None, "win_reason": None,
        "log": [], "turn_count": 0, "_es": True,
    }

def next_cp(G):
    """Siguiente jugador. En el duelo de 2 se usa orden serpiente
    (J1·J2·J2·J1·J1…) para romper la paridad de los celestes en X.
    Con 3 o más la rotación normal ya la rompe."""
    n = G["np"]
    if n == 2 and G["variant"] != "classic":
        G["_sn"] = G.get("_sn", 0) + 1
        seq = [0, 1, 1, 0]
        return seq[G["_sn"] % 4]
    for step in range(1, n+1):
        c = (G["cp"] + step) % n
        if not G["out"][c]: return c
    return G["cp"]

def alive(G):
    return [p for p in range(G["np"]) if not G["out"][p]]

def find_free(G, direction):
    lv = G["lv"]; n = LEVELS[lv]; b = G["board"][lv]
    si = (G["ptr_cw"] if direction == "cw" else G["ptr_ccw"]) % n
    for _ in range(n):
        if b[si] is None: return si
        si = (si+1) % n if direction == "cw" else (si-1) % n
    return None

def add_log(G, who, msg, pts=0, lv=None, si=None, t=None):
    G["turn_count"] += 1
    G["log"].append({"t":G["turn_count"], "who":who, "msg":msg, "pts":pts,
                     "p":G["cp"], "lv":lv, "si":si, "bead":t})

# ══════════════════════════ MOVIMIENTOS ══════════════════════════
def toll_here(G, lv, space, meta):
    """¿Esta colocación paga la 1ª pelota del peaje (pierde propiedades)?"""
    if G["toll_pending"] is not None: return False
    if G["variant"] == "classic":
        if G["toll_lv"] != lv: return False
        if meta == "cw":  return G["toll_cw"]
        if meta == "ccw": return G["toll_ccw"]
        return False
    return (lv, space) in G["toll_at"]

def valid_moves(G):
    """Lista de (tipo, nivel, espacio, meta)."""
    cp = G["cp"]; pc = G["pieces"][cp]
    if pc["black"] <= 0 and pc["white"] <= 0 and pc["blue"] <= 0: return []

    seed = False
    slots = []      # (lv, space, meta)

    if G["variant"] == "classic":
        lv = G["lv"]
        if not G["started"]:
            slots = [(0, 0, "start")]; seed = True
        elif G["forced"] is not None:
            slots = [(G["forced"][0], G["forced"][1], "forced")]
        elif G["toll_pending"] is not None:
            t = find_free(G, G["toll_pending"])
            if t is not None: slots = [(lv, t, G["toll_pending"])]
        else:
            seen = set()
            for d in ("cw", "ccw"):
                t = find_free(G, d)
                if t is None or t in seen: continue
                seen.add(t); slots.append((lv, t, d))
    else:
        if not G["seeded"][cp] and G["board"][0][G["origins"][cp]] is None:
            slots = [(0, G["origins"][cp], "seed")]; seed = True
        elif G["forced"] is not None:
            slots = [(G["forced"][0], G["forced"][1], "forced")]
        elif G["toll_pending"] is not None:
            slots = [(G["toll_pending"][0], G["toll_pending"][1], "second")]
        else:
            # todos los niveles abiertos siguen jugables
            for lv in range(G["lv"] + 1):
                for s in frontier(G["board"], lv):
                    slots.append((lv, s, "free"))
            if not slots:
                for lv in range(G["lv"] + 1):
                    for s, x in enumerate(G["board"][lv]):
                        if x is None: slots.append((lv, s, "free"))

    moves = []
    for lv, s, meta in slots:
        if pc["black"] > 0: moves.append(("black", lv, s, meta))
        if pc["white"] > 0: moves.append(("white", lv, s, meta))
        # la azul se ofrece siempre (sobre un peaje se malgasta: es decisión del jugador)
        if pc["blue"] > 0 and not G["last_was_blue"] and not seed:
            moves.append(("blue", lv, s, meta))
    return moves

# ══════════════════════════ JUGADA ══════════════════════════
def open_next_level(G, lv, from_si):
    """Abre el nivel lv+1 y devuelve (nivel, espacio de entrada) o None."""
    if lv >= 5: return None
    e = entry_space(G["board"], lv, from_si, lv+1)
    if e is None: return None
    if lv + 1 > G["lv"]: G["lv"] = lv + 1
    if G["variant"] == "classic":
        n = LEVELS[lv+1]
        G["ptr_cw"] = (e+1) % n; G["ptr_ccw"] = (e-1) % n
        G["toll_cw"] = G["toll_ccw"] = False; G["toll_lv"] = None
        G["lv"] = lv + 1
    return (lv+1, e)

def level_done(G, lv, cp, who, ES, from_si):
    """Bono (si corresponde) y apertura del siguiente nivel al completar uno."""
    if not all(x is not None for x in G["board"][lv]): return None
    if cfg(G)["arch"] and lv <= 2:
        G["scores"][cp] += 4
        add_log(G, who, f"Nv{lv+1} completo +4" if ES else f"Lv{lv+1} complete +4", 4)
    if lv + 1 > G["lv"] or G["variant"] == "classic":
        return open_next_level(G, lv, from_si)
    return None

def do_play(G, ptype, lv, space, meta, mode):
    if G["over"]: return
    cp = G["cp"]; pc = G["pieces"][cp]; ES = G["_es"]
    who = player_label(G, cp, mode)
    tn = {"black":"negra" if ES else "black",
          "white":"blanca" if ES else "white",
          "blue":"azul" if ES else "blue"}[ptype]
    lvtag = f"Nv{lv+1}·" if cfg(G)["open"] else ""

    paying = toll_here(G, lv, space, meta)
    second = (G["toll_pending"] is not None)
    pc[ptype] -= 1
    if meta == "seed":   G["seeded"][cp] = True; G["started"] = True
    if meta == "start":  G["started"] = True
    if meta == "forced": G["forced"] = None

    # ─── AZUL con propiedades ───
    if ptype == "blue" and not paying:
        cel = is_cel(G, lv, space)
        pts = space_pts(G, lv, space) if cel else 0
        G["scores"][cp] += pts
        G["board"][lv][space] = {"p":cp, "t":"blue", "neu":False}
        if second: G["toll_pending"] = None
        if G["variant"] == "classic" and meta in ("cw","ccw"):
            n = LEVELS[lv]
            if meta == "cw": G["ptr_cw"] = (space+1) % n
            else: G["ptr_ccw"] = (space-1) % n
        if cel and lv < 5:
            nxt = open_next_level(G, lv, space)
            add_log(G, who, f"{tn} {lvtag}{space+1} +{pts} → Nv{lv+2}", pts, lv, space, ptype)
            G["last_was_blue"] = True
            G["forced"] = nxt
            if nxt is None: G["cp"] = next_cp(G)
            check_end(G, mode); return                # repite turno
        add_log(G, who, f"{tn} {lvtag}{space+1}" + (f" +{pts}" if pts else ""), pts, lv, space, ptype)
        G["last_was_blue"] = False
        f = level_done(G, lv, cp, who, ES, space)
        if f: G["forced"] = f
        G["cp"] = next_cp(G)
        check_end(G, mode); return

    # ─── Pieza normal (o azul neutralizada por peaje) ───
    eff = "black" if paying else ptype
    G["board"][lv][space] = {"p":cp, "t":ptype, "neu":paying}
    G["last_was_blue"] = False
    note = " ·peaje" if paying else ""
    add_log(G, who, f"{tn} {lvtag}{space+1}{note}", 0, lv, space, ptype)

    if G["variant"] == "classic":
        n = LEVELS[lv]
        if meta == "start":
            G["ptr_cw"] = 1; G["ptr_ccw"] = n-1
            G["toll_cw"] = G["toll_ccw"] = False; G["toll_lv"] = None
        elif meta == "forced":
            G["ptr_cw"] = (space+1) % n; G["ptr_ccw"] = (space-1) % n
        elif meta == "cw":  G["ptr_cw"] = (space+1) % n
        elif meta == "ccw": G["ptr_ccw"] = (space-1) % n

    # 1ª pelota del peaje → el mismo jugador coloca la 2ª
    if paying:
        if G["variant"] == "classic":
            if meta == "cw": G["toll_cw"] = False
            else: G["toll_ccw"] = False
            nxt = meta
        else:
            G["toll_at"].discard((lv, space))
            nb = empty_neighbor(G["board"], lv, space)
            nxt = (lv, nb) if nb is not None else None
        f = level_done(G, lv, cp, who, ES, space)
        if f:
            G["toll_pending"] = f if G["variant"] != "classic" else nxt
            if G["variant"] == "classic": G["forced"] = f
            check_end(G, mode); return
        G["toll_pending"] = nxt
        if nxt is None: G["cp"] = next_cp(G)
        check_end(G, mode); return

    if second: G["toll_pending"] = None

    if eff == "white":
        if G["variant"] == "classic":
            if meta in ("cw", "ccw"):
                if meta == "cw": G["toll_cw"] = True
                else: G["toll_ccw"] = True
            else:
                G["toll_cw"] = G["toll_ccw"] = True
            G["toll_lv"] = lv
        else:
            for nb in neighbors(lv, space):
                if G["board"][lv][nb] is None:
                    G["toll_at"].add((lv, nb))

    f = level_done(G, lv, cp, who, ES, space)
    if f: G["forced"] = f
    G["cp"] = next_cp(G)
    check_end(G, mode)

def check_end(G, mode):
    ES = G["_es"]
    # ── centro: +12 y fin de partida ──
    if G["board"][5][0] is not None and not G["board"][5][0].get("scored"):
        w = G["board"][5][0]["p"]
        G["scores"][w] += CENTER_PTS
        G["board"][5][0]["scored"] = True
        add_log(G, player_label(G, w, mode), "¡CENTRO! +12" if ES else "CENTER! +12", CENTER_PTS)
        G["over"] = True; G["win_reason"] = "center"
        G["winner"] = best_by_points(G)
        return
    # ── sin piezas: derrota (2 jugadores) o eliminación (3+) ──
    for _ in range(G["np"] + 1):
        cp = G["cp"]; pc = G["pieces"][cp]
        empty = (pc["black"] <= 0 and pc["white"] <= 0 and pc["blue"] <= 0)
        if not empty and valid_moves(G): return
        if G["np"] == 2:
            G["over"] = True; G["win_reason"] = "nopcs"
            add_log(G, player_label(G, cp, mode), "sin piezas" if ES else "out of beads", 0)
            G["winner"] = resolve_exhaust(G, cp); return
        G["out"][cp] = True
        add_log(G, player_label(G, cp, mode),
                "eliminado · sin piezas" if ES else "eliminated · out of beads", 0)
        liv = alive(G)
        if len(liv) <= 1:
            G["over"] = True; G["win_reason"] = "nopcs"
            G["winner"] = (team_of(liv[0]) if G["teams"] else liv[0]) if liv else best_by_points(G)
            return
        G["cp"] = next_cp(G)

def depth_score(G, p):
    """Desempate: cuánto se adentró cada jugador (pelotas × profundidad)."""
    return sum((lv+1) for lv in range(6) for x in G["board"][lv]
               if x is not None and x["p"] == p)

def pick_best(G, pool):
    """Del grupo dado, el de más puntos; empate → el que llegó más adentro."""
    if not pool: return -1
    best = max(G["scores"][p] for p in pool)
    tied = [p for p in pool if G["scores"][p] == best]
    if len(tied) == 1: return tied[0]
    d = max(depth_score(G, p) for p in tied)
    tied2 = [p for p in tied if depth_score(G, p) == d]
    return tied2[0] if len(tied2) == 1 else -1

def best_by_points(G):
    if G["teams"]:
        a = G["scores"][0] + G["scores"][2]; b = G["scores"][1] + G["scores"][3]
        if a != b: return 0 if a > b else 1
        da = depth_score(G,0) + depth_score(G,2); db = depth_score(G,1) + depth_score(G,3)
        return 0 if da > db else (1 if db > da else -1)
    pool = alive(G) or list(range(G["np"]))   # los eliminados no pueden ganar
    return pick_best(G, pool)

def resolve_exhaust(G, loser):
    if G["teams"]: return 1 - team_of(loser)
    return pick_best(G, [p for p in range(G["np"]) if p != loser])

def player_label(G, p, mode):
    ES = G["_es"]
    if mode == "ai" and p > 0:
        return ("IA" if ES else "AI") + (str(p) if G["np"] > 2 else "")
    return f"J{p+1}"

# ══════════════════════════ IA ══════════════════════════
def ai_move(G, mode):
    mv = valid_moves(G)
    if not mv: return
    b = G["board"]
    def cels(lv): return cfg(G)["cel"].get(lv, {})

    take = [m for m in mv if m[0]=="blue" and m[2] in cels(m[1])
            and not toll_here(G, m[1], m[2], m[3])]
    if take:
        take.sort(key=lambda m: -space_pts(G, m[1], m[2]))
        m = take[0]; do_play(G, *m, mode); return
    block = [m for m in mv if m[0]=="black" and m[2] in cels(m[1])]
    if block:
        block.sort(key=lambda m: -space_pts(G, m[1], m[2]))
        m = block[0]; do_play(G, *m, mode); return
    poison = []
    for m in mv:
        if m[0] != "white": continue
        nb = empty_neighbor(b, m[1], m[2])
        if nb is not None and nb in cels(m[1]): poison.append(m)
    if poison:
        m = poison[0]; do_play(G, *m, mode); return
    blacks = [m for m in mv if m[0]=="black"]
    if blacks:
        def score(m):
            lv, s = m[1], m[2]; n = LEVELS[lv]
            free = [c for c in cels(lv) if b[lv][c] is None]
            d = min((min((s-c) % n, (c-s) % n) for c in free), default=99)
            near_done = sum(1 for x in b[lv] if x is None)
            return (d, near_done)
        blacks.sort(key=score)
        m = blacks[0]; do_play(G, *m, mode); return
    import random as _r
    m = _r.choice(mv); do_play(G, *m, mode)

# ══════════════════════════ TABLERO ══════════════════════════
def render_board_svg(G, options=None, chosen=None, recent=None):
    options = set(options or [])
    recent = recent or []   # [(lv, si, color, orden)]
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
    axis = [0,1,2,3] if G["variant"] == "classic" else [0.5,1.5,2.5,3.5]
    for i in axis:
        a = -math.pi/2 + i*math.pi/2
        L.append(f'<line x1="{cx+18*math.cos(a):.1f}" y1="{cy+18*math.sin(a):.1f}" x2="{cx+(cx-8)*math.cos(a):.1f}" y2="{cy+(cx-8)*math.sin(a):.1f}" stroke="rgba(120,90,40,0.14)" stroke-width="0.8" stroke-dasharray="2,5"/>')
    for i in range(12):
        a = -math.pi/2 + i*math.pi/6; r1 = cx-6; r2 = r1-(5 if i%3==0 else 3)
        L.append(f'<line x1="{cx+r1*math.cos(a):.1f}" y1="{cy+r1*math.sin(a):.1f}" x2="{cx+r2*math.cos(a):.1f}" y2="{cy+r2*math.sin(a):.1f}" stroke="rgba(120,90,40,0.22)" stroke-width="{1.5 if i%3==0 else 0.7}"/>')

    forced = G.get("forced")
    for li in range(6):
        n = LEVELS[li]; r_dot = 22 if li == 5 else 10
        for si in range(n):
            if li == 5: x, y = cx, cy
            else:
                a = -math.pi/2 + (si/n)*math.pi*2
                x = cx + radii[li]*math.cos(a); y = cy + radii[li]*math.sin(a)
            cel = is_cel(G, li, si); cell = G["board"][li][si]
            opt = ((li, si) in options and cell is None)
            sel = (chosen == (li, si) and cell is None)
            frc = (forced is not None and forced == (li, si) and cell is None and not G["over"])

            if li == 5 and cell is None and (li,si) not in options:
                fill,stroke,sw = "#DDF0CC","#3B6D11",2
            elif sel:   fill,stroke,sw = "rgba(34,160,34,0.45)","#22A022",3.5
            elif frc:   fill,stroke,sw = "rgba(59,109,17,0.30)","#3B6D11",3
            elif opt:   fill,stroke,sw = "rgba(255,107,0,0.22)","#FF6B00",2.5
            elif cel:   fill,stroke,sw = "#C5E8FF","#185FA5",1.5
            elif li == 5: fill,stroke,sw = "#DDF0CC","#3B6D11",2
            else:       fill,stroke,sw = "rgba(80,60,20,0.05)","rgba(80,60,20,0.15)",0.7
            L.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r_dot}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

            if (opt or sel) and li < 5:
                L.append(f'<text x="{x:.1f}" y="{y+3:.1f}" text-anchor="middle" font-size="9" font-weight="600" fill="#7A3B00" font-family="DM Sans,sans-serif">{si+1}</text>')
            elif cel and not cell and not frc:
                L.append(f'<text x="{x:.1f}" y="{y+3:.1f}" text-anchor="middle" font-size="{7 if li==0 else 8}" fill="#0C447C" font-family="DM Sans,sans-serif">{space_pts(G,li,si)}</text>')
            if li == 5 and G["board"][5][0] is None and not opt and not sel:
                L.append(f'<text x="{cx}" y="{cy+5}" text-anchor="middle" font-size="12" font-weight="600" fill="#27500A" font-family="DM Sans,sans-serif">{CENTER_PTS}</text>')

            if cell:
                t = cell["t"]; neu = cell.get("neu", False); pr = r_dot-2.5
                if neu or t == "black": pf, ps = "#111110", "#999990"
                elif t == "white":      pf, ps = "#E8D44D", "#B89A10"
                else:                   pf, ps = "#378ADD", "#185FA5"
                L.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{pr}" fill="{pf}" stroke="{ps}" stroke-width="1.5"/>')
                L.append(f'<circle cx="{x:.1f}" cy="{y+pr-2:.1f}" r="2.0" fill="{pcolor(G, cell["p"])}"/>')

    # halos de las jugadas recientes (lo que pasó desde tu último turno)
    for (rlv, rsi, rcol, rord) in recent:
        if rlv == 5: hx, hy, hr = cx, cy, 22
        else:
            aa = -math.pi/2 + (rsi/LEVELS[rlv])*math.pi*2
            hx = cx + radii[rlv]*math.cos(aa); hy = cy + radii[rlv]*math.sin(aa); hr = 10
        L.append(f'<circle cx="{hx:.1f}" cy="{hy:.1f}" r="{hr+4.5}" fill="none" stroke="{rcol}" stroke-width="2.5" opacity="0.95"/>')
        bx = hx + (hr+4.5)*0.72; by = hy - (hr+4.5)*0.72
        L.append(f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="6" fill="{rcol}"/>')
        L.append(f'<text x="{bx:.1f}" y="{by+3.2:.1f}" text-anchor="middle" font-size="8.5" font-weight="700" fill="#fff" font-family="DM Sans,sans-serif">{rord}</text>')

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
    if G["np"] == 4: mx = {"black":12, "white":3, "blue":1}
    elif G["variant"] == "classic": mx = {"black":20, "white":6, "blue":2}
    else: mx = {"black":24, "white":6, "blue":2}
    rows = ""
    for t, col in [("black","#111110"), ("white","#E8D44D"), ("blue","#378ADD")]:
        rows += f'<div>{dots(pc[t], mx[t], col)}<small style="color:#888;font-size:0.65rem;">{pc[t]}</small></div>'
    return rows

# ══════════════════════════ APP ══════════════════════════
if "game" not in st.session_state:
    st.session_state.game = init_game("dynamic", 2)
    st.session_state.mode = "ai"
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
    vn = "clásico" if ES else "classic"
elif G["teams"]:
    vn = "Duel · " + ("parejas" if ES else "teams")
elif G["np"] > 2:
    vn = f"Duel · {G['np']} " + ("jugadores" if ES else "players")
else:
    vn = "Duel · 2"
st.markdown(f'<div class="jazam-subtitle">{"meditación competitiva" if ES else "competitive meditation"} · {vn}</div>',
            unsafe_allow_html=True)

tab_game, tab_rules = st.tabs(["🎮 " + ("Juego" if ES else "Game"),
                               "📖 " + ("Reglas" if ES else "Rules")])

# ─────────────────────────── REGLAS ───────────────────────────
with tab_rules:
    st.divider()
    if ES:
        st.markdown("### Dos juegos, un tablero")
        c1, c2 = st.columns(2)
        with c1: st.markdown('<div class="rule-box"><b>⚔️ Jazam Duel</b><br><small>Frentes dinámicos · celestes en X · todos los niveles abiertos · hasta 4 jugadores, solos o en parejas.</small></div>', unsafe_allow_html=True)
        with c2: st.markdown('<div class="rule-box"><b>🔵 Jazam clásico</b><br><small>Dos frentes desde 12:00 · celestes en 12/3/6/9 · un nivel a la vez · bono del arquitecto · 2 jugadores.</small></div>', unsafe_allow_html=True)
        st.divider()
        st.markdown("### El tablero")
        ca, cb = st.columns(2)
        with ca:
            st.markdown("| Nivel | Espacios |\n|---|---|\n| 1 (exterior) | 32 |\n| 2 | 16 |\n| 3 | 8 |\n| 4 | 4 |\n| 5 | 2 |\n| 6 — Centro | 1 |")
        with cb:
            st.markdown("**Duel:** cada jugador siembra su primera pelota en su origen (12:00, 3:00, 6:00 o 9:00). Después juegas en **cualquier espacio vacío que toque una pelota ya puesta** — y los niveles ya abiertos **siguen disponibles**, así que puedes volver atrás a completar puntos.\n\n**Clásico:** dos frentes avanzan ↻ y ↺ desde 12:00, un nivel a la vez.")
        st.divider()
        st.markdown("### Las pelotas")
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown('<div class="rule-box" style="text-align:center;"><b>⚫ Negra</b><br><small>Ocupa un espacio. Nada más.</small></div>', unsafe_allow_html=True)
        with c2: st.markdown('<div class="rule-box" style="text-align:center;"><b>🟡 Blanca</b><br><small>Deja un peaje en el espacio siguiente.</small></div>', unsafe_allow_html=True)
        with c3: st.markdown('<div class="rule-box" style="text-align:center;"><b>🔵 Azul</b><br><small>Va en cualquier espacio · solo en celeste puntúa, abre el nivel siguiente y repite turno.</small></div>', unsafe_allow_html=True)
        st.markdown('<div class="rule-box">🟡 <b>El peaje:</b> después de una blanca, el próximo que juegue en el espacio marcado pone 2 pelotas. Ojo: la primera no cuenta — solo ocupa el espacio. La segunda es la que realmente juega.<br><br><b>Ejemplo:</b> la blanca queda justo antes de un celeste. El siguiente jugador pone su primera pelota ahí — pero no tiene efecto (aunque sea azul, no sube de nivel ni puntúa). La segunda es la que juega normalmente.</div>', unsafe_allow_html=True)
        st.markdown("*No se pueden jugar dos azules seguidas.*")
        st.markdown('<div class="rule-box">🔄 <b>Orden de turnos.</b> En el <b>duelo de 2</b> se juega en serpiente: J1 · J2 · J2 · J1 · J1 · J2… Los celestes están a la misma distancia de los dos orígenes, y con turnos alternos simples caerían siempre del mismo lado. Con <b>3 o más jugadores</b> el turno rota normalmente.</div>', unsafe_allow_html=True)
        st.divider()
        st.markdown("### Puntuación")
        st.markdown("| Nivel | Celestes | Puntos |\n|---|---|---|\n| 1 | los cuatro | 9 |\n| 2 | los cuatro | 6 |\n| 3 | los cuatro | 3 |\n| 6 | centro | 12 |")
        st.markdown('<div class="rule-box">🏛️ <b>Bono del Arquitecto (+4)</b> — solo en <b>Jazam clásico</b>: completar un nivel del 1 al 3.</div>', unsafe_allow_html=True)
        st.divider()
        st.markdown("### Fin del juego")
        st.markdown('<div class="rule-box">Llegar al <b>centro</b> da +12 y <b>termina la partida</b> — pero no gana por sí solo: gana quien tenga <b>más puntos</b>.<br><br><b>En el duelo de 2:</b> quien se queda sin pelotas en su turno pierde.<br><br><b>Con 3 o más:</b> quien se queda sin pelotas queda <b>eliminado</b> y su turno se salta, pero la partida sigue. Los eliminados ya no pueden ganar; entre los que quedan, gana quien tenga más puntos.</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;margin-top:2rem;font-style:italic;color:#BA7517;">"Jazam no es un juego… es una meditación competitiva."</div>', unsafe_allow_html=True)
    else:
        st.markdown("### Two games, one board")
        c1, c2 = st.columns(2)
        with c1: st.markdown('<div class="rule-box"><b>⚔️ Jazam Duel</b><br><small>Dynamic fronts · X celestials · all levels stay open · up to 4 players, solo or in teams.</small></div>', unsafe_allow_html=True)
        with c2: st.markdown('<div class="rule-box"><b>🔵 Jazam classic</b><br><small>Two fronts from 12:00 · celestials at 12/3/6/9 · one level at a time · architect bonus · 2 players.</small></div>', unsafe_allow_html=True)
        st.divider()
        st.markdown("### The board")
        ca, cb = st.columns(2)
        with ca:
            st.markdown("| Level | Spaces |\n|---|---|\n| 1 (outer) | 32 |\n| 2 | 16 |\n| 3 | 8 |\n| 4 | 4 |\n| 5 | 2 |\n| 6 — Center | 1 |")
        with cb:
            st.markdown("**Duel:** each player seeds their first bead at their origin. After that you play on **any empty space touching a placed bead** — and levels already opened **stay available**, so you can go back for points.\n\n**Classic:** two fronts advance ↻ and ↺ from 12:00, one level at a time.")
        st.divider()
        st.markdown("### The beads")
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown('<div class="rule-box" style="text-align:center;"><b>⚫ Black</b><br><small>Fills a space. Nothing else.</small></div>', unsafe_allow_html=True)
        with c2: st.markdown('<div class="rule-box" style="text-align:center;"><b>🟡 White</b><br><small>Leaves a toll on the next space.</small></div>', unsafe_allow_html=True)
        with c3: st.markdown('<div class="rule-box" style="text-align:center;"><b>🔵 Blue</b><br><small>Any space · only on a celestial does it score, open the next level and repeat turn.</small></div>', unsafe_allow_html=True)
        st.markdown('<div class="rule-box">🟡 <b>The toll:</b> after a white, the next player to use the marked space places 2 beads. The first doesn\'t count — it just fills the space. The second is the one that really plays.</div>', unsafe_allow_html=True)
        st.markdown("*Two blues cannot be played in a row.*")
        st.markdown('<div class="rule-box">🔄 <b>Turn order.</b> In the <b>2-player duel</b>, play snakes: P1 · P2 · P2 · P1 · P1 · P2… With <b>3+ players</b> turns rotate normally.</div>', unsafe_allow_html=True)
        st.divider()
        st.markdown("### Scoring")
        st.markdown("| Level | Celestials | Points |\n|---|---|---|\n| 1 | all four | 9 |\n| 2 | all four | 6 |\n| 3 | all four | 3 |\n| 6 | center | 12 |")
        st.markdown('<div class="rule-box">🏛️ <b>Architect Bonus (+4)</b> — <b>Jazam classic</b> only: complete a level from 1 to 3.</div>', unsafe_allow_html=True)
        st.divider()
        st.markdown("### End of game")
        st.markdown('<div class="rule-box">Reaching the <b>center</b> scores +12 and <b>ends the game</b> — but doesn\'t win by itself: <b>most points wins</b>.<br><br><b>In the 2-player duel:</b> a player with no beads on their turn loses.<br><br><b>With 3+:</b> that player is <b>eliminated</b> and skipped, but the game continues. Eliminated players cannot win; among the rest, most points wins.</div>', unsafe_allow_html=True)

# ─────────────────────────── JUEGO ───────────────────────────
with tab_game:
    fresh = (G["turn_count"] == 0)
    with st.expander("⚙️ " + ("Configurar partida" if ES else "Set up game"), expanded=fresh):
        v = st.radio("Juego" if ES else "Game",
                     ["⚔️ Jazam Duel", "🔵 " + ("Jazam clásico" if ES else "Jazam classic")],
                     index=0 if G["variant"] == "dynamic" else 1, horizontal=True)
        is_duel = v.startswith("⚔️")
        opp = st.radio("¿Contra quién?" if ES else "Opponent",
                       ["👤 " + ("Otro jugador" if ES else "Another player"), "🤖 IA" if ES else "🤖 AI"],
                       index=0 if mode == "2p" else 1, horizontal=True)
        vs_ai = opp.startswith("🤖")
        n_extra = 1; team_mode = False
        if is_duel:
            lbl = ("¿Cuántas IA?" if vs_ai else "¿Cuántos jugadores más?") if ES \
                  else ("How many AIs?" if vs_ai else "How many more players?")
            n_extra = st.radio(lbl, [1, 3], index=0 if G["np"] == 2 else 1, horizontal=True)
            if n_extra == 3:
                tm = st.radio("Modo" if ES else "Mode",
                              ["⚔️ " + ("Todos contra todos" if ES else "Free for all"),
                               "🤝 " + ("Parejas" if ES else "Teams")],
                              index=1 if G["teams"] else 0, horizontal=True)
                team_mode = tm.startswith("🤝")
                if team_mode:
                    st.caption(("Equipo A: 12:00 + 6:00 (naranjas) · Equipo B: 3:00 + 9:00 (azules)")
                               if ES else "Team A: 12:00 + 6:00 (orange) · Team B: 3:00 + 9:00 (blue)")
        if st.button("▶ " + ("Empezar" if ES else "Start"), use_container_width=True, type="primary"):
            variant = "dynamic" if is_duel else "classic"
            npl = (n_extra + 1) if is_duel else 2
            st.session_state.game = init_game(variant, npl, team_mode)
            st.session_state.mode = "ai" if vs_ai else "2p"
            st.session_state.pop("sel", None)
            st.rerun()

    G = st.session_state.game; mode = st.session_state.mode; G["_es"] = ES

    # marcadores
    cols = st.columns(G["np"])
    for p in range(G["np"]):
        with cols[p]:
            act = (G["cp"] == p and not G["over"])
            col = pcolor(G, p)
            bord = f"border:2px solid {col};" if act else ""
            nm = player_label(G, p, mode)
            if G["np"] == 4:
                nm += f" · {PNAME[p]}"
                if G["teams"]: nm = ("A · " if p % 2 == 0 else "B · ") + nm
            st.markdown(f"""<div class="score-box" style="{bord}">
              <div class="score-name" style="color:{col};">{nm}</div>
              <div class="score-pts">{G['scores'][p]}<span>pts</span></div>
              <div>{pieces_html(G, p)}</div></div>""", unsafe_allow_html=True)

    if G["teams"]:
        A = G["scores"][0] + G["scores"][2]; B = G["scores"][1] + G["scores"][3]
        st.markdown(f'<div class="status-bar"><b style="color:{COL_TEAM[0]}">A {A}</b> — <b style="color:{COL_TEAM[1]}">{B} B</b></div>',
                    unsafe_allow_html=True)

    # jugadas ocurridas desde la última del jugador que ahora mira el tablero
    viewer = G["cp"]
    placements = [e for e in G["log"] if e.get("si") is not None]
    cut = 0
    for i in range(len(placements)-1, -1, -1):
        if placements[i]["p"] == viewer: cut = i+1; break
    since = placements[cut:] if not G["over"] else placements[-4:]
    recent = [(e["lv"], e["si"], pcolor(G, e["p"]), k+1) for k, e in enumerate(since)]

    moves = valid_moves(G) if not G["over"] else []
    slots = sorted({(m[1], m[2]) for m in moves})
    multi_lv = len({s[0] for s in slots}) > 1
    sel = st.session_state.get("sel")
    if sel is not None and tuple(sel) not in slots:
        sel = None; st.session_state.pop("sel", None)
    sel = tuple(sel) if sel else None

    if not G["over"]:
        cp = G["cp"]; nm = player_label(G, cp, mode); col = pcolor(G, cp)
        if G["variant"] != "classic" and not G["seeded"][cp]:
            cls, txt = "status-bar first", f"🟢 <b>{nm}</b> — {'siembra en' if ES else 'seed at'} {PNAME[cp]}"
        elif G["forced"] is not None:
            cls, txt = "status-bar first", f"🟢 <b>{nm}</b> — {'entra al Nv' if ES else 'enters Lv'}{G['forced'][0]+1}"
        elif G["toll_pending"] is not None:
            cls, txt = "status-bar", f"<b>{nm}</b> — {'2ª pelota del peaje' if ES else '2nd toll bead'}"
        elif not moves:
            cls, txt = "status-bar warning", f"⚠️ <b>{nm}</b> — {'sin movimientos' if ES else 'no moves'}"
        elif any(is_cel(G, lv, s) for lv, s in slots):
            cls, txt = "status-bar celestial", f"★ <b>{nm}</b> — {'celeste disponible' if ES else 'celestial available'}"
        else:
            cls, txt = "status-bar", f"<b style='color:{col}'>{nm}</b> — {len(slots)} {'opciones' if ES else 'options'}"
        st.markdown(f'<div class="{cls}">{txt}</div>', unsafe_allow_html=True)

    if since and (G["np"] > 2 or mode == "ai"):
        ico = {"black":"⚫", "white":"🟡", "blue":"🔵"}
        chips = ""
        for k, e in enumerate(since):
            c = pcolor(G, e["p"])
            pts = f' +{e["pts"]}' if e.get("pts") else ""
            loc = f'Nv{e["lv"]+1}·{e["si"]+1}' if e["lv"] < 5 else ("centro" if ES else "center")
            chips += (f'<span style="display:inline-block;background:{c}1A;border:1px solid {c};'
                      f'border-radius:12px;padding:1px 8px;margin:2px 3px 2px 0;font-size:0.72rem;color:#333;">'
                      f'<b style="color:{c};">{k+1}</b> {e["who"]} {ico.get(e.get("bead"),"")} {loc}{pts}</span>')
        lbl = ("Desde tu turno:" if ES else "Since your turn:")
        st.markdown(f'<div style="font-size:0.72rem;color:#888;margin:2px 0 0 2px;">{lbl}</div>'
                    f'<div style="margin-bottom:2px;">{chips}</div>', unsafe_allow_html=True)

    st.markdown(f'<div style="width:100%;max-width:440px;margin:6px auto;">{render_board_svg(G, slots, sel, recent)}</div>',
                unsafe_allow_html=True)

    if not G["over"]:
        cp = G["cp"]
        human = not (mode == "ai" and cp > 0)
        if human and moves:
            pc = G["pieces"][cp]
            if sel is None:
                if len(slots) == 1:
                    st.session_state.sel = slots[0]; st.rerun()
                st.markdown(f"**{'1 · Elige espacio:' if ES else '1 · Choose space:'}**")
                per = 4
                for i in range(0, len(slots), per):
                    chunk = slots[i:i+per]
                    cc = st.columns(per)
                    for j, (lv, s) in enumerate(chunk):
                        with cc[j]:
                            star = "★" if is_cel(G, lv, s) else ""
                            tag = f"N{lv+1}·" if multi_lv else ""
                            if lv == 5: tag, star = "", "◎"
                            if st.button(f"{star}{tag}{s+1}", key=f"sp{lv}_{s}", use_container_width=True):
                                st.session_state.sel = (lv, s); st.rerun()
            else:
                lv, s = sel
                star = " ★" if is_cel(G, lv, s) else ""
                where = f"Nv{lv+1} · esp {s+1}" if lv < 5 else ("Centro" if ES else "Center")
                st.markdown(f"**{'2 ·' if ES else '2 ·'} {where}{star} — {'elige color:' if ES else 'choose colour:'}**")
                avail = [m for m in moves if (m[1], m[2]) == sel]
                types = list(dict.fromkeys(m[0] for m in avail))
                lab = {"black":f"⚫ {pc['black']}", "white":f"🟡 {pc['white']}", "blue":f"🔵 {pc['blue']}"}
                cc = st.columns(len(types) + (0 if len(slots) == 1 else 1))
                for i, t in enumerate(types):
                    with cc[i]:
                        if st.button(lab[t], key=f"c{t}", use_container_width=True):
                            m = next(x for x in avail if x[0] == t)
                            do_play(G, m[0], m[1], m[2], m[3], mode)
                            st.session_state.pop("sel", None); st.rerun()
                if len(slots) > 1:
                    with cc[-1]:
                        if st.button("✕", key="cancel", use_container_width=True):
                            st.session_state.pop("sel", None); st.rerun()
        elif human and not moves:
            st.warning("Sin movimientos." if ES else "No moves.")
        else:
            nm_ai = player_label(G, cp, mode)
            st.info(f"🤖 {nm_ai} " + ("está pensando…" if ES else "is thinking…"), icon="⏳")
            time.sleep(1.1 if G["np"] > 2 else 0.7); ai_move(G, mode)
            st.session_state.pop("sel", None); st.rerun()

    if G["over"]:
        w = G["winner"]; rz = G["win_reason"]
        rtxt = " · " + (("llegó al centro" if ES else "center reached") if rz == "center"
                        else ("sin pelotas" if ES else "out of beads"))
        if G["teams"]:
            A = G["scores"][0] + G["scores"][2]; B = G["scores"][1] + G["scores"][3]
            if w == -1: title = "¡Empate!" if ES else "Tie!"
            else: title = ("¡Gana el equipo " if ES else "Team ") + ("A!" if w == 0 else "B!") + " 🎉"
            desc = f"A: {A} — B: {B}{rtxt}"
        else:
            if w == -1: title = "¡Empate!" if ES else "Tie!"
            else: title = f"¡{player_label(G, w, mode)} " + ("gana!" if ES else "wins!") + " 🎉"
            desc = " · ".join(f"{player_label(G,p,mode)}: {G['scores'][p]}" for p in range(G["np"])) + rtxt
        st.markdown(f'<div class="winner-box"><div class="winner-title">{title}</div><div class="winner-scores">{desc}</div></div>',
                    unsafe_allow_html=True)
        if st.button("↺ " + ("Revancha" if ES else "Rematch"), use_container_width=True, type="primary"):
            st.session_state.game = init_game(G["variant"], G["np"], G["teams"])
            st.session_state.pop("sel", None); st.rerun()

    if G["log"]:
        st.markdown("#### " + ("Historial" if ES else "Game log"))
        ent = ""
        for e in reversed(G["log"][-40:]):
            c = pcolor(G, e.get("p", 0))
            pts = f' <span class="log-pts">+{e["pts"]}</span>' if e["pts"] else ""
            ent += f'<div class="log-entry"><span style="color:#bbb;">#{e["t"]}</span> <b style="color:{c};">{e["who"]}</b> {e["msg"]}{pts}</div>'
        st.markdown(f'<div class="log-container">{ent}</div>', unsafe_allow_html=True)
