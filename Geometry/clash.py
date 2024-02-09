from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Tuple, Any, Optional

try:
    import pymesh
except ImportError:
    from Geometry.mocks import mypymesh

    pymesh = mypymesh

from speckle_automate import AutomationContext

from Geometry.element import Element
from Geometry.mesh import cast


def detect_clashes_old(
        reference_elements: List[Element], latest_elements: List[Element], _tolerance: float
) -> list[tuple[str, str, float]]:
    """
    Detect clashes between two sets of mesh elements using Pymesh.

    Args:
        reference_elements (List[Element]): Elements from the reference model.
        latest_elements (List[Element]): Elements from the latest model.
        _tolerance (float): Tolerance value for clash detection. TODO: how to implement this?

    Returns:
        List[Tuple[str, str]]: List of tuples indicating clashes, with each tuple
                               containing the IDs of the clashing elements.
    """
    # TODO: Spatial partitioning to reduce number of comparisons
    # TODO: Tolerance
    # TODO: parallel processing

    clashes = []
    for ref_element in reference_elements:
        for latest_element in latest_elements:
            for ref_mesh in ref_element.meshes:
                for latest_mesh in latest_element.meshes:
                    # Convert Trimesh meshes to Pymesh if necessary
                    ref_pymesh: pymesh.Mesh = cast(ref_mesh, pymesh.Mesh)
                    latest_pymesh: pymesh.Mesh = cast(latest_mesh, pymesh.Mesh)

                    if not ref_pymesh or not latest_pymesh:
                        continue

                    intersection = pymesh.boolean(
                        latest_pymesh, ref_pymesh, operation="intersection"
                    )

                    if (
                            intersection and intersection.volume > 0
                    ):  # TODO: could tolerance relate to this?
                        severity = intersection.volume / min(
                            ref_pymesh.volume, latest_pymesh.volume
                        )
                        clashes.append((ref_element.id, latest_element.id, severity))
                        break

    return clashes


def check_for_clash(
        ref_element: Element, latest_element: Element
) -> Optional[tuple[Any, Any]]:
    """
    Check for a clash between two elements and calculate the severity of the clash.

    Args:
        ref_element (Element): An element from the reference model.
        latest_element (Element): An element from the latest model.

    Returns:
        Tuple[str, str, float]: A tuple containing the IDs of the clashing elements and the severity, if a clash is found.
    """

    for ref_mesh in ref_element.meshes:
        for latest_mesh in latest_element.meshes:
            ref_pymesh = cast(ref_mesh, pymesh.Mesh)
            latest_pymesh = cast(latest_mesh, pymesh.Mesh)

            if not ref_pymesh or not latest_pymesh:
                continue

            intersection = pymesh.boolean(latest_pymesh, ref_pymesh, operation="intersection")

            if intersection and intersection.volume > 0:

                return ref_element.id, latest_element.id
    return None


def detect_clashes(
        reference_elements: List[Element], latest_elements: List[Element], _tolerance: float
) -> List[Tuple[str, str]]:
    """
    Detect clashes between two sets of mesh elements using parallel processing.

    Args:
        reference_elements (List[Element]): Elements from the reference model.
        latest_elements (List[Element]): Elements from the latest model.
        _tolerance (float): Tolerance value for clash detection. TODO: how to implement this?

    Returns:
        List[Tuple[str, str, float]]: A list of tuples indicating clashes.
    """
    clashes = []
    with ProcessPoolExecutor() as executor:
        future_clash = {
            executor.submit(check_for_clash, ref, latest): (ref, latest)
            for ref in reference_elements
            for latest in latest_elements
        }
        for future in as_completed(future_clash):
            result = future.result()
            if result:
                clashes.append(result)

    return clashes


def detect_and_report_clashes(
        reference_elements: list[Element],
        latest_elements: list[Element],
        tolerance: float,
        automate_context: AutomationContext,
) -> list[tuple[str, str]]:

    clashes = detect_clashes(reference_elements, latest_elements, tolerance)

    grouped_clashes = defaultdict(list)

    for ref, latest in clashes:
        if not latest:
            continue
        grouped_clashes[ref].append(latest)

    for group_number, clashing_objects in enumerate(grouped_clashes.items(), start=1):

        ref_id, latest_elements = clashing_objects

        all_clashing_objects = [ref_id] + [element_id for element_id in  latest_elements]

        automate_context.attach_error_to_objects(
            category="Clash", object_ids=all_clashing_objects, message=str(group_number)
        )

    return clashes
