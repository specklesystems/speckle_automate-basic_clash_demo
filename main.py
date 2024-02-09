"""This module contains the business logic of the function.

use the automation_context module to wrap your function in an Automate context helper
"""

from collections import defaultdict
from typing import Optional

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

from Geometry.clash import detect_and_report_clashes
from Geometry.element import speckle_to_element
from Rules.checks import ElementCheckRules
from Utilities.flatten import extract_base_and_transform


class FunctionInputs(AutomateBase):
    """These are function author defined values.

    Automate will make sure to supply them matching the types specified here.
    Please use the pydantic model schema to define your inputs:
    https://docs.pydantic.dev/latest/usage/models/
    """

    static_model_name: str = Field(
        ...,
        title="Static Model Name",
        description="Name of the static structural model.",
    )
    tolerance: float = Field(
        default=25.0,
        title="Tolerance",
        description="Specify the tolerance value for the analysis. \
        Negative values relaxes the test, positive values make it more strict.",
        json_schema_extra={
            "readOnly": True,
        },
    )
    tolerance_unit: str = Field(  # Using the SpecklePy Units enum here
        default=Units.mm,
        title="Tolerance Unit",
        description="Unit of the tolerance value.",
        json_schema_extra={
          "examples": ["mm", "cm", "m"], 
          "readOnly": True
        },
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
        reference_model_version, reference_model_id, reference_model_version_id = (
            get_reference_model(automate_context, function_inputs.static_model_name)
        )
        print(
            f"Reference model id: {reference_model_id}, version id: {reference_model_version_id}"
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
        "Objects.Other.Revit.RevitInstance:Objects.BuiltElements.Revit.RevitMEPFamilyInstance",
        "Objects.BuiltElements.Revit.RevitElementType:Objects.BuiltElements.Revit.RevitSymbolElementType"
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

    tolerance = function_inputs.tolerance

    if len(reference_mesh_elements) == 0 or len(latest_mesh_elements) == 0:
        automate_context.mark_run_failed(
            status_message="Clash detection failed. No objects to compare."
        )
        return

    clashes = detect_and_report_clashes(
        reference_mesh_elements, latest_mesh_elements, tolerance, automate_context
    )

    percentage_reference_objects_clashing = (
        len(set([ref_id for ref_id, latest_id in clashes]))
        / len(reference_mesh_elements)
        * 100
    )
    percentage_latest_objects_clashing = (
        len(set([latest_id for ref_id, latest_id in clashes]))
        / len(latest_mesh_elements)
        * 100
    )

    # all clashes count
    all_objects_count = len(reference_mesh_elements) + len(latest_mesh_elements)
    all_clashes_count = len(clashes)

    clash_report_message = (
        f"Clash detection report: {all_clashes_count} clashes found "
        f"between {all_objects_count} objects. "
        f"Percentage of reference objects clashing: "
        f"{percentage_reference_objects_clashing}%. "
        f"Percentage of latest objects clashing: "
        f"{percentage_latest_objects_clashing}%."
    )

    reference_view = [f"{reference_model_id}@{reference_model_version_id}"]

    automate_context.set_context_view(reference_view)

    automate_context.mark_run_success(
        status_message="Clash detection completed. " + clash_report_message
    )


def get_reference_model(
    automate_context: AutomationContext, static_model_name: str
) -> tuple[Base, Optional[str], Optional[str]]:
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

    return latest_reference_model_version, model.id, reference_model_commits[0].id


# make sure to call the function with the executor
if __name__ == "__main__":
    # NOTE: always pass in the automate function by its reference, do not invoke it!

    # pass in the function reference with the inputs schema to the executor
    execute_automate_function(automate_function, FunctionInputs)

    # if the function has no arguments, the executor can handle it like so
    # execute_automate_function(automate_function_without_inputs)
