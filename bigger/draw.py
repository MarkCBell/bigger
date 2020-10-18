""" A module for making images of laminations. """

from __future__ import annotations

from math import sin, cos, pi, ceil
from queue import PriorityQueue
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from PIL import Image, ImageDraw  # type: ignore

import bigger
from bigger.types import Edge, Triangle, Coord, FlatTriangle, SupportsLayout

# Vectors to offset a label by to produce backing.
OFFSETS = [(1.5 * cos(2 * pi * i / 12), 1.5 * sin(2 * pi * i / 12)) for i in range(12)]

# Colours of things.
DEFAULT_EDGE_LABEL_COLOUR = "black"
DEFAULT_EDGE_LABEL_BG_COLOUR = "white"
MAX_DRAWABLE = 100  # Maximum weight of a multicurve to draw fully.
ZOOM_FRACTION = 0.9
VERTEX_BUFFER = 0.2

LAMINATION_COLOUR = "#555555"
TRIANGLE_COLOURS = {"bw": ["#b5b5b5", "#c0c0c0", "#c7c7c7", "#cfcfcf"], "rainbow": ["hsl({}, 50%, 50%)".format(i) for i in range(0, 360, 10)]}


def deduplicate(items: List[Edge]) -> List[Edge]:
    """ Return the same list but without duplicates. """

    output = []
    seen = set()
    for item in items:
        if item not in seen:
            output.append(item)
            seen.add(item)
    return output


def add(A: Coord, B: Coord, s: float = 1.0, t: float = 1.0) -> Coord:
    """ Return the point sA + tB. """

    return (s * A[0] + t * B[0], s * A[1] + t * B[1])


def interpolate(A: Coord, B: Coord, r: float = 0.5) -> Coord:
    """ Return the point that is r% from B to A. """

    return add(A, B, r, 1 - r)


def support(triangulation: bigger.Triangulation[Edge], edge: Edge) -> Tuple[Triangle, Triangle]:
    """ Return the two triangles that support and edge. """

    a, b, c, d = triangulation.link(edge)
    triangle1, triangle2 = (a, b, edge), (c, d, edge)
    # Cyclically permute to the canonical position.
    triangle1 = min(triangle1, triangle1[1:] + triangle1[:1], triangle1[2:] + triangle1[:2])
    triangle2 = min(triangle2, triangle2[1:] + triangle2[:1], triangle2[2:] + triangle2[:2])
    return triangle1, triangle2


def adjacent(triangulation: bigger.Triangulation[Edge], current: Triangle, side: int) -> Tuple[Triangle, int]:
    """ Return the (other triangle, other side) which shares an edge with triangle[side]. """

    return next(
        (other, other_side)
        for other in support(triangulation, current[side])
        for other_side in range(3)
        if other[other_side] == current[side] and (other != current or other_side != side)
    )


def supporting_triangles(triangulation: bigger.Triangulation[Edge], edges: List[Edge]) -> Tuple[List[List[Triangle]], Set[Edge]]:
    """ Return a list of list of triangles that support these edges, grouped by connectedness, and a set of edges that in the interior. """

    position_index = dict((edge, index) for index, edge in enumerate(edges))
    edge_set = set(edges)

    # Compute the connect components of the supporting triangles of the given edges.
    components = bigger.UnionFind(deduplicate([triangle for edge in edges for triangle in support(triangulation, edge)]))
    for edge in edges:
        components.union(*support(triangulation, edge))

    # Order the triangles of each component by their position_index.
    ordered_components = [sorted(list(component), key=lambda triangle: tuple(position_index.get(edge, len(position_index)) for edge in triangle)) for component in components]
    interior = set()
    for component in ordered_components:
        # Get a starting triangle.
        start = component[0]

        # Expore out to find out which edges are in the interior.
        placed = set([start])
        to_check: PriorityQueue = PriorityQueue()
        for i in range(3):
            if start[i] in edge_set:
                to_check.put((position_index.get(start[i], len(position_index)), (start, i)))
        while not to_check.empty():
            _, (current, side) = to_check.get()
            other, _ = adjacent(triangulation, current, side)
            if other not in placed:
                interior.add(current[side])
                placed.add(other)
                for other_side in range(3):
                    if other[other_side] != current[side] and other[other_side] in edge_set:
                        to_check.put((position_index.get(other[other_side], len(position_index)), (other, other_side)))

    return ordered_components, interior


def default_layout_triangulation(triangulation: bigger.Triangulation[Edge], components: List[List[Triangle]], interior: Set[Edge]) -> Dict[Triangle, FlatTriangle]:
    """Return a dictionary mapping the triangles that meet the given edges to coordinates in the plane.

    Triangle T is mapped to ((x1, y1), (x2, y2), (x3, y3)) where (xi, yi) is at the tail of side i of T when oriented anti-clockwise.
    Coordinate are within the w x h rectangle."""

    r = 1000.0

    layout = dict()
    for component in components:
        # Create the vertices.
        num_outside = sum(1 for triangle in component for edge in triangle if edge not in interior)
        vertices = [(r * sin(2 * pi * (i - 0.5) / num_outside), r * cos(2 * pi * (i - 0.5) / num_outside)) for i in range(num_outside)]
        # Determine how many boundary edges occur between each edge's endpoints.
        # We really should do this in a sensible order so that it only takes a single pass.
        num_decendents = dict(((triangle, side), 1) for triangle in component for side in range(3) if triangle[side] not in interior)
        stack = [(triangle, side) for triangle in component for side in range(3)]
        while stack:
            current, side = stack.pop()
            if (current, side) in num_decendents:
                continue

            # So current[side] is in interior.
            other, _ = adjacent(triangulation, current, side)
            other_sides = [other_side for other_side in range(3) if other[other_side] != current[side]]
            try:
                num_decendents[(current, side)] = sum(num_decendents[(other, other_side)] for other_side in other_sides)
            except KeyError:  # We need to evaluate one of the other sides first.
                stack.append((current, side))  # Re-evaluate when we get back here.
                stack.extend([(other, other_side) for other_side in other_sides])

        # Work out which vertex (number) each side of each triangle starts at.
        start = component[0]
        triangle_vertex_number = {
            (start, 0): 0,
            (start, 1): num_decendents[(start, 0)],
            (start, 2): num_decendents[(start, 0)] + num_decendents[(start, 1)],
        }
        to_extend = [(start, side) for side in range(3) if start[side] in interior]
        while to_extend:
            current, side = to_extend.pop()
            other, other_side = adjacent(triangulation, current, side)

            triangle_vertex_number[(other, (other_side + 0) % 3)] = triangle_vertex_number[(current, (side + 1) % 3)]
            triangle_vertex_number[(other, (other_side + 1) % 3)] = triangle_vertex_number[(current, (side + 0) % 3)]
            triangle_vertex_number[(other, (other_side + 2) % 3)] = triangle_vertex_number[(other, (other_side + 1) % 3)] + num_decendents[(other, (other_side + 1) % 3)]

            for i in [1, 2]:
                if other[(other_side + i) % 3] in interior:
                    to_extend.append((other, (other_side + i) % 3))

        for triangle in component:
            layout[triangle] = (vertices[triangle_vertex_number[(triangle, 0)]], vertices[triangle_vertex_number[(triangle, 1)]], vertices[triangle_vertex_number[(triangle, 2)]])

    return layout


def draw_block_triangle(canvas: ImageDraw, vertices: FlatTriangle, weights: List[int], master: int) -> None:
    """ Draw a flat triangle with (blocks of) lines inside it. """

    weights_0 = [max(weight, 0) for weight in weights]
    sum_weights_0 = sum(weights_0)
    correction = min(min(sum_weights_0 - 2 * e for e in weights_0), 0)
    dual_weights = [bigger.half(sum_weights_0 - 2 * e + correction) for e in weights_0]
    parallel_weights = [max(-weight, 0) for weight in weights]
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
            canvas.polygon([S1, E1, E2, S2], fill=LAMINATION_COLOUR)
        elif dual_weights[i] < 0:  # Terminal arc.
            s_0 = (1 - 2 * VERTEX_BUFFER) * weights_0[i] / master

            scale_a = (1 - s_0) / 2 + s_0 * dual_weights[i - 1] / weights_0[i]
            scale_a2 = scale_a + s_0 * (-dual_weights[i]) / weights_0[i]

            S1 = interpolate(vertices[i - 0], vertices[i - 2], scale_a)
            E1 = vertices[i - 1]
            S2 = interpolate(vertices[i - 0], vertices[i - 2], scale_a2)
            E2 = vertices[i - 1]
            canvas.polygon([S1, E1, E2, S2], fill=LAMINATION_COLOUR)
        else:  # dual_weights[i] == 0:  # Nothing to draw.
            pass

        # Parallel arcs.
        if parallel_weights[i]:
            S, O, E = vertices[i - 2], vertices[i - 1], vertices[i]
            SS = interpolate(O, S, VERTEX_BUFFER)
            EE = interpolate(O, E, VERTEX_BUFFER)
            M = interpolate(S, E)
            MM = interpolate(SS, EE)
            s = parallel_weights[i] / master
            P = interpolate(MM, M, s)
            canvas.polygon([S, P, E], fill=LAMINATION_COLOUR)


def draw_line_triangle(canvas: ImageDraw, vertices: FlatTriangle, weights: List[int], master: int) -> None:
    """ Draw a flat triangle with (individual) lines inside it. """

    weights_0 = [max(weight, 0) for weight in weights]
    sum_weights_0 = sum(weights_0)
    correction = min(min(sum_weights_0 - 2 * e for e in weights_0), 0)
    dual_weights = [bigger.half(sum_weights_0 - 2 * e + correction) for e in weights_0]
    parallel_weights = [max(-weight, 0) for weight in weights]
    for i in range(3):  # Dual arcs:
        if dual_weights[i] > 0:
            s_a = 1 - 2 * VERTEX_BUFFER
            s_b = 1 - 2 * VERTEX_BUFFER
            for j in range(dual_weights[i]):
                scale_a = 0.5 if weights_0[i - 2] == 1 else (1 - s_a) / 2 + s_a * j / (weights_0[i - 2] - 1)
                scale_b = 0.5 if weights_0[i - 1] == 1 else (1 - s_b) / 2 + s_b * j / (weights_0[i - 1] - 1)

                S1 = interpolate(vertices[i - 2], vertices[i - 1], scale_a)
                E1 = interpolate(vertices[i - 0], vertices[i - 1], scale_b)
                canvas.line([S1, E1], fill=LAMINATION_COLOUR, width=2)
        elif dual_weights[i] < 0:  # Terminal arc.
            s_0 = 1 - 2 * VERTEX_BUFFER
            for j in range(-dual_weights[i]):
                scale_a = 0.5 if weights_0[i] == 1 else (1 - s_0) / 2 + s_0 * dual_weights[i - 1] / (weights_0[i] - 1) + s_0 * j / (weights_0[i] - 1)

                S1 = interpolate(vertices[i - 0], vertices[i - 2], scale_a)
                E1 = vertices[i - 1]
                canvas.line([S1, E1], fill=LAMINATION_COLOUR, width=2)
        else:  # dual_weights[i] == 0:  # Nothing to draw.
            pass

        # Parallel arcs:
        if parallel_weights[i]:
            S, O, E = vertices[i - 2], vertices[i - 1], vertices[i]
            SS = interpolate(O, S, VERTEX_BUFFER)
            EE = interpolate(O, E, VERTEX_BUFFER)
            M = interpolate(S, E)
            MM = interpolate(SS, EE)
            for j in range(parallel_weights[i] // 2):
                s = float(j + 1) / master
                P = interpolate(MM, M, s)
                canvas.line([S, P, E], fill=LAMINATION_COLOUR, width=2)
            if parallel_weights[i] % 2 == 1:
                canvas.line([S, E], fill=LAMINATION_COLOUR, width=2)


def draw_lamination(lamination: bigger.Lamination[Edge], edges: List[Edge], layout: Optional[SupportsLayout] = None, **options: Any) -> Image:  # pylint: disable=too-many-branches
    """ Return an image of this lamination on the specified edges. """
    options = {"w": 400, "h": 400, "label": "none", "colour": "bw", "outline": False, **options}

    image = Image.new("RGB", (options["w"], options["h"]), color="White")
    canvas = ImageDraw.Draw(image)

    # Draw these triangles.
    components, interior = supporting_triangles(lamination.triangulation, edges)
    if layout is None:
        layout2 = default_layout_triangulation(lamination.triangulation, components, interior)
    else:
        layout2 = dict((triangle, layout.layout(triangle)) for component in components for triangle in component)

    # We will layout the components in a p x q grid.
    # Aim to maximise r := min(w / p, h / q) subject to pq >= num_components.
    # There is probably a closed formula for the optimal value of p (and so q).
    num_components = len(components)
    p = max(range(1, num_components + 1), key=lambda p: min(options["w"] / p, options["h"] / ceil(float(num_components) / p)))
    q = int(ceil(float(num_components) / p))
    ww = options["w"] / p * (1 + ZOOM_FRACTION) / 4
    hh = options["h"] / q * (1 + ZOOM_FRACTION) / 4
    dx = options["w"] / p
    dy = options["h"] / q

    # Scale & translate to fit into the [-r, r] x [-r, r] box.
    layout3 = dict()
    for component in components:
        bb_w = min(vertex[0] for triangle in component for vertex in layout2[triangle])
        bb_e = max(vertex[0] for triangle in component for vertex in layout2[triangle])
        bb_n = min(vertex[1] for triangle in component for vertex in layout2[triangle])
        bb_s = max(vertex[1] for triangle in component for vertex in layout2[triangle])
        for triangle in component:
            a, b, c = layout2[triangle]
            layout3[triangle] = (
                ((a[0] - bb_w) * 2 * ww / (bb_e - bb_w) - ww, (a[1] - bb_n) * 2 * hh / (bb_s - bb_n) - hh),
                ((b[0] - bb_w) * 2 * ww / (bb_e - bb_w) - ww, (b[1] - bb_n) * 2 * hh / (bb_s - bb_n) - hh),
                ((c[0] - bb_w) * 2 * ww / (bb_e - bb_w) - ww, (c[1] - bb_n) * 2 * hh / (bb_s - bb_n) - hh),
            )

    # Move to correct region within the image.
    layout4 = dict()
    for index, component in enumerate(components):
        for triangle in component:
            centre = (dx * (index % p) + dx / 2, dy * int(index / p) + dy / 2)
            a, b, c = layout3[triangle]
            layout4[triangle] = (add(a, centre), add(b, centre), add(c, centre))

    # Draw triangles.
    triangle_colours = TRIANGLE_COLOURS[options["colour"]]
    for index, (triangle, vertices) in enumerate(layout4.items()):
        canvas.polygon(vertices, fill=triangle_colours[index % len(triangle_colours)], outline="white" if options["outline"] else None)

    weights = dict((edge, lamination(edge)) for edge in set(edge for triangle in layout4 for edge in triangle))

    master = max(abs(weights[edge]) for triangle in layout4 for edge in triangle)
    shown_is_integral = all(isinstance(weights[edge], int) for edge in weights)

    # Draw lamination.
    for index, (triangle, vertices) in enumerate(layout4.items()):
        if master < MAX_DRAWABLE and shown_is_integral:
            draw_line_triangle(canvas, vertices, [weights[edge] for edge in triangle], master)
        else:  # Draw everything. Caution, this is is VERY slow (O(n) not O(log(n))) so we only do it when the weight is low.
            draw_block_triangle(canvas, vertices, [weights[edge] for edge in triangle], master)

    # Draw labels.
    for index, (triangle, vertices) in enumerate(layout4.items()):
        for side in range(3):
            if options["label"] == "edge":
                text = str(triangle[side])
            if options["label"] == "weight":
                text = str(weights[triangle[side]])
            if options["label"] == "none":
                text = ""
            w, h = canvas.textsize(text)
            point = interpolate(vertices[side - 0], vertices[side - 2])
            point = (point[0] - w / 2, point[1] - h / 2)
            for offset in OFFSETS:
                canvas.text(add(point, offset), text, fill="White", anchor="centre")

            canvas.text(point, text, fill="Black", anchor="centre")

    return image


class DrawStructure:  # pylint: disable=too-few-public-methods
    """ A class to record intermediate draw commands. """

    def __init__(self, edges: Optional[List[Edge]] = None, **options: Any):
        self.edges = edges
        self.options = options

    def __call__(
        self, obj: Optional[Union[bigger.Lamination[Edge], bigger.MCG[Edge], bigger.Triangulation[Edge]]] = None, edges: Optional[List[Edge]] = None, **kwargs: Any
    ) -> Union[DrawStructure, Image]:
        draw_structure = DrawStructure(edges=edges if edges is not None else self.edges, **{**self.options, **kwargs})
        if obj is None:
            return draw_structure
        elif draw_structure.edges is None:
            raise TypeError("draw() missing 1 required positional argument: 'edges'")
        elif isinstance(obj, bigger.Lamination):
            return draw_lamination(obj, draw_structure.edges, **draw_structure.options)
        elif isinstance(obj, bigger.Triangulation):
            return draw_structure(obj.empty_lamination())
        elif isinstance(obj, bigger.MCG):
            return draw_structure(obj.triangulation)

        raise TypeError("Unable to draw objects of type: {}".format(type(obj)))


def draw(
    obj: Optional[Union[bigger.Lamination[Edge], bigger.MCG[Edge], bigger.Triangulation[Edge]]] = None, edges: Optional[List[Edge]] = None, **options: Any
) -> Union[DrawStructure, Image]:
    """ Draw the given object with the provided options. """

    return DrawStructure(edges=edges, **options)(obj)
