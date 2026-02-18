"""
El Impostor — Aplicación Web Pass & Play
=========================================
v2.0 — Rediseño completo con nombres de jugadores, UI premium y tarjetas flip corregidas.
Las tarjetas se renderizan con st.components.v1.html() para soporte completo de CSS/JS.
"""

import random
import time
from dataclasses import dataclass, field
from typing import List, Optional

import streamlit as st
import streamlit.components.v1 as components

# ╔══════════════════════════════════════════════════════════════╗
#  SECCIÓN 1 — MODELOS DE DATOS
# ╚══════════════════════════════════════════════════════════════╝

@dataclass(frozen=True)
class WordEntry:
    word: str
    hints: List[str]

    def __post_init__(self) -> None:
        if len(self.hints) < 3:
            raise ValueError(f"'{self.word}' requiere mínimo 3 pistas.")


@dataclass
class Player:
    id: int
    name: str
    is_impostor: bool
    word: Optional[str] = None
    hint: Optional[str] = None


@dataclass
class GameConfig:
    player_names: List[str] = field(default_factory=list)
    impostor_count: int = 1
    hints_enabled: bool = True
    custom_mode: bool = False
    chaos_mode: bool = False

    @property
    def total_players(self) -> int:
        return len(self.player_names)


@dataclass
class GameState:
    players: List[Player] = field(default_factory=list)
    current_player_index: int = 0
    selected_word_entry: Optional[WordEntry] = None
    round_start_time: Optional[float] = None
    starting_player_name: Optional[str] = None
    reveal_done: bool = False


# ╔══════════════════════════════════════════════════════════════╗
#  SECCIÓN 2 — ESTADOS FSM
# ╚══════════════════════════════════════════════════════════════╝

STATE_SETUP        = "SETUP"
STATE_CUSTOM_WORDS = "CUSTOM_WORDS"
STATE_ROLE_DIST    = "ROLE_DISTRIBUTION"
STATE_GAME_ACTIVE  = "GAME_ACTIVE"
STATE_VOTING       = "VOTING"

# ╔══════════════════════════════════════════════════════════════╗
#  SECCIÓN 3 — DATASET
# ╚══════════════════════════════════════════════════════════════╝

DEFAULT_DATASET: List[WordEntry] = [
    WordEntry("Aeropuerto",  ["Pista", "Sala de embarque", "Control", "Tiendas", "Torre"]),
    WordEntry("Restaurante", ["Camarero", "Carta", "Propina", "Chef", "Reserva"]),
    WordEntry("Estadio",     ["Grada", "Marcador", "Árbitro", "Butacas", "Himno"]),
    WordEntry("Hospital",    ["Urgencias", "Quirófano", "Camilla", "Bata", "Monitor"]),
    WordEntry("Biblioteca",  ["Silencio", "Carnet", "Estanterías", "Préstamo", "Estudiar"]),
    WordEntry("Playa",       ["Sombrilla", "Arena", "Socorrista", "Chiringuito", "Olas"]),
    WordEntry("Montaña",     ["Nevada", "Senderismo", "Refugio", "Altitud", "Osos"]),
    WordEntry("Cine",        ["Palomitas", "Pantalla", "Oscuro", "Taquilla", "Butacas"]),
    WordEntry("Mercado",     ["Fruta", "Centro", "Olores", "Carrito", "Pescadería"]),
    WordEntry("Barco",       ["Cubierta", "Ancla", "Capitán", "Mar", "Salvavidas"]),
]

# ╔══════════════════════════════════════════════════════════════╗
#  SECCIÓN 4 — ESTILOS GLOBALES STREAMLIT
# ╚══════════════════════════════════════════════════════════════╝

GLOBAL_PAGE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600&display=swap');

*, *::before, *::after { box-sizing: border-box; }
html, body, [data-testid="stApp"] {
    background-color: #0a0a0a !important;
    color: #e8e8e8;
    font-family: 'DM Sans', sans-serif;
}
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }
.block-container { padding: 2rem 1.5rem 4rem !important; max-width: 720px !important; }

.section-header {
    font-size: .98rem;
    font-weight: 600;
    letter-spacing: .25em;
    text-transform: uppercase;
    color: #555;
    margin: 1.8rem 0 .7rem;
    display: flex;
    align-items: center;
    gap: .6rem;
}
.section-header::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, #222, transparent);
}

.hero-wrap { text-align: center; padding: 2rem 0 1.2rem; }
.hero-el { font-family: 'Bebas Neue', sans-serif; font-size: clamp(3rem,10vw,5rem); letter-spacing:.1em; color:#fff; line-height:1; }
.hero-impostor { font-family:'Bebas Neue',sans-serif; font-size:clamp(4rem,14vw,7rem); letter-spacing:.05em; color:#e63329; line-height:.9; display:block; text-shadow: 0 0 80px rgba(230,51,41,.25); }
.hero-sub { font-size:.78rem; letter-spacing:.3em; text-transform:uppercase; color:#3a3a3a; margin-top:.9rem; }

.game-card {
    background: #0f0f0f;
    border: 1px solid #1c1c1c;
    border-radius: 12px;
    padding: 1.1rem 1.4rem;
    margin: .45rem 0;
}
.game-card.red-border { border-color: rgba(230,51,41,.4); background: rgba(230,51,41,.03); }
.game-card.green-border { border-color: rgba(0,210,100,.3); background: rgba(0,210,100,.03); }

[data-testid="stTextArea"] textarea {
    background: #0f0f0f !important;
    border: 1px solid #1e1e1e !important;
    border-radius: 8px !important;
    color: #e8e8e8 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: .95rem !important;
}
[data-testid="stTextArea"] textarea:focus {
    border-color: #e63329 !important;
    box-shadow: 0 0 0 2px rgba(230,51,41,.12) !important;
}
[data-testid="stTextInput"] input {
    background: #0f0f0f !important;
    border: 1px solid #1e1e1e !important;
    border-radius: 8px !important;
    color: #e8e8e8 !important;
}
[data-testid="stNumberInput"] input {
    background: #0f0f0f !important;
    border: 1px solid #1e1e1e !important;
    color: #e8e8e8 !important;
    border-radius: 8px !important;
}
[data-testid="stSelectbox"] > div > div {
    background: #0f0f0f !important;
    border: 1px solid #1e1e1e !important;
    color: #e8e8e8 !important;
    border-radius: 8px !important;
}

.stButton > button {
    background: #e63329 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: .92rem !important;
    padding: .7rem 1.4rem !important;
    letter-spacing: .02em !important;
    transition: all .18s ease !important;
    width: 100%;
}
.stButton > button:hover {
    background: #c9261d !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(230,51,41,.28) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

[data-testid="stProgress"] > div > div { background: #e63329 !important; border-radius: 99px !important; }
[data-testid="stProgress"] { background: #1a1a1a !important; border-radius: 99px !important; }

.info-pill {
    display: inline-flex;
    align-items: center;
    gap: .35rem;
    font-size: .76rem;
    color: #444;
    padding: .28rem .65rem;
    border: 1px solid #1c1c1c;
    border-radius: 99px;
    margin-bottom: .4rem;
}

.starter-wrap {
    background: #0f0f0f;
    border: 1px solid #1c1c1c;
    border-radius: 12px;
    padding: 1.4rem;
    text-align: center;
    margin: .8rem 0;
}
.starter-label { font-size:.62rem; text-transform:uppercase; letter-spacing:.25em; color:#3a3a3a; margin-bottom:.4rem; }
.starter-name { font-family:'Bebas Neue',sans-serif; font-size:2.6rem; color:#e63329; letter-spacing:.05em; }
.starter-sub { font-size:.76rem; color:#2e2e2e; margin-top:.25rem; }
</style>
"""
# ╔══════════════════════════════════════════════════════════════╗
#  MÓDULO DE BASE DE DATOS (NEON / POSTGRESQL)
# ╚══════════════════════════════════════════════════════════════╝
from sqlalchemy import text

def get_db_connection():
    # "neon" coincide con [connections.neon] en secrets.toml
    return st.connection("neon", type="sql") 

def init_db():
    conn = get_db_connection()
    try:
        with conn.session as s:
            # Tabla de palabras
            s.execute(text("""
                CREATE TABLE IF NOT EXISTS custom_words (
                    id SERIAL PRIMARY KEY,
                    word TEXT UNIQUE NOT NULL,
                    hints TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            # Grupos de Jugadores
            s.execute(text("""
                CREATE TABLE IF NOT EXISTS player_groups (
                    id SERIAL PRIMARY KEY,
                    group_name TEXT UNIQUE NOT NULL,
                    player_names TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            s.commit()
    except Exception as e:
        st.error(f"Error inicializando DB: {e}")

def load_words_from_db() -> List[WordEntry]:
    conn = get_db_connection()
    # ttl=0 asegura que siempre traiga datos frescos, no cacheados
    try:
        df = conn.query("SELECT word, hints FROM custom_words ORDER BY created_at DESC", ttl=0)
        dataset = []
        if not df.empty:
            for _, row in df.iterrows():
                dataset.append(WordEntry(word=row['word'], hints=row['hints'].split('|')))
        return dataset
    except Exception:
        return []

def add_word_to_db(word: str, hints: List[str]) -> bool:
    conn = get_db_connection()
    hints_str = "|".join(hints)
    try:
        with conn.session as s:
            s.execute(
                text("INSERT INTO custom_words (word, hints) VALUES (:w, :h)"),
                {"w": word, "h": hints_str}
            )
            s.commit()
        return True
    except Exception:
        return False

def delete_word_from_db(word: str):
    conn = get_db_connection()
    try:
        with conn.session as s:
            s.execute(text("DELETE FROM custom_words WHERE word = :w"), {"w": word})
            s.commit()
    except Exception:
        pass

def save_player_group_db(group_name: str, players: List[str]) -> bool:
    conn = get_db_connection()
    players_str = "|".join(players)
    try:
        with conn.session as s:
            # Upsert: Si existe el nombre, actualiza la lista
            s.execute(
                text("""
                    INSERT INTO player_groups (group_name, player_names) 
                    VALUES (:n, :p)
                    ON CONFLICT (group_name) 
                    DO UPDATE SET player_names = EXCLUDED.player_names;
                """),
                {"n": group_name, "p": players_str}
            )
            s.commit()
        return True
    except Exception:
        return False

def load_player_groups_db() -> dict:
    conn = get_db_connection()
    try:
        df = conn.query("SELECT group_name, player_names FROM player_groups ORDER BY created_at DESC", ttl=0)
        groups = {}
        if not df.empty:
            for _, row in df.iterrows():
                groups[row['group_name']] = row['player_names'].split('|')
        return groups
    except Exception:
        return {}

def delete_player_group_db(group_name: str):
    conn = get_db_connection()
    try:
        with conn.session as s:
            s.execute(text("DELETE FROM player_groups WHERE group_name = :n"), {"n": group_name})
            s.commit()
    except Exception:
        pass

# ╔══════════════════════════════════════════════════════════════╗
#  SECCIÓN 5 — INIT SESSION STATE
# ╚══════════════════════════════════════════════════════════════╝

def init_session_state() -> None:
    defaults = {
        "current_state":  STATE_SETUP,
        "game_config":    GameConfig(),
        "game_state":     GameState(),
        "custom_dataset": [],
        "db_initialized": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    if not st.session_state.db_initialized:
        init_db()
        st.session_state.db_initialized = True

    if not st.session_state.custom_dataset:
        db_words = load_words_from_db()
        if db_words:
            st.session_state.custom_dataset = db_words


def change_state(s: str) -> None:
    st.session_state.current_state = s

# ╔══════════════════════════════════════════════════════════════╗
#  SECCIÓN 6 — LÓGICA DE NEGOCIO
# ╚══════════════════════════════════════════════════════════════╝

def build_players(config: GameConfig, entry: WordEntry) -> List[Player]:
    names = config.player_names
    n = len(names)
    
    # Lógica Modo Caos (20% prob: 10% todos impostores, 10% todos inocentes)
    chaos_trigger = False
    force_all_impostors = False
    
    if config.chaos_mode and random.random() < 0.20:
        chaos_trigger = True
        force_all_impostors = random.choice([True, False])

    if chaos_trigger:
        roles = [force_all_impostors] * n
    else:
        roles = [True] * config.impostor_count + [False] * (n - config.impostor_count)
        random.shuffle(roles)

    pool = entry.hints.copy()
    impostor_total = sum(roles)
    sample_size = min(impostor_total, len(pool)) if impostor_total > 0 else 0
    unique_hints = random.sample(pool, sample_size)
    
    while len(unique_hints) < impostor_total:
        remaining = [h for h in pool if h not in unique_hints[-len(pool):]] or pool.copy()
        unique_hints.append(random.choice(remaining))

    players, hc = [], 0
    for idx, is_imp in enumerate(roles):
        pid, pname = idx + 1, names[idx]
        if is_imp:
            hint = unique_hints[hc] if config.hints_enabled else None
            hc += 1
            players.append(Player(id=pid, name=pname, is_impostor=True, hint=hint))
        else:
            players.append(Player(id=pid, name=pname, is_impostor=False, word=entry.word))
    
    return players


def start_role_distribution() -> None:
    config: GameConfig = st.session_state.game_config
    state:  GameState  = st.session_state.game_state

    dataset = st.session_state.custom_dataset if config.custom_mode else []
    if not dataset:
        dataset = DEFAULT_DATASET

    entry = random.choice(dataset)
    state.selected_word_entry  = entry
    state.players              = build_players(config, entry)
    state.current_player_index = 0
    state.round_start_time     = None
    state.starting_player_name = random.choice(state.players).name
    state.reveal_done          = False
    change_state(STATE_ROLE_DIST)

# ╔══════════════════════════════════════════════════════════════╗
#  SECCIÓN 7 — HTML COMPONENTS (iframe-rendered, sin limitaciones)
# ╚══════════════════════════════════════════════════════════════╝

def flip_card_component(player: Player, hints_enabled: bool) -> None:
    """
    Renderiza la tarjeta flip en un iframe con components.html().
    El iframe no hereda las restricciones de st.markdown, por lo que
    el CSS 3D y el checkbox toggle funcionan perfectamente.
    """
    if player.is_impostor:
        role_label  = "IMPOSTOR"
        role_color  = "#e63329"
        role_icon   = "&#9888;"
        role_bg     = "rgba(230,51,41,0.07)"
        role_border = "rgba(230,51,41,0.45)"
        if hints_enabled and player.hint:
            secret_block = f"""
                <div class="stag">TU PISTA</div>
                <div class="sval" style="color:{role_color};">{player.hint}</div>
                <div class="snote">Usa esta pista sin revelar que eres el impostor.</div>
            """
        else:
            secret_block = f"""
                <div class="stag">MODO SIN PISTAS</div>
                <div class="sval" style="color:#444;font-size:1.4rem;">Sin pista asignada</div>
                <div class="snote">Improvisa. Confunde. Sobrevive.</div>
            """
    else:
        role_label  = "JUGADOR"
        role_color  = "#00d264"
        role_icon   = "&#10003;"
        role_bg     = "rgba(0,210,100,0.05)"
        role_border = "rgba(0,210,100,0.35)"
        secret_block = f"""
            <div class="stag">PALABRA SECRETA</div>
            <div class="sval" style="color:{role_color};">{player.word}</div>
            <div class="snote">Defiéndela sin revelarla directamente.</div>
        """

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;600;700&display=swap');
  *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
  body{{background:transparent;font-family:'DM Sans',sans-serif;overflow:hidden;}}

  .scene{{width:100%;height:350px;perspective:1400px;}}
  .scene label{{display:block;width:100%;height:100%;cursor:pointer;user-select:none;-webkit-user-select:none;}}
  .chk{{display:none;}}
  .body{{
    position:relative;width:100%;height:100%;
    transform-style:preserve-3d;
    transition:transform .7s cubic-bezier(.4,0,.2,1);
  }}
  .chk:checked ~ .body{{transform:rotateY(180deg);}}

  .face{{
    position:absolute;inset:0;border-radius:14px;
    backface-visibility:hidden;-webkit-backface-visibility:hidden;
    display:flex;flex-direction:column;align-items:center;justify-content:center;
    padding:1.8rem;gap:.4rem;
  }}

  /* FRONT */
  .face.front{{
    background:linear-gradient(160deg,#141414 0%,#1a1a1a 100%);
    border:1px solid #222;
    box-shadow:0 20px 50px rgba(0,0,0,.7);
  }}
  .fl{{font-size:2.8rem;filter:grayscale(1) opacity(.35);margin-bottom:.3rem;}}
  .fp{{font-size:.6rem;letter-spacing:.25em;text-transform:uppercase;color:#3a3a3a;}}
  .fn{{font-family:'Bebas Neue',sans-serif;font-size:2.4rem;color:#fff;letter-spacing:.06em;line-height:1;}}
  .fh{{font-size:.72rem;color:#2a2a2a;margin-top:.6rem;border:1px solid #1e1e1e;padding:.35rem .85rem;border-radius:99px;}}

  /* BACK */
  .face.back{{
    background:linear-gradient(160deg,#0c0c0c 0%,#141414 100%);
    border:2px solid {role_border};
    background-color:{role_bg};
    box-shadow:0 20px 50px rgba(0,0,0,.8),inset 0 0 80px {role_bg};
    transform:rotateY(180deg);
    gap:.35rem;
  }}
  .ri{{font-size:1.8rem;margin-bottom:.1rem;color:{role_color};}}
  .rb{{
    font-size:.58rem;font-weight:700;letter-spacing:.2em;text-transform:uppercase;
    color:{role_color};border:1px solid {role_border};
    background:{role_bg};padding:.28rem .75rem;border-radius:99px;margin-bottom:.6rem;
  }}
  .stag{{font-size:.58rem;letter-spacing:.2em;text-transform:uppercase;color:#3a3a3a;margin-bottom:.25rem;}}
  .sval{{font-family:'Bebas Neue',sans-serif;font-size:2.8rem;letter-spacing:.04em;text-align:center;line-height:1.1;}}
  .snote{{font-size:.7rem;color:#2e2e2e;text-align:center;margin-top:.4rem;max-width:260px;line-height:1.4;}}
  .bf{{font-size:.6rem;color:#1e1e1e;margin-top:auto;}}
</style>
</head>
<body>
<div class="scene">
  <label>
    <input type="checkbox" class="chk">
    <div class="body">
      <div class="face front">
        <div class="fl">&#128274;</div>
        <div class="fp">turno de</div>
        <div class="fn">{player.name}</div>
        <div class="fh">Toca para ver tu rol en privado</div>
      </div>
      <div class="face back">
        <div class="ri">{role_icon}</div>
        <div class="rb">{role_label}</div>
        {secret_block}
        <div class="bf">&#8617; Toca de nuevo para ocultar antes de pasar</div>
      </div>
    </div>
  </label>
</div>
</body>
</html>"""
    components.html(html, height=360)


def timer_component(start_epoch: float) -> None:
    html = f"""<!DOCTYPE html>
<html>
<head>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@400&display=swap');
  body{{margin:0;background:transparent;font-family:'DM Sans',sans-serif;overflow:hidden;}}
  .w{{background:#0f0f0f;border:1px solid #1c1c1c;border-radius:10px;padding:1rem 2rem;text-align:center;}}
  .l{{font-size:.6rem;letter-spacing:.25em;text-transform:uppercase;color:#3a3a3a;margin-bottom:.2rem;}}
  .d{{font-family:'Bebas Neue',sans-serif;font-size:3.2rem;color:#e8e8e8;letter-spacing:.1em;}}
</style>
</head>
<body>
<div class="w">
  <div class="l">&#9201; tiempo de ronda</div>
  <div class="d" id="t">00:00</div>
</div>
<script>
const s={start_epoch*1000};
function pad(n){{return String(n).padStart(2,'0');}}
function tick(){{
  const e=Math.floor((Date.now()-s)/1000);
  document.getElementById('t').textContent=pad(Math.floor(e/60))+':'+pad(e%60);
}}
tick();setInterval(tick,1000);
</script>
</body>
</html>"""
    components.html(html, height=100)

# ╔══════════════════════════════════════════════════════════════╗
#  SECCIÓN 8 — PANTALLAS
# ╚══════════════════════════════════════════════════════════════╝

def render_setup() -> None:
    st.markdown(GLOBAL_PAGE_CSS, unsafe_allow_html=True)

    st.markdown("""
    <div class="hero-wrap">
        <div class="hero-el">EL</div>
        <span class="hero-impostor">IMPOSTOR</span>
        <div class="hero-sub">El juego de engaño y deducción social</div>
    </div>
    """, unsafe_allow_html=True)
    # ── GESTIÓN DE GRUPOS DE JUGADORES ──
    saved_groups = load_player_groups_db() 

    if "selected_group_names" not in st.session_state:
        st.session_state.selected_group_names = "Ana\nBerto\nCarla\nDavid"
    
    with st.expander("&#128190; Cargar / Guardar Grupo de Jugadores", expanded=False):
        c1, c2 = st.columns([2, 1])
        with c1:
            group_options = ["-- Seleccionar --"] + list(saved_groups.keys())
            selected_group = st.selectbox("Cargar grupo existente:", group_options, label_visibility="collapsed")
        with c2:
            if st.button("Cargar", use_container_width=True):
                if selected_group and selected_group != "-- Seleccionar --":
                    st.session_state.selected_group_names = "\n".join(saved_groups[selected_group])
                    st.rerun()
        
        st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
        
        # Guardar grupo actual
        c3, c4 = st.columns([2, 1])
        with c3:
            new_group_name = st.text_input("Guardar actuales como:", placeholder="Ej: Familia Domingos", label_visibility="collapsed")
        with c4:
            if st.button("Guardar", use_container_width=True):
                current_list = [x.strip() for x in st.session_state.selected_group_names.splitlines() if x.strip()]
                if len(current_list) < 3:
                    st.error("Mínimo 3 jugadores")
                elif not new_group_name:
                    st.error("Pon un nombre")
                else:
                    save_player_group_db(new_group_name, current_list)
                    st.success(f"Grupo '{new_group_name}' guardado.")
                    time.sleep(1) # Pequeña pausa para ver el mensaje
                    st.rerun()
                    
        # Borrar grupo
        if selected_group and selected_group != "-- Seleccionar --":
            if st.button(f"Borrar grupo '{selected_group}'", type="secondary"):
                delete_player_group_db(selected_group)
                st.rerun()

    # ── JUGADORES ──
    st.markdown('<div class="section-header">&#128101; JUGADORES</div>', unsafe_allow_html=True)
    st.caption("Un nombre por línea (mínimo 3):")
    default_names = st.session_state.get("_uploaded_names", "Ana\nBerto\nCarla\nDavid")
    names_raw = st.text_area(
        label="Nombres",
        value=st.session_state.selected_group_names,
        height=130,
        label_visibility="collapsed",
        placeholder="Ana\nBerto\nCarla\nDavid...",
        key="players_input_area" 
    )

    if names_raw != st.session_state.selected_group_names:
        st.session_state.selected_group_names = names_raw

    player_names = [n.strip() for n in names_raw.strip().splitlines() if n.strip()]

    count_color = "#e63329" if len(player_names) < 3 else "#00d264"
    st.markdown(
        f'<div class="info-pill">&#127918; <span style="color:{count_color};font-weight:600;">{len(player_names)}</span>&nbsp;jugadores detectados</div>',
        unsafe_allow_html=True,
    )

    # ── OPCIONES ──
    handle_config_persistence(player_names)

    st.markdown('<div class="section-header">&#9881; OPCIONES</div>', unsafe_allow_html=True)

    col_a, col_b = st.columns([1, 1])
    with col_a:
        max_imp = max(1, len(player_names) - 1)
        impostor_count = st.number_input(
            "Número de impostores",
            min_value=1, max_value=max_imp, value=1,
            help=f"Máximo {max_imp} con {len(player_names)} jugadores",
        )
    with col_b:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        hints_enabled = st.toggle(
            "&#128269; Pistas para impostores", value=True,
            help="Los impostores reciben una pista de la palabra secreta.",
        )
        chaos_mode = st.toggle(
            "&#127922; Modo Caos (20%)", value=False,
            help="Probabilidad de que TODOS sean impostores o TODOS inocentes.",
        )

    # ── BANCO DE PALABRAS ──
    st.markdown('<div class="section-header">&#128218; BANCO DE PALABRAS</div>', unsafe_allow_html=True)
    custom_mode = st.toggle(
        "&#128296; Modo Personalizado",
        help="Usa tus propias palabras y pistas.",
    )

    # Validación
    errors = []
    if len(player_names) < 3:
        errors.append("Se necesitan al menos 3 jugadores.")
    if len(player_names) > 0 and impostor_count >= len(player_names):
        errors.append("Los impostores no pueden igualar o superar el total de jugadores.")
    for e in errors:
        st.error(e)

    st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)

    if st.button("&#128640; Iniciar partida", type="primary", use_container_width=True, disabled=bool(errors)):
        st.session_state.game_config = GameConfig(
            player_names   = player_names,
            impostor_count = int(impostor_count),
            hints_enabled  = hints_enabled,
            custom_mode    = custom_mode,
            chaos_mode     = chaos_mode,
        )
        if custom_mode:
            change_state(STATE_CUSTOM_WORDS)
        else:
            start_role_distribution()
        st.rerun()

    with st.expander("&#8505; Cómo jugar"):
        st.markdown("""
1. **Configura** jugadores, impostores y opciones.
2. **Reparte roles**: cada jugador gira su tarjeta en privado.
3. **Todos describen** la palabra en voz alta — los impostores fingen.
4. **Votad** y revelad quién era el impostor.
        """)


def render_custom_words() -> None:
    st.markdown(GLOBAL_PAGE_CSS, unsafe_allow_html=True)
    st.markdown('<div style="font-family:\'Bebas Neue\',sans-serif;font-size:2.5rem;color:#fff;letter-spacing:.05em;">&#128221; Palabras Personalizadas</div>', unsafe_allow_html=True)
    st.caption("Añade palabras con al menos 3 pistas cada una.")

    with st.form("custom_form", clear_on_submit=True):
        word_input  = st.text_input("Palabra secreta", placeholder="Ej: Viaje a...")
        hints_input = st.text_input("Pistas (separadas por coma)", placeholder="Ej: Coche de..., Vuelo, Maleta")
        if st.form_submit_button("&#10133; Añadir palabra", use_container_width=True):
            ph = [h.strip() for h in hints_input.split(",") if h.strip()]
            if not word_input.strip():
                st.error("La palabra no puede estar vacía.")
            elif len(ph) < 3:
                st.error("Necesitas al menos 3 pistas.")
            else:
                if add_word_to_db(word_input.strip(), ph):
                    st.success(f"'{word_input.strip()}' guardada exitosamente.")
                    st.session_state.custom_dataset = load_words_from_db()
                else:
                    st.error("Error al guardar. Puede que la palabra ya exista.")

    dataset: List[WordEntry] = st.session_state.custom_dataset
    st.markdown(f'<div class="info-pill">&#128230; {len(dataset)} palabras en el banco</div>', unsafe_allow_html=True)
    for i, entry in enumerate(dataset):
        with st.expander(f"&#128204; {entry.word}  ({len(entry.hints)} pistas)"):
            st.write(" · ".join(entry.hints))
            if st.button("&#128465; Eliminar", key=f"del_{i}"):
                delete_word_from_db(entry.word)
                st.session_state.custom_dataset = load_words_from_db() # Recargar
                st.rerun()

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("&#9654; Iniciar con estas palabras", type="primary", use_container_width=True):
            if dataset:
                start_role_distribution(); st.rerun()
            else:
                st.error("Añade al menos una palabra.")
    with col2:
        if st.button("&#8592; Volver", use_container_width=True):
            change_state(STATE_SETUP); st.rerun()


def render_role_distribution() -> None:
    state:  GameState  = st.session_state.game_state
    config: GameConfig = st.session_state.game_config
    idx = state.current_player_index

    if idx >= len(state.players):
        state.round_start_time = time.time()
        change_state(STATE_GAME_ACTIVE)
        st.rerun()
        return

    player = state.players[idx]
    total  = len(state.players)

    st.markdown(GLOBAL_PAGE_CSS, unsafe_allow_html=True)
    st.markdown(
        f'<div style="font-size:.7rem;color:#3a3a3a;text-align:right;margin-bottom:.3rem;">{idx+1} / {total} jugadores</div>',
        unsafe_allow_html=True
    )
    st.progress(idx / total)

    flip_card_component(player, config.hints_enabled)

    col1, col2 = st.columns([4, 1])
    with col1:
        label = "Siguiente jugador &#8594;" if idx < total - 1 else "&#10003; Comenzar partida"
        if st.button(label, type="primary", use_container_width=True):
            state.current_player_index += 1
            st.rerun()
    with col2:
        if st.button("&#8634;", use_container_width=True, help="Reiniciar"):
            st.session_state.game_state = GameState()
            change_state(STATE_SETUP); st.rerun()


def render_game_active() -> None:
    state: GameState = st.session_state.game_state
    st.markdown(GLOBAL_PAGE_CSS, unsafe_allow_html=True)

    st.markdown('<div style="font-family:\'Bebas Neue\',sans-serif;font-size:2.6rem;letter-spacing:.06em;color:#fff;margin-bottom:.3rem;">&#128483; FASE DE DISCUSIÓN</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="starter-wrap">
        <div class="starter-label">&#127922; empieza la ronda</div>
        <div class="starter-name">{state.starting_player_name}</div>
        <div class="starter-sub">Describe la palabra sin revelarla directamente</div>
    </div>
    """, unsafe_allow_html=True)

    if state.round_start_time:
        timer_component(state.round_start_time)

    st.caption("Cada jugador da una descripción. Los impostores fingen conocer la palabra usando su pista.")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("&#9878; Pasar a votación", type="primary", use_container_width=True):
            change_state(STATE_VOTING); st.rerun()
    with col2:
        if st.button("&#128065; Revelar ya", use_container_width=True):
            change_state(STATE_VOTING); st.rerun()


def render_voting() -> None:
    state: GameState = st.session_state.game_state
    st.markdown(GLOBAL_PAGE_CSS, unsafe_allow_html=True)

    st.markdown('<div style="font-family:\'Bebas Neue\',sans-serif;font-size:2.6rem;letter-spacing:.06em;color:#fff;margin-bottom:.3rem;">&#9878; VOTACIÓN</div>', unsafe_allow_html=True)

    if not state.reveal_done:
        st.caption("El grupo debate y elige su sospechoso antes de la revelación.")
        st.markdown('<div class="section-header">&#128499; votar jugador</div>', unsafe_allow_html=True)
        player_names = [p.name for p in state.players]
        st.selectbox("Sospechoso principal:", ["— Sin seleccionar —"] + player_names)
        st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)
        if st.button("&#128269; Revelar resultado", type="primary", use_container_width=True):
            state.reveal_done = True; st.rerun()
    else:
        word = state.selected_word_entry.word
        st.markdown(f"""
        <div class="game-card" style="text-align:center;padding:1.8rem;">
            <div style="font-size:.58rem;letter-spacing:.22em;text-transform:uppercase;color:#3a3a3a;margin-bottom:.3rem;">Palabra secreta</div>
            <div style="font-family:'Bebas Neue',sans-serif;font-size:3.2rem;color:#fff;letter-spacing:.05em;">{word}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-header">&#128680; IMPOSTORES</div>', unsafe_allow_html=True)
        for p in state.players:
            if p.is_impostor:
                hint_display = p.hint or "Sin pista"
                st.markdown(f"""
                <div class="game-card red-border">
                    <div style="font-weight:700;color:#e63329;font-size:1rem;">&#9888; {p.name}</div>
                    <div style="font-size:.78rem;color:#444;margin-top:.25rem;">Pista recibida: <span style="color:#666;">{hint_display}</span></div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown('<div class="section-header">&#10003; AGENTES REGULARES</div>', unsafe_allow_html=True)
        for p in state.players:
            if not p.is_impostor:
                st.markdown(f"""
                <div class="game-card green-border">
                    <div style="font-weight:600;color:#00d264;">&#10003; {p.name}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("&#8635; Nueva ronda", type="primary", use_container_width=True):
                st.session_state.game_state = GameState()
                start_role_distribution(); st.rerun()
        with col2:
            if st.button("&#127968; Inicio", use_container_width=True):
                st.session_state.game_state  = GameState()
                st.session_state.game_config = GameConfig()
                change_state(STATE_SETUP); st.rerun()


# ╔══════════════════════════════════════════════════════════════╗
#  SECCIÓN 9 — ROUTER PRINCIPAL
# ╚══════════════════════════════════════════════════════════════╝

ROUTE_MAP = {
    STATE_SETUP:        render_setup,
    STATE_CUSTOM_WORDS: render_custom_words,
    STATE_ROLE_DIST:    render_role_distribution,
    STATE_GAME_ACTIVE:  render_game_active,
    STATE_VOTING:       render_voting,
}


def main() -> None:
    st.set_page_config(
        page_title="El Impostor",
        page_icon="🕵️",
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    init_session_state()
    renderer = ROUTE_MAP.get(st.session_state.current_state)
    if renderer:
        renderer()
    else:
        st.error(f"Estado desconocido: '{st.session_state.current_state}'")
        if st.button("Reiniciar"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


if __name__ == "__main__":
    main()