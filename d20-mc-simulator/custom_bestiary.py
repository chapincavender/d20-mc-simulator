"""
    Classes derived from the Creature class to represent monsters
"""

import spells
from adventuring_day import Encounter
from creature import Creature, LegendaryCreature, Weapon, get_abilities
from dice_roller import Dice, ExtraWeaponDice, d4, d6, d8, d10, d12, d20, rng
from duration import (
    Duration,
    EngulfedDuration,
    FrightenedDuration,
    FrightenedOneTurnDuration,
    GrappleDuration,
    ParalyzedDuration,
    PoisonedDuration,
    RestrainedDuration,
    SlowedDuration,
    StunnedDuration,
    SwallowedDuration,
)


class Test(Creature):
    """Tester for stats by tier."""

    def __init__(
        self,
        attack: int,
        ac: int,
        damage: int,
        hp: int,
        N_attacks: int = 1,
        proficiency: int = 2,
        name: str | None = None,
        verbose: bool = False,
    ):
        """
        Constructor for the Test Creature class.

        Parameters
        ----------
        attack
            The test creature's total attack modifier, including its
            proficiency bonus.
        ac
            The test creature's armor class.
        damage
            The test creature's total damage per turn.
        hp
            The test creature's total hit points.
        N_attacks
            The number of attacks the test creature makes per turn.
        proficiency
            The test creature's proficiency bonus.
        name
            String to identify this Creature in verbose prints.
        verbose
            Whether to print information about this Creature during encounters.
        """

        self.test_attack = attack
        self.test_ac = ac
        self.test_damage = damage
        self.test_hp = hp
        self.N_attacks = N_attacks
        self.test_proficiency = proficiency
        super().__init__(name=name, verbose=verbose)

    def initialize_features(self):
        damage_per_attack = int(self.test_damage / self.N_attacks)

        self.abilities = get_abilities(0, 0, 0, 0, 0, 0)
        self.base_armor_class = self.test_ac

        # Find a multiple of 2d8 whose mean is closest to the desired total hit
        # points, then add a constant (which might be negative) to make up the
        # difference
        self.hit_die = lambda x: (
            d8(2 * int((self.test_hp + 2) / 9)) + (self.test_hp + 2) % 9 - 2
        )

        self.proficiency = self.test_proficiency
        self.save_proficiencies["dex"] = True
        self.save_proficiencies["con"] = True
        self.save_proficiencies["wis"] = True
        self.skill_proficiencies["perception"] = True
        self.total_hit_dice = 1

        # Create a weapon attack whose damage is a multiple of 2d6 whose mean is
        # closest to the desired damage per attack, then use a damage modifier
        # (which might be negative) to make up the difference
        self.weapon = Weapon(
            self,
            Dice(d6, 2 * int((damage_per_attack + 2) / 7)),
            "bludgeoning",
            attack_modifier=self.test_attack - self.proficiency,
            damage_modifier=(damage_per_attack + 2) % 7 - 2,
        )

    def take_turn(self, encounter: Encounter):
        # Weapon attack
        if self.action:
            self.action = False
            for i in range(self.N_attacks):
                self.weapon(encounter.choose_target(self))


custom_creatures = {
    "Test": Test,
}
