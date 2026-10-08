# Gas Flow Network Analysis

Builds a directed network of global natural gas trade (pipeline and LNG) from model flow reports, calculates network metrics for each country, and produces charts and CSV tables. It can analyse single years or compare two years, for the full world or for one region.

## What it does

1. Reads pipeline and LNG flow reports.
2. Standardises country names (see [Data preparation](#data-preparation)).
3. Builds a directed graph for each selected year. Nodes are countries and edges are gas flows in bcm.
4. Optionally restricts the graph to one region (EMEA, NORAM, LATAM or APAC).
5. Calculates network metrics and detects communities (single-year mode), or calculates flow changes between two years (comparison mode).
6. Saves charts (PNG) and tables (CSV) to a `network_outputs` folder.

## Requirements

- Python 3.9+
- `pandas`, `networkx`, `matplotlib`

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install pandas networkx matplotlib
```

## Input files

Two CSV files must be in the data folder:

| File | Rows used |
|---|---|
| `report_pipeflow.csv` | `ITEM` contains "flow" and does not contain "gross" |
| `report_lngflow.csv` | `ITEM` contains "flow" and contains "gross" (gross LNG flow) |

Required columns: `YEAR`, `COUNTRY_FROM`, `COUNTRY_TO`, `VALUE`, plus `ITEM` for row selection. Flow values are assumed to be in bcm. Valid years are 2023-2054.

## Usage

```powershell
# Use the current folder as the data folder
python network.py

# Or point to a data folder
python network.py "C:\path\to\data"
```

The script then asks for:

1. **Mode**: `1` single-year analysis (one or more years) or `2` comparison of two years.
2. **Year(s)**: for example `2026, 2030, 2040`, or `2026,2030` in comparison mode.
3. **Region**: `EMEA`, `NORAM`, `LATAM`, `APAC`, or Enter for the full network.
4. **Include trade partners outside the region?** (only if a region was chosen). The default is `N`, which keeps only flows where both countries are in the region. `y` also keeps flows where just one end is in the region, which pulls in outside partners.

## Outputs

Everything is written to `<data folder>\network_outputs\`. `<region>` is omitted when no region is chosen.

### Single-year mode (per year)

| File | Contents |
|---|---|
| `Network_Degree_Centrality_(<year>).png`, `..._Betweenness_...`, `..._PageRank_...`, `..._Clustering_Coefficient_...` | Network charts with nodes coloured and labelled by the metric |
| `Network_Communities_<year>.png` | Nodes coloured by detected community |
| `node_metrics_<region>_<year>.csv` | One row per country with all metrics below |
| `edge_flows_<region>_<year>.csv` | One row per flow: from, to, `flow_bcm`, `flow_types` (pipeline and/or lng) |
| `communities_<region>_<year>.csv` | One row per community: members, internal and external flow, net imports, key nodes |

### Comparison mode

| File | Contents |
|---|---|
| `Network_Changes_<y1>_to_<y2>.png` | Flow changes by route (green = increase, red = decrease) |
| `edge_changes_<region>_<y1>_to_<y2>.csv` | Flow in each year and the change, per route |
| `node_changes_<region>_<y1>_to_<y2>.csv` | Imports, exports and net change per country |

## Metric definitions

Flows are directed (exporter -> importer) and weighted by volume in bcm.

| Metric | Definition | How to read it |
|---|---|---|
| **Imports (bcm)** | Sum of flows into a country (weighted in-degree) | Total gas received |
| **Exports (bcm)** | Sum of flows out of a country (weighted out-degree) | Total gas sent |
| **Net imports (bcm)** | Imports minus exports | Positive = net importer, negative = net exporter or transit |
| **Degree centrality** | Number of trade links (in + out) divided by the maximum possible (n - 1) | How many partners a country connects to, regardless of volume |
| **Betweenness centrality** | Share of shortest paths between other country pairs that pass through the country (unweighted) | High values mark transit or hub countries that connect different parts of the network |
| **PageRank** | Importance score based on flow-weighted links from other important countries | High values mark countries that receive large flows from well-connected sources |
| **Clustering coefficient** | Share of a country's trading partners that also trade with each other (computed on the undirected graph) | High values mean a tightly interconnected neighbourhood |
| **Community** | Group of countries more densely connected to each other than to the rest, found with greedy modularity maximisation (weighted by flow) | Identifies trading blocs |
| **Modularity** | Quality of the community split, roughly -0.5 to 1 | Higher means communities are more clearly separated; above about 0.3 is usually considered meaningful |
| **Internal flow (bcm)** | Flow between two countries in the same community | |
| **External flow (bcm)** | Flow between a community member and a country outside it | |
| **Internal %** | Internal flow / (internal + external) | How self-contained a community is |
| **Import / export / net change (bcm)** | Value in the later year minus the value in the earlier year | Positive = growth |
| **Route change (bcm)** | Flow on a route in the later year minus the earlier year | Routes with changes under 0.001 bcm are ignored |

Note: centrality values depend on the selected region and partner setting, because they are calculated on the filtered graph.

## Data preparation

- **Negligible flows**: flows of 0.001 bcm or less are dropped.
- **Pipeline and LNG** flows between the same two countries are summed into a single edge, and the types are recorded in `flow_types`.
- **Country names** are standardised:
  - Parenthetical suffixes are removed, for example `Poland (Yamal)` -> `Poland`.
  - US sub-regions (for example Texas, Mid-Atlantic, Gulf of Mexico) -> `US`.
  - `Canada East` and `Canada West` -> `Canada`.
  - `Interconnector Greece Bulgaria` -> `Greece`.
- **Self-loops** created by standardisation are removed in single-year mode.
- **"Unspecified"** nodes represent unallocated flows (trading intermediaries or portfolio players) where the model does not track the final destination.

## Region definitions

Regions are defined in the `region_groups` dictionary at the top of `network.py`. Countries not listed in any region are only shown when no region filter is applied (or, with partners enabled, as partners of a listed country). Edit the dictionary to change the groupings.

## Other files

- `test_flows.py`: a small script for checking the `ITEM` categories and country-name standardisation against the input files.
