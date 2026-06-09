import panel as pn
import pandas as pd
import numpy as np
import hvplot.pandas  # noqa: F401 — registers .hvplot accessor on DataFrames

pn.extension(sizing_mode="stretch_width")

# --- Sample data ---------------------------------------------------------

def generate_sample_data(n: int = 200) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    return pd.DataFrame({
        "date":     dates,
        "sales":    rng.integers(50, 300, n).astype(float),
        "costs":    rng.integers(30, 200, n).astype(float),
        "category": rng.choice(["A", "B", "C"], n),
    })

df = generate_sample_data()

# --- Widgets -------------------------------------------------------------

date_range = pn.widgets.DateRangeSlider(
    name="Zeitraum",
    start=df["date"].min().date(),
    end=df["date"].max().date(),
    value=(df["date"].min().date(), df["date"].max().date()),
)

category_filter = pn.widgets.CheckBoxGroup(
    name="Kategorie",
    value=["A", "B", "C"],
    options=["A", "B", "C"],
    inline=True,
)

metric_select = pn.widgets.Select(
    name="Kennzahl",
    options=["sales", "costs"],
    value="sales",
)

# --- Reactive pipeline ---------------------------------------------------

@pn.depends(date_range, category_filter, metric_select)
def filtered_data(date_range_val, categories, metric):
    start, end = pd.Timestamp(date_range_val[0]), pd.Timestamp(date_range_val[1])
    mask = (
        df["date"].between(start, end) &
        df["category"].isin(categories)
    )
    return df.loc[mask]


@pn.depends(date_range, category_filter, metric_select)
def line_chart(date_range_val, categories, metric):
    data = filtered_data(date_range_val, categories, metric)
    if data.empty:
        return pn.pane.Markdown("_Keine Daten für den gewählten Filter._")
    return (
        data.groupby("date")[metric]
        .mean()
        .hvplot.line(title=f"{metric.capitalize()} über Zeit", ylabel=metric)
    )


@pn.depends(date_range, category_filter, metric_select)
def bar_chart(date_range_val, categories, metric):
    data = filtered_data(date_range_val, categories, metric)
    if data.empty:
        return pn.pane.Markdown("_Keine Daten für den gewählten Filter._")
    return (
        data.groupby("category")[metric]
        .mean()
        .hvplot.bar(title=f"{metric.capitalize()} nach Kategorie", ylabel=metric)
    )


@pn.depends(date_range, category_filter, metric_select)
def summary_table(date_range_val, categories, metric):
    data = filtered_data(date_range_val, categories, metric)
    if data.empty:
        return pn.pane.Markdown("_Keine Daten._")
    summary = (
        data.groupby("category")[metric]
        .agg(["mean", "min", "max", "sum"])
        .round(1)
        .reset_index()
        .rename(columns={"mean": "Ø", "min": "Min", "max": "Max", "sum": "Summe"})
    )
    return pn.widgets.Tabulator(summary, show_index=False, height=200)


# --- Layout --------------------------------------------------------------

sidebar = pn.Column(
    "## Filter",
    date_range,
    pn.layout.Divider(),
    category_filter,
    pn.layout.Divider(),
    metric_select,
    width=280,
)

main = pn.Column(
    pn.Row(line_chart, bar_chart),
    pn.layout.Divider(),
    "### Zusammenfassung",
    summary_table,
)

template = pn.template.FastListTemplate(
    title="Datenanalyse Dashboard",
    sidebar=[sidebar],
    main=[main],
    accent="#0072B5",
)

template.servable()

# --- Dev entry point (panel serve app.py --autoreload) ------------------
if __name__ == "__main__":
    pn.serve(template, show=True)
