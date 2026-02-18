# 🕵️ El Impostor — Aplicación Web Pass & Play

Juego de engaño y deducción social construido con **Python + Streamlit**.

---

## 🏗️ Arquitectura

```
el_impostor/
├── app.py            # Aplicación completa (single-file, modular por secciones)
├── requirements.txt
└── README.md
```

El código está organizado en **6 capas lógicas** dentro de `app.py`:

| Capa | Responsabilidad |
|---|---|
| **MODELOS** | `GamePhase`, `WordEntry`, `PlayerCard` (dataclasses) |
| **DATASET** | `DEFAULT_WORDS` — 5 palabras × 4 pistas |
| **LÓGICA** | `GameManager` — asignación de roles, conteo de votos |
| **ESTADO** | `init_session_state`, `start_game`, `reset_game` |
| **ESTILOS** | `CUSTOM_CSS` — tema noir con fuentes Bebas Neue + DM Sans |
| **UI FASES** | Un renderer por fase de la máquina de estados |

---

## 🔄 Máquina de Estados

```
SETUP ──► DEALING ──► PLAYING ──► VOTING ──► REVEAL
  ▲                                              │
  └──────────────── reset_game() ───────────────┘
```

- **SETUP**: Configurar jugadores, impostores, pistas, banco de palabras.
- **DEALING**: Reparto Pass & Play — tarjeta por tarjeta, oculta hasta revelar.
- **PLAYING**: Ronda de pistas en el orden sugerido aleatorio.
- **VOTING**: Cada jugador elige a su sospechoso con un selectbox.
- **REVEAL**: Muestra resultados, ganador, roles y palabra secreta.

---

## 🎲 Asignación Única de Pistas para Múltiples Impostores

```python
# GameManager.assign_roles()
sample_size  = min(num_impostors, len(word.hints))
unique_hints = random.sample(word.hints, sample_size)  # SIN repetición
hint_pool    = iter(unique_hints)

# Cada impostor consume UNA pista del iterador → nunca repiten
hint = next(hint_pool, None)
```

`random.sample()` garantiza que nunca se repita la misma pista entre impostores.
Si hay más impostores que pistas disponibles, los sobrantes reciben `hint=None`.

---

## 🚀 Ejecución Local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## ☁️ Deploy en Streamlit Community Cloud

1. Sube el repositorio a GitHub.
2. Ve a [share.streamlit.io](https://share.streamlit.io).
3. Apunta al archivo `app.py`. ¡Listo!

---

## 🎮 Cómo Jugar

1. **SETUP**: Agrega los nombres de los jugadores (mínimo 3), elige cuántos impostores, activa/desactiva las pistas.
2. **DEALING**: Pasa el dispositivo a cada jugador en privado para que vea su tarjeta.
3. **PLAYING**: Cada jugador da una pista en el orden indicado.
4. **VOTING**: Todos votan a quién creen que es el impostor.
5. **REVEAL**: Se descubre quién ganó.

---

## ✅ Características

- ✔ Máquina de estados robusta con `st.session_state`
- ✔ Pistas únicas por impostor garantizadas (`random.sample`)
- ✔ Modo personalizado: gestiona tu propio banco de palabras/pistas
- ✔ Activar/desactivar pistas para impostores
- ✔ UI dark con tipografía editorial (Bebas Neue + DM Sans)
- ✔ Sin recarga accidental: toda la lógica vive en session_state
- ✔ Soporte para múltiples impostores
- ✔ Dataset de 5 palabras × 4 pistas incluido
