from typing import Tuple, Optional, List

import numpy as np
import trimesh
from specklepy.objects import Base
from specklepy.objects.geometry import Mesh as SpeckleMesh
from specklepy.objects.other import Transform

from Geometry.helpers import combine_transform_matrices
from Geometry.mesh import speckle_mesh_to_trimesh


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


def speckle_to_element(
    base_id_transforms: Tuple[Base, str, Optional[List[Transform]]]
) -> Element:
    """
    Convert a SpecklePy Base object, its identifier, and an optional list of transforms
    to an Element object.

    Args:
        base_id_transforms (tuple): Contains a SpecklePy Base object, its identifier,
            and an optional list of Transform objects.

    Returns:
        Element: The resulting Element object.
    """
    base, speckle_id, transforms = base_id_transforms

    display_value = base.displayValue
    if isinstance(display_value, SpeckleMesh):
        display_value = [display_value]

    element = Element(speckle_id, meshes=[])

    # Combine all transforms into a single matrix
    combined_transform = (
        combine_transform_matrices(transforms) if transforms else np.identity(4)
    )

    if isinstance(display_value, list):
        for mesh in display_value:
            if mesh:
                t_mesh = speckle_mesh_to_trimesh(mesh)
                if not isinstance(t_mesh, trimesh.Trimesh):
                    continue

                # Apply the combined transformation matrix
                t_mesh.apply_transform(combined_transform)
                element.meshes.append(t_mesh)

    return element
