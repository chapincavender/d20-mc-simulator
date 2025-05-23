"""Implements classes for temporary combat effects with a fixed duration."""

from abc import ABC, abstractmethod

import numpy

from dice_roller import Dice, Die


class Duration(ABC):
    """
    Abstract class for handling temporary combat effects with a fixed duration.
    For each duration effect, a derived class should be created that overrides
    the method end(self) to remove the effect and optionally overrides
    start_turn_effect(self) and end_turn_effect(self) that will trigger at the
    start or end of a creature's turn. Call the tick() method to decrement the
    duration attribute and trigger end() when it reaches zero. Typically, the
    constructor for the derived class should set the duration attribute and
    add itself to start_turn_duration or end_turn_duration for at least one
    Creature, and the end() method should remove itself from that list.
    """

    @abstractmethod
    def end(self):
        pass

    def end_turn_effect(self):
        pass

    def start_turn_effect(self):
        pass

    def tick(self):
        """Decrement duration and end effect if duration is zero."""

        self.duration -= 1
        if self.duration == 0:
            self.end()


class BleedingDuration(Duration):
    """
    Class for a bleeding condition that deals damage at the start of each turn
    and ends upon receiving magical healing, e.g. the bearded devil's glaive
    attack.
    """

    def __init__(
        self,
        target: "Creature",
        wound_damage: Die | Dice,
        damage_type: str,
        max_duration: int,
    ):
        """
        Constructor for BleedingDuration.

        Parameters
        ----------
        target
            Creature targeted by the bleeding effect.
        wound_damage
            Dice rolled to determine damage taken per stack of bleeding applied.
        damage_type
            Damage type for wound damage.
        max_duration
            Maximum number of rounds until the effect ends.
        """

        # If the target already has the bleedingcondition, reset the duration of
        # the existing effect
        for effect in target.start_turn_duration:
            if isinstance(effect, BleedingDuration):
                effect.N_wounds += 1
                effect.duration = numpy.amax([effect.duration, max_duration])
                return

        self.duration = max_duration
        self.target = target
        self.wound_damage = wound_damage
        self.damage_type = damage_type
        self.N_wounds = 1
        target.start_turn_duration.append(self)

        if target.verbose:
            print(f"{target()} is bleeding")

    def start_turn_effect(self):
        """
        At the start of the target's turn, apply wound damage and decrement the
        duration.
        """

        damage = 0
        for i in range(self.N_wounds):
            damage += self.wound_damage()
        self.target.take_damage(damage, self.damage_type)

        self.tick()

    def end(self):
        self.target.start_turn_duration.remove(self)

        if self.target.verbose:
            print(f"{self.target()} is no longer bleeding")


class EngulfedDuration(Duration):
    """
    Class for an engulfed condition that restrains the target, e.g. the
    Shambling Mound's Engulf.
    """

    def __init__(self, engulfer: "Creature", target: "Creature", save_dc: int):
        """
        Constructor for EngulfedDuration.

        Parameters
        ----------
        engulfer
            The creature applying the engulfed condition.
        target
            The creature receiving the engulfed condition.
        save_dc
            The save DC for the skill check to end the effect.
        """

        self.engulfer = engulfer
        self.save_dc = save_dc
        self.target = target

        target.restrained += 1
        target.engulfed = self
        target.start_turn_duration.append(self)
        engulfer.engulfed_creature.append(target)

        if engulfer.verbose or target.verbose:
            print(f"{target()} is engulfed")

    def end(self):
        self.target.restrained -= 1
        self.target.engulfed = None
        self.target.start_turn_duration.remove(self)
        self.engulfer.engulfed_creatures.remove(self.target)

        if self.engulfer.verbose or self.target.verbose:
            print(f"{self.target()} is no longer engulfed")


class FrightenedDuration(Duration):
    """
    Class for a frightened condition with a Wisdom saving throw with
    disadvantage to end the effect at the end of the target's turn, e.g. the
    banshee's horrifying visage attack.
    """

    def __init__(
        self,
        frightener: "Creature",
        target: "Creature",
        save_dc: int,
        max_duration: int,
    ):
        """
        Constructor for FrightenedDuration.

        Parameters
        ----------
        frightener
            The creature applying the frightened condition.
        target
            The creature receiving the frightened condition.
        save_dc
            The save DC for the Wisom saving throw to end the effect.
        max_duration
            Maximum number of rounds until the effect ends.
        """

        self.frightener = frightener
        self.target = target
        self.save_dc = save_dc
        self.duration = max_duration

        target.frightened += 1
        target.end_turn_duration.append(self)
        frightener.start_turn_duration.append(self)

        if frightener.verbose or target.verbose:
            print(f"{target()} is frightened")

    def end(self):
        self.target.frightened -= 1
        self.target.end_turn_duration.remove(self)
        self.frightener.start_turn_duration.remove(self)

        if self.frightener.verbose or self.target.verbose:
            print(f"{self.target()} is no longer frightened")

    def end_turn_effect(self):
        """
        At the end of the target's turn, the target makes a Wisdom saving throw
        to end the effect.
        """

        if self.target.saving_throw("wis", self.save_dc, disadv=True):
            self.end()

    def start_turn_effect(self):
        """At the start of the frightener's turn, decrement the duration."""

        self.tick()


class FrightenedOneTurnDuration(Duration):
    """
    Class for a frightened condition that lasts until the end of the target's
    next turn, e.g. the chain devil's Unnverving Mask.
    """

    def __init__(self, target: "Creature"):
        """
        Constructor for FrightenedOneTurnDuration.

        Parameters
        ----------
        target
            The creature receiving the frightened condition.
        """

        self.target = target

        target.frightened += 1
        target.end_turn_duration.append(self)

        if target.verbose:
            print(f"{target()} is frightened")

    def end(self):
        self.target.frightened -= 1
        self.target.end_turn_duration.remove(self)

        if self.target.verbose:
            print(f"{self.target()} is no longer frightened")

    def end_turn_effect(self):
        """At the end of the target's turn, end the effect."""

        self.end()


class GrappleDuration(Duration):
    """
    Class for the grappled condition that optionally applies the restrained or
    stunned condition to the target."""

    def __init__(
        self,
        grappler: "Creature",
        target: "Creature",
        restrained: bool = False,
        stunned: bool = False,
        escape_priority: bool = False,
    ):
        """
        Constructor for GrappleDuration.

        Parameters
        ----------
        grappler
            The creature applying the grappled condition.
        target
            The creature receiving the grappled condition.
        restrained
            Whether the target is restrained while grappled.
        stunned
            Whether the target is stunned while grappled.
        escape_priority
            Whether the target should use their action to attempt to escape the
            grapple.
        """

        self.escape_priority = escape_priority
        self.grappler = grappler
        self.restrained = restrained
        self.stunned = stunned
        self.target = target

        grappler.grappling.append(self)
        target.grappled.append(self)

        if escape_priority:
            target.start_turn_duration.append(self)

        if restrained:
            target.restrained += 1

        if stunned:
            target.stunned += 1

        if grappler.verbose or target.verbose:
            print(f"{target()} is grappled by {grappler()}")

    def end(self):
        self.grappler.grappling.remove(self)
        self.target.grappled.remove(self)

        if self.escape_priority:
            self.target.start_turn_duration.remove(self)

        if self.restrained:
            self.target.restrained -= 1

        if self.stunned:
            self.target.stunned -= 1

        if self.grappler.verbose or self.target.verbose:
            print(f"{self.target()} is no longer grappled by {self.grappler()}")

    def start_turn_effect(self):
        """The target uses its action to attempt to escape the grapple."""

        if self.target.action:
            self.target.action = False
            escape_grapple_check = self.target.escape_grapple()

            if self.target.verbose:
                print(
                    f"{self.target()} rolled {escape_grapple_check} to escape "
                    "a grapple"
                )

            for grapple in self.target.grappled[:]:
                escape_dc = (
                    8 + grapple.grappler.proficiency + grapple.grappler.abilities["str"]
                )

                if escape_grapple_check >= escape_dc:
                    grapple.end()

    def tick(self):
        # Override the base Duration tick() method since the grapple does not have
        # a fixed duration.
        pass


class ParalyzedDuration(Duration):
    """
    Class for a paralyzed condition with a Constitution saving throw to end the
    effect at end of the target's turn, e.g. the ghoul's claws attack.
    """

    def __init__(
        self,
        paralyzer: "Creature",
        target: "Creature",
        save_dc: int,
        max_duration: int,
    ):
        """
        Constructor for ParalyzedDuration.

        Parameters
        ----------
        paralyzer
            The creature applying the paralyzed condition.
        target
            The creature receiving the paralyzed condition.
        save_dc
            The save DC for the Constitution saving throw to end the effect.
        max_duration
            Maximum number of rounds until the effect ends.
        """

        self.paralyzer = paralyzer
        self.target = target
        self.save_dc = save_dc
        self.duration = max_duration

        target.paralyzed += 1
        target.end_turn_duration.append(self)
        paralyzer.start_turn_duration.append(self)

        if paralyzer.verbose or target.verbose:
            print(f"{target()} is paralyzed")

        if target.concentration != None:
            target.concentration.end()

    def end(self):
        self.target.paralyzed -= 1
        self.target.end_turn_duration.remove(self)
        self.paralyzer.start_turn_duration.remove(self)

        if self.paralyzer.verbose or self.target.verbose:
            print(f"{self.target()} is no longer paralyzed")

    def end_turn_effect(self):
        """
        At the end of the target's turn, the target makes a Constitution saving
        throw to end the effect.
        """

        if self.target.saving_throw("con", self.save_dc):
            self.end()

    def start_turn_effect(self):
        """At the start of the paralyzer's turn, decrement the duration."""

        self.tick()


class PoisonedDuration(Duration):
    """
    Class for a poisoned condition with a Constitution saving throw to end the
    effect at end of the target's turn, e.g. the bone devil's sting attack.
    """

    def __init__(
        self,
        poisoner: "Creature",
        target: "Creature",
        save_dc: int,
        max_duration: int,
    ):
        """
        Constructor for PoisonedDuration.

        Parameters
        ----------
        poisoner
            The creature applying the poisoned condition.
        target
            The creature receiving the poisoned condition.
        save_dc
            The save DC for the Constitution saving throw to end the effect.
        max_duration
            Maximum number of rounds until the effect ends.
        """

        self.poisoner = poisoner
        self.target = target
        self.save_dc = save_dc
        self.duration = max_duration

        target.poisoned += 1
        target.end_turn_duartion.append(self)
        poisoner.start_turn_duration.append(self)

        if poisoner.verbose or target.verbose:
            print(f"{target()} is poisoned")

    def end(self):
        self.target.poisoned -= 1
        self.target.end_turn_duration.remove(self)
        self.poisoner.start_turn_duration.remove(self)

        if self.poisoner.verbose or self.target.verbose:
            print(f"{self.target()} is no longer poisoned")

    def end_turn_effect(self):
        """
        At the end of the target's turn, the target makes a Constitution saving
        throw to end the effect.
        """

        if self.target.saving_throw("con", self.save_dc):
            self.end()

    def start_turn_effect(self):
        """At the start of the poisoner's turn, decrement the duration."""

        self.tick()


class RecklessDuration(Duration):
    """
    Class for a reckless condition that gives advantage on attacks against a
    creature, e.g. the berserker's reckless ability.
    """

    def __init__(self, creature: "Creature", max_duration: int = 1):
        """
        Constructor for RecklessDuration.

        Parameters
        ----------
        creature
            The creature receiving the reckless condition.
        max_duration
            Maximum number of rounds until the effect ends.
        """

        self.creature = creature
        self.duration = max_duration

        creature.target_adv += 1
        creature.start_turn_duration.append(self)

    def end(self):
        self.creature.target_adv -= 1
        self.creature.start_turn_duration.remove(self)

    def start_turn_effect(self):
        """At the start of the creature's turn, decrement the duration."""

        self.tick()


class RestrainedDuration(Duration):
    """
    Class for a restrained condition with an unskilled Strength check to end the
    effect, e.g. the giant spider's Web attack.
    """

    def __init__(self, target: "Creature", check_dc: int):
        """
        Constructor for StunnedDuration.

        Parameters
        ----------
        target
            The creature receiving the stunned condition.
        check_dc
            The check DC for the unskilled Strength check to end the effect.
        """

        self.check_dc = check_dc
        self.target = target

        target.restrained += 1
        target.start_turn_duration.append(self)

        if target.verbose:
            print(f"{target()} is restrained")

    def end(self):
        self.target.restrained -= 1
        self.target.start_turn_duration.remove(self)

        if self.target.verbose:
            print(f"{self.target()} is no longer restrained")

    def start_turn_effect(self):
        if self.target.action:
            self.target.action = False

            if self.target.skill_check("str", self.check_dc):
                self.end()


class SlowedDuration(Duration):
    """
    Class for a slowed condition with a Wisdom saving throw to end the effect at
    the end of the target's turn, e.g. the Stone Golem's slow attack.
    """

    def __init__(self, slower: "Creature", target: "Creature", save_dc: int):
        self.slower = slower
        self.target = target
        self.save_dc = save_dc
        self.duration = 10

        target.slowed += 1
        target.end_turn_duration.append(self)
        slower.start_turn_duration.append(self)

        if slower.verbose or target.verbose:
            print(f"{target()} is slowed")

    def end(self):
        self.target.slowed -= 1
        self.target.end_turn_duration.remove(self)
        self.slower.start_turn_duration.remove(self)

        if self.slower.verbose or self.target.verbose:
            print(f"{self.target()} is no longer slowed")

    def end_turn_effect(self):
        if self.target.saving_throw("wis", self.save_dc):
            self.end()

    def start_turn_effect(self):
        self.tick()


class StunnedDuration(Duration):
    """
    Class for a stunned condition with an Intelligence saving throw to end the
    effect at end of the target's turn, e.g. the mind flayer's mind blast attack.
    """

    def __init__(
        self,
        stunner: "Creature",
        target: "Creature",
        save_dc: int,
        max_duration: int,
    ):
        """
        Constructor for StunnedDuration.

        Parameters
        ----------
        stunner
            The creature applying the stunned condition.
        target
            The creature receiving the stunned condition.
        save_dc
            The save DC for the Intelligence saving throw to end the effect.
        max_duration
            Maximum number of rounds until the effect ends.
        """

        self.stunner = stunner
        self.target = target
        self.save_dc = save_dc
        self.duration = max_duration

        target.stunned += 1
        target.end_turn_duration.append(self)
        stunner.start_turn_duration.append(self)

        if stunner.verbose or target.verbose:
            print(f"{target()} is stunned")

        if target.concentration != None:
            target.concentration.end()

    def end(self):
        self.target.stunned -= 1
        self.target.end_turn_duration.remove(self)
        self.stunner.start_turn_duration.remove(self)

        if self.stunner.verbose or self.target.verbose:
            print(f"{self.target()} is no longer stunned")

    def end_turn_effect(self):
        """
        At the end of the target's turn, the target makes a Intelligence saving
        throw to end the effect.
        """

        if self.target.saving_throw("int", self.save_dc):
            self.end()

    def start_turn_effect(self):
        """At the start of the stunner's turn, decrement the duration."""

        self.tick()


class SwallowedDuration(Duration):
    """
    Class for a swallowed condition that ends when the swallower takes a
    threshold of damage from the target in a single turn, e.g. the behir's
    Swallow.
    """

    def __init__(
        self,
        swallower: "Creature",
        target: "Creature",
        regurgitation_threshold: int,
        regurgitation_save_dc: int,
    ):
        """
        Constructor for SwallowedDuration.

        Parameters
        ----------
        swallower
            The Creature applying the swallowed condition.
        target
            The Creature receiving the swallowed condition.
        regurgitation_threshold
            The damage threshold to regurgitate the swallowed creature.
        regurgitation_save_dc
            The save DC for the Constitution saving throw to avoid regurgitating
            the swallowed creature.
        """

        self.swallower = swallower
        self.target = target
        self.regurgitation_threshold = regurgitation_threshold
        self.regurgitation_save_dc = regurgitation_save_dc

        swallower.swallowed_creatures.append(target)
        target.swallowed = self
        target.start_turn_duration.append(self)
        target.end_turn_duration.append(self)
        target.blinded += 1
        target.restrained += 1

        if swallower.verbose or target.verbose:
            print(f"{target()} is swallowed")

    def end(self):
        self.swallower.swallowed_creatures.remove(self.target)
        self.target.swallowed = None
        self.target.start_turn_duration.remove(self)
        self.target.end_turn_duration.remove(self)
        self.target.blinded -= 1
        self.target.restrained -= 1
        self.target.prone = True

        if self.swallower.verbose or self.target.verbose:
            print(f"{self.target()} is no longer swallowed")

    def start_turn_effect(self):
        self.swallower.damage_taken_this_turn = 0

    def end_turn_effect(self):
        # If the swallowed creature dealt damage to meet the regurgitation
        # threshold this turn, the swallower makes a Con save or ends the effect
        if (
            self.swallower.damage_taken_this_turn >= self.regurgitation_threshold
            and not self.swallower.saving_throw(
                "con",
                self.regurgitation_save_dc,
            )
        ):
            for creature in self.swallower.swallowed_creatures[:]:
                creature.swallowed.end()


# Turned undead
class TurnUndeadDuration(Duration):
    """
    Class for a turned condition that consumes the target's action and reaction,
    e.g. the cleric's Turn Undead Channel Divinity feature.
    """

    def __init__(self, turner: "Creature", target: "Creature"):
        """
        Constructor for TurnUndeadDuration.

        Parameters
        ----------
        turner
            The creature applying the turned condition.
        target
            The creature receiving the turned condition.
        """

        self.duration = 10
        self.target = target
        self.turner = turner

        target.turned = self
        turner.start_turn_duration.append(self)

        if turner.verbose or target.verbose:
            print(f"{target} is turned")

    def end(self):
        self.target.turned = None
        self.turner.start_turn_duration.remove(self)

        if self.target.verbose:
            print(f"{self.target()} is no longer turned")

    def start_turn_effect(self):
        """At the start of the turner's turn, decrement the duration."""

        self.tick()
