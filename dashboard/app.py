"""Dashboard Dash : graphiques interactifs, filtres, insights. Valeurs manquantes en gris."""
import sys
import os
# Ajoute le dossier racine du projet au PATH de Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import plotly.graph_objects as go
from dash import Dash, Input, Output, dcc, html

from backend.data_processing import MISSING, missing_report
from backend.database import read_offers_df
from backend.services import apply_filters, compute_stats, get_clean_df

from . import theme

MISSING_LABELS = {"domain": "Domaine", "city": "Ville", "level": "Niveau", "salary_mad": "Rémunération",
                  "deadline": "Date limite", "posted_date": "Date de publication", "skills": "Compétences"}


def _style(fig, title, note=None, height=370):
    text = f"<b>{title}</b>" + (f"<br><span style='font-size:12px;color:{theme.GREY}'>{note}</span>" if note else "")
    fig.update_layout(title=dict(text=text, x=0.02, font=dict(size=16, color=theme.PRIMARY)), height=height,
                      font=dict(family=theme.FONT, color=theme.TEXT), paper_bgcolor="white", plot_bgcolor="white",
                      margin=dict(l=10, r=30, t=75, b=20), showlegend=False)
    fig.update_xaxes(gridcolor="#E2E8F0", zeroline=False)
    fig.update_yaxes(gridcolor="#E2E8F0", zeroline=False)
    return fig


def _note(df, col, label):
    n = int((df[col] == MISSING).sum())
    return f"{n} offre(s) sans {label} (en gris)" if n else None


def _hbar(series, color_fn, title, note=None):
    s = series.sort_values()
    fig = go.Figure(go.Bar(x=s.values, y=list(s.index), orientation="h", text=s.values, textposition="outside",
                           marker_color=[color_fn(i) for i in s.index], hovertemplate="%{y} : %{x}<extra></extra>"))
    return _style(fig, title, note)


def _color(label):
    return theme.GREY if label == MISSING else theme.ACCENT


def empty_fig(msg="Aucune offre pour ces filtres"):
    fig = go.Figure()
    fig.add_annotation(text=msg, showarrow=False, font=dict(size=15, color=theme.GREY))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return _style(fig, " ")


def build_figures(df):
    """Retourne les 6 figures à partir d'un DataFrame propre (testable sans Dash)."""
    if df.empty:
        return [empty_fig() for _ in range(6)]
    f_city = _hbar(df["city"].value_counts(), _color, "Offres par ville", _note(df, "city", "ville"))

    contracts = df["contract"].value_counts()
    colors = [theme.GREY if c == MISSING else theme.BLUES[i % len(theme.BLUES)] for i, c in enumerate(contracts.index)]
    f_contract = go.Figure(go.Pie(labels=list(contracts.index), values=contracts.values, hole=0.55, sort=False,
                                  marker=dict(colors=colors, line=dict(color="white", width=2)), textinfo="percent"))
    _style(f_contract, "Répartition par type d'offre", _note(df, "contract", "type"))
    f_contract.update_layout(showlegend=True, legend=dict(orientation="v", x=1.0, y=0.5))

    top = df[df["company"] != MISSING]["company"].value_counts().head(10)
    f_comp = _hbar(top, lambda _: theme.PRIMARY, "Top 10 des entreprises qui recrutent") if len(top) else empty_fig("Aucune entreprise renseignée")

    monthly = df.groupby(df["posted_date"].dt.to_period("M").dt.to_timestamp()).size()
    est = int(df["date_imputed"].sum())
    f_time = go.Figure(go.Scatter(x=monthly.index, y=monthly.values, mode="lines+markers", line=dict(color=theme.ACCENT, width=3),
                                  fill="tozeroy", fillcolor="rgba(59,130,246,0.15)", hovertemplate="%{x|%b %Y} : %{y} offres<extra></extra>"))
    _style(f_time, "Évolution des offres dans le temps", f"{est} date(s) estimée(s) à partir de la date de collecte" if est else None)

    f_domain = _hbar(df["domain"].value_counts(), _color, "Répartition par domaine / filière", _note(df, "domain", "domaine"))

    rep = missing_report(read_offers_df())
    rep = rep[rep["colonne"].isin(MISSING_LABELS)].sort_values("pourcentage")
    f_missing = go.Figure(go.Bar(x=rep["pourcentage"], y=[MISSING_LABELS[c] for c in rep["colonne"]], orientation="h",
                                 marker_color=[theme.PRIMARY if v < 10 else theme.ACCENT if v < 30 else theme.GREY for v in rep["pourcentage"]],
                                 text=[f"{v} %" for v in rep["pourcentage"]], textposition="outside"))
    _style(f_missing, "Qualité des données : % de valeurs manquantes", "Calculé sur toutes les offres brutes")
    f_missing.update_xaxes(range=[0, 110], title="%")
    return [f_city, f_contract, f_comp, f_time, f_domain, f_missing]


def _kpi(value, label):
    return html.Div(className="kpi", children=[html.B(value), html.Span(label)])


def create_dash_app():
    app = Dash(__name__, requests_pathname_prefix="/dashboard/", routes_pathname_prefix="/",
               title="OPPORTUNITEMAROC — Statistiques", update_title=None)

    def serve_layout():  # recalculé à chaque chargement de page
        df = get_clean_df()
        dropdown = lambda col, label: dcc.Dropdown(  # noqa: E731
            id=f"f-{col}", multi=True, placeholder=label,
            options=[{"label": v, "value": v} for v in sorted(df[col].unique()) if v != MISSING])
        graph = lambda gid: html.Div(className="card", children=[dcc.Graph(id=gid, config={"displayModeBar": False})])  # noqa: E731
        return html.Div(className="page", children=[
            html.Div(className="hero", children=[html.H1("Statistiques & Insights"),
                                                 html.P("Explorez le marché des stages et emplois digitaux au Maroc.")]),
            html.Div(className="filters", children=[dropdown("city", "Ville"), dropdown("contract", "Type d'offre"), dropdown("domain", "Domaine")]),
            html.Div(id="kpis", className="kpis"),
            html.Div(className="grid", children=[graph(g) for g in ("g-city", "g-contract", "g-comp", "g-time", "g-domain", "g-missing")]),
            html.Div(id="insights", className="insights"),
        ])

    app.layout = serve_layout

    @app.callback([Output("kpis", "children")] + [Output(g, "figure") for g in ("g-city", "g-contract", "g-comp", "g-time", "g-domain", "g-missing")]
                  + [Output("insights", "children")],
                  [Input("f-city", "value"), Input("f-contract", "value"), Input("f-domain", "value")])
    def update(city, contract, domain):
        df = apply_filters(get_clean_df(), city=city or [], contract=contract or [], domain=domain or [])
        st = compute_stats(df)
        kpis = [_kpi(st["total"], "offres"), _kpi(st["cities"], "villes"), _kpi(st["companies"], "entreprises"),
                _kpi(f"{st['salary_share']} %", "avec rémunération indiquée")]
        insights = [html.H3("Insights"), html.Ul([html.Li(t) for t in st["insights"]])]
        return [kpis, *build_figures(df), insights]

    return app
