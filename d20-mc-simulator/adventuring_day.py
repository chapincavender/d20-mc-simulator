"""
    Implements classes for running a combat encounter and an adventuring day.
"""

import numpy

from creature import Creature, LairAction
from dice_roller import rng


class Encounter:
    """A combat encounter with two groups of combatants."""

    def __init__(
        self,
        side_A: list[Creature],
        side_B: list[Creature],
        encounters_since_short_rest: int = 0,
        encounters_since_long_rest: int = 0,
        generator: numpy.random.Generator = rng,
    ):
        """
        Set up the combat encounter with lists of combatants and rest counts.

        Parameters
        ----------
        side_A
            List of creatures in the first side of combatants.
        side_B
            List of creatures in the second side of combatants.
        encounters_since_short_rest
            Number of encounters since the party has taken a short rest.
        encounters_since_long_rest
            Number of encounters since the party has taken a long rest.
        generator
            Pseudorandom number generator from numpy.random used for choosing
            random targets.
        """

        self.side_A = side_A
        self.side_B = side_B
        self.encounters_since_short_rest = encounters_since_short_rest
        self.encounters_since_long_rest = encounters_since_long_rest
        self.choice = generator.choice
        self.N_rounds = 0

        # Initialize lair actions
        self.lair_actions = []
        for creature in side_A + side_B:
            # Checks whether the creature's lair_action method has been
            # overwritten from the base Creature class
            if creature.lair_action.__func__ is not Creature.lair_action:
                self.lair_actions.append(LairAction(creature))

        # Determine initiative order. For ties, side_A will beat side_B. Within
        # sides, creatures should be in order of tie-breaking. Lair actions
        # occur at initiative 20, losing ties with side_A and side_B.
        self.initiative_order = sorted(
            side_A + side_B + self.lair_actions,
            key=lambda x: x.roll_initiative(),
            reverse=True,
        )

        if numpy.any([creature.verbose for creature in side_A + side_B]):

            message = "Initiative order:"
            for creature in self.initiative_order:
                message += f" {creature()}"
            print(message)

        # Features that trigger at the start of the encounter
        for creature in self.initiative_order:
            creature.start_encounter(self)

    def __call__(self):
        """
        Resolve the encounter, i.e. run combat rounds until one side is
        defeated.
        """
        while self.active():
            self.one_round()

    def active(self) -> bool:
        """Return whether at least one creature is alive on both sides."""

        return numpy.any([creature.hp > 0 for creature in self.side_A]) and numpy.any(
            [creature.hp > 0 for creature in self.side_B]
        )

    def choose_target(
        self,
        chooser: Creature,
        N_targets: int = 1,
        target_allies: bool = False,
        replacement: bool = False,
    ) -> Creature | list[Creature]:
        """
        Randomly choose one or more targets with positive hit points.

        Parameters
        ----------
        chooser
            Creature choosing targets. Used to decide which side to choose
            targets from.
        N_targets
            Number of targets to choose.
        target_allies
            Choose targets from allies rather than from foes.
        replacement
            Choose multiple targets with replacement rather than unique targets.
        """

        # Must target a swallowing creature
        if chooser.swallowed != None:
            valid_targets = [chooser.swallowed.swallower]

        elif target_allies:
            valid_targets = [
                creature for creature in self.get_allies(chooser) if creature.hp > 0
            ]

        else:
            valid_targets = [
                creature for creature in self.get_foes(chooser) if creature.hp > 0
            ]

        # Check if any targets are valid
        N_valid_targets = len(valid_targets)
        if N_valid_targets == 0:
            return None

        # Choose targets at random using numpy.random.generator.choice
        if N_targets == 1:
            return self.choice(valid_targets)

        elif N_targets >= N_valid_targets and not replacement:
            # More unique targets than number of valid targets
            return valid_targets

        else:
            return self.choice(
                valid_targets,
                size=N_targets,
                replace=replacement,
            )

    def get_allies(self, creature: Creature) -> list[Creature]:
        """
        Get list of creatures on the same side of the encounter as a specified
        creature.

        Parameters
        ----------
        creature
            Creature used to determine whether a side is allies or foes.
        """

        return self.side_A if creature in self.side_A else self.side_B

    def get_foes(self, creature: Creature) -> list[Creature]:
        """
        Get list of creatures on the opposite side of the encounter as a
        specified creature.

        Parameters
        ----------
        creature
            Creature used to determine whether a side is allies or foes.
        """

        return self.side_B if creature in self.side_A else self.side_A

    def one_round(self):
        """Resolve one round of combat."""

        self.N_rounds += 1

        for creature in self.initiative_order:
            if not self.active():
                break

            if creature.hp <= 0:
                continue

            creature.start_turn(self)


class AdventuringDay:
    """
    An adventuring day consisting of many identical encounters with a short rest
    after a fixed number of encounters.
    """

    # Constructor
    def __init__(
        self,
        pcs: list[Creature],
        adversaries: list[Creature],
        encounters_per_long_rest: int = 6,
        encounters_per_short_rest: int = 2,
    ):
        """
        Initialize the adventuring day.

        Parameters
        ----------
        pcs
            List of player characters.
        adversaries
            List of adversaries for a single encounter.
        encounters_per_long_rest
            Number of encounters before the party takes a long rest.
        encounters_per_short_rest
            Number of encounters before the party takes a short rest.
        """

        self.pcs = pcs
        self.adversaries = adversaries
        self.encounters_per_long_rest = encounters_per_long_rest
        self.encounters_per_short_rest = encounters_per_short_rest
        self.encounter_index = 0

    def __call__(self):
        """Resolve one adventuring day."""

        self.one_encounter()

        while (
            numpy.any([pc.hp > 0 for pc in self.pcs])
            and self.encounter_index < self.encounters_per_long_rest
        ):

            if self.encounter_index % self.encounters_per_short_rest == 0:
                self.take_short_rest()
            else:
                self.reset_pcs()

            self.reset_adversaries()
            self.one_encounter()

    def one_encounter(self):
        """Resolve one encounter."""

        encounter = Encounter(
            self.pcs,
            self.adversaries,
            encounters_since_short_rest=(
                self.encounter_index % self.encounters_per_short_rest
            ),
            encounters_since_long_rest=self.encounter_index,
        )

        # Resolve the encounter
        encounter()

        # Resolve end-of-encounter actions for PCs who are still alive
        for character in self.pcs:
            if character.hp > 0:
                character.end_encounter(encounter)

        self.encounter_index += 1

    def reset_adversaries(self):
        """Reset the combat state and hit points for the adversaries."""

        for creature in self.adversaries:
            creature.reset_conditions()
            creature.reset_hp()

    def reset_pcs(self):
        """Reset the combat state for the PCs."""

        for character in self.pcs:
            character.reset_conditions()

    def take_short_rest(self):
        """The PCs take a short rest."""

        if numpy.any([pc.verbose for pc in self.pcs]):
            print("The party took a short rest")

        for character in self.pcs:
            character.short_rest()

    def take_long_rest(self):
        """The PCs take a long rest."""

        if numpy.any([pc.verbose for pc in self.pcs]):
            print("The party took a long rest")

        self.encounter_index = 0

        for character in self.pcs:
            character.long_rest()
