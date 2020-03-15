""" A module for making images of laminations. """

from math import sin, cos, pi, ceil
from typing import Union, List, Iterable, TypeVar, Tuple, Dict
import heapq

from PIL import Image, ImageDraw  # type: ignore

import bigger

Edge = TypeVar("Edge")
Triangle = Tuple[Edge, Edge, Edge]
Coord = Tuple[float, float]

# Vectors to offset a label by to produce backing.
OFFSETS = [(1.5 * cos(2 * pi * i / 12), 1.5 * sin(2 * pi * i / 12)) for i in range(12)]

# Colours of things.
DEFAULT_EDGE_LABEL_COLOUR = "black"
DEFAULT_EDGE_LABEL_BG_COLOUR = "white"
MAX_DRAWABLE = 1000  # Maximum weight of a multicurve to draw fully.
ZOOM_FRACTION = 0.8
VERTEX_BUFFER = 0.2


def deduplicate(items: List[Edge]) -> List[Edge]:
    """ Return the same list but without duplicates. """
    output = []
    seen = set()
    for item in items:
        if item not in seen:
            output.append(item)
            seen.add(item)
    return output


def rotate(items: List[Edge], target: Edge) -> List[Edge]:
    """ Rotate a list until the given item is at the front. """
    i = items.index(target)
    return items[i:] + items[:i]


def interpolate(A, B, C, r, s):
    """ Interpolate from B to A (resp. C) by r (resp. s). """

    return ((1 - r) * B[0] + (r) * A[0], (1 - r) * B[1] + (r) * A[1]), ((1 - s) * B[0] + (s) * C[0], (1 - s) * B[1] + (s) * C[1])


def layout_triangulation(triangulation: "bigger.Triangulation[Edge]", edges: List[Edge], w: int, h: int) -> Dict[Triangle, Tuple[Coord, Coord, Coord]]:
    """ Return a dictionary mapping the triangles that meet the given edges to coordinates in the plane.

    Triangle T is mapped to ((x1, y1), (x2, y2), (x3, y3)) where (xi, yi) is at the tail of side i of T when oriented anti-clockwise.
    Coordinate are within the w x h rectangle. """
    position_index = dict((edge, index) for index, edge in enumerate(edges))
    edge_set = set(edges)

    def support(edge: Edge) -> Tuple[Triangle, Triangle]:
        """ Return the two triangles that support and edge. """
        a, b, c, d = triangulation.link(edge)
        triangle1, triangle2 = (a, b, edge), (c, d, edge)
        triangle1 = min(triangle1[i:] + triangle1[:i] for i in range(3))
        triangle2 = min(triangle2[i:] + triangle2[:i] for i in range(3))
        return triangle1, triangle2

    # Compute the connect components of the supporting triangles of the given edges.
    components = bigger.UnionFind(deduplicate([triangle for edge in edges for triangle in support(edge)]))
    for edge in edges:
        components.union(*support(edge))

    num_components = len(components)

    # We will layout the components in a p x q grid.
    # Aim to maximise r := min(w / p, h / q) subject to pq >= num_components.
    # There is probably a closed formula for the optimal value of p (and so q).
    p = max(range(1, num_components + 1), key=lambda p: min(w / p, h / ceil(float(num_components) / p)))
    q = int(ceil(float(num_components) / p))

    r = min(w / p, h / q) * (1 + ZOOM_FRACTION) / 4
    dx = w / p
    dy = h / q

    layout = dict()
    for index, component in enumerate(components):
        # Get a starting triangle.
        start = min(component, key=lambda triangle: tuple(position_index.get(edge, len(position_index)) for edge in triangle))

        # Expore out to find out which edges are in the interior.
        interior = set()
        placed = set([start])
        to_check = [(position_index.get(edge, len(position_index)), (start, edge)) for edge in start if edge in edge_set]
        while to_check:
            _, (current, side) = heapq.heappop(to_check)
            other = next(triangle for triangle in support(side) if triangle != current)
            if other not in placed:
                interior.add(side)
                placed.add(other)
                for other_side in other:
                    if other_side != side and other_side in edge_set:
                        heapq.heappush(to_check, (position_index.get(other_side, len(position_index)), (other, other_side)))

        # Create the vertices.
        num_outside = 3 * len(component) - 2 * len(interior)
        vertices = [
            (dx * (index % p) + dx / 2 + r * sin(2 * pi * (i + 0.5) / num_outside), dy * int(index / p) + dy / 2 + r * cos(2 * pi * (i + 0.5) / num_outside))
            for i in range(num_outside)
        ]

        # Determine how many boundary edges occur between each edge's endpoints.
        # We really should do this in a sensible order so that it only takes a single pass.
        num_decendents = dict(((triangle, side), 1) for triangle in component for side in triangle if side not in interior)
        while len(num_decendents) < 3 * len(component):
            for current in component:
                for side in current:
                    if (current, side) not in num_decendents:
                        other = next(triangle for triangle in support(side) if triangle != current)
                        if all((other, other_side) in num_decendents or other_side == side for other_side in other):
                            num_decendents[(current, side)] = sum(num_decendents[(other, other_side)] for other_side in other if other_side != side)

        # Work out which vertex (number) each side of each triangle starts at.
        triangle_vertex_number = {
            (start, start[0]): 0,
            (start, start[1]): num_decendents[(start, start[0])],
            (start, start[2]): num_decendents[(start, start[0])] + num_decendents[(start, start[1])],
        }
        to_extend = [(start, side) for side in start if side in interior]
        while to_extend:
            current, side = to_extend.pop()
            other = next(triangle for triangle in support(side) if triangle != current)
            a, b, _ = rotate(current, side)
            x, y, z = rotate(other, side)

            triangle_vertex_number[(other, x)] = triangle_vertex_number[(current, b)]
            triangle_vertex_number[(other, y)] = triangle_vertex_number[(current, a)]
            triangle_vertex_number[(other, z)] = triangle_vertex_number[(other, y)] + num_decendents[(other, y)]

            if y in interior:
                to_extend.append((other, y))
            if z in interior:
                to_extend.append((other, z))

        for triangle in component:
            layout[triangle] = tuple(vertices[triangle_vertex_number[(triangle, side)]] for side in triangle)

    return layout


def show_lamination(lamination: "bigger.Lamination", edges: Iterable, **options) -> Image:
    """ Return an image of this lamination on the specified edges. """
    image = Image.new("RGB", (options["w"], options["h"]), color="White")
    draw = ImageDraw.Draw(image)

    # Draw these triangles.
    layout = layout_triangulation(lamination.triangulation, edges, options["w"], options["h"])

    for index, triangle in enumerate(layout):
        draw.polygon(layout[triangle], fill=["Green", "Red", "Blue"][index % 3])

    master = float(sum(abs(lamination(edge)) for triangle in layout for edge in triangle))
    if master > MAX_DRAWABLE:
        for triangle in layout:
            weights = [float(lamination(side)) for side in triangle]
            weights_0 = [max(weight, 0) for weight in weights]
            sum_weights_0 = sum(weights_0)
            correction = min(min(sum_weights_0 - 2 * e for e in weights_0), 0)
            dual_weights = [(sum_weights_0 - 2 * e + correction) / 2 for e in weights_0]
            parallel_weights = [max(-weight, 0) / 2 for weight in weights]  # noqa: F841  # Remove once we can draw parallel things.
            for i in range(3):
                # Dual arcs.
                if dual_weights[i] > 0:
                    # We first do the edge to the left of the vertex.
                    # Correction factor to take into account the weight on this edge.
                    s_a = (1 - 2 * VERTEX_BUFFER) * weights_0[i - 2] / master
                    # The fractions of the distance of the two points on this edge.
                    scale_a = (1 - s_a) / 2
                    scale_a2 = scale_a + s_a * dual_weights[i] / weights_0[i - 2]

                    # Now repeat for the other edge of the triangle.
                    s_b = (1 - 2 * VERTEX_BUFFER) * weights_0[i - 1] / master
                    scale_b = (1 - s_b) / 2
                    scale_b2 = scale_b + s_b * dual_weights[i] / weights_0[i - 1]

                    S1, E1 = interpolate(layout[triangle][i - 1], layout[triangle][i], layout[triangle][i - 2], scale_a, scale_b)
                    S2, E2 = interpolate(layout[triangle][i - 1], layout[triangle][i], layout[triangle][i - 2], scale_a2, scale_b2)
                    draw.polygon([S1, E1, E2, S2], fill="Gray")
                elif dual_weights[i] < 0:  # Terminal arc.
                    s_0 = (1 - 2 * VERTEX_BUFFER) * weights_0[i] / master

                    scale_a = (1 - s_0) / 2 + s_0 * dual_weights[i - 2] / weights_0[i]
                    scale_a2 = scale_a + s_0 * (-dual_weights[i]) / weights_0[i]

                    S1, E1 = interpolate(layout[triangle][i - 1], layout[triangle][i], layout[triangle][i - 2], scale_a, 1.0)
                    S2, E2 = interpolate(layout[triangle][i - 1], layout[triangle][i], layout[triangle][i - 2], scale_a2, 1.0)
                    draw.polygon([S1, E1, E2, S2], fill="Gray")
                else:  # dual_weights[i] == 0:  # Nothing to draw.
                    pass

                # Parallel arcs.
                # if parallel_weights[i]:
                # S, O, E = triangle[i-2].vector, triangle[i].vector, triangle[i-1].vector
                # M = (S + E) / 2.0
                # centroid = (S + O + E) / 3.0
                # P = M + 1.0 * (centroid - M) * (parallel_weights[i]+1) / master
                # self.create_curve_component([S, S, P, E, E, S, S], thin=False)
    else:  # Draw everything. Caution, this is is VERY slow (O(n) not O(log(n))) so we only do it when the weight is low.
        for triangle in layout:
            weights = [lamination(side) for side in triangle]
            weights_0 = [max(weight, 0) for weight in weights]
            sum_weights_0 = sum(weights_0)
            correction = min(min(sum_weights_0 - 2 * e for e in weights_0), 0)
            dual_weights = [(sum_weights_0 - 2 * e + correction) // 2 for e in weights_0]
            parallel_weights = [max(-weight, 0) // 2 for weight in weights]  # noqa: F841  # Remove once we can draw parallel things.
            for i in range(3):  # Dual arcs:
                if dual_weights[i] > 0:
                    s_a = 1 - 2 * VERTEX_BUFFER
                    s_b = 1 - 2 * VERTEX_BUFFER
                    for j in range(dual_weights[i]):
                        scale_a = 0.5 if weights_0[i - 2] == 1 else (1 - s_a) / 2 + s_a * j / (weights_0[i - 2] - 1)
                        scale_b = 0.5 if weights_0[i - 1] == 1 else (1 - s_b) / 2 + s_b * j / (weights_0[i - 1] - 1)

                        S1, E1 = interpolate(layout[triangle][i - 1], layout[triangle][i], layout[triangle][i - 2], scale_a, scale_b)
                        draw.line([S1, E1], fill="Gray")
                elif dual_weights[i] < 0:  # Terminal arc.
                    s_0 = 1 - 2 * VERTEX_BUFFER
                    for j in range(-dual_weights[i]):
                        scale_a = 0.5 if weights_0[i] == 1 else (1 - s_0) / 2 + s_0 * dual_weights[i - 1] / (weights_0[i] - 1) + s_0 * j / (weights_0[i] - 1)

                        S1, E1 = interpolate(layout[triangle][i - 1], layout[triangle][i], layout[triangle][i - 2], scale_a, 1.0)
                        draw.line([S1, E1], fill="Gray")
                else:  # dual_weights[i] == 0:  # Nothing to draw.
                    pass

                # Parallel arcs:
                # S, O, E = triangle[i-2].vector, triangle[i].vector, triangle[i-1].vector
                # # M = (S + E) / 2.0
                # centroid = (S + O + E) / 3.0
                # for j in range(parallel_weights[i]):
                # P = M + float(j+1) / (parallel_weights[i] + 1) * (centroid - M) * (parallel_weights[i] + 1) / master
                # self.create_curve_component([S, P, E])

    return image


def show(item: Union["bigger.Triangulation", "bigger.Lamination"], edges: List[Edge], **options) -> Image:
    """ Return a PIL image of a Lamination or Triangulation around the given edges. """

    if "w" not in options:
        options["w"] = 400
    if "h" not in options:
        options["h"] = 400

    if isinstance(item, bigger.Triangulation):
        return show_lamination(item.empty_lamination(), edges, **options)
    else:  # isinstance(item, bigger.Lamination):
        return show_lamination(item, edges, **options)
