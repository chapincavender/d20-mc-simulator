"""
    Implements Python classes derived from the Character abstract class for
    D&D player character classes.
"""

from adventuring_day import Encounter
from creature import Character, Creature
from dice_roller import d6, d8, d10


class Cleric(Character):
    """Python class for the D&D Cleric class."""

    hit_die = d8

    def initialize_class_features(self):
        # Saving throw proficiencies
        self.save_proficiencies["wis"] = True
        self.save_proficiencies["cha"] = True

        # Spellcasting ability
        self.spell_ability = "wis"

        # Spell slots for spell levels one through nine
        total_spell_slots_by_level = {
            1: [2, 0, 0, 0, 0, 0, 0, 0, 0],
            2: [3, 0, 0, 0, 0, 0, 0, 0, 0],
            3: [4, 2, 0, 0, 0, 0, 0, 0, 0],
            4: [4, 3, 0, 0, 0, 0, 0, 0, 0],
            5: [4, 3, 2, 0, 0, 0, 0, 0, 0],
            6: [4, 3, 3, 0, 0, 0, 0, 0, 0],
            7: [4, 3, 3, 1, 0, 0, 0, 0, 0],
            8: [4, 3, 3, 2, 0, 0, 0, 0, 0],
            9: [4, 3, 3, 3, 1, 0, 0, 0, 0],
            10: [4, 3, 3, 3, 2, 0, 0, 0, 0],
            11: [4, 3, 3, 3, 2, 1, 0, 0, 0],
            12: [4, 3, 3, 3, 2, 1, 0, 0, 0],
            13: [4, 3, 3, 3, 2, 1, 1, 0, 0],
            14: [4, 3, 3, 3, 2, 1, 1, 0, 0],
            15: [4, 3, 3, 3, 2, 1, 1, 1, 0],
            16: [4, 3, 3, 3, 2, 1, 1, 1, 0],
            17: [4, 3, 3, 3, 2, 1, 1, 1, 1],
            18: [4, 3, 3, 3, 3, 1, 1, 1, 1],
            19: [4, 3, 3, 3, 3, 2, 1, 1, 1],
            20: [4, 3, 3, 3, 3, 2, 2, 1, 1],
        }
        self.total_spell_slots = total_spell_slots_by_level[self.level]

        # Channel Divinity
        if self.level >= 18:
            self.total_channel_divinity = 3
        elif self.level >= 6:
            self.total_channel_divinity = 2
        elif self.level >= 2:
            self.total_channel_divinity = 1
        else:
            self.total_channel_divinity = 0

        # Destroy Undead
        if self.level >= 17:
            self.destroy_undead = 4
        elif self.level >= 14:
            self.destroy_undead = 3
        elif self.level >= 11:
            self.destroy_undead = 2
        elif self.level >= 8:
            self.destroy_undead = 1
        elif self.level >= 5:
            self.destroy_undead = 0.5
        else:
            self.destroy_undead = 0

        self.divine_intervention = False

    def lowest_spell_slots(self) -> list[int | None]:
        """
        Returns the lowest available spell slot greater than each spell level.
        """

        lowest_slots = [None for i in range(9)]

        if self.N_spell_slots[8] > 0:
            lowest_slots[8] = 9

        for slot in range(7, -1, -1):
            if self.N_spell_slots[slot] > 0:
                lowest_slots[slot] = slot + 1
            else:
                lowest_slots[slot] = lowest_slots[slot + 1]

        return lowest_slots

    def reset_long_rest_features(self):
        self.N_spell_slots = [i for i in self.total_spell_slots]
        if self.level >= 10:
            self.divine_intervention = True

    def reset_short_rest_features(self):
        self.N_channel_divinity = self.total_channel_divinity

    def save_dc(self) -> int:
        """Determine save DC for spells."""

        return 8 + self.abilities[self.spell_ability] + self.proficiency


class Fighter(Character):
    """Python class for the D&D Fighter class."""

    hit_die = d10

    def initialize_class_features(self):
        # Saving throw proficiencies
        self.save_proficiencies["str"] = True
        self.save_proficiencies["con"] = True

        # Action surge
        if self.level >= 17:
            self.total_action_surge = 2
        elif self.level >= 2:
            self.total_action_surge = 1
        else:
            self.total_action_surge = 0

        # Extra attack
        if self.level >= 20:
            self.N_attacks = 4
        elif self.level >= 11:
            self.N_attacks = 3
        elif self.level >= 5:
            self.N_attacks = 2
        else:
            self.N_attacks = 1

        # Indomitable
        if self.level >= 17:
            self.total_indomitable = 3
        elif self.level >= 13:
            self.total_indomitable = 2
        elif self.level >= 9:
            self.total_indomitable = 1
        else:
            self.total_indomitable = 0

    def reset_long_rest_features(self):
        self.N_indomitable = self.total_indomitable

    def reset_short_rest_features(self):
        # Use second wind to recover hit points
        if self.hp > 0 and self.hp < self.total_hp and self.second_wind:
            self.use_second_wind()

        self.second_wind = True
        self.N_action_surge = self.total_action_surge

    def saving_throw(
        self,
        ability: str,
        difficulty_class: int,
        adv: bool = False,
        disadv: bool = False,
        save_type: str = None,
    ):
        # Override saving_throw() to use Indomitable
        result = super().saving_throw(
            ability,
            difficulty_class,
            adv=adv,
            disadv=disadv,
            save_type=save_type,
        )

        if self.N_indomitable > 0 and not result:
            if self.verbose:
                print(f"{self()} used Indomitable")

            self.N_indomitable -= 1
            return super().roll_save(ability, adv, disadv) >= difficulty_class

        else:
            return result

    def use_second_wind(self):
        """Use Second Wind to recover hit points."""

        if self.verbose:
            print(f"{self()} used Second Wind")

        self.second_wind = False
        self.bonus = False
        self.heal(d10() + self.level)


class Rogue(Character):
    """Python class for the D&D Rogue class."""

    hit_die = d8

    def initialize_class_features(self):
        # Saving throw proficiencies
        self.save_proficiencies["dex"] = True
        self.save_proficiencies["int"] = True
        if self.level >= 15:
            self.save_proficiencies["wis"] = True

        # Rogue class features
        if self.level >= 7:
            self.evasion = True
        if self.level >= 18:
            self.elusive = True

        self.stroke_of_luck = False

    def reset_short_rest_features(self):
        if self.level >= 20:
            self.stroke_of_luck = True

    def roll_skill(self, skill: str, adv: bool = False, disadv: bool = False):
        # Override roll_skill() to use Reliable Talent
        if self.level >= 11 and self.skill_proficiencies[skill]:

            return max(
                super().roll_skill(skill, adv=adv, disadv=disadv),
                10
                + self.abilities[self.SKILLS[skill]]
                + self.skill_modifiers[skill]
                + self.proficiency,
            )

        else:
            return super().roll_skill(skill, adv=adv, disadv=disadv)

    def start_turn(self, encounter: Encounter):
        # Extend start_turn() to reset use of Sneak Attack
        self.sneak_attack = True
        super().start_turn(encounter)

    def take_damage(
        self,
        primary_damage: int,
        primary_type: str,
        dealer: Creature = None,
        ranged: bool = False,
        secondary_damage: int = 0,
        secondary_type: str = None,
    ) -> tuple[int, int]:
        # Extend take_damage() to use Uncanny Dodge
        if (
            self.level >= 5
            and self.reaction
            and self.hp > 0
            and not self.is_incapacitated()
            and dealer is not None
            and not dealer.is_hidden(self)
        ):
            self.reaction = False
            primary_damage = int(primary_damage / 2)
            secondary_damage = int(secondary_damage / 2)

            if self.verbose:
                print(f"{self()} used Uncanny Dodge")

        primary_damage_taken, secondary_damage_taken = super().take_damage(
            primary_damage,
            primary_type,
            dealer=dealer,
            ranged=ranged,
            secondary_damage=secondary_damage,
            secondary_type=secondary_type,
        )

        return primary_damage_taken, secondary_damage_taken


class Wizard(Character):
    """Python class for the D&D Wizard class."""

    hit_die = d6

    def initialize_class_features(self):
        # Saving throw proficiencies
        self.save_proficiencies["int"] = True
        self.save_proficiencies["wis"] = True

        # Spellcasting ability
        self.spell_ability = "int"

        # Spell slots for spell levels one through nine
        total_spell_slots_by_level = {
            1: [2, 0, 0, 0, 0, 0, 0, 0, 0],
            2: [3, 0, 0, 0, 0, 0, 0, 0, 0],
            3: [4, 2, 0, 0, 0, 0, 0, 0, 0],
            4: [4, 3, 0, 0, 0, 0, 0, 0, 0],
            5: [4, 3, 2, 0, 0, 0, 0, 0, 0],
            6: [4, 3, 3, 0, 0, 0, 0, 0, 0],
            7: [4, 3, 3, 1, 0, 0, 0, 0, 0],
            8: [4, 3, 3, 2, 0, 0, 0, 0, 0],
            9: [4, 3, 3, 3, 1, 0, 0, 0, 0],
            10: [4, 3, 3, 3, 2, 0, 0, 0, 0],
            11: [4, 3, 3, 3, 2, 1, 0, 0, 0],
            12: [4, 3, 3, 3, 2, 1, 0, 0, 0],
            13: [4, 3, 3, 3, 2, 1, 1, 0, 0],
            14: [4, 3, 3, 3, 2, 1, 1, 0, 0],
            15: [4, 3, 3, 3, 2, 1, 1, 1, 0],
            16: [4, 3, 3, 3, 2, 1, 1, 1, 0],
            17: [4, 3, 3, 3, 2, 1, 1, 1, 1],
            18: [4, 3, 3, 3, 3, 1, 1, 1, 1],
            19: [4, 3, 3, 3, 3, 2, 1, 1, 1],
            20: [4, 3, 3, 3, 3, 2, 2, 1, 1],
        }
        self.total_spell_slots = total_spell_slots_by_level[self.level]

    def lowest_spell_slots(self) -> list[int | None]:
        """
        Returns the lowest available spell slot greater than each spell level.
        """

        lowest_slots = [None for i in range(9)]

        if self.N_spell_slots[8] > 0:
            lowest_slots[8] = 9

        for slot in range(7, -1, -1):
            if self.N_spell_slots[slot] > 0:
                lowest_slots[slot] = slot + 1
            else:
                lowest_slots[slot] = lowest_slots[slot + 1]

        return lowest_slots

    def reset_long_rest_features(self):
        self.N_spell_slots = [i for i in self.total_spell_slots]
        self.arcane_recovery = True

    def save_dc(self) -> int:
        """Determine save DC for spells."""

        return 8 + self.abilities[self.spell_ability] + self.proficiency
