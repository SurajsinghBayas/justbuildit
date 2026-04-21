"""
Graph Encoder — Dependency DAG Feature Extractor.

Builds a NetworkX directed acyclic graph from task dependency edges and
computes graph-theoretic features for each node (task). These features
expose structural importance that neither text nor tabular features can capture.

Graph features per node (8-dim):
  [0] in_degree           — how many tasks this depends ON (blockers)
  [1] out_degree          — how many tasks depend ON this (downstream)
  [2] pagerank            — Google PageRank (flow-importance in DAG)
  [3] betweenness_centrality — task is a critical path connector
  [4] closeness_centrality   — reachability / isolation
  [5] depth               — longest path from any source to this node
  [6] num_descendants     — total downstream tasks (transitive)
  [7] is_critical_path    — 1.0 if on the longest path in the graph

Design note:
  For N tasks in a sprint, we build one shared graph.
  Inference: inject any subset of edges (known dependency UUIDs).
  GNN upgrade path: replace this with a PyTorch Geometric GCN that takes
  the same adjacency matrix + node features and produces learnable embeddings.
"""

import numpy as np
import networkx as nx
from typing import Dict, List, Tuple, Optional

GRAPH_DIM = 8


class GraphEncoder:
    """
    Stateless graph feature extractor backed by NetworkX.
    Builds a DAG from (source_task_id, target_task_id) edges
    where edge A→B means "A must complete before B".
    """

    def build_graph(self, edges: List[Tuple[str, str]]) -> nx.DiGraph:
        G = nx.DiGraph()
        G.add_edges_from(edges)
        return G

    def encode_node(self, G: nx.DiGraph, node_id: str) -> np.ndarray:
        """
        Extract 8 graph features for a single node.
        Returns zeros if the node has no graph context.
        """
        if node_id not in G:
            return np.zeros(GRAPH_DIM, dtype=np.float32)

        n = len(G.nodes)

        # PageRank (damping=0.85, max_iter=100)
        try:
            pr = nx.pagerank(G, alpha=0.85, max_iter=100)
            page_rank = pr.get(node_id, 0.0)
        except Exception:
            page_rank = 0.0

        # Betweenness centrality (normalized)
        try:
            bc = nx.betweenness_centrality(G, normalized=True)
            betweenness = bc.get(node_id, 0.0)
        except Exception:
            betweenness = 0.0

        # Closeness centrality
        try:
            cc = nx.closeness_centrality(G)
            closeness = cc.get(node_id, 0.0)
        except Exception:
            closeness = 0.0

        # Depth (longest shortest path from any source to this node)
        sources = [n for n in G.nodes if G.in_degree(n) == 0]
        depth = 0
        for src in sources:
            try:
                if nx.has_path(G, src, node_id):
                    d = nx.shortest_path_length(G, src, node_id)
                    depth = max(depth, d)
            except Exception:
                pass

        # Descendants (transitive downstream)
        try:
            num_desc = len(nx.descendants(G, node_id))
        except Exception:
            num_desc = 0

        # Critical path: is this node on the longest path?
        is_critical = 0.0
        try:
            longest = nx.dag_longest_path(G)
            is_critical = 1.0 if node_id in longest else 0.0
        except Exception:
            pass

        return np.array([
            float(G.in_degree(node_id)),
            float(G.out_degree(node_id)),
            float(page_rank),
            float(betweenness),
            float(closeness),
            float(depth),
            float(num_desc),
            is_critical,
        ], dtype=np.float32)

    def encode_all(self, edges: List[Tuple[str, str]], node_ids: List[str]) -> Dict[str, np.ndarray]:
        """
        Encode all nodes in the graph at once (more efficient than node-by-node).
        Returns dict: { task_id → 8-dim feature vector }
        """
        G = self.build_graph(edges)
        # Add isolated nodes not in any edge
        for nid in node_ids:
            if nid not in G:
                G.add_node(nid)

        pr = nx.pagerank(G, alpha=0.85, max_iter=100) if len(G) > 0 else {}
        bc = nx.betweenness_centrality(G, normalized=True) if len(G) > 0 else {}
        cc = nx.closeness_centrality(G) if len(G) > 0 else {}

        try:
            longest_path = set(nx.dag_longest_path(G))
        except Exception:
            longest_path = set()

        result = {}
        sources = [n for n in G.nodes if G.in_degree(n) == 0]

        for nid in node_ids:
            depth = 0
            if nid in G:
                for src in sources:
                    try:
                        if nx.has_path(G, src, nid):
                            d = nx.shortest_path_length(G, src, nid)
                            depth = max(depth, d)
                    except Exception:
                        pass
            try:
                num_desc = len(nx.descendants(G, nid)) if nid in G else 0
            except Exception:
                num_desc = 0

            result[nid] = np.array([
                float(G.in_degree(nid)) if nid in G else 0.0,
                float(G.out_degree(nid)) if nid in G else 0.0,
                float(pr.get(nid, 0.0)),
                float(bc.get(nid, 0.0)),
                float(cc.get(nid, 0.0)),
                float(depth),
                float(num_desc),
                1.0 if nid in longest_path else 0.0,
            ], dtype=np.float32)

        return result


def synthesize_graph_features(n: int, rng: np.random.Generator) -> np.ndarray:
    """
    Generate n synthetic graph feature rows for training.
    Simulates realistic DAG structures.
    """
    features = np.zeros((n, GRAPH_DIM), dtype=np.float32)
    features[:, 0] = rng.integers(0, 5, n).astype(float)      # in_degree
    features[:, 1] = rng.integers(0, 8, n).astype(float)      # out_degree
    features[:, 2] = rng.uniform(0.01, 0.3, n)                # pagerank
    features[:, 3] = rng.uniform(0.0, 0.5, n)                 # betweenness
    features[:, 4] = rng.uniform(0.0, 1.0, n)                 # closeness
    features[:, 5] = rng.integers(0, 6, n).astype(float)      # depth
    features[:, 6] = rng.integers(0, 10, n).astype(float)     # num_descendants
    features[:, 7] = rng.choice([0.0, 1.0], n, p=[0.7, 0.3]) # is_critical_path
    return features
