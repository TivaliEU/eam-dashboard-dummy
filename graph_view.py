import param
import panel as pn
import networkx as nx

from bokeh_graph import NetworkGraph
from data.dummy_model import nodes as all_nodes, connections as all_connections

pn.extension(sizing_mode="stretch_width")

# ---------------------------------------------------------------------------
# ArchiMate-Farbschema & Domänen-Konstanten
# ---------------------------------------------------------------------------
NODE_COLORS = {
    "business-role":          "#FFD966",
    "business-process":       "#FFAA44",
    "business-service":       "#FFE599",
    "application-component":  "#6BAED6",
    "application-service":    "#9ECAE1",
    "application-interface":  "#C6DBEF",
    "data-object":            "#74C476",
}
BUSINESS_LAYER  = {"business-role", "business-process", "business-service"}
ALL_STEREOTYPES = sorted({n.stereotypename for n in all_nodes})
ALL_RELATIONS   = sorted({c.stereotypename for c in all_connections})
uuid_to_node    = {n.uuid: n for n in all_nodes}

# ---------------------------------------------------------------------------
# Shared application state — survives filter rebuilds
# ---------------------------------------------------------------------------
class AppState(param.Parameterized):
    selected_uuid = param.String(default="")

app_state = AppState()

# ---------------------------------------------------------------------------
# Domain helpers: SimpleNamespace → NetworkGraph dicts
# ---------------------------------------------------------------------------
def archimate_layout(
    node_list, conn_list=()
) -> dict[str, tuple[float, float]]:
    """Spring-layout (Fruchterman-Reingold) via NetworkX."""
    G = nx.Graph()
    for n in node_list:
        G.add_node(n.uuid)
    for c in conn_list:
        s, t = c.sourcenode[0], c.targetnode[0]
        if G.has_node(s) and G.has_node(t):
            G.add_edge(s, t)

    raw = nx.spring_layout(G, seed=42, k=1.5)   # seed → reproduzierbar

    # Normalisieren auf [0.05, 0.95] damit Nodes nicht am Rand kleben
    xs = [p[0] for p in raw.values()]
    ys = [p[1] for p in raw.values()]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)

    def norm(v, lo, hi):
        return 0.05 + 0.9 * (v - lo) / (hi - lo) if hi != lo else 0.5

    return {
        uuid: (norm(p[0], x_min, x_max), norm(p[1], y_min, y_max))
        for uuid, p in raw.items()
    }


def to_nodes_data(node_list, pos: dict) -> list[dict]:
    return [
        {
            "id":         n.uuid,
            "label":      n.displayname,
            "x":          pos[n.uuid][0],
            "y":          pos[n.uuid][1],
            "color":      NODE_COLORS.get(n.stereotypename, "#CCCCCC"),
            "stereotype": n.stereotypename,
        }
        for n in node_list
    ]


def to_edges_data(conn_list, active_uuids: set) -> list[dict]:
    return [
        {
            "source": c.sourcenode[0],
            "target": c.targetnode[0],
            "label":  c.stereotypename,
        }
        for c in conn_list
        if c.sourcenode[0] in active_uuids and c.targetnode[0] in active_uuids
    ]

# ---------------------------------------------------------------------------
# Widgets
# ---------------------------------------------------------------------------
stereotype_filter = pn.widgets.CheckBoxGroup(
    name="Node-Typen", value=ALL_STEREOTYPES[:], options=ALL_STEREOTYPES,
)
relation_filter = pn.widgets.CheckBoxGroup(
    name="Beziehungstypen", value=ALL_RELATIONS[:], options=ALL_RELATIONS,
)

# ---------------------------------------------------------------------------
# Graph pane — rebuilt on filter change
# ---------------------------------------------------------------------------
@pn.depends(stereotype_filter, relation_filter)
def graph_pane(stereotypes, relations):
    if not stereotypes:
        return pn.pane.Markdown("_Bitte mindestens einen Node-Typ auswählen._")

    visible_nodes = [n for n in all_nodes if n.stereotypename in stereotypes]
    if not visible_nodes:
        return pn.pane.Markdown("_Keine Nodes nach aktuellem Filter._")

    active_uuids  = {n.uuid for n in visible_nodes}
    visible_conns = [c for c in all_connections
                     if c.stereotypename in relations
                     and c.sourcenode[0] in active_uuids
                     and c.targetnode[0] in active_uuids]

    pos        = archimate_layout(visible_nodes, visible_conns)
    nodes_data = to_nodes_data(visible_nodes, pos)
    edges_data = to_edges_data(visible_conns, active_uuids)

    # Reset previous selection when filters change
    app_state.selected_uuid = ""

    g = NetworkGraph(
        nodes_data,
        edges_data,
        tooltips=[("Name", "@label"), ("Stereotyp", "@stereotype")],
        show_edge_labels=True,
        on_select=lambda uid: setattr(app_state, "selected_uuid", uid),
    )

    return pn.pane.Bokeh(g.figure, sizing_mode="stretch_width")

# ---------------------------------------------------------------------------
# Detail pane — updates on node selection
# ---------------------------------------------------------------------------
@pn.depends(app_state.param.selected_uuid)
def detail_pane(uuid):
    if not uuid:
        return _empty_detail()

    node = uuid_to_node.get(uuid)
    if node is None:
        return _empty_detail()

    active_uuids = {n.uuid for n in all_nodes
                    if n.stereotypename in stereotype_filter.value}

    outgoing = [c for c in all_connections
                if c.sourcenode[0] == uuid and c.targetnode[0] in active_uuids]
    incoming = [c for c in all_connections
                if c.targetnode[0] == uuid and c.sourcenode[0] in active_uuids]

    return _build_detail(node, outgoing, incoming)


def _empty_detail():
    return pn.pane.HTML(
        '<div style="color:#aaa;font-size:13px;padding:16px 0;text-align:center">'
        '&#8592; Node anklicken'
        '</div>'
    )


def _conn_item(partner_name: str, rel_type: str, direction: str) -> str:
    arrow = "→" if direction == "out" else "←"
    bg    = "#EBF5FB" if direction == "out" else "#FEF9E7"
    return (
        f'<div style="padding:6px 8px;margin:4px 0;border-radius:5px;background:{bg};'
        f'font-size:12px;line-height:1.5">'
        f'<b>{arrow} {partner_name}</b><br>'
        f'<span style="color:#666;font-family:monospace;font-size:11px">{rel_type}</span>'
        f'</div>'
    )


def _build_detail(node, outgoing, incoming) -> pn.Column:
    color = NODE_COLORS.get(node.stereotypename, "#eee")
    parts = [
        f'<div style="background:{color};padding:10px 12px;border-radius:6px;margin-bottom:8px">'
        f'<div style="font-size:14px;font-weight:bold">{node.displayname}</div>'
        f'<div style="font-size:11px;color:#555;margin-top:3px;font-family:monospace">'
        f'{node.stereotypename}</div></div>'
    ]

    if outgoing:
        parts.append('<div style="font-size:12px;font-weight:bold;margin:10px 0 4px">Ausgehend</div>')
        for c in outgoing:
            partner = uuid_to_node.get(c.targetnode[0])
            if partner:
                parts.append(_conn_item(partner.displayname, c.stereotypename, "out"))

    if incoming:
        parts.append('<div style="font-size:12px;font-weight:bold;margin:10px 0 4px">Eingehend</div>')
        for c in incoming:
            partner = uuid_to_node.get(c.sourcenode[0])
            if partner:
                parts.append(_conn_item(partner.displayname, c.stereotypename, "in"))

    if not outgoing and not incoming:
        parts.append('<div style="color:#aaa;font-size:12px">Keine Verbindungen im Filter.</div>')

    parts.append(
        f'<div style="font-size:10px;color:#ccc;margin-top:12px;'
        f'font-family:monospace;word-break:break-all">{node.uuid}</div>'
    )

    return pn.pane.HTML("".join(parts), sizing_mode="stretch_width")

# ---------------------------------------------------------------------------
# Legende
# ---------------------------------------------------------------------------
def legend_html() -> str:
    return "".join(
        f'<div style="display:flex;align-items:center;gap:6px;margin:3px 0">'
        f'<div style="width:12px;height:12px;border-radius:50%;background:{color};'
        f'border:1px solid #aaa;flex-shrink:0"></div>'
        f'<span style="font-size:11px">{stereo}</span></div>'
        for stereo, color in NODE_COLORS.items()
    )

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
sidebar = pn.Column(
    "## Filter",
    pn.layout.Divider(),
    "**Node-Typen**",
    stereotype_filter,
    pn.layout.Divider(),
    "**Beziehungstypen**",
    relation_filter,
    pn.layout.Divider(),
    "**Legende**",
    pn.pane.HTML(legend_html()),
    width=250,
)

detail_card = pn.Card(
    detail_pane,
    title="Node-Details",
    collapsible=False,
    width=280,
    styles={"overflow-y": "auto"},
)

main_area = pn.Row(
    pn.Column(
        "# ArchiMate Graphansicht",
        pn.pane.Markdown(
            "_Business-Layer (oben) · Application-Layer (unten) · "
            "Node anklicken für Details_",
            styles={"color": "#888", "margin-bottom": "4px"},
        ),
        graph_pane,
        sizing_mode="stretch_width",
    ),
    detail_card,
    sizing_mode="stretch_width",
)

template = pn.template.FastListTemplate(
    title="EAM Graph Analyse",
    sidebar=[sidebar],
    main=[main_area],
    accent="#0072B5",
)

template.servable()

if __name__ == "__main__":
    pn.serve(template, show=True, port=5007)
