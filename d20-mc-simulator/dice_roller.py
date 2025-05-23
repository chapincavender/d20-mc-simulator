"""Implements classes for dice rollers."""

import numpy


class Die:
    """A die with an arbitrary number of sides."""

    def __init__(self, sides: int, generator: numpy.random.Generator):
        """
        Constructor for a die.

        Parameters
        ----------
        sides
            Number of sides for the die.
        generator
            Pre-initialized random number generator from numpy.random.
        """

        self.sides = sides

        # Mean of a single roll rounded up to the nearest integer
        self.mean = int(sides / 2) + 1

        # The integers method of the pre-initialized numpy.random Generator
        self.integers = generator.integers

    def __call__(self, N_dice: int = 1) -> int:
        """
        Callable for a die. Rolls one or more dice and returns their sum.

        Parameters
        ----------
        N_dice
            Number of dice to roll.
        """

        if N_dice == 1:
            return self.roll(1)
        else:
            return self.sum(N_dice)

    def reroll(self, reroll_threshold: int) -> int:
        """
        Roll one die and reroll if the result is less than a threshold.

        Parameters
        ----------
        reroll_threshold
        """

        result = self.roll(1)
        if result <= reroll_threshold:
            return self.roll(1)
        else:
            return result

    def roll(self, N_dice: int) -> int | numpy.typing.NDArray[numpy.int_]:
        """
        Roll one or more dice.

        Parameters
        ----------
        N_dice
            Number of dice to roll.
        """

        if N_dice == 1:
            return self.integers(1, self.sides, endpoint=True)
        else:
            return self.integers(1, self.sides, size=N_dice, endpoint=True)

    def sum(self, N_dice: int) -> int:
        """
        Roll one or more dice and return their sum.

        Parameters
        ----------
        N_dice
            Number of dice to roll.
        """

        return self.roll(N_dice).sum()


class Dice:
    """Callable class that returns the sum of multiple rolls of the same die."""

    def __init__(self, die: Die, N_dice: int):
        """
        Constructor for Dice.

        Parameters
        ----------
        die
            Rollable die.
        N_dice
            Number of dice to roll.
        """

        self.die = die
        self.N_dice = N_dice

    def __call__(self) -> int:
        """
        Callable for Dice. Returns the sum of self.N_dice rolls.
        """

        return self.die.sum(self.N_dice)


# Set up random number generator
rng = numpy.random.default_rng()

# Basic dice rollers
d4 = Die(4, rng)
d6 = Die(6, rng)
d8 = Die(8, rng)
d10 = Die(10, rng)
d12 = Die(12, rng)
d20 = Die(20, rng)


def twod6_reroll_1_2() -> int:
    """Roll 2d6 and reroll 1s and 2s once."""
    return d6.reroll(2) + d6.reroll(2)


def roll_d20(
    advantage: bool = False, disadvantage: bool = False, verbose: bool = False
) -> int:
    """Roll a d20 that handles advantage and disadvantage."""

    if advantage and not disadvantage:
        if verbose:
            print("Rolled with advantage")

        return numpy.amax(d20.roll(2))

    elif disadvantage and not advantage:
        if verbose:
            print("Rolled with disadvantage")

        return numpy.amin(d20.roll(2))

    else:
        return d20()


class ExtraWeaponDice:
    """
    Dice roller for weapons with additional damage dice of the same type, e.g.
    sneak attack.
    """

    def __init__(self, weapon_dice: Die | Dice, extra_die: Die, N_extra_dice: int):
        """
        Constructor for ExtraWeaponDice.

        Parameters
        ----------
        weapon_dice
            Base damage dice for the weapon attack.
        extra_die
            Damage die added to the base damage dice.
        N_extra_dice
            Number of extra dice added to the base damage dice.
        """

        self.weapon_dice = weapon_dice
        self.extra_die = extra_die
        self.N_extra_dice = N_extra_dice

    def __call__(self) -> int:
        """
        Callable for ExtraWeaponDice. Returns the sum of the base damage dice
        and extra dice.
        """

        return self.weapon_dice() + self.extra_die(self.N_extra_dice)
