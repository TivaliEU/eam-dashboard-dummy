"""
bokeh_graph.py — reusable directed-graph component built on Bokeh.

Intended use
------------
    from bokeh_graph import NetworkGraph

    g = NetworkGraph(nodes, edges, on_select=my_callback)
    pn.pane.Bokeh(g.figure)

Node dict keys
--------------
    Required : id (str), label (str), x (float 0–1), y (float 0–1), color (CSS str)
    Optional : any extra key → added to hover tooltip automatically

Edge dict keys
--------------
    Required : source (str id), target (str id)
    Optional : label (str) — rendered at edge midpoint
"""

import math
import param
from bokeh.plotting import figure
from bokeh.models import (
    ColumnDataSource,
    LabelSet,
    Arrow,
    VeeHead,
    HoverTool,
)


class NetworkGraph(param.Parameterized):
    """Bokeh-based directed-graph component.

    Emits ``selected_id`` (param.String) whenever a node is tapped.
    Pass ``on_select`` for a direct callback instead of (or in addition to)
    watching the param.
    """

    selected_id = param.String(default="")

    # ------------------------------------------------------------------ #
    # Visual constants — override via subclass if needed
    # ------------------------------------------------------------------ #
    _X_RANGE  = (-0.1,  1.1)   # 1.2 data-units wide
    _Y_RANGE  = (-0.35, 1.45)  # 1.8 data-units tall
    _NODE_R_PX = 16             # node-circle radius in screen pixels

    def __init__(
        self,
        nodes: list[dict],
        edges: list[dict],
        *,
        width: int = 720,
        height: int = 460,
        tooltips: list[tuple] | None = None,
        show_edge_labels: bool = True,
        background: str = "#FAFAFA",
        on_select=None,
    ):
        super().__init__()
        self._nodes    = nodes
        self._edges    = edges
        self._width    = width
        self._height   = height
        self._show_el  = show_edge_labels
        self._ext_cb   = on_select
        self._id_xy    = {n["id"]: (n["x"], n["y"]) for n in nodes}
        self._tooltips = tooltips or self._default_tooltips(nodes)
        self.figure    = self._build(background)

    # ------------------------------------------------------------------ #
    # Construction
    # ------------------------------------------------------------------ #

    @staticmethod
    def _default_tooltips(nodes: list[dict]) -> list[tuple]:
        base = {"id", "label", "x", "y", "color"}
        extra = [k for k in (nodes[0].keys() if nodes else []) if k not in base]
        return [("Name", "@label")] + [(k.capitalize(), f"@{k}") for k in extra]

    def _px_to_data(self) -> tuple[float, float]:
        """Return (data-units per pixel) for x and y axes."""
        xw = self._X_RANGE[1] - self._X_RANGE[0]
        yw = self._Y_RANGE[1] - self._Y_RANGE[0]
        return xw / self._width, yw / self._height

    def _build(self, background: str):
        fig = figure(
            width=self._width, height=self._height,
            tools="pan,wheel_zoom,reset,tap",
            toolbar_location="above",
            x_range=self._X_RANGE,
            y_range=self._Y_RANGE,
            background_fill_color=background,
        )
        fig.xaxis.visible      = False
        fig.yaxis.visible      = False
        fig.grid.visible       = False
        fig.outline_line_color = None

        self._draw_edges(fig)
        node_src = self._draw_nodes(fig)
        self._draw_node_labels(fig)
        self._wire_selection(node_src)

        return fig

    # ------------------------------------------------------------------ #
    # Drawing helpers
    # ------------------------------------------------------------------ #

    def _draw_edges(self, fig):
        """Arrow per directed edge, offset from node borders."""
        px, py   = self._px_to_data()
        offset_x = px * self._NODE_R_PX
        offset_y = py * self._NODE_R_PX
        el_data: dict = {"x": [], "y": [], "text": []}

        for e in self._edges:
            sid, tid = e["source"], e["target"]
            if sid not in self._id_xy or tid not in self._id_xy:
                continue
            x0, y0 = self._id_xy[sid]
            x1, y1 = self._id_xy[tid]
            dx, dy = x1 - x0, y1 - y0
            dist   = math.hypot(dx, dy)
            if dist < 1e-9:
                continue
            ux, uy = dx / dist, dy / dist

            xs = x0 + ux * offset_x
            ys = y0 + uy * offset_y
            xe = x1 - ux * offset_x
            ye = y1 - uy * offset_y

            fig.add_layout(Arrow(
                end=VeeHead(size=10, fill_color="#999", line_color="#999"),
                x_start=xs, y_start=ys,
                x_end=xe,   y_end=ye,
                line_color="#bbb", line_width=1.5,
            ))

            if self._show_el and e.get("label"):
                el_data["x"].append((x0 + x1) / 2)
                el_data["y"].append((y0 + y1) / 2)
                el_data["text"].append(e["label"])

        if el_data["x"]:
            fig.add_layout(LabelSet(
                x="x", y="y", text="text",
                source=ColumnDataSource(el_data),
                x_offset=4, y_offset=4,
                text_font_size="7pt", text_color="#bbb",
                text_align="left",
            ))

    def _draw_nodes(self, fig) -> ColumnDataSource:
        """Circles for nodes; returns the ColumnDataSource."""
        base  = {"id", "label", "x", "y", "color"}
        extra = {k for n in self._nodes for k in n.keys()} - base

        data: dict = {
            "x":     [n["x"]     for n in self._nodes],
            "y":     [n["y"]     for n in self._nodes],
            "id":    [n["id"]    for n in self._nodes],
            "label": [n["label"] for n in self._nodes],
            "color": [n["color"] for n in self._nodes],
        }
        for k in extra:
            data[k] = [n.get(k, "") for n in self._nodes]

        src = ColumnDataSource(data)
        fig.scatter(
            x="x", y="y",
            marker="circle",
            size=self._NODE_R_PX * 2,   # diameter in screen px → always a true circle
            fill_color="color",
            line_color="#888", line_width=1,
            source=src,
            nonselection_fill_alpha=0.4,
            nonselection_line_color="#ccc",
            selection_line_color="#E53935", selection_line_width=3,
            selection_fill_color="color",
        )
        fig.add_tools(HoverTool(tooltips=self._tooltips))
        return src

    def _draw_node_labels(self, fig):
        """Short text labels above each node circle."""
        src = ColumnDataSource({
            "x":    [n["x"]     for n in self._nodes],
            "y":    [n["y"]     for n in self._nodes],
            "text": [n["label"] for n in self._nodes],
        })
        fig.add_layout(LabelSet(
            x="x", y="y", text="text", source=src,
            x_offset=0,
            y_offset=self._NODE_R_PX + 4,  # 4 px above circle top
            text_font_size="8pt", text_color="#333",
            text_align="center",
        ))

    # ------------------------------------------------------------------ #
    # Selection
    # ------------------------------------------------------------------ #

    def _wire_selection(self, src: ColumnDataSource):
        def _on_change(attr, old, new):
            uid = src.data["id"][new[0]] if new else ""
            self.selected_id = uid
            if self._ext_cb is not None:
                self._ext_cb(uid)

        src.selected.on_change("indices", _on_change)
