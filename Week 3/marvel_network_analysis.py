#!/usr/bin/env python3
"""Analyse the Week 1 Marvel files and generate data for week2_post.html.

Put these files in the same folder as this script:

    week1_nodes.tsv
    week1_edges.tsv
    week2_post.html

Then run:

    python marvel_network_analysis.py

The script creates ``analysis_data.js``, which the HTML page loads
automatically. The two filenames below are placeholders and can be changed if
the course files are renamed.
"""

from __future__ import annotations

import argparse
import csv
import json
import pickle
import random
from pathlib import Path
from statistics import mean
from typing import Hashable, Iterable

import networkx as nx


# ---------------------------------------------------------------------------
# FILE PLACEHOLDERS — keep the two TSV files beside this Python file.
# ---------------------------------------------------------------------------
NODES_FILE = "week1_nodes.tsv"
EDGES_FILE = "week1_edges.tsv"


def _clean_graph(graph: nx.Graph) -> nx.Graph:
    """Return a simple undirected giant component without self-loops."""
    undirected = nx.Graph(graph)
    undirected.remove_edges_from(nx.selfloop_edges(undirected))
    if undirected.number_of_nodes() == 0:
        raise ValueError("The supplied graph has no nodes.")
    giant_nodes = max(nx.connected_components(undirected), key=len)
    return undirected.subgraph(giant_nodes).copy()


def _load_delimited(path: Path, delimiter: str) -> nx.Graph:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, delimiter=delimiter)
        rows = [row for row in reader if len(row) >= 2 and row[0].strip() and row[1].strip()]
    if not rows:
        raise ValueError(f"No edges found in {path}")
    header = [cell.strip().lower() for cell in rows[0]]
    known = {"source", "target", "from", "to", "node1", "node2", "character1", "character2"}
    if len(set(header) & known) >= 2:
        rows = rows[1:]
    graph = nx.Graph()
    graph.add_edges_from((row[0].strip(), row[1].strip()) for row in rows)
    return graph


def _pick_column(fieldnames: list[str], preferred: tuple[str, ...], fallback: int) -> str:
    """Find a column without requiring one exact course-file schema."""
    lookup = {name.strip().lower(): name for name in fieldnames}
    for candidate in preferred:
        if candidate in lookup:
            return lookup[candidate]
    if len(fieldnames) <= fallback:
        raise ValueError("The TSV file does not contain enough columns.")
    return fieldnames[fallback]


def load_week1_files(
    nodes_path: str | Path = NODES_FILE,
    edges_path: str | Path = EDGES_FILE,
) -> nx.Graph:
    """Load the two Week 1 TSV files and use node labels as character names."""
    nodes_path = Path(nodes_path)
    edges_path = Path(edges_path)
    missing = [str(path) for path in (nodes_path, edges_path) if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing course file(s): " + ", ".join(missing)
            + ". Put both TSV files in the same folder as this script."
        )

    graph = nx.Graph()

    with nodes_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if not reader.fieldnames:
            raise ValueError(f"No header found in {nodes_path}")
        node_id = _pick_column(reader.fieldnames, ("id", "node", "node_id", "index"), 0)
        label = _pick_column(
            reader.fieldnames,
            ("label", "name", "character", "title", "page"),
            min(1, len(reader.fieldnames) - 1),
        )
        labels = {}
        for row in reader:
            identifier = (row.get(node_id) or "").strip()
            if not identifier:
                continue
            character = (row.get(label) or identifier).strip()
            labels[identifier] = character
            graph.add_node(identifier)

    with edges_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if not reader.fieldnames:
            raise ValueError(f"No header found in {edges_path}")
        source = _pick_column(
            reader.fieldnames,
            ("source", "from", "node1", "character1", "src"),
            0,
        )
        target = _pick_column(
            reader.fieldnames,
            ("target", "to", "node2", "character2", "dst"),
            1,
        )
        for row in reader:
            left = (row.get(source) or "").strip()
            right = (row.get(target) or "").strip()
            if left and right:
                graph.add_edge(left, right)

    # If the edge file uses IDs, replace them with readable character labels.
    # Unknown IDs are kept as-is instead of being discarded.
    return nx.relabel_nodes(graph, labels, copy=True)


def load_graph(path: str | Path) -> nx.Graph:
    """Load a NetworkX-compatible graph from a common file format."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".graphml":
        return nx.read_graphml(path)
    if suffix == ".gexf":
        return nx.read_gexf(path)
    if suffix == ".gml":
        return nx.read_gml(path)
    if suffix == ".net":
        return nx.read_pajek(path)
    if suffix in {".edgelist", ".txt"}:
        return nx.read_edgelist(path, comments="#", data=False)
    if suffix == ".csv":
        return _load_delimited(path, ",")
    if suffix == ".tsv":
        return _load_delimited(path, "\t")
    if suffix == ".json":
        with path.open("r", encoding="utf-8") as handle:
            return nx.node_link_graph(json.load(handle), edges="links")
    if suffix in {".gpickle", ".pickle", ".pkl"}:
        with path.open("rb") as handle:
            graph = pickle.load(handle)
        if not isinstance(graph, nx.Graph):
            raise TypeError("The pickle does not contain a NetworkX graph.")
        return graph
    raise ValueError(f"Unsupported graph format: {suffix or '(none)'}")


def _largest_component_size(graph: nx.Graph) -> int:
    return max((len(c) for c in nx.connected_components(graph)), default=0)


def _betweenness(graph: nx.Graph, samples: int | None, seed: int) -> dict[Hashable, float]:
    if samples and samples < graph.number_of_nodes():
        return nx.betweenness_centrality(graph, k=samples, seed=seed, normalized=True)
    return nx.betweenness_centrality(graph, normalized=True)


def _single_removal_damage(
    graph: nx.Graph,
    betweenness: dict[Hashable, float],
) -> list[dict]:
    """Evaluate nodes that can exceed the unavoidable one-node size drop.

    Only articulation points can split a connected graph. Every other node has
    a drop of exactly one, so this avoids copying the full graph for all nodes.
    """
    original_size = graph.number_of_nodes()
    candidates = set(nx.articulation_points(graph))
    if not candidates:
        candidates.add(max(graph, key=lambda n: betweenness[n]))

    results = []
    for node in candidates:
        reduced = graph.copy()
        reduced.remove_node(node)
        largest = _largest_component_size(reduced)
        drop = original_size - largest
        results.append({
            "character": str(node),
            "drop": int(drop),
            "relative_drop": drop / original_size,
            "largest_component_after_removal": int(largest),
            "components_after_removal": nx.number_connected_components(reduced),
            "betweenness": float(betweenness[node]),
            "node": node,
        })
    return sorted(results, key=lambda row: (row["drop"], row["betweenness"]), reverse=True)


def _removal_curve(graph: nx.Graph, order: Iterable[Hashable], steps: int) -> list[dict]:
    working = graph.copy()
    curve = [{"removed": 0, "giant_component": graph.number_of_nodes()}]
    for index, node in enumerate(list(order)[:steps], start=1):
        if working.has_node(node):
            working.remove_node(node)
        curve.append({"removed": index, "giant_component": _largest_component_size(working)})
    return curve


def _random_curve(graph: nx.Graph, steps: int, repeats: int, seed: int) -> list[dict]:
    curves = []
    nodes = list(graph.nodes())
    for run in range(repeats):
        order = nodes.copy()
        random.Random(seed + run).shuffle(order)
        curves.append(_removal_curve(graph, order, steps))
    output = []
    for index in range(steps + 1):
        values = [curve[index]["giant_component"] for curve in curves]
        output.append({
            "removed": index,
            "giant_component": mean(values),
            "min": min(values),
            "max": max(values),
        })
    return output


def analyse_graph(
    graph: nx.Graph,
    output: str | Path = "analysis_data.js",
    *,
    samples: int | None = None,
    max_removed: int = 100,
    random_repeats: int = 20,
    seed: int = 42,
) -> dict:
    """Run the analysis, write JavaScript data, and return the result dict."""
    graph = _clean_graph(graph)
    node_count = graph.number_of_nodes()
    steps = min(max_removed, max(node_count - 1, 0))

    betweenness = _betweenness(graph, samples, seed)
    degree = dict(graph.degree())
    between_order = sorted(graph, key=lambda n: betweenness[n], reverse=True)
    degree_order = sorted(graph, key=lambda n: degree[n], reverse=True)
    betweenness_rank = {node: rank for rank, node in enumerate(between_order, start=1)}

    damage = _single_removal_damage(graph, betweenness)
    top_damage = damage[0]
    top_between_node = between_order[0]
    top_rows = []
    for row in damage[:10]:
        top_rows.append({
            "character": row["character"],
            "drop": row["drop"],
            "relative_drop": row["relative_drop"],
            "betweenness": row["betweenness"],
            "betweenness_rank": betweenness_rank[row["node"]],
        })

    result = {
        "network": {
            "nodes": node_count,
            "edges": graph.number_of_edges(),
            "density": nx.density(graph),
        },
        "settings": {
            "betweenness_samples": samples,
            "max_removed": steps,
            "random_repeats": random_repeats,
            "seed": seed,
        },
        "key_results": {
            "highest_betweenness": {
                "character": str(top_between_node),
                "betweenness": betweenness[top_between_node],
            },
            "most_damaging": {
                "character": top_damage["character"],
                "drop": top_damage["drop"],
                "relative_drop": top_damage["relative_drop"],
            },
            "same_character": top_between_node == top_damage["node"],
        },
        "top_removals": top_rows,
        "robustness": {
            "betweenness": _removal_curve(graph, between_order, steps),
            "degree": _removal_curve(graph, degree_order, steps),
            "random_mean": _random_curve(graph, steps, random_repeats, seed),
        },
    }

    output = Path(output)
    output.write_text(
        "window.MARVEL_ANALYSIS = " + json.dumps(result, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )
    print(f"Analysed {node_count:,} nodes and {graph.number_of_edges():,} edges.")
    print(f"Highest betweenness: {top_between_node}")
    print(f"Most damaging removal: {top_damage['character']} (drop: {top_damage['drop']})")
    print(f"Wrote {output.resolve()}")
    return result


def _positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "graph",
        nargs="?",
        help="Optional single graph file. Omit this to use week1_nodes.tsv and week1_edges.tsv.",
    )
    parser.add_argument("--nodes", default=NODES_FILE, help="Week 1 node TSV placeholder")
    parser.add_argument("--edges", default=EDGES_FILE, help="Week 1 edge TSV placeholder")
    parser.add_argument("-o", "--output", default="analysis_data.js", help="Output JavaScript file")
    parser.add_argument("--samples", type=_positive_int, help="Approximate betweenness using this many sampled nodes")
    parser.add_argument("--max-removed", type=_positive_int, default=100, help="Maximum cumulative removals")
    parser.add_argument("--random-repeats", type=_positive_int, default=20, help="Number of random baselines")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    graph = load_graph(args.graph) if args.graph else load_week1_files(args.nodes, args.edges)

    analyse_graph(
        graph,
        args.output,
        samples=args.samples,
        max_removed=args.max_removed,
        random_repeats=args.random_repeats,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
