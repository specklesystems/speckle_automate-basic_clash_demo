from typing import Union, Type, TYPE_CHECKING


import pymesh


import trimesh


class MockPyMesh:
    def __init__(self, vertices, faces):
        self.vertices = vertices or []
        self.faces = faces or []

    def boolean(self, other, operation):
        return MockPyMesh([], [])


def trimesh_to_pymesh(mesh: trimesh.Trimesh) -> pymesh.Mesh:
    """
    Convert a Trimesh object to a Pymesh object.
    Args:
        mesh (Trimesh): The Trimesh object to convert.
    Returns:
        pymesh.Mesh: The resulting Pymesh object.
    """
    return pymesh.form_mesh(mesh.vertices, mesh.faces)


def pymesh_to_trimesh(mesh: pymesh.Mesh) -> trimesh.Trimesh:
    """
    Convert a Pymesh object to a Trimesh object.
    Args:
        mesh (pymesh.Mesh): The Pymesh object to convert.
    Returns:
        trimesh.Trimesh: The resulting Trimesh object.
    """
    return trimesh.Trimesh(vertices=mesh.vertices, faces=mesh.faces)


def cast(
    mesh: Union[trimesh.Trimesh, pymesh.Mesh], target_type: Type
) -> Union[trimesh.Trimesh, pymesh.Mesh]:
    """
    Casts a mesh object to a specified type.

    Args:
        mesh (Union[trimesh.Trimesh, pymesh.Mesh]): The mesh object to cast.
        target_type (Type): The type to cast the mesh to.

    Returns:
        Union[trimesh.Trimesh, pymesh.Mesh]: The cast mesh object.
    """

    if isinstance(mesh, trimesh.Trimesh) and target_type is pymesh.Mesh:
        return trimesh_to_pymesh(mesh)
    elif isinstance(mesh, pymesh.Mesh) and target_type is trimesh.Trimesh:
        return pymesh_to_trimesh(mesh)
    else:
        raise TypeError("Unsupported mesh type or target type.")


import numpy as np
import trimesh
from specklepy.objects.geometry import Mesh as SpeckleMesh, Vector


def speckle_mesh_to_trimesh(input_mesh: SpeckleMesh) -> trimesh.Trimesh:
    vertices = np.array(input_mesh.vertices).reshape((-1, 3))
    faces = []

    i = 0
    while i < len(input_mesh.faces):
        face_vertex_count = input_mesh.faces[i]
        i += 1  # Skip the vertex count

        face_vertex_indices = input_mesh.faces[i : i + face_vertex_count]

        face_vertices = [
            Vector.from_list(vertices[idx].tolist()) for idx in face_vertex_indices
        ]

        if face_vertex_count == 3:
            faces.append(face_vertex_indices)
        else:
            triangulated = triangulate_face(face_vertices)
            faces.extend(
                [[face_vertex_indices[idx] for idx in tri] for tri in triangulated]
            )

        i += face_vertex_count

    return trimesh.Trimesh(vertices=vertices, faces=np.array(faces))
