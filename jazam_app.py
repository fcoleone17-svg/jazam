"""
JAZAM — aplicación Streamlit.

Solo interfaz: toda la lógica del juego vive en jazam_core.py.
Este es el archivo que ejecuta Streamlit Cloud.
"""
import streamlit as st
import math, time

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


from jazam_core import *

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
        with c3: st.markdown('<div class="rule-box" style="text-align:center;"><b>🔵 Azul</b><br><small>Va en cualquier espacio · solo en celeste puntúa, sube de nivel y repite turno.</small></div>', unsafe_allow_html=True)
        st.markdown('<div class="rule-box">🟡 <b>El peaje:</b> después de una blanca, el próximo que juegue en el espacio marcado pone 2 pelotas. Ojo: la primera no cuenta — solo ocupa el espacio. La segunda es la que realmente juega.<br><br><b>Ejemplo:</b> la blanca queda justo antes de un celeste. El siguiente jugador pone su primera pelota ahí — pero no tiene efecto (aunque sea azul, no puntúa ni abre nivel). La segunda es la que juega normalmente.</div>', unsafe_allow_html=True)
        st.markdown('<div class="rule-box">🔵 <b>La azul sube de nivel y repite turno.</b> Al colocarla en un celeste te llevas sus puntos, se abre el nivel siguiente y vuelves a jugar: colocas tú la primera pelota ahí, en el espacio de entrada.<br><br>Esa pelota de entrada <b>no puede ser azul</b>. El espacio de entrada siempre cae sobre un celeste del nivel nuevo, así que permitirlo encadenaría ascensos uno tras otro sin límite.</div>', unsafe_allow_html=True)
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
        with c3: st.markdown('<div class="rule-box" style="text-align:center;"><b>🔵 Blue</b><br><small>Any space · only on a celestial does it score, go up a level and repeat turn.</small></div>', unsafe_allow_html=True)
        st.markdown('<div class="rule-box">🟡 <b>The toll:</b> after a white, the next player to use the marked space places 2 beads. The first doesn\'t count — it just fills the space. The second is the one that really plays.</div>', unsafe_allow_html=True)
        st.markdown('<div class="rule-box">🔵 <b>Blue goes up a level and repeats your turn.</b> On a celestial it scores its points, opens the next level and you play again, placing the first bead there at the entry space.<br><br>That entry bead <b>cannot be blue</b>: the entry space always lands on a celestial of the new level, so allowing it would chain ascents without limit.</div>', unsafe_allow_html=True)
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
            flv = G["forced"][0]
            opener = G.get("opened_by", {}).get(flv)
            byw = f" ({'abierto por' if ES else 'opened by'} {player_label(G, opener, mode)})" if opener is not None else ""
            nm_lv = ("el Centro" if ES else "the Center") if flv == 5 else f"Nv{flv+1}"
            cls = "status-bar first"
            txt = f"🔓 <b>{nm}</b> — {'entra a' if ES else 'enters'} {nm_lv}{byw} · esp {G['forced'][1]+1}"
        elif G["toll_pending"] is not None:
            cls, txt = "status-bar", f"<b>{nm}</b> — {'2ª pelota del peaje' if ES else '2nd toll bead'}"
        elif not moves:
            cls, txt = "status-bar warning", f"⚠️ <b>{nm}</b> — {'sin movimientos' if ES else 'no moves'}"
        elif any(is_cel(G, lv, s) for lv, s in slots):
            cls, txt = "status-bar celestial", f"★ <b>{nm}</b> — {'celeste disponible' if ES else 'celestial available'}"
        else:
            cls, txt = "status-bar", f"<b style='color:{col}'>{nm}</b> — {len(slots)} {'opciones' if ES else 'options'}"
        st.markdown(f'<div class="{cls}">{txt}</div>', unsafe_allow_html=True)

    ob = G.get("opened_by", {})
    chips_lv = ""
    for li in range(G["lv"]+1):
        full = all(x is not None for x in G["board"][li])
        who_p = ob.get(li)
        col = pcolor(G, who_p) if who_p is not None else "#8A7A55"
        tag = f' · {player_label(G, who_p, mode)}' if who_p is not None else ""
        nm_lv = ("Centro" if ES else "Center") if li == 5 else f"Nv{li+1}"
        style = "opacity:.45;text-decoration:line-through;" if full else ""
        chips_lv += (f'<span style="display:inline-block;border:1.5px solid {col};color:{col};'
                     f'border-radius:10px;padding:1px 9px;margin:2px 4px 2px 0;font-size:0.72rem;'
                     f'font-weight:600;{style}">{nm_lv}{tag}</span>')
    st.markdown(f'<div style="font-size:0.7rem;color:#999;margin:6px 0 0 2px;">'
                f'{"Niveles abiertos" if ES else "Levels open"}</div>'
                f'<div style="margin-bottom:4px;">{chips_lv}</div>', unsafe_allow_html=True)

    if since and (G["np"] > 2 or mode == "ai"):
        ico = {"black":"⚫", "white":"🟡", "blue":"🔵"}
        chips = ""
        for k, e in enumerate(since):
            c = pcolor(G, e["p"])
            pts = f' +{e["pts"]}' if e.get("pts") else ""
            loc = f'Nv{e["lv"]+1}·{e["si"]+1}' if e["lv"] < 5 else ("centro" if ES else "center")
            if e.get("bead") == "blue" and e.get("pts"): loc += " 🔓"
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
        rtxt = " · " + {"center": "llegó al centro" if ES else "center reached",
                        "nomoves": "sin movimientos" if ES else "no legal move"}.get(
                            rz, "sin pelotas" if ES else "out of beads")
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
