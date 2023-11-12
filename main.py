"""This module contains the business logic of the function.

use the automation_context module to wrap your function in an Automate context helper
"""
from typing import List, Optional, Tuple

from pydantic import Field
from speckle_automate import (
    AutomateBase,
    AutomationContext,
    execute_automate_function,
)
from specklepy.api import operations
from specklepy.api.models import Branch
from specklepy.objects import Base
from specklepy.objects.other import Transform
from specklepy.objects.units import Units
from specklepy.transports.server import ServerTransport
from trimesh import Trimesh

from Geometry.mesh import speckle_to_element, Element
from Rules.checks import ElementCheckRules
from flatten import extract_base_and_transform


class FunctionInputs(AutomateBase):
    """These are function author defined values.

    Automate will make sure to supply them matching the types specified here.
    Please use the pydantic model schema to define your inputs:
    https://docs.pydantic.dev/latest/usage/models/
    """

    tolerance: float = Field(
        default=25.0,
        title="Tolerance",
        description="Specify the tolerance value for the analysis. \
            Negative values relaxes the test, positive values make it more strict.",
    )
    tolerance_unit: str = Field(  # Using the SpecklePy Units enum here
        default=Units.mm,
        json_schema_extra={"examples": ["mm", "cm", "m"]},
        title="Tolerance Unit",
        description="Unit of the tolerance value.",
    )
    static_model_name: str = Field(
        ...,
        title="Static Model Name",
        description="Name of the static structural model.",
    )


def automate_function(
    automate_context: AutomationContext,
    function_inputs: FunctionInputs,
) -> None:
    """This is an example Speckle Automate function.

    Args:
        automate_context: A context helper object, that carries relevant information
            about the runtime context of this function.
            It gives access to the Speckle project data, that triggered this run.
            It also has convenience methods attach result data to the Speckle model.
        function_inputs: An instance object matching the defined schema.
    """
    # the context provides a convenient way, to receive the triggering version
    changed_model_version = automate_context.receive_version()

    try:
        reference_model_version = get_reference_model(
            automate_context, function_inputs.static_model_name
        )

    except Exception as ex:
        automate_context.mark_run_failed(status_message=str(ex))
        return

    reference_objects: tuple[
        Base,
        str,
        Optional[Transform],
    ] = extract_base_and_transform(reference_model_version)
    latest_objects: tuple[
        Base,
        str,
        Optional[Transform],
    ] = extract_base_and_transform(changed_model_version)

    element_rules = ElementCheckRules()

    beam_types = [
        "Objects.BuiltElements.Beam:Objects.BuiltElements.Revit.RevitBeam",
    ]
    duct_types = [
        "Objects.BuiltElements.Duct",
        "Objects.BuiltElements.Duct:Objects.BuiltElements.Revit.RevitDuct",
        "Objects.BuiltElements.Duct:Objects.BuiltElements.Revit.RevitDuct:Objects.BuiltElements.Revit.RevitFlexDuct",
    ]

    visible_beams_rule = element_rules.rule_combiner(
        element_rules.speckle_type_rule(beam_types),
        element_rules.is_displayable_rule(),
    )

    visible_ducts_rule = element_rules.rule_combiner(
        element_rules.speckle_type_rule(duct_types),
        element_rules.is_displayable_rule(),
    )

    reference_displayable_objects = [
        (base_obj, id, transform)
        for base_obj, id, transform in reference_objects
        if visible_beams_rule(base_obj)
    ]
    latest_displayable_objects = [
        (base_obj, id, transform)
        for base_obj, id, transform in latest_objects
        if visible_ducts_rule(base_obj)
    ]

    reference_mesh_elements = [
        speckle_to_element(obj) for obj in reference_displayable_objects
    ]
    latest_mesh_elements = [
        speckle_to_element(obj) for obj in latest_displayable_objects
    ]

    # using trimesh library process all these meshes in the form of A vs B
    # and get the clashes

    clashes = detect_clashes(
        reference_mesh_elements, latest_mesh_elements, function_inputs.tolerance
    )

    print(len(clashes))

    automate_context.mark_run_success(status_message="Clash detection completed.")



def detect_clashes(
    elements_a: List[Element], elements_b: List[Element], length_tolerance: float
) -> List[Tuple[Element, Element]]:
    """
    Detects clashes between two sets of elements with a specified tolerance.

    This function checks each combination of elements from `elements_a` and `elements_b`
    to see if any of their respective meshes intersect within the specified tolerance.
    If a clash is detected between any mesh from an element in `elements_a` and any mesh
    from an element in `elements_b`, the pair of elements is added to the results.

    Args:
    - elements_a (List[Element]): A list of `Element` objects to be checked for clashes.
    - elements_b (List[Element]): A second list of `Element` objects to be checked for clashes against `elements_a`.
    - length_tolerance (float): The distance to offset mesh vertices for intersection check.

    Returns:
    - List[Tuple[Element, Element]]: A list of tuples where each tuple contains a pair of `Element` objects that clash.
    """

    # Use list comprehension to get pairs of elements that have clashing meshes
    clashes = [
        (element_a, element_b)
        for element_a in elements_a
        for element_b in elements_b
        if any(
            check_intersection_with_tolerance(mesh_a, mesh_b, length_tolerance)
            for mesh_a in element_a.meshes
            for mesh_b in element_b.meshes
        )
    ]

    return clashes


def check_intersection_with_tolerance(
    mesh_a: Trimesh, mesh_b: Trimesh, tolerance: float
) -> bool:
    """
    Checks for intersections between two meshes within a specified tolerance.

    Args:
    - mesh_a: The first mesh to check.
    - mesh_b: The second mesh to check.
    - tolerance (float): The distance to offset mesh vertices for intersection check.
                         Positive values expand the mesh, negative values contract it.

    Returns:
    - bool: True if the meshes intersect within the specified tolerance, otherwise False.
    """
    half_tolerance = tolerance / 2.0  # TODO: how to shrink bloat mesh?
    offset_mesh_a: Trimesh = mesh_a  # mesh_a.offset_mesh(half_tolerance)
    offset_mesh_b: Trimesh = mesh_b  # mesh_b.offset_mesh(half_tolerance)

    # return offset_mesh_a.intersection(offset_mesh_b).volume > 0 TODO: Install Blender as the engine

    # return a random boolean for testing - significantly favouring false
    import random

    return random.random() < 0.05


def get_reference_model(
    automate_context: AutomationContext, static_model_name: str
) -> Base:
    # the static reference model will be retrieved from the project using model name stored in the inputs
    speckle_client = automate_context.speckle_client
    project_id = automate_context.automation_run_data.project_id
    remote_transport = ServerTransport(
        automate_context.automation_run_data.project_id, speckle_client
    )

    model: Branch = speckle_client.branch.get(
        project_id, static_model_name, commits_limit=1
    )  # get the latest commit of the static model

    if not model:
        raise Exception("The static model named does not exist, skipping the function.")

    reference_model_commits = model.commits.items

    if not reference_model_commits:
        raise Exception("The static model has no versions, skipping the function.")

    latest_reference_model_id = model.id

    latest_reference_model_version_object = reference_model_commits[0].referencedObject

    if latest_reference_model_id == automate_context.automation_run_data.model_id:
        raise Exception(
            "The static model is the same as the changed model, skipping the function."
        )

    latest_reference_model_version = operations.receive(
        latest_reference_model_version_object,
        remote_transport,
    )  # receive the static model

    return latest_reference_model_version


# make sure to call the function with the executor
if __name__ == "__main__":
    # NOTE: always pass in the automate function by its reference, do not invoke it!

    # pass in the function reference with the inputs schema to the executor
    execute_automate_function(automate_function, FunctionInputs)

    # if the function has no arguments, the executor can handle it like so
    # execute_automate_function(automate_function_without_inputs)
