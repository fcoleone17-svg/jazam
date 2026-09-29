"""
JAZAM — núcleo del juego.

Lógica pura: no importa Streamlit ni dibuja nada. Se puede ejecutar y testear
sin levantar la aplicación.

Dos variantes comparten este motor:
  · "classic"  Jazam       — dos frentes desde 12:00, celestes en 12/3/6/9,
                             un nivel a la vez, bono del arquitecto, 2 jugadores.
  · "dynamic"  Jazam Duel  — frentes dinámicos, celestes en X, todos los niveles
                             abiertos, 2 o 4 jugadores (solos o en parejas).
"""
import random

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
    if np_ != 4: teams = False        # los bandos sólo existen con 4 jugadores
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
        "opened_by": {},   # nivel → jugador que lo abrió
        "over": False, "winner": None, "win_reason": None,
        "log": [], "turn_count": 0, "_es": True,
    }

def next_cp(G):
    """Siguiente jugador, saltando a los eliminados."""
    n = G["np"]
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

def add_log(G, who, msg, pts=0, lv=None, si=None, t=None, p=None):
    """`p` sólo se pasa cuando quien puntúa no es el jugador en turno (el
    centro se cobra en check_end, ya con el turno cedido)."""
    G["turn_count"] += 1
    G["log"].append({"t":G["turn_count"], "who":who, "msg":msg, "pts":pts,
                     "p":G["cp"] if p is None else p, "lv":lv, "si":si, "bead":t})

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
        # La azul se ofrece siempre (sobre un peaje se malgasta: es decisión del jugador),
        # salvo en la siembra y en el espacio de entrada a un nivel — ese espacio es
        # siempre un celeste, y permitir la azul ahí encadenaría ascensos sin fin.
        if pc["blue"] > 0 and not seed and meta != "forced":
            moves.append(("blue", lv, s, meta))
    return moves

# ══════════════════════════ JUGADA ══════════════════════════
def open_next_level(G, lv, from_si):
    """Abre el nivel lv+1 y devuelve (nivel, espacio de entrada) o None."""
    if lv >= 5: return None
    e = entry_space(G["board"], lv, from_si, lv+1)
    if e is None: return None
    if lv + 1 > G["lv"]:
        G["lv"] = lv + 1
        G["opened_by"][lv+1] = G["cp"]
    if G["variant"] == "classic":
        n = LEVELS[lv+1]
        G["ptr_cw"] = (e+1) % n; G["ptr_ccw"] = (e-1) % n
        G["toll_cw"] = G["toll_ccw"] = False; G["toll_lv"] = None
        G["lv"] = lv + 1
    return (lv+1, e)

def arch_bonus(G, lv, cp, who, ES):
    """+4 del arquitecto si esta jugada completó el nivel (sólo clásico, Nv1-3).
    Vive aparte de level_done porque la azul sobre celeste abre el nivel por su
    cuenta y antes se saltaba el bono."""
    if not all(x is not None for x in G["board"][lv]): return
    if cfg(G)["arch"] and lv <= 2:
        G["scores"][cp] += 4
        add_log(G, who, f"Nv{lv+1} completo +4" if ES else f"Lv{lv+1} complete +4", 4)

def level_done(G, lv, cp, who, ES, from_si):
    """Bono (si corresponde) y apertura del siguiente nivel al completar uno."""
    if not all(x is not None for x in G["board"][lv]): return None
    arch_bonus(G, lv, cp, who, ES)
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
    G["toll_at"].discard((lv, space))   # ocupado: su marca ya no puede cobrarse
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
            arch_bonus(G, lv, cp, who, ES)   # la azul también puede completar el nivel
            G["forced"] = nxt
            if nxt is None: G["cp"] = next_cp(G)   # sin entrada no hay ascenso: pasa el turno
            check_end(G, mode); return
        add_log(G, who, f"{tn} {lvtag}{space+1}" + (f" +{pts}" if pts else ""), pts, lv, space, ptype)
        f = level_done(G, lv, cp, who, ES, space)
        if f: G["forced"] = f
        G["cp"] = next_cp(G)
        check_end(G, mode); return

    # ─── Pieza normal (o azul neutralizada por peaje) ───
    G["board"][lv][space] = {"p":cp, "t":ptype, "neu":paying}
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
            nb = empty_neighbor(G["board"], lv, space)
            nxt = (lv, nb) if nb is not None else None
        f = level_done(G, lv, cp, who, ES, space)
        if f:
            # La entrada al nivel nuevo va SIEMPRE por `forced`: valid_moves la
            # sirve con meta="forced", que es donde la azul está prohibida.
            # Servirla como 2ª pelota del peaje (meta="second") se saltaba esa
            # regla y encadenaba ascensos.
            G["forced"] = f
            G["toll_pending"] = nxt if G["variant"] == "classic" else None
            check_end(G, mode); return
        G["toll_pending"] = nxt
        if nxt is None: G["cp"] = next_cp(G)
        check_end(G, mode); return

    if second: G["toll_pending"] = None

    if ptype == "white":
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
        add_log(G, player_label(G, w, mode), "¡CENTRO! +12" if ES else "CENTER! +12",
                CENTER_PTS, p=w)
        G["over"] = True; G["win_reason"] = "center"
        G["winner"] = best_by_points(G)
        return
    # ── sin piezas (o sin jugada legal): derrota (2 jug.) o eliminación (3+) ──
    for _ in range(G["np"] + 1):
        cp = G["cp"]; pc = G["pieces"][cp]
        empty = (pc["black"] <= 0 and pc["white"] <= 0 and pc["blue"] <= 0)
        if not empty and valid_moves(G): return
        # Quedarse sin pelotas y quedarse sin jugada legal (p. ej. sólo azules
        # frente a una entrada de nivel) son cosas distintas: se informan distinto.
        why = ("sin piezas" if ES else "out of beads") if empty else \
              ("sin movimientos" if ES else "no legal move")
        reason = "nopcs" if empty else "nomoves"
        if G["np"] == 2:
            G["over"] = True; G["win_reason"] = reason
            add_log(G, player_label(G, cp, mode), why, 0)
            G["winner"] = resolve_exhaust(G, cp); return
        G["out"][cp] = True
        # La deuda muere con el jugador: sin esto el siguiente heredaba su
        # peaje o su entrada forzada y podía quedar eliminado en cadena.
        G["forced"] = None; G["toll_pending"] = None
        add_log(G, player_label(G, cp, mode),
                ("eliminado · " if ES else "eliminated · ") + why, 0)
        liv = alive(G)
        if len(liv) <= 1:
            G["over"] = True; G["win_reason"] = reason
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
def _dist_to_cel(G, lv, si):
    """Distancia al celeste libre más cercano del anillo. None si no queda ninguno."""
    n = LEVELS[lv]; C = cfg(G)["cel"].get(lv, {})
    free = [c for c in C if G["board"][lv][c] is None]
    if not free: return None
    return min(min((si-c) % n, (c-si) % n) for c in free)

def ai_move(G, mode):
    mv = valid_moves(G)
    if not mv: return
    b = G["board"]; me = G["cp"]
    def C(lv): return cfg(G)["cel"].get(lv, {})

    # 1. tomar un celeste con azul — el de más valor
    take = [m for m in mv if m[0]=="blue" and m[2] in C(m[1])
            and not toll_here(G, m[1], m[2], m[3])]
    if take:
        best = max(space_pts(G, m[1], m[2]) for m in take)
        do_play(G, *random.choice([m for m in take if space_pts(G, m[1], m[2])==best]), mode); return

    # 2. si no puedo tomarlo, taparlo con negra para que no lo tome el rival
    block = [m for m in mv if m[0]=="black" and m[2] in C(m[1])]
    if block:
        best = max(space_pts(G, m[1], m[2]) for m in block)
        do_play(G, *random.choice([m for m in block if space_pts(G, m[1], m[2])==best]), mode); return

    # 3. BLANCA para invertir la paridad: si el celeste está a distancia par,
    #    le tocaría al rival. El peaje cuesta dos pelotas y desplaza el turno.
    if G["pieces"][me]["white"] > 0:
        flip = []
        for m in mv:
            if m[0] != "white": continue
            d = _dist_to_cel(G, m[1], m[2])
            if d is not None and d > 0 and d % 2 == 0:
                flip.append((d, -space_pts(G, m[1], m[2]), m))
        if flip:
            key = min((x[0], x[1]) for x in flip)
            do_play(G, *random.choice([x[2] for x in flip if (x[0], x[1])==key]), mode); return

    # 4. blanca justo antes de un celeste libre (envenenar el acceso)
    poison = []
    for m in mv:
        if m[0] != "white": continue
        nb = empty_neighbor(b, m[1], m[2])
        if nb is not None and nb in C(m[1]): poison.append(m)
    if poison:
        do_play(G, *random.choice(poison), mode); return

    # 5. negra avanzando hacia el celeste libre más cercano
    blacks = [m for m in mv if m[0]=="black"]
    if blacks:
        def key(m):
            d = _dist_to_cel(G, m[1], m[2])
            return (d if d is not None else 99, sum(1 for x in b[m[1]] if x is None))
        k = min(key(m) for m in blacks)
        do_play(G, *random.choice([m for m in blacks if key(m)==k]), mode); return

    do_play(G, *random.choice(mv), mode)

