""" A module for making images of laminations. """

from __future__ import annotations

import os
from copy import deepcopy
from math import sin, cos, pi, ceil
from typing import Any, Generic, Optional, TypeVar, Union

from PIL import Image, ImageDraw, ImageFont  # type: ignore

import bigger
from bigger.types import Edge, Coord, FlatTriangle
from .triangulation import Triangle

# Vectors to offset a label by to produce backing.
OFFSETS = [(1.5 * cos(2 * pi * i / 12), 1.5 * sin(2 * pi * i / 12)) for i in range(12)]

# Colours of things.
DEFAULT_EDGE_LABEL_COLOUR = "black"
DEFAULT_EDGE_LABEL_BG_COLOUR = "white"
MAX_DRAWABLE = 100  # Maximum weight of a multicurve to draw fully.
ZOOM_FRACTION = 0.8
VERTEX_BUFFER = 0.2

LAMINATION_COLOUR = "#555555"
VERTEX_COLOUR = "#404040"
TRIANGLE_COLOURS = {"bw": ["#b5b5b5", "#c0c0c0", "#c7c7c7", "#cfcfcf"], "rainbow": ["hsl({}, 50%, 50%)".format(i) for i in range(0, 360, 10)]}

T = TypeVar("T")


def deduplicate(items: list[T]) -> list[T]:
    """Return the same list but without duplicates."""

    output = []
    seen = set()
    for item in items:
        if item not in seen:
            output.append(item)
            seen.add(item)
    return output


def add(A: Coord, B: Coord, s: float = 1.0, t: float = 1.0) -> Coord:
    """Return the point sA + tB."""

    return (s * A[0] + t * B[0], s * A[1] + t * B[1])


def interpolate(A: Coord, B: Coord, r: float = 0.5) -> Coord:
    """Return the point that is r% from B to A."""

    return add(A, B, r, 1 - r)


def support(triangulation: bigger.Triangulation[Edge], edge: Edge) -> tuple[Triangle[Edge], Triangle[Edge]]:
    """Return the two triangles that support and edge."""

    side = bigger.Side(edge)
    return triangulation.triangle(side), triangulation.triangle(~side)


def connected_components(triangulation: bigger.Triangulation[Edge], edges: list[Edge]) -> tuple[list[list[Triangle[Edge]]], set[Edge]]:
    """Return a list of list of triangles that support these edges, grouped by connectedness, and a set of edges that in the interior."""

    position_index = dict((edge, index) for index, edge in enumerate(edges))

    interior = set()
    # Kruskal's algorithm
    components = bigger.UnionFind(deduplicate([triangle for edge in edges for triangle in support(triangulation, edge)]))
    for edge in edges:
        t1, t2 = support(triangulation, edge)
        if components(t1) != components(t2):  # Don't merge if it would create a loop in the dual graph.
            interior.add(edge)
            components.union2(t1, t2)

    # Order the triangles of each component by their position_index.
    ordered_components = [sorted(list(component), key=lambda triangle: tuple(position_index.get(side.edge, len(position_index)) for side in triangle)) for component in components]

    return ordered_components, interior


def default_layout_triangulation(triangulation: bigger.Triangulation[Edge], component: list[Triangle[Edge]], interior: set[Edge]) -> dict[Triangle[Edge], FlatTriangle]:
    """Return a dictionary mapping the triangles that meet the given edges to coordinates in the plane.

    Triangle T is mapped to ((x1, y1), (x2, y2), (x3, y3)) where (xi, yi) is at the tail of side i of T when oriented anti-clockwise.
    Coordinate are within the w x h rectangle."""

    r = 1000.0

    # Create the vertices.
    num_outside = sum(1 for triangle in component for side in triangle if side.edge not in interior)
    vertices = [(r * sin(2 * pi * (i - 0.5) / num_outside), r * cos(2 * pi * (i - 0.5) / num_outside)) for i in range(num_outside)]
    # Determine how many boundary edges occur between each edge's endpoints.
    # We really should do this in a sensible order so that it only takes a single pass.
    num_descendants = dict((side, 1) for triangle in component for side in triangle if side.edge not in interior)
    stack = [side for triangle in component for side in triangle if side.edge in interior]
    while stack:
        current = stack.pop()
        if current in num_descendants:
            continue

        # So current is in interior.
        other = ~current
        other_sides = [other_side for other_side in triangulation.triangle(other) if other_side != other]
        try:
            num_descendants[current] = sum(num_descendants[other_side] for other_side in other_sides)
        except KeyError:  # We need to evaluate one of the other sides first.
            stack.append(current)  # Re-evaluate when we get back here.
            stack.extend(other_sides)

    # Work out which vertex (number) each side of each triangle starts at.
    start = component[0]
    triangle_vertex_number = {start[0]: 0, start[1]: num_descendants[start[0]], start[2]: num_descendants[start[0]] + num_descendants[start[1]]}
    to_extend = [side for side in start if side.edge in interior]
    while to_extend:
        current = to_extend.pop()

        A = triangulation.corner(current)
        B = triangulation.corner(~current)

        triangle_vertex_number[B[0]] = triangle_vertex_number[A[1]]
        triangle_vertex_number[B[1]] = triangle_vertex_number[A[0]]
        triangle_vertex_number[B[2]] = triangle_vertex_number[B[1]] + num_descendants[B[1]]

        for i in [1, 2]:
            if B[i].edge in interior:
                to_extend.append(B[i])

    layout = dict()
    for triangle in component:
        layout[triangle] = (vertices[triangle_vertex_number[triangle[0]]], vertices[triangle_vertex_number[triangle[1]]], vertices[triangle_vertex_number[triangle[2]]])

    return layout


def draw_block_triangle(canvas: ImageDraw, vertices: FlatTriangle, weights: list[int], master: int) -> None:
    """Draw a flat triangle with (blocks of) lines inside it."""

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


def draw_line_triangle(canvas: ImageDraw, vertices: FlatTriangle, weights: list[int], master: int) -> None:
    """Draw a flat triangle with (individual) lines inside it."""

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


class DrawStructure(Generic[Edge]):  # pylint: disable=too-many-instance-attributes
    """A class to record intermediate draw commands."""

    def __init__(self, **options: Any):
        self.edges: Optional[list[Edge]] = None
        self.w = 400
        self.h = 400
        self.label = "none"
        self.layout = None
        self.colour = "bw"
        self.outline = False
        self.textsize = 12
        self.set_options(**options)

    def set_options(self, **options: Any) -> None:
        """Set the options passed in."""

        for key, value in options.items():
            setattr(self, key, value)

    def __call__(self, *objs: Union[bigger.Lamination[Edge], bigger.MCG[Edge], bigger.Triangulation[Edge]], **options: Any) -> Union[DrawStructure, Image]:
        draw_structure = deepcopy(self)
        draw_structure.set_options(**options)

        if not objs:
            return draw_structure
        elif not draw_structure.edges:
            raise TypeError("draw() missing 1 required positional argument: 'edges'")
        for obj in objs:
            if not isinstance(obj, (bigger.Triangulation, bigger.Lamination, bigger.MCG)):
                raise TypeError("Unable to draw objects of type: {}".format(type(obj)))

        return draw_structure.draw_objs(*objs)

    def draw_objs(self, *objs: Union[bigger.Triangulation[Edge], bigger.Lamination[Edge], bigger.MCG[Edge]]) -> Image:  # pylint: disable=too-many-statements, too-many-branches
        """Return an image of these objects.

        This method assumes that:
         - at least one object is given,
         - that all objects exist on the first triangulation, and
         - self.edges has been set."""

        image = Image.new("RGB", (self.w, self.h), color="White")
        font = ImageFont.truetype(os.path.join(os.path.dirname(__file__), "fonts", "FreeMonoBold.ttf"), self.textsize)
        canvas = ImageDraw.Draw(image)

        assert self.edges is not None

        if isinstance(objs[0], bigger.Triangulation):
            triangulation = objs[0]
        elif isinstance(objs[0], bigger.Lamination):
            triangulation = objs[0].triangulation
        elif isinstance(objs[0], bigger.MCG):
            triangulation = objs[0].triangulation
        else:
            raise TypeError("Unable to draw objects of type: {}".format(type(objs[0])))

        # Draw these triangles.
        components, interior = connected_components(triangulation, self.edges)
        if self.layout is None:
            layout2 = dict(item for component in components for item in default_layout_triangulation(triangulation, component, interior).items())
        else:
            layout2 = dict((triangle, self.layout.layout(triangle)) for component in components for triangle in component)

        # We will layout the components in a p x q grid.
        # Aim to maximise r := min(w / p, h / q) subject to pq >= num_components.
        # There is probably a closed formula for the optimal value of p (and so q).
        num_components = len(components)
        p = max(range(1, num_components + 1), key=lambda p: min(self.w / p, self.h / ceil(float(num_components) / p)))
        q = int(ceil(float(num_components) / p))
        ww = self.w / p * (1 + ZOOM_FRACTION) / 4
        hh = self.h / q * (1 + ZOOM_FRACTION) / 4
        dx = self.w / p
        dy = self.h / q

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
        triangle_colours = TRIANGLE_COLOURS[self.colour]
        for index, (triangle, vertices) in enumerate(layout4.items()):
            canvas.polygon(vertices, fill=triangle_colours[index % len(triangle_colours)], outline="white" if self.outline else None)

        laminations = [obj for obj in objs if isinstance(obj, bigger.Lamination)]
        for lamination in laminations:
            weights = dict((edge, lamination(edge)) for edge in set(side.edge for triangle in layout4 for side in triangle))

            master = max(abs(weights[side.edge]) for triangle in layout4 for side in triangle)
            shown_is_integral = all(isinstance(weights[edge], int) for edge in weights)

            # Draw lamination.
            for index, (triangle, vertices) in enumerate(layout4.items()):
                if master < MAX_DRAWABLE and shown_is_integral:
                    draw_line_triangle(canvas, vertices, [weights[side.edge] for side in triangle], master)
                else:  # Draw everything. Caution, this is is VERY slow (O(n) not O(log(n))) so we only do it when the weight is low.
                    draw_block_triangle(canvas, vertices, [weights[side.edge] for side in triangle], master)

        # Draw labels.
        for triangle, vertices in layout4.items():
            for index, side in enumerate(triangle):
                if self.label == "edge":
                    text = str(side.edge)
                elif self.label == "weight" and len(laminations) == 1:  # Only draw weights if there is a single lamination.
                    text = str(weights[side.edge])
                else:
                    text = ""
                point = interpolate(vertices[index - 0], vertices[index - 2])
                # For some reason anchor="mm" does not work. So we will have to manually center the text ourselves.
                w, h = canvas.textsize(text, font=font)
                point = (point[0] - w / 2, point[1] - h / 2)
                for offset in OFFSETS:
                    canvas.text(add(point, offset), text, fill="White", font=font)

                canvas.text(point, text, fill="Black", font=font)

        # Draw vertices.
        for vertices in layout4.values():
            for vertex in vertices:
                canvas.ellipse([vertex[0] - 2, vertex[1] - 2, vertex[0] + 2, vertex[1] + 2], fill=VERTEX_COLOUR)

        return image


def draw(*objs: Union[bigger.Lamination[Edge], bigger.MCG[Edge], bigger.Triangulation[Edge]], edges: Optional[list[Edge]] = None, **options: Any) -> Union[DrawStructure, Image]:
    """Draw the given object with the provided options."""

    # This is only really here so we can provide "edges" as a keyword argument to users.

    return DrawStructure[Edge](edges=edges, **options)(*objs)
