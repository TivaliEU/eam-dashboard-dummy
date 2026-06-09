import panel as pn
import networkx as nx
import hvplot.networkx as hvnx
import holoviews as hv
import pandas as pd

from data.dummy_model import nodes, connections

pn.extension(sizing_mode="stretch_width")

# ---------------------------------------------------------------------------
# ArchiMate-Farbschema (angelehnt an Standard-Notation)
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

BUSINESS_LAYER = {"business-role", "business-process", "business-service"}

ALL_STEREOTYPES = sorted({n.stereotypename for n in nodes})
ALL_RELATIONS   = sorted({c.stereotypename for c in connections})

# ---------------------------------------------------------------------------
# Graph-Aufbau
# ---------------------------------------------------------------------------
def build_graph(stereotypes: list[str], relations: list[str]) -> nx.DiGraph:
    G = nx.DiGraph()
    active = {n.uuid for n in nodes if n.stereotypename in stereotypes}

    for n in nodes:
        if n.uuid in active:
            G.add_node(n.uuid, label=n.displayname, stereotype=n.stereotypename)

    for c in connections:
        src, tgt = c.sourcenode[0], c.targetnode[0]
        if c.stereotypename in relations and src in active and tgt in active:
            G.add_edge(src, tgt, rel_type=c.stereotypename)

    return G


def archimate_layout(G: nx.DiGraph) -> dict:
    """Business-Layer oben (y=1), Application-Layer unten (y=0)."""
    top    = [n for n in G if G.nodes[n]["stereotype"] in BUSINESS_LAYER]
    bottom = [n for n in G if G.nodes[n]["stereotype"] not in BUSINESS_LAYER]

    pos = {}
    for i, n in enumerate(top):
        pos[n] = ((i + 1) / (len(top) + 1), 1.0)
    for i, n in enumerate(bottom):
        pos[n] = ((i + 1) / (len(bottom) + 1), 0.0)
    return pos


# ---------------------------------------------------------------------------
# Widgets
# ---------------------------------------------------------------------------
stereotype_filter = pn.widgets.CheckBoxGroup(
    name="Node-Typen",
    value=ALL_STEREOTYPES[:],
    options=ALL_STEREOTYPES,
)

relation_filter = pn.widgets.CheckBoxGroup(
    name="Beziehungstypen",
    value=ALL_RELATIONS[:],
    options=ALL_RELATIONS,
)

# ---------------------------------------------------------------------------
# Reaktive Graphdarstellung
# ---------------------------------------------------------------------------
@pn.depends(stereotype_filter, relation_filter)
def graph_panel(stereotypes, relations):
    if not stereotypes:
        return pn.pane.Markdown("_Bitte mindestens einen Node-Typ auswählen._")

    G = build_graph(stereotypes, relations)

    if G.number_of_nodes() == 0:
        return pn.pane.Markdown("_Keine Nodes nach aktuellem Filter._")

    pos    = archimate_layout(G)
    labels = {n: G.nodes[n]["label"] for n in G}
    colors = [NODE_COLORS.get(G.nodes[n]["stereotype"], "#CCCCCC") for n in G]

    node_plot = hvnx.draw_networkx_nodes(G, pos, node_color=colors, node_size=1500,
                                          alpha=0.9)
    edge_plot = hvnx.draw_networkx_edges(G, pos, arrows=True, arrowstyle="-|>",
                                          arrowsize=20, edge_color="#555555")
    # draw_networkx_labels hat einen API-Bug in aktuellen hvplot-Versionen →
    # Labels direkt als HoloViews-Element aufbauen
    label_df   = pd.DataFrame(
        [{"x": pos[n][0], "y": pos[n][1], "text": labels[n]} for n in G.nodes]
    )
    label_plot = hv.Labels(label_df, kdims=["x", "y"], vdims=["text"])

    # opts separat pro Element-Typ setzen, um Float-Width-Fehler im Overlay zu vermeiden
    combined = (node_plot * edge_plot * label_plot).opts(
        hv.opts.Labels(text_font_size="8pt", text_color="black", yoffset=0.06),
        hv.opts.Overlay(xaxis=None, yaxis=None, toolbar="above",
                        width=860, height=520),
    )

    return pn.pane.HoloViews(combined, sizing_mode="stretch_width")


# ---------------------------------------------------------------------------
# Legende
# ---------------------------------------------------------------------------
def legend_html() -> str:
    items = "".join(
        f'<div style="display:flex;align-items:center;gap:6px;margin:3px 0">'
        f'<div style="width:14px;height:14px;border-radius:3px;background:{color};'
        f'border:1px solid #aaa"></div>'
        f'<span style="font-size:12px">{stereo}</span></div>'
        for stereo, color in NODE_COLORS.items()
    )
    return f"<div>{items}</div>"


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
    width=260,
)

main = pn.Column(
    "# ArchiMate Graphansicht",
    pn.pane.Markdown(
        "_Business-Layer (oben) → Application-Layer (unten). "
        "Filter über die Sidebar._",
        styles={"color": "#666"},
    ),
    graph_panel,
)

template = pn.template.FastListTemplate(
    title="EAM Graph Analyse",
    sidebar=[sidebar],
    main=[main],
    accent="#0072B5",
)

template.servable()

if __name__ == "__main__":
    pn.serve(template, show=True, port=5007)
