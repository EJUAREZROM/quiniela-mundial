import unicodedata
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import streamlit as st

# =========================
# Configuración general
# =========================
APP_TITLE = "Quiniela Mundial 2026"
PUNTOS_ACIERTO = 1  # Cambia a 3 si quieren que cada acierto valga 3 puntos.
ESPN_ENDPOINT = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"
ESPN_DATES = "20260611-20260719"
TIMEZONE = "America/Mexico_City"

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🏆",
    layout="wide",
)

# =========================
# Estilos
# =========================
st.markdown(
    """
    <style>
    .block-container {padding-top: 1.6rem; padding-bottom: 2rem;}
    .main-title {font-size: 2.1rem; font-weight: 800; margin-bottom: 0.1rem;}
    .subtitle {color: #5f6368; font-size: 1rem; margin-bottom: 1.2rem;}
    .pill {display: inline-block; padding: 0.15rem 0.55rem; border-radius: 999px; background: #f1f3f4; margin-right: 0.25rem; font-size: 0.85rem;}
    .small-note {color: #6b7280; font-size: 0.88rem;}
    div[data-testid="stMetricValue"] {font-size: 1.8rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================
# Utilidades
# =========================
def normalize_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.replace("&", "and")
    text = text.replace(".", "")
    text = text.replace("'", "")
    text = text.replace("’", "")
    return " ".join(text.split())

TEAM_ALIASES = {
    # Grupo A
    "mexico": "México",
    "mex": "México",
    "south africa": "Sudáfrica",
    "sudafrica": "Sudáfrica",
    "rsa": "Sudáfrica",
    "south korea": "Corea del Sur",
    "korea republic": "Corea del Sur",
    "corea del sur": "Corea del Sur",
    "kor": "Corea del Sur",
    "czechia": "Chequia",
    "czech republic": "Chequia",
    "chequia": "Chequia",
    "cze": "Chequia",
    # Grupo B
    "canada": "Canadá",
    "canadá": "Canadá",
    "bosnia and herzegovina": "Bosnia y Herzegovina",
    "bosnia y herzegovina": "Bosnia y Herzegovina",
    "bosnia-herzegovina": "Bosnia y Herzegovina",
    "qatar": "Qatar",
    "switzerland": "Suiza",
    "suiza": "Suiza",
    # Grupo C
    "brazil": "Brasil",
    "brasil": "Brasil",
    "morocco": "Marruecos",
    "marruecos": "Marruecos",
    "haiti": "Haití",
    "haití": "Haití",
    "scotland": "Escocia",
    "escocia": "Escocia",
    # Grupo D
    "united states": "Estados Unidos",
    "usa": "Estados Unidos",
    "us": "Estados Unidos",
    "estados unidos": "Estados Unidos",
    "paraguay": "Paraguay",
    "australia": "Australia",
    "turkey": "Turquía",
    "turkiye": "Turquía",
    "turquía": "Turquía",
    "turquia": "Turquía",
    # Grupo E
    "germany": "Alemania",
    "alemania": "Alemania",
    "curacao": "Curazao",
    "curazao": "Curazao",
    "curaçao": "Curazao",
    "ivory coast": "Costa de Marfil",
    "cote divoire": "Costa de Marfil",
    "côte divoire": "Costa de Marfil",
    "costa de marfil": "Costa de Marfil",
    "ecuador": "Ecuador",
    # Grupo F
    "netherlands": "Países Bajos",
    "paises bajos": "Países Bajos",
    "países bajos": "Países Bajos",
    "holland": "Países Bajos",
    "japan": "Japón",
    "japon": "Japón",
    "japón": "Japón",
    "sweden": "Suecia",
    "suecia": "Suecia",
    "tunisia": "Túnez",
    "tunez": "Túnez",
    "túnez": "Túnez",
    # Grupo G
    "belgium": "Bélgica",
    "belgica": "Bélgica",
    "bélgica": "Bélgica",
    "egypt": "Egipto",
    "egipto": "Egipto",
    "iran": "Irán",
    "iran islamic republic": "Irán",
    "irán": "Irán",
    "new zealand": "Nueva Zelanda",
    "nueva zelanda": "Nueva Zelanda",
    # Grupo H
    "spain": "España",
    "espana": "España",
    "españa": "España",
    "cape verde": "Cabo Verde",
    "cabo verde": "Cabo Verde",
    "saudi arabia": "Arabia Saudita",
    "arabia saudita": "Arabia Saudita",
    "uruguay": "Uruguay",
    # Grupo I
    "france": "Francia",
    "francia": "Francia",
    "senegal": "Senegal",
    "iraq": "Irak",
    "irak": "Irak",
    "norway": "Noruega",
    "noruega": "Noruega",
    # Grupo J
    "argentina": "Argentina",
    "algeria": "Argelia",
    "argelia": "Argelia",
    "austria": "Austria",
    "jordan": "Jordania",
    "jordania": "Jordania",
    # Grupo K
    "portugal": "Portugal",
    "dr congo": "RD Congo",
    "congo dr": "RD Congo",
    "democratic republic of congo": "RD Congo",
    "rd congo": "RD Congo",
    "uzbekistan": "Uzbekistán",
    "uzbekistán": "Uzbekistán",
    "uzbequistan": "Uzbekistán",
    "colombia": "Colombia",
    # Grupo L
    "england": "Inglaterra",
    "inglaterra": "Inglaterra",
    "croatia": "Croacia",
    "croacia": "Croacia",
    "ghana": "Ghana",
    "panama": "Panamá",
    "panamá": "Panamá",
}

PICK_LABELS = {
    "L": "Local",
    "E": "Empate",
    "V": "Visitante",
}

STATUS_PRIORITY = {
    "Finalizado": 3,
    "En vivo": 2,
    "Pendiente": 1,
    "Sin dato": 0,
}


def canonical_team(name: object) -> str:
    clean = normalize_text(name)
    return TEAM_ALIASES.get(clean, str(name).strip() if name is not None else "")


def get_outcome(local_score, visitor_score):
    if pd.isna(local_score) or pd.isna(visitor_score):
        return None
    if int(local_score) > int(visitor_score):
        return "L"
    if int(local_score) < int(visitor_score):
        return "V"
    return "E"


def to_numeric_score(value):
    if value in [None, "", "-"]:
        return pd.NA
    try:
        return int(float(value))
    except Exception:
        return pd.NA


@st.cache_data(ttl=600, show_spinner=False)
def load_predictions() -> pd.DataFrame:
    df = pd.read_csv("predicciones.csv")
    df["match_id"] = df["match_id"].astype(int)
    for col in ["participant", "group", "local", "visitor", "pick"]:
        df[col] = df[col].astype(str).str.strip()
    return df


@st.cache_data(ttl=600, show_spinner=False)
def load_manual_results() -> pd.DataFrame:
    try:
        df = pd.read_csv("resultados_manual.csv")
    except FileNotFoundError:
        return pd.DataFrame(columns=["match_id", "local_score", "visitor_score", "status"])

    if df.empty:
        return pd.DataFrame(columns=["match_id", "local_score", "visitor_score", "status"])

    df["match_id"] = df["match_id"].astype(int)
    if "local_score" not in df.columns:
        df["local_score"] = pd.NA
    if "visitor_score" not in df.columns:
        df["visitor_score"] = pd.NA
    if "status" not in df.columns:
        df["status"] = "Pendiente"

    df["local_score"] = df["local_score"].apply(to_numeric_score)
    df["visitor_score"] = df["visitor_score"].apply(to_numeric_score)
    df["status"] = df["status"].fillna("Pendiente")
    return df[["match_id", "local_score", "visitor_score", "status"]]


@st.cache_data(ttl=300, show_spinner=False)
def fetch_espn_results(fixtures: pd.DataFrame) -> tuple[pd.DataFrame, str, str]:
    """Trae resultados de ESPN y los cruza contra los partidos del archivo."""
    try:
        response = requests.get(
            ESPN_ENDPOINT,
            params={"dates": ESPN_DATES, "limit": 500},
            timeout=12,
        )
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        return pd.DataFrame(), "error", f"No se pudo consultar ESPN: {exc}"

    events = payload.get("events", [])
    if not events:
        return pd.DataFrame(), "warning", "ESPN respondió, pero no encontré partidos para el rango configurado."

    api_rows = []
    for event in events:
        competitions = event.get("competitions", [])
        if not competitions:
            continue
        comp = competitions[0]
        competitors = comp.get("competitors", [])
        if len(competitors) < 2:
            continue

        parsed = []
        for competitor in competitors:
            team = competitor.get("team", {})
            team_name = team.get("displayName") or team.get("shortDisplayName") or team.get("name") or ""
            score = to_numeric_score(competitor.get("score"))
            parsed.append(
                {
                    "team": canonical_team(team_name),
                    "raw_team": team_name,
                    "homeAway": competitor.get("homeAway"),
                    "score": score,
                }
            )

        home = next((row for row in parsed if row["homeAway"] == "home"), parsed[0])
        away = next((row for row in parsed if row["homeAway"] == "away"), parsed[1])
        status_type = event.get("status", {}).get("type", {})
        completed = bool(status_type.get("completed", False))
        state = str(status_type.get("state", "")).lower()
        description = status_type.get("description") or status_type.get("shortDetail") or ""

        if completed:
            status = "Finalizado"
        elif state == "in":
            status = "En vivo"
        else:
            status = "Pendiente"

        api_rows.append(
            {
                "api_event_id": event.get("id"),
                "home_team": home["team"],
                "away_team": away["team"],
                "home_score": home["score"],
                "away_score": away["score"],
                "api_status": status,
                "api_status_detail": description,
            }
        )

    matched = []
    for _, fixture in fixtures.iterrows():
        local = canonical_team(fixture["local"])
        visitor = canonical_team(fixture["visitor"])
        candidates = []
        for row in api_rows:
            same_order = row["home_team"] == local and row["away_team"] == visitor
            reverse_order = row["home_team"] == visitor and row["away_team"] == local
            if same_order or reverse_order:
                candidates.append((row, same_order, reverse_order))

        if not candidates:
            continue

        # Si hay duplicados, preferimos finalizado > en vivo > pendiente.
        candidates = sorted(
            candidates,
            key=lambda item: STATUS_PRIORITY.get(item[0]["api_status"], 0),
            reverse=True,
        )
        row, same_order, reverse_order = candidates[0]

        if same_order:
            local_score = row["home_score"]
            visitor_score = row["away_score"]
        else:
            local_score = row["away_score"]
            visitor_score = row["home_score"]

        matched.append(
            {
                "match_id": int(fixture["match_id"]),
                "local_score": local_score,
                "visitor_score": visitor_score,
                "status": row["api_status"],
                "api_event_id": row["api_event_id"],
            }
        )

    result = pd.DataFrame(matched)
    return result, "ok", f"Resultados cruzados desde ESPN: {len(result)} de {len(fixtures)} partidos."


def build_matches(predictions: pd.DataFrame) -> tuple[pd.DataFrame, str, str]:
    fixtures = predictions[["match_id", "group", "local", "visitor"]].drop_duplicates().sort_values("match_id")
    manual = load_manual_results()
    api, api_status, api_message = fetch_espn_results(fixtures)

    matches = fixtures.merge(manual, on="match_id", how="left")
    matches["status"] = matches["status"].fillna("Pendiente")

    if not api.empty:
        api_cols = api.rename(
            columns={
                "local_score": "api_local_score",
                "visitor_score": "api_visitor_score",
                "status": "api_status",
            }
        )
        matches = matches.merge(api_cols, on="match_id", how="left")

        has_api_score = matches["api_local_score"].notna() & matches["api_visitor_score"].notna()
        matches.loc[has_api_score, "local_score"] = matches.loc[has_api_score, "api_local_score"]
        matches.loc[has_api_score, "visitor_score"] = matches.loc[has_api_score, "api_visitor_score"]
        matches.loc[matches["api_status"].notna(), "status"] = matches.loc[matches["api_status"].notna(), "api_status"]

    matches["local_score"] = matches["local_score"].apply(to_numeric_score)
    matches["visitor_score"] = matches["visitor_score"].apply(to_numeric_score)
    matches["resultado"] = matches.apply(lambda r: get_outcome(r["local_score"], r["visitor_score"]), axis=1)
    matches["resultado_texto"] = matches["resultado"].map(PICK_LABELS).fillna("-")
    matches["marcador"] = matches.apply(
        lambda r: "-" if pd.isna(r["local_score"]) or pd.isna(r["visitor_score"]) else f"{int(r['local_score'])} - {int(r['visitor_score'])}",
        axis=1,
    )
    return matches, api_status, api_message


def build_scores(predictions: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
    detail = predictions.merge(
        matches[["match_id", "status", "local_score", "visitor_score", "resultado", "resultado_texto", "marcador"]],
        on="match_id",
        how="left",
    )
    detail["prediccion"] = detail["pick"].map(PICK_LABELS).fillna(detail["pick"])
    detail["partido_finalizado"] = detail["status"].eq("Finalizado") & detail["resultado"].notna()
    detail["puntos"] = ((detail["pick"] == detail["resultado"]) & detail["partido_finalizado"]).astype(int) * PUNTOS_ACIERTO

    ranking = (
        detail.groupby("participant", as_index=False)
        .agg(
            puntos=("puntos", "sum"),
            aciertos=("puntos", lambda x: int((x > 0).sum())),
            partidos_calificados=("partido_finalizado", "sum"),
            total_predicciones=("match_id", "count"),
        )
        .sort_values(["puntos", "aciertos", "participant"], ascending=[False, False, True])
    )
    ranking["efectividad"] = ranking.apply(
        lambda r: 0 if r["partidos_calificados"] == 0 else r["aciertos"] / r["partidos_calificados"],
        axis=1,
    )
    ranking.insert(0, "lugar", range(1, len(ranking) + 1))
    return detail, ranking


# =========================
# App
# =========================
st.markdown(f'<div class="main-title">🏆 {APP_TITLE}</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Ranking automático de la quiniela con resultados del Mundial y consulta de predicciones por participante.</div>',
    unsafe_allow_html=True,
)

col_action, col_note = st.columns([1, 4])
with col_action:
    if st.button("🔄 Actualizar resultados"):
        st.cache_data.clear()
        st.rerun()
with col_note:
    now = datetime.now(ZoneInfo(TIMEZONE)).strftime("%d/%m/%Y %H:%M")
    st.markdown(f'<span class="small-note">Última carga de la página: {now} · Regla actual: {PUNTOS_ACIERTO} punto por resultado correcto.</span>', unsafe_allow_html=True)

predictions = load_predictions()
matches, api_status, api_message = build_matches(predictions)
detail, ranking = build_scores(predictions, matches)

if api_status == "ok":
    st.success(api_message, icon="✅")
elif api_status == "warning":
    st.warning(api_message, icon="⚠️")
else:
    st.warning(api_message + " Se usará resultados_manual.csv como respaldo.", icon="⚠️")

finished_matches = int(matches["status"].eq("Finalizado").sum())
live_matches = int(matches["status"].eq("En vivo").sum())
total_matches = int(matches["match_id"].nunique())
leader = ranking.iloc[0] if not ranking.empty else None

k1, k2, k3, k4 = st.columns(4)
k1.metric("Líder", leader["participant"] if leader is not None else "-")
k2.metric("Puntos del líder", int(leader["puntos"]) if leader is not None else 0)
k3.metric("Partidos calificados", f"{finished_matches}/{total_matches}")
k4.metric("Partidos en vivo", live_matches)

tab_ranking, tab_persona, tab_partidos, tab_reglas = st.tabs([
    "🏅 Ranking",
    "👤 Predicciones por persona",
    "⚽ Partidos y resultados",
    "ℹ️ Reglas / datos",
])

with tab_ranking:
    st.subheader("Ranking general")
    ranking_view = ranking.copy()
    ranking_view["efectividad"] = (ranking_view["efectividad"] * 100).round(1).astype(str) + "%"
    st.dataframe(
        ranking_view.rename(
            columns={
                "lugar": "Lugar",
                "participant": "Participante",
                "puntos": "Puntos",
                "aciertos": "Aciertos",
                "partidos_calificados": "Partidos calificados",
                "total_predicciones": "Predicciones totales",
                "efectividad": "Efectividad",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

    chart_df = ranking.set_index("participant")[["puntos"]].sort_values("puntos", ascending=True)
    st.bar_chart(chart_df)

    st.markdown("**Desempate sugerido:** primero puntos, después aciertos, después orden alfabético. Si quieren otro criterio lo cambiamos.")

with tab_persona:
    st.subheader("Consulta de predicciones")
    c1, c2, c3 = st.columns([1.4, 1, 1])
    with c1:
        participant = st.selectbox("Selecciona participante", sorted(predictions["participant"].unique()))
    with c2:
        groups = ["Todos"] + sorted(predictions["group"].unique())
        selected_group = st.selectbox("Grupo", groups)
    with c3:
        status_options = ["Todos", "Finalizado", "En vivo", "Pendiente"]
        selected_status = st.selectbox("Estatus", status_options)

    person_df = detail[detail["participant"] == participant].copy()
    if selected_group != "Todos":
        person_df = person_df[person_df["group"] == selected_group]
    if selected_status != "Todos":
        person_df = person_df[person_df["status"] == selected_status]

    total_points = int(person_df["puntos"].sum())
    total_hits = int((person_df["puntos"] > 0).sum())
    evaluated = int(person_df["partido_finalizado"].sum())
    p1, p2, p3 = st.columns(3)
    p1.metric("Puntos filtrados", total_points)
    p2.metric("Aciertos filtrados", total_hits)
    p3.metric("Partidos finalizados filtrados", evaluated)

    person_view = person_df[[
        "match_id", "group", "local", "visitor", "prediccion", "status", "marcador", "resultado_texto", "puntos"
    ]].sort_values("match_id")
    st.dataframe(
        person_view.rename(
            columns={
                "match_id": "ID",
                "group": "Grupo",
                "local": "Local",
                "visitor": "Visitante",
                "prediccion": "Predicción",
                "status": "Estatus",
                "marcador": "Marcador",
                "resultado_texto": "Resultado",
                "puntos": "Puntos",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

with tab_partidos:
    st.subheader("Partidos y resultados detectados")
    c1, c2 = st.columns(2)
    with c1:
        group_filter = st.selectbox("Filtrar grupo", ["Todos"] + sorted(matches["group"].unique()), key="match_group")
    with c2:
        status_filter = st.selectbox("Filtrar estatus", ["Todos", "Finalizado", "En vivo", "Pendiente"], key="match_status")

    matches_view = matches.copy()
    if group_filter != "Todos":
        matches_view = matches_view[matches_view["group"] == group_filter]
    if status_filter != "Todos":
        matches_view = matches_view[matches_view["status"] == status_filter]

    st.dataframe(
        matches_view[["match_id", "group", "local", "visitor", "status", "marcador", "resultado_texto"]]
        .sort_values("match_id")
        .rename(
            columns={
                "match_id": "ID",
                "group": "Grupo",
                "local": "Local",
                "visitor": "Visitante",
                "status": "Estatus",
                "marcador": "Marcador",
                "resultado_texto": "Resultado",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

    missing = matches[matches["local_score"].isna() | matches["visitor_score"].isna()]
    if not missing.empty:
        st.caption(f"Partidos sin marcador todavía: {len(missing)}. Es normal si aún no se juegan o si la API no los regresó.")

with tab_reglas:
    st.subheader("Reglas y notas técnicas")
    st.markdown(
        f"""
        - El archivo trae predicciones **L/E/V**: **Local**, **Empate** o **Visitante**.
        - Regla configurada: **{PUNTOS_ACIERTO} punto por acierto** cuando el partido aparece como finalizado.
        - El dashboard intenta leer marcadores desde ESPN y cruza los partidos por nombre de equipos.
        - Si la API no responde, puedes actualizar manualmente `resultados_manual.csv` con `local_score`, `visitor_score` y `status`.
        - Para cambiar la puntuación, modifica la variable `PUNTOS_ACIERTO` al inicio de `app.py`.
        """
    )
    st.markdown("**Archivos que debe tener el repositorio:**")
    st.code("app.py\npredicciones.csv\nresultados_manual.csv\nrequirements.txt", language="text")
