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
PUNTOS_ACIERTO = 1
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
    .block-container {
        padding-top: 1.1rem;
        padding-bottom: 2rem;
        max-width: 1350px;
    }
    .main {
        background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
    }
    .hero {
        background: linear-gradient(135deg, #0f172a 0%, #14532d 55%, #166534 100%);
        color: white;
        padding: 1.35rem 1.5rem;
        border-radius: 22px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.16);
        margin-bottom: 1rem;
    }
    .hero h1 {
        margin: 0;
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.03em;
    }
    .hero p {
        margin: 0.45rem 0 0 0;
        color: rgba(255,255,255,0.88);
        font-size: 1rem;
    }
    .hero-mini {
        margin-top: 0.75rem;
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
    }
    .mini-chip {
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.18);
        padding: 0.35rem 0.7rem;
        border-radius: 999px;
        font-size: 0.86rem;
    }
    .section-title {
        font-size: 1.5rem;
        font-weight: 800;
        margin: 0.25rem 0 0.9rem 0;
        color: #111827;
    }
    .small-note {
        color: #6b7280;
        font-size: 0.9rem;
    }
    .podium-card {
        border-radius: 22px;
        padding: 1rem 1rem 0.9rem 1rem;
        color: #111827;
        min-height: 150px;
        box-shadow: 0 10px 24px rgba(15,23,42,0.10);
        border: 1px solid rgba(15,23,42,0.06);
        margin-bottom: 0.3rem;
    }
    .podium-gold {background: linear-gradient(135deg, #fff8dc 0%, #fde68a 100%);}
    .podium-silver {background: linear-gradient(135deg, #f9fafb 0%, #e5e7eb 100%);}
    .podium-bronze {background: linear-gradient(135deg, #fff7ed 0%, #fdba74 100%);}
    .podium-place {font-size: 0.9rem; font-weight: 700; opacity: 0.85;}
    .podium-name {font-size: 1.55rem; font-weight: 800; margin-top: 0.1rem;}
    .podium-points {font-size: 2rem; font-weight: 900; line-height: 1.1; margin-top: 0.45rem;}
    .podium-meta {font-size: 0.93rem; color: #374151; margin-top: 0.45rem;}
    .info-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        padding: 1rem 1rem 0.9rem 1rem;
        box-shadow: 0 6px 18px rgba(15,23,42,0.06);
    }
    .label-muted {font-size: 0.88rem; color: #6b7280;}
    .value-strong {font-size: 1.25rem; font-weight: 800; color: #111827;}
    .status-ok {
        background: #ecfdf5;
        color: #065f46;
        border: 1px solid #a7f3d0;
        padding: 0.75rem 0.95rem;
        border-radius: 14px;
        margin-bottom: 0.8rem;
        font-weight: 600;
    }
    .status-warn {
        background: #fff7ed;
        color: #9a3412;
        border: 1px solid #fdba74;
        padding: 0.75rem 0.95rem;
        border-radius: 14px;
        margin-bottom: 0.8rem;
        font-weight: 600;
    }
    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e5e7eb;
        padding: 0.8rem 1rem;
        border-radius: 18px;
        box-shadow: 0 6px 18px rgba(15,23,42,0.06);
    }
    div[data-testid="stMetricLabel"] {
        font-weight: 600;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.75rem;
        font-weight: 800;
    }
    button[kind="primary"] {
        border-radius: 12px;
    }
    div[data-baseweb="tab-list"] {
        gap: 0.3rem;
    }
    button[data-baseweb="tab"] {
        height: 45px;
        background: #f3f4f6;
        border-radius: 12px 12px 0 0;
        padding-left: 1rem;
        padding-right: 1rem;
        font-weight: 700;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background: #166534;
        color: white;
    }
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
    "mexico": "México", "mex": "México",
    "south africa": "Sudáfrica", "sudafrica": "Sudáfrica", "rsa": "Sudáfrica",
    "south korea": "Corea del Sur", "korea republic": "Corea del Sur", "corea del sur": "Corea del Sur", "kor": "Corea del Sur",
    "czechia": "Chequia", "czech republic": "Chequia", "chequia": "Chequia", "cze": "Chequia",
    "canada": "Canadá", "canadá": "Canadá",
    "bosnia and herzegovina": "Bosnia y Herzegovina", "bosnia y herzegovina": "Bosnia y Herzegovina", "bosnia-herzegovina": "Bosnia y Herzegovina",
    "qatar": "Qatar", "switzerland": "Suiza", "suiza": "Suiza",
    "brazil": "Brasil", "brasil": "Brasil", "morocco": "Marruecos", "marruecos": "Marruecos", "haiti": "Haití", "haití": "Haití", "scotland": "Escocia", "escocia": "Escocia",
    "united states": "Estados Unidos", "usa": "Estados Unidos", "us": "Estados Unidos", "estados unidos": "Estados Unidos", "paraguay": "Paraguay", "australia": "Australia", "turkey": "Turquía", "turkiye": "Turquía", "turquía": "Turquía", "turquia": "Turquía",
    "germany": "Alemania", "alemania": "Alemania", "curacao": "Curazao", "curazao": "Curazao", "curaçao": "Curazao", "ivory coast": "Costa de Marfil", "cote divoire": "Costa de Marfil", "côte divoire": "Costa de Marfil", "costa de marfil": "Costa de Marfil", "ecuador": "Ecuador",
    "netherlands": "Países Bajos", "paises bajos": "Países Bajos", "países bajos": "Países Bajos", "holland": "Países Bajos", "japan": "Japón", "japon": "Japón", "japón": "Japón", "sweden": "Suecia", "suecia": "Suecia", "tunisia": "Túnez", "tunez": "Túnez", "túnez": "Túnez",
    "belgium": "Bélgica", "belgica": "Bélgica", "bélgica": "Bélgica", "egypt": "Egipto", "egipto": "Egipto", "iran": "Irán", "iran islamic republic": "Irán", "irán": "Irán", "new zealand": "Nueva Zelanda", "nueva zelanda": "Nueva Zelanda",
    "spain": "España", "espana": "España", "españa": "España", "cape verde": "Cabo Verde", "cabo verde": "Cabo Verde", "saudi arabia": "Arabia Saudita", "arabia saudita": "Arabia Saudita", "uruguay": "Uruguay",
    "france": "Francia", "francia": "Francia", "senegal": "Senegal", "iraq": "Irak", "irak": "Irak", "norway": "Noruega", "noruega": "Noruega",
    "argentina": "Argentina", "algeria": "Argelia", "argelia": "Argelia", "austria": "Austria", "jordan": "Jordania", "jordania": "Jordania",
    "portugal": "Portugal", "dr congo": "RD Congo", "congo dr": "RD Congo", "democratic republic of congo": "RD Congo", "rd congo": "RD Congo", "uzbekistan": "Uzbekistán", "uzbekistán": "Uzbekistán", "uzbequistan": "Uzbekistán", "colombia": "Colombia",
    "england": "Inglaterra", "inglaterra": "Inglaterra", "croatia": "Croacia", "croacia": "Croacia", "ghana": "Ghana", "panama": "Panamá", "panamá": "Panamá",
}

PICK_LABELS = {"L": "Local", "E": "Empate", "V": "Visitante"}
STATUS_PRIORITY = {"Finalizado": 3, "En vivo": 2, "Pendiente": 1, "Sin dato": 0}
STATUS_EMOJI = {"Finalizado": "✅", "En vivo": "🔴", "Pendiente": "🕒", "Sin dato": "⚪"}
PICK_EMOJI = {"Local": "🏠", "Empate": "🤝", "Visitante": "✈️"}


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


def label_status(status: str) -> str:
    status = str(status)
    return f"{STATUS_EMOJI.get(status, '⚪')} {status}"


def render_podium_card(place: int, name: str, points: int, accuracy: float, hits: int, finished: int):
    classes = {1: "podium-gold", 2: "podium-silver", 3: "podium-bronze"}
    medals = {1: "🥇 1er lugar", 2: "🥈 2do lugar", 3: "🥉 3er lugar"}
    st.markdown(
        f"""
        <div class="podium-card {classes.get(place, 'podium-silver')}">
            <div class="podium-place">{medals.get(place, f'{place}° lugar')}</div>
            <div class="podium-name">{name}</div>
            <div class="podium-points">{points} pts</div>
            <div class="podium-meta">Aciertos: {hits} · Efectividad: {accuracy:.1%} · Calificados: {finished}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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
def fetch_espn_results(fixtures: pd.DataFrame):
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

        candidates = sorted(candidates, key=lambda item: STATUS_PRIORITY.get(item[0]["api_status"], 0), reverse=True)
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


def build_matches(predictions: pd.DataFrame):
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
    matches["partido"] = matches["local"] + " vs " + matches["visitor"]
    matches["status_label"] = matches["status"].apply(label_status)
    return matches, api_status, api_message


def build_scores(predictions: pd.DataFrame, matches: pd.DataFrame):
    detail = predictions.merge(
        matches[["match_id", "status", "local_score", "visitor_score", "resultado", "resultado_texto", "marcador", "partido", "status_label"]],
        on="match_id",
        how="left",
    )
    detail["prediccion"] = detail["pick"].map(PICK_LABELS).fillna(detail["pick"])
    detail["prediccion_label"] = detail["prediccion"].apply(lambda x: f"{PICK_EMOJI.get(x, '⚽')} {x}")
    detail["partido_finalizado"] = detail["status"].eq("Finalizado") & detail["resultado"].notna()
    detail["puntos"] = ((detail["pick"] == detail["resultado"]) & detail["partido_finalizado"]).astype(int) * PUNTOS_ACIERTO
    detail["acerto"] = detail["puntos"] > 0

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
predictions = load_predictions()
matches, api_status, api_message = build_matches(predictions)
detail, ranking = build_scores(predictions, matches)

last_update = datetime.now(ZoneInfo(TIMEZONE)).strftime("%d/%m/%Y %H:%M")
finished_matches = int(matches["status"].eq("Finalizado").sum())
live_matches = int(matches["status"].eq("En vivo").sum())
pending_matches = int(matches["status"].eq("Pendiente").sum())
total_matches = int(matches["match_id"].nunique())
participants_count = int(predictions["participant"].nunique())
leader = ranking.iloc[0] if not ranking.empty else None
second = ranking.iloc[1] if len(ranking) > 1 else None

st.markdown(
    f"""
    <div class="hero">
        <h1>🏆 {APP_TITLE}</h1>
        <p>Ranking automático de la quiniela, consulta de predicciones y seguimiento de resultados del Mundial.</p>
        <div class="hero-mini">
            <div class="mini-chip">👥 {participants_count} participantes</div>
            <div class="mini-chip">⚽ {total_matches} partidos</div>
            <div class="mini-chip">✅ {finished_matches} calificados</div>
            <div class="mini-chip">🕒 Actualizado: {last_update}</div>
            <div class="mini-chip">📌 Regla: {PUNTOS_ACIERTO} punto por acierto</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

c_refresh, c_note = st.columns([1, 3])
with c_refresh:
    if st.button("🔄 Actualizar resultados", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()
with c_note:
    st.markdown(
        "<div class='small-note'>Tip: si actualizas resultados manualmente o cambia la API, usa este botón para recalcular el ranking.</div>",
        unsafe_allow_html=True,
    )

if api_status == "ok":
    st.markdown(f"<div class='status-ok'>✅ {api_message}</div>", unsafe_allow_html=True)
elif api_status == "warning":
    st.markdown(f"<div class='status-warn'>⚠️ {api_message}</div>", unsafe_allow_html=True)
else:
    st.markdown(f"<div class='status-warn'>⚠️ {api_message} Se usará resultados_manual.csv como respaldo.</div>", unsafe_allow_html=True)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Líder actual", leader["participant"] if leader is not None else "-")
k2.metric("Puntos del líder", int(leader["puntos"]) if leader is not None else 0)
k3.metric("Partidos calificados", f"{finished_matches}/{total_matches}")
k4.metric("Partidos en vivo", live_matches)

st.markdown("<div class='section-title'>Podio de la quiniela</div>", unsafe_allow_html=True)
p1, p2, p3 = st.columns(3)
with p1:
    if len(ranking) >= 1:
        row = ranking.iloc[0]
        render_podium_card(1, row["participant"], int(row["puntos"]), float(row["efectividad"]), int(row["aciertos"]), int(row["partidos_calificados"]))
with p2:
    if len(ranking) >= 2:
        row = ranking.iloc[1]
        render_podium_card(2, row["participant"], int(row["puntos"]), float(row["efectividad"]), int(row["aciertos"]), int(row["partidos_calificados"]))
with p3:
    if len(ranking) >= 3:
        row = ranking.iloc[2]
        render_podium_card(3, row["participant"], int(row["puntos"]), float(row["efectividad"]), int(row["aciertos"]), int(row["partidos_calificados"]))

extra1, extra2, extra3 = st.columns(3)
with extra1:
    chase = 0
    if leader is not None and second is not None:
        chase = int(leader["puntos"] - second["puntos"])
    st.markdown(f"<div class='info-card'><div class='label-muted'>Diferencia con 2do lugar</div><div class='value-strong'>{chase} pts</div></div>", unsafe_allow_html=True)
with extra2:
    best_eff = ranking.sort_values(["efectividad", "aciertos"], ascending=[False, False]).iloc[0] if not ranking.empty else None
    best_eff_txt = f"{best_eff['participant']} · {best_eff['efectividad']:.1%}" if best_eff is not None else "-"
    st.markdown(f"<div class='info-card'><div class='label-muted'>Mejor efectividad</div><div class='value-strong'>{best_eff_txt}</div></div>", unsafe_allow_html=True)
with extra3:
    st.markdown(f"<div class='info-card'><div class='label-muted'>Pendientes por jugar</div><div class='value-strong'>{pending_matches}</div></div>", unsafe_allow_html=True)


tab_ranking, tab_persona, tab_partidos, tab_reglas = st.tabs([
    "🏅 Ranking",
    "👤 Predicciones por persona",
    "⚽ Partidos y resultados",
    "ℹ️ Reglas / datos",
])

with tab_ranking:
    st.markdown("<div class='section-title'>Ranking general</div>", unsafe_allow_html=True)

    ranking_view = ranking.copy()
    ranking_view["efectividad"] = (ranking_view["efectividad"] * 100).round(1)
    ranking_view["racha"] = ranking_view["puntos"].apply(lambda x: "🔥" if x == ranking["puntos"].max() else "")

    st.dataframe(
        ranking_view.rename(
            columns={
                "lugar": "Lugar",
                "participant": "Participante",
                "puntos": "Puntos",
                "aciertos": "Aciertos",
                "partidos_calificados": "Calificados",
                "total_predicciones": "Predicciones",
                "efectividad": "Efectividad %",
                "racha": "Forma",
            }
        ),
        hide_index=True,
        use_container_width=True,
        column_config={
            "Lugar": st.column_config.NumberColumn(format="%d"),
            "Puntos": st.column_config.NumberColumn(format="%d pts"),
            "Aciertos": st.column_config.NumberColumn(format="%d"),
            "Calificados": st.column_config.NumberColumn(format="%d"),
            "Predicciones": st.column_config.NumberColumn(format="%d"),
            "Efectividad %": st.column_config.ProgressColumn(
                "Efectividad %",
                min_value=0,
                max_value=100,
                format="%.1f%%",
            ),
        },
    )

    chart_df = ranking[["participant", "puntos"]].sort_values("puntos", ascending=False).set_index("participant")
    st.bar_chart(chart_df)

    st.caption("Desempate actual: puntos, luego aciertos y después orden alfabético.")

with tab_persona:
    st.markdown("<div class='section-title'>Consulta de predicciones</div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1.35, 1, 1])
    with c1:
        participant = st.selectbox("Selecciona participante", sorted(predictions["participant"].unique()))
    with c2:
        groups = ["Todos"] + sorted(predictions["group"].unique())
        selected_group = st.selectbox("Grupo", groups)
    with c3:
        status_options = ["Todos", "Finalizado", "En vivo", "Pendiente"]
        selected_status = st.selectbox("Estatus", status_options)

    person_df = detail[detail["participant"] == participant].copy()
    person_rank_row = ranking[ranking["participant"] == participant].iloc[0]
    if selected_group != "Todos":
        person_df = person_df[person_df["group"] == selected_group]
    if selected_status != "Todos":
        person_df = person_df[person_df["status"] == selected_status]

    stat1, stat2, stat3, stat4 = st.columns(4)
    stat1.metric("Lugar actual", int(person_rank_row["lugar"]))
    stat2.metric("Puntos totales", int(person_rank_row["puntos"]))
    stat3.metric("Aciertos totales", int(person_rank_row["aciertos"]))
    stat4.metric("Efectividad", f"{person_rank_row['efectividad']:.1%}")

    person_view = person_df[[
        "match_id", "group", "partido", "prediccion_label", "status_label", "marcador", "resultado_texto", "puntos"
    ]].sort_values("match_id")

    st.dataframe(
        person_view.rename(
            columns={
                "match_id": "ID",
                "group": "Grupo",
                "partido": "Partido",
                "prediccion_label": "Predicción",
                "status_label": "Estatus",
                "marcador": "Marcador",
                "resultado_texto": "Resultado real",
                "puntos": "Puntos",
            }
        ),
        hide_index=True,
        use_container_width=True,
        column_config={
            "Puntos": st.column_config.NumberColumn(format="%d pts"),
        },
    )

with tab_partidos:
    st.markdown("<div class='section-title'>Partidos y resultados</div>", unsafe_allow_html=True)
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

    topa, topb, topc = st.columns(3)
    topa.metric("Finalizados", finished_matches)
    topb.metric("En vivo", live_matches)
    topc.metric("Pendientes", pending_matches)

    st.dataframe(
        matches_view[["match_id", "group", "partido", "status_label", "marcador", "resultado_texto"]]
        .sort_values("match_id")
        .rename(
            columns={
                "match_id": "ID",
                "group": "Grupo",
                "partido": "Partido",
                "status_label": "Estatus",
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
    st.markdown("<div class='section-title'>Reglas y notas</div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        - Las predicciones se leen como **L/E/V**: **Local**, **Empate** o **Visitante**.
        - Regla actual: **{PUNTOS_ACIERTO} punto por acierto** cuando el partido aparece como finalizado.
        - Los marcadores se intentan consultar desde ESPN y se cruzan por nombres de equipos.
        - Si la API no responde, el dashboard usa el archivo **resultados_manual.csv** como respaldo.
        - Puedes cambiar la puntuación modificando la variable **PUNTOS_ACIERTO** al inicio de `app.py`.
        """
    )
    st.markdown("**Archivos esperados en el repositorio**")
    st.code("app.py\npredicciones.csv\nresultados_manual.csv\nrequirements.txt", language="text")
