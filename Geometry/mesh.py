from typing import Tuple, Optional

import numpy as np
import trimesh
from specklepy.objects import Base
from specklepy.objects.geometry import Mesh as SpeckleMesh
from specklepy.objects.other import Transform
from trimesh import Trimesh


class Element:
    def __init__(self, id, meshes):
        """
        Initialize an Element object with an ID and a list of meshes.

        Args:
        id (str): The ID of the Element.
        meshes (List[Trimesh]): List of trimesh Mesh objects.
        """
        self.id = id
        self.meshes = meshes


def speckle_transform_to_trimesh_matrix(transform: Transform) -> np.ndarray:
    """
    Convert the Speckle Transform matrix to a NumPy array format suitable for trimesh.

    Returns:
        np.ndarray: 4x4 transformation matrix in NumPy array format.
    """
    return np.array(transform.value).reshape(4, 4)


def speckle_to_element(
    base_with_transforms: Tuple[Base, str, Optional[Transform]]
) -> Element:
    """
    Convert a SpecklePy Base object and its associated Transform to an Element object.

    Args:
        base_with_transforms (tuple): Contains a SpecklePy Base object and its
            associated Transform object.

    Returns:
        Element: The resulting Element object.
    """

    # Unpack the tuple to get the base, speckle ID, and transform.
    base, speckle_id, transform = base_with_transforms

    # To convert the Base object to a trimesh Mesh, use the displayValue property.
    # This property provides the display mesh, expected to be an iterable of
    # SpecklePy Mesh objects. However, legacy objects might be a single mesh.
    display_value = base.displayValue
    if isinstance(display_value, SpeckleMesh):
        display_value = [display_value]

    if isinstance(display_value, list):
        # Initialize an Element with an empty list of meshes.
        element = Element(speckle_id, meshes=[])

        for mesh in display_value:
            if mesh:
                # Convert the SpecklePy Mesh to a trimesh Mesh.
                t_mesh = speckle_to_trimesh(mesh)
                if not isinstance(t_mesh, Trimesh):
                    continue

                # If there's a transform, apply it to the trimesh Mesh.
                if transform is not None:
                    trimesh_matrix = speckle_transform_to_trimesh_matrix(transform)
                    t_mesh.apply_transform(trimesh_matrix)

                # Append the trimesh Mesh to the Element's list of meshes.
                element.meshes.append(t_mesh)

        return element


def speckle_to_trimesh(speckle_mesh: SpeckleMesh) -> Trimesh:
    """
    Convert a SpecklePy Mesh to a trimesh Mesh object.

    Args:
        speckle_mesh: The SpecklePy Mesh to convert.

    Returns:
        trimesh.Trimesh: The resulting trimesh Mesh object.
    """

    # Convert the list of vertices to a numpy array. Reshape it to
    # (num_vertices, 3) to fit the trimesh format.
    vertices_array = np.array(speckle_mesh.vertices).reshape((-1, 3))

    # Faces are expected to be triangular. Reshape the faces list accordingly.

    # Convert the faces list to a numpy array
    faces_array_raw = np.array(speckle_mesh.faces)

    # Remove the leading 3s by skipping every 4th value
    faces_cleaned = np.delete(faces_array_raw, np.arange(0, faces_array_raw.size, 4))

    # Reshape the array into (-1, 3) shape
    faces_array = faces_cleaned.reshape((-1, 3))

    # Return a new trimesh object using the reshaped vertices and faces.
    return trimesh.Trimesh(vertices=vertices_array, faces=faces_array)
