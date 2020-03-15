""" A module for making images of laminations. """

from math import sin, cos, pi, ceil
from typing import Union, List, TypeVar, Tuple, Dict, Any
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


def interpolate(A: Coord, B: Coord, r: float = 0.5) -> Coord:
    """ Return the point that is r% from B to A. """

    return (r * A[0] + (1 - r) * B[0], r * A[1] + (1 - r) * B[1])


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
        # Cyclically permute to the canonical position.
        triangle1 = min(triangle1, triangle1[1:] + triangle1[:1], triangle1[2:] + triangle1[:2])
        triangle2 = min(triangle2, triangle2[1:] + triangle2[:1], triangle2[2:] + triangle2[:2])
        return triangle1, triangle2

    def adjacent(current: Triangle, side: int) -> Tuple[Triangle, int]:
        """ Return the (other triangle, other side) which shares an edge with triangle[side]. """

        return next(
            (other, other_side) for other in support(current[side]) for other_side in range(3) if other[other_side] == current[side] and (other != current or other_side != side)
        )

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

    layout: Dict[Triangle, Tuple[Coord, Coord, Coord]] = dict()
    for index, component in enumerate(components):
        # Get a starting triangle.
        start = min(component, key=lambda triangle: tuple(position_index.get(edge, len(position_index)) for edge in triangle))

        # Expore out to find out which edges are in the interior.
        interior = set()
        placed = set([start])
        to_check = [(position_index.get(start[i], len(position_index)), (start, i)) for i in range(3) if start[i] in edge_set]  # A priority queue.
        heapq.heapify(to_check)
        while to_check:
            _, (current, side) = heapq.heappop(to_check)
            other, _ = adjacent(current, side)
            if other not in placed:
                interior.add(current[side])
                placed.add(other)
                for other_side in range(3):
                    if other[other_side] != current[side] and other[other_side] in edge_set:
                        heapq.heappush(to_check, (position_index.get(other[other_side], len(position_index)), (other, other_side)))

        # Determine how many boundary edges occur between each edge's endpoints.
        # We really should do this in a sensible order so that it only takes a single pass.
        num_decendents = dict(((triangle, side), 1) for triangle in component for side in range(3) if triangle[side] not in interior)
        while len(num_decendents) < 3 * len(component):
            for current in component:
                for side in range(3):
                    if (current, side) not in num_decendents:
                        other, _ = adjacent(current, side)
                        if all((other, other_side) in num_decendents or other[other_side] == current[side] for other_side in range(3)):
                            num_decendents[(current, side)] = sum(num_decendents[(other, other_side)] for other_side in range(3) if other[other_side] != current[side])

        # Work out which vertex (number) each side of each triangle starts at.
        triangle_vertex_number = {
            (start, 0): 0,
            (start, 1): num_decendents[(start, 0)],
            (start, 2): num_decendents[(start, 0)] + num_decendents[(start, 1)],
        }
        to_extend = [(start, side) for side in range(3) if start[side] in interior]
        while to_extend:
            current, side = to_extend.pop()
            other, other_side = adjacent(current, side)

            triangle_vertex_number[(other, (other_side + 0) % 3)] = triangle_vertex_number[(current, (side + 1) % 3)]
            triangle_vertex_number[(other, (other_side + 1) % 3)] = triangle_vertex_number[(current, (side + 0) % 3)]
            triangle_vertex_number[(other, (other_side + 2) % 3)] = triangle_vertex_number[(other, (other_side + 1) % 3)] + num_decendents[(other, (other_side + 1) % 3)]

            for i in [1, 2]:
                if other[(other_side + i) % 3] in interior:
                    to_extend.append((other, (other_side + i) % 3))

        # Create the vertices.
        num_outside = 3 * len(component) - 2 * len(interior)
        vertices = [
            (dx * (index % p) + dx / 2 + r * sin(2 * pi * (i + 0.5) / num_outside), dy * int(index / p) + dy / 2 + r * cos(2 * pi * (i + 0.5) / num_outside))
            for i in range(num_outside)
        ]
        for triangle in component:
            layout[triangle] = (vertices[triangle_vertex_number[(triangle, 0)]], vertices[triangle_vertex_number[(triangle, 1)]], vertices[triangle_vertex_number[(triangle, 2)]])

    return layout


def show_lamination(lamination: "bigger.Lamination[Edge]", edges: List[Edge], **options: Any) -> Image:
    """ Return an image of this lamination on the specified edges. """

    image = Image.new("RGB", (options["w"], options["h"]), color="White")
    draw = ImageDraw.Draw(image)

    if "label" not in options:
        options["label"] = "none"

    # Draw these triangles.
    layout = layout_triangulation(lamination.triangulation, edges, options["w"], options["h"])

    for index, triangle in enumerate(layout):
        draw.polygon(layout[triangle], fill=["Gray", "LightGray"][index % 2])

    master = max(abs(lamination(edge)) for triangle in layout for edge in triangle)
    if master > MAX_DRAWABLE:
        for triangle in layout:
            weights = [lamination(side) for side in triangle]
            weights_0 = [max(weight, 0) for weight in weights]
            sum_weights_0 = sum(weights_0)
            correction = min(min(sum_weights_0 - 2 * e for e in weights_0), 0)
            dual_weights = [bigger.half(sum_weights_0 - 2 * e + correction) for e in weights_0]
            parallel_weights = [bigger.half(max(-weight, 0)) for weight in weights]  # noqa: F841  # Remove once we can draw parallel things.
            vertices = layout[triangle]
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

                    S1 = interpolate(vertices[i - 2], vertices[i - 1], scale_a)
                    E1 = interpolate(vertices[i - 0], vertices[i - 1], scale_b)
                    S2 = interpolate(vertices[i - 2], vertices[i - 1], scale_a2)
                    E2 = interpolate(vertices[i - 0], vertices[i - 1], scale_b2)
                    draw.polygon([S1, E1, E2, S2], fill="DarkGray")
                elif dual_weights[i] < 0:  # Terminal arc.
                    s_0 = (1 - 2 * VERTEX_BUFFER) * weights_0[i] / master

                    scale_a = (1 - s_0) / 2 + s_0 * dual_weights[i - 2] / weights_0[i]
                    scale_a2 = scale_a + s_0 * (-dual_weights[i]) / weights_0[i]

                    S1 = interpolate(vertices[i - 0], vertices[i - 2], scale_a)
                    E1 = vertices[i - 1]
                    S2 = interpolate(vertices[i - 0], vertices[i - 2], scale_a2)
                    E2 = vertices[i - 1]
                    draw.polygon([S1, E1, E2, S2], fill="DarkGray")
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
            dual_weights = [bigger.half(sum_weights_0 - 2 * e + correction) for e in weights_0]
            parallel_weights = [bigger.half(max(-weight, 0)) for weight in weights]  # noqa: F841  # Remove once we can draw parallel things.
            vertices = layout[triangle]
            for i in range(3):  # Dual arcs:
                if dual_weights[i] > 0:
                    s_a = 1 - 2 * VERTEX_BUFFER
                    s_b = 1 - 2 * VERTEX_BUFFER
                    for j in range(dual_weights[i]):
                        scale_a = 0.5 if weights_0[i - 2] == 1 else (1 - s_a) / 2 + s_a * j / (weights_0[i - 2] - 1)
                        scale_b = 0.5 if weights_0[i - 1] == 1 else (1 - s_b) / 2 + s_b * j / (weights_0[i - 1] - 1)

                        S1 = interpolate(vertices[i - 2], vertices[i - 1], scale_a)
                        E1 = interpolate(vertices[i - 0], vertices[i - 1], scale_b)
                        draw.line([S1, E1], fill="DarkGray", width=2)
                elif dual_weights[i] < 0:  # Terminal arc.
                    s_0 = 1 - 2 * VERTEX_BUFFER
                    for j in range(-dual_weights[i]):
                        scale_a = 0.5 if weights_0[i] == 1 else (1 - s_0) / 2 + s_0 * dual_weights[i - 1] / (weights_0[i] - 1) + s_0 * j / (weights_0[i] - 1)

                        S1 = interpolate(vertices[i - 0], vertices[i - 2], scale_a)
                        E1 = vertices[i - 1]
                        draw.line([S1, E1], fill="DarkGray", width=2)
                else:  # dual_weights[i] == 0:  # Nothing to draw.
                    pass

                # Parallel arcs:
                # S, O, E = triangle[i-2].vector, triangle[i].vector, triangle[i-1].vector
                # # M = (S + E) / 2.0
                # centroid = (S + O + E) / 3.0
                # for j in range(parallel_weights[i]):
                # P = M + float(j+1) / (parallel_weights[i] + 1) * (centroid - M) * (parallel_weights[i] + 1) / master
                # self.create_curve_component([S, P, E])

    for triangle in layout:
        weights = [lamination(side) for side in triangle]
        weights_0 = [max(weight, 0) for weight in weights]
        sum_weights_0 = sum(weights_0)
        correction = min(min(sum_weights_0 - 2 * e for e in weights_0), 0)
        dual_weights = [bigger.half(sum_weights_0 - 2 * e + correction) for e in weights_0]
        parallel_weights = [bigger.half(max(-weight, 0)) for weight in weights]  # noqa: F841  # Remove once we can draw parallel things.
        vertices = layout[triangle]
        for i in range(3):
            if options["label"] == "edge":
                draw.text(interpolate(vertices[i - 0], vertices[i - 2]), str(triangle[i]), fill="Black")
            if options["label"] == "weight":
                draw.text(interpolate(vertices[i - 0], vertices[i - 2]), str(weights[i]), fill="Black")

    return image


def show(item: Union["bigger.Triangulation[Edge]", "bigger.Lamination[Edge]"], edges: List[Edge], **options: Any) -> Image:
    """ Return a PIL image of a Lamination or Triangulation around the given edges. """

    if "w" not in options:
        options["w"] = 400
    if "h" not in options:
        options["h"] = 400

    if isinstance(item, bigger.Triangulation):
        return show_lamination(item.empty_lamination(), edges, **options)
    else:  # isinstance(item, bigger.Lamination):
        return show_lamination(item, edges, **options)
