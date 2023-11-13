from typing import List

import numpy as np
from specklepy.objects.geometry import Vector
from specklepy.objects.other import Transform as SpeckleTransform


def calculate_polygon_normal(vertices: List[Vector]) -> Vector:
    """
    Calculate the normal vector for a polygon represented by a list of vertices.

    Args:
        vertices (List[Vector]): A list of vertices representing the polygon.

    Returns:
        Vector: The normal vector of the polygon.
    """
    normal = Vector.from_list([0.0, 0.0, 0.0])
    num_vertices = len(vertices)
    for i in range(num_vertices):
        curr, nxt = vertices[i], vertices[(i + 1) % num_vertices]
        # Cross product components are accumulated to find the normal.
        normal.x += (curr.y - nxt.y) * (curr.z + nxt.z)
        normal.y += (curr.z - nxt.z) * (curr.x + nxt.x)
        normal.z += (curr.x - nxt.x) * (curr.y + nxt.y)

    # Normalize the calculated normal vector.
    length = np.sqrt(normal.x**2 + normal.y**2 + normal.z**2)
    normal.x, normal.y, normal.z = (
        normal.x / length,
        normal.y / length,
        normal.z / length,
    )
    return normal


def is_point_within_triangle(pt: Vector, v1: Vector, v2: Vector, v3: Vector) -> bool:
    """
    Check if a point is inside a given triangle.

    Args:
        pt (Vector): The point to check.
        v1, v2, v3 (Vector): The vertices of the triangle.

    Returns:
        bool: True if the point is inside the triangle, False otherwise.
    """

    def sign(p1, p2, p3):
        return (p1.x - p3.x) * (p2.y - p3.y) - (p2.x - p3.x) * (p1.y - p3.y)

    b1 = sign(pt, v1, v2) < 0.0
    b2 = sign(pt, v2, v3) < 0.0
    b3 = sign(pt, v3, v1) < 0.0

    return (b1 == b2) and (b2 == b3)


def triangulate_face(vertices: List[Vector]) -> List[List[int]]:
    """
    Triangulate a polygon defined by a list of vertices.

    Args:
        vertices (List[Vector]): The vertices of the polygon.

    Returns:
        List[List[int]]: A list of triangles, each represented as a list of vertex indices.
    """
    triangles = []
    indices = list(range(len(vertices)))
    normal = calculate_polygon_normal(vertices)

    # The ear clipping algorithm is used for triangulation.
    while len(indices) > 2:
        for i in range(len(indices)):
            prev, curr, nxt = (
                indices[i - 1],
                indices[i],
                indices[(i + 1) % len(indices)],
            )
            if is_convex(vertices[prev], vertices[curr], vertices[nxt], normal):
                triangles.append([prev, curr, nxt])
                del indices[i]
                break

    return triangles


def is_convex(a: Vector, b: Vector, c: Vector, normal: Vector) -> bool:
    """
    Check if a triangle formed by three vertices (a, b, c) is convex with respect to a given normal.

    Args:
        a (Vector): The first vertex of the triangle.
        b (Vector): The second vertex of the triangle.
        c (Vector): The third vertex of the triangle.
        normal (Vector): The normal vector with respect to which convexity is checked.

    Returns:
        bool: True if the triangle is convex with respect to the normal, False otherwise.
    """
    ab = Vector.from_list([b.x - a.x, b.y - a.y, b.z - a.z])
    bc = Vector.from_list([c.x - b.x, c.y - b.y, c.z - b.z])
    cross = Vector.from_list(
        [
            ab.y * bc.z - ab.z * bc.y,
            ab.z * bc.x - ab.x * bc.z,
            ab.x * bc.y - ab.y * bc.x,
        ]
    )

    # Dot product to compare with the face normal
    return cross.x * normal.x + cross.y * normal.y + cross.z * normal.z > 0


def combine_transform_matrices(transforms: List[SpeckleTransform]) -> np.ndarray:
    """
    Combine multiple transformation matrices into a single matrix.

    Args:
        transforms (List[SpeckleTransform]): A list of Speckle Transform objects.

    Returns:
        np.ndarray: A combined 4x4 transformation matrix.
    """
    combined_matrix = np.identity(4)
    for transform in transforms:
        matrix = convert_speckle_transform_to_matrix(transform)
        combined_matrix = np.dot(combined_matrix, matrix)
    return combined_matrix


def convert_speckle_transform_to_matrix(transform: SpeckleTransform) -> np.ndarray:
    """
    Convert a Speckle Transform object to a 4x4 NumPy matrix.

    Args:
        transform (SpeckleTransform): The Speckle Transform object.

    Returns:
        np.ndarray: A 4x4 transformation matrix.
    """
    return np.array(transform.value).reshape(4, 4)
