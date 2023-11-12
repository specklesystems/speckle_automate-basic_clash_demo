# Required imports
from typing import Callable, List, Union

from specklepy.objects import Base


# We're going to define a set of rules that will allow us to filter and
# process parameters in our Speckle objects. These rules will be encapsulated
# in a class called `ParameterRules`.


class ElementCheckRules:
    """A collection of rules for processing parameters in Speckle objects.

    This class provides static methods that return lambda functions. These
    lambda functions serve as filters or conditions we can use in our main
    processing logic. By encapsulating these rules, we can easily extend
    or modify them in the future.
    """

    @staticmethod
    def rule_combiner(*rules: Callable[[Base], bool]) -> Callable[[Base], bool]:
        def combined(obj: Base) -> bool:
            return all(rule(obj) for rule in rules)

        return combined

    @staticmethod
    def is_displayable_rule() -> Callable[[Base], bool]:
        """Rule: Check if a parameter is displayable."""
        return (
            lambda parameter: parameter.displayValue
            and parameter.displayValue is not None
        )

    @staticmethod
    def speckle_type_rule(
        desired_type: Union[str, List[str]]
    ) -> Callable[[Base], bool]:
        """Rule: Check if a parameter's speckle_type matches the desired type."""

        # Convert single string to list for consistent handling
        if isinstance(desired_type, str):
            desired_type = [desired_type]

        print(desired_type)

        return (
            lambda speckle_object: getattr(speckle_object, "speckle_type", None)
            in desired_type
        )
