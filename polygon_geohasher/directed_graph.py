import networkx as nx
import pandas as pd
import functools
import queue


class DirectedGraph:
    def __init__(self, **kwargs):
        self.source_nodes = set()
        self.target_nodes = set()
        self.weights = {}
        self.dg = nx.DiGraph()

        if len(kwargs) > 0:
            for arg in ["path", "source_column", "target_column", "weights"]:
                if arg not in kwargs.keys():
                    raise KeyError("Missing argument {argument}.".format(argument=arg))

            if not isinstance(kwargs.get("weights"), set):
                raise ValueError("Parameter weights must be a set.")

            path = kwargs.get("path")
            source_column = kwargs.get("source_column")
            target_column = kwargs.get("target_column")
            weights = list(kwargs.get("weights"))
            fill_missing_edges = kwargs.get("fill_missing_edges", False)

            columns = [source_column, target_column] + weights

            gdf = pd.read_csv(path, usecols=columns)

            for features in gdf[columns].values:
                self.add_edge(features[0], features[1],
                              {weight: features[index + 2] for index, weight in enumerate(weights)})

    def is_empty(self):
        """
        :return: True if the graph is or not empty.
        """
        return len(self.source_nodes) == 0

    def exists_edge(self, source, target):
        """
        :param source: Source node.
        :param target: Target node.
        :return: True if edge from source to target exist in the graph.
        """
        try:
            return self.dg.get_edge_data(source, target) is not None
        except KeyError:
            return False

    def add_edge(self, source, target, weights):
        """
        :param source: Source node.
        :param target: Target node.
        :param weights: Dictionary of weighted path.

        Mutable method that adds a path to internal graph.
        """
        if not isinstance(weights, dict):
            raise ValueError("Parameter weights must be a dictionary.")

        self.dg.add_edge(source, target, **weights)
        self.source_nodes.add(source)
        self.target_nodes.add(target)

        # updates self.weights which is a dictionary
        for weight, v in weights.items():
            if weight not in self.weights.keys():
                self.weights[weight] = []

            self.weights[weight].append((source, target))

    def remove_edge(self, source, target):
        """
        :param source: Source node.
        :param target: Target node.

        Mutable method that removes a path from internal graph.
        """

        if not self.exists_edge(source, target):
            raise ValueError("Couldn't find path from {source} to {target} in current graph.".format(source=source,
                                                                                                     target=target))
        implied_weights = self.dg.get_edge_data(source, target)

        self.dg.remove_edge(source, target)

        if self.dg.number_of_edges(u=source) < 1:
            self.source_nodes.remove(source)

        if self.dg.number_of_edges(v=target) < 1:
            self.target_nodes.remove(target)

        for implied_weight in implied_weights.keys():
            self.weights[implied_weight].remove((source, target))

            if len(self.weights[implied_weight]) == 0:
                del self.weights[implied_weight]

    def dijkstra_trip_length(self, source, target, weight):
        """
        :param source: Source node.
        :param target: Target node.
        :param weight: Name of the weight property.
        :return: Returns shortest path weight from source to target, if no path could be found infinity is returned.
        """
        if weight not in self.weights.keys():
            raise ValueError("Only {weights} are valid weights.".format(weights=",".join(self.weights.keys())))

        try:
            return nx.dijkstra_path_length(self.dg, source, target, weight=weight)
        except nx.NetworkXNoPath:
            return float("inf")

    def astar_trip_length(self, source, target, weight):
        """
        :param source: Source node.
        :param target: Target node.
        :param weight: Name of the weight property.
        :return: Returns shortest path weight from source to target, if no path could be found infinity is returned.
        """
        if weight not in self.weights.keys():
            raise ValueError("Only {weights} are valid weights.".format(weights=",".join(self.weights.keys())))

        try:
            return nx.astar_path_length(self.dg, source, target, weight=weight)
        except nx.NetworkXNoPath:
            return float("inf")

    def subset(self, source, thresholds, restricted=set()):
        """
        :param source: Source node from where to measure weights.
        :param thresholds: Dictionary of thresholds where the key is the weight's name.
        :param restricted: Set of nodes that won't be integrated to resulting graph.
        :return: A graph formed by all nodes reachable from source.
        """

        if source not in self.source_nodes and source not in self.target_nodes:
            raise ValueError("Not valid node. {source} couldn't be found in the graph.".format(source=source))
        if source in restricted:
            raise ValueError("Source is a restricted node.")

        reachable_nodes = {source: {k: 0 for k in thresholds.keys()}}
        tested_nodes = restricted.union(reachable_nodes.keys())

        following_nodes = queue.Queue()
        following_nodes.put(source)

        while not following_nodes.empty():
            node = following_nodes.get()

            for target in self.dg.neighbors(node):
                # If neighbor wasn't already tested
                if target not in tested_nodes:
                    weights = {k: self.dijkstra_trip_length(source, target, k) for k in thresholds.keys()}
                    passed = all([weights[key] <= thresholds[key] for key in thresholds.keys()])

                    # If all weights are smaller than threshold then that edge is part of the resulting graph.
                    if passed:
                        reachable_nodes[target] = weights
                        following_nodes.put(target)

                    tested_nodes.add(target)

        return reachable_nodes

    # todo case when there is a intermediate node reachable by two nodes and a final node,
    # ramdonly could select different sources
    def disjoint_subsets(self, sources, thresholds, weight_name, restricted=set()):
        """
        :param sources: Source node from where to measure weights.
        :param thresholds: Dictionary of thresholds where the key is the weight's name.
        :param weight_name: Weight's name used as criteria to obtain the minimum.
        :param restricted: Set of nodes that won't be integrated to resulting graph.
        :return: Dictionary where keys are source nodes, values are dictionaries of nodes and weights.
        """
        if len(set(sources)) < len(sources):
            raise ValueError("All sources must be different.")

        subsets = {source: self.subset(source, thresholds, restricted) for source in sources}
        targets = functools.reduce(lambda a, b: a.union(b), [{*vs.keys()} for vs in subsets.values()])
        result = {source: {} for source in sources}
        inf = float("inf")

        target_source_min = {target: min([(source, subsets.get(source).get(target).get(weight_name, inf))
                                          for source in sources
                                          if source in subsets and target in subsets[source]], key=lambda xs: xs[1])
                             for target in targets}

        for target, (source, _) in target_source_min.items():
            result[source][target] = subsets[source][target]

        return result
