"""
    Classes derived from the Creature class to represent monsters from the
    Monster Manual
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


class Aboleth(LegendaryCreature):
    """Aboleth from the Monster Manual p. 13."""

    def initialize_features(self):
        self.abilities = get_abilities(5, -1, 2, 4, 2, 4)
        self.base_armor_class = 18
        self.hit_die = d10
        self.proficiency = 4
        self.skill_modifiers["history"] = self.proficiency
        self.skill_modifiers["perception"] = self.proficiency
        self.skill_proficiencies["history"] = True
        self.skill_proficiencies["perception"] = True
        self.save_proficiencies["con"] = True
        self.save_proficiencies["int"] = True
        self.save_proficiencies["wis"] = True
        self.total_hit_dice = 18
        self.total_legendary_actions = 3

        self.tentacle_weapon = Weapon(self, Dice(d6, 2), "bludgeoning")
        self.tail_weapon = Weapon(self, Dice(d6, 3), "bludgeoning")

    def lair_action(self, encounter: Encounter):
        valid_targets = [enemy for enemy in encounter.get_foes(self) if enemy.hp > 0]

        # Area of effect features hit two targets
        if len(valid_targets) <= 2:
            targets = valid_targets
        else:
            targets = encounter.choice(valid_targets, 2, replace=False)

        # Alternate between psychic and prone lair actions, but prefer psychic
        # lair action when available
        if self.psychic_lair_action:
            self.psychic_lair_action = False

            if self.verbose:
                print(f"{self()} used psychic lair action")

            # Roll damage once for all targets
            damage = d6(2)

            for target in targets:
                if not target.saving_throw(
                    "wis",
                    8 + self.proficiency + self.abilities["wis"],
                ):
                    target.take_damage(damage, "psychic")

        else:
            self.psychic_lair_action = True

            if self.verbose:
                print(f"{self()} used prone lair action")

            for target in targets:
                if not target.saving_throw(
                    "str",
                    8 + self.proficiency + self.abilities["wis"],
                ):
                    target.prone = True

    def legendary_action(self, encounter: Encounter):
        if self.verbose:
            print(f"{self()} made an attack with Tail")

        self.tail_weapon(encounter.choose_target(self))

    def reset_conditions(self):
        # Extend reset_conditions() to recover psychic lair action
        super().reset_conditions()
        self.psychic_lair_action = True

    def take_turn(self, encounter: Encounter):
        if self.action:
            self.action = False

            # Weapon attacks
            if self.verbose:
                print(f"{self()} made an attack with Tentacle")

            self.tentacle_weapon(encounter.choose_target(self))
            self.tentacle_weapon(encounter.choose_target(self))
            self.tentacle_weapon(encounter.choose_target(self))


class AbominableYeti(Creature):
    """Abominable yeti from the Monster Manual p. 306."""

    def initialize_features(self):
        self.abilities = get_abilities(7, 0, 6, -1, 1, -1)
        self.base_armor_class = 15
        self.hit_die = d12
        self.immunities["cold"] = True
        self.proficiency = 4
        self.skill_proficiencies["perception"] = True
        self.skill_proficiencies["stealth"] = True
        self.total_hit_dice = 11

        self.weapon = Weapon(
            self,
            Dice(d6, 2),
            "slashing",
            secondary_dice=Dice(d6, 2),
            secondary_type="cold",
        )

    def reset_conditions(self):
        # Extend reset_conditions() to recover use of breath weapon and give
        # advantage on Perception and Stealth checks
        super().reset_conditions()
        self.breath_weapon = True
        self.skill_adv["perception"] += 1
        self.skill_adv["stealth"] += 1

    def start_encounter(self, encounter: Encounter):
        # Initialize list of opponents for Chilling Gaze
        self.chilling_gaze_targets = [
            enemy for enemy in encounter.get_foes(self) if not enemy.immunities["cold"]
        ]

    def take_turn(self, encounter: Encounter):
        # Recover breath weapon
        if not self.breath_weapon and rng.random() >= (5.0 / 6):
            self.breath_weapon = True

        if self.action:
            self.action = False

            # Cold Breath
            if self.breath_weapon:
                if self.verbose:
                    print(f"{self()} used Cold Breath")

                self.breath_weapon = False

                # Roll damage once for both targets in area of effect
                damage = d8(10)

                for target in encounter.choose_target(self, N_targets=2):
                    target.half_saving_throw(
                        "con",
                        8 + self.proficiency + self.abilities["con"],
                        damage,
                        "cold",
                    )

            else:
                # Chilling Gaze
                valid_targets = [
                    enemy
                    for enemy in self.chilling_gaze_targets
                    if enemy.hp > 0 and enemy.paralyzed == 0
                ]

                if len(valid_targets) > 0:
                    if self.verbose:
                        print(f"{self()} used Chilling Gaze")

                    target = encounter.choice(valid_targets)

                    self.chilling_gaze_targets.remove(target)

                    if not target.saving_throw(
                        "con",
                        8 + self.proficiency + self.abilities["con"],
                    ):
                        paralyzed_duration = ParalyzedDuration(
                            self,
                            target,
                            8 + self.proficiency + self.abilities["con"],
                            10,
                        )

                # Weapon attack
                if self.verbose:
                    print(f"{self()} made an attack with Claw")

                self.weapon(encounter.choose_target(self))
                self.weapon(encounter.choose_target(self))


class Bandit(Creature):
    """Bandit from the Monster Manual p. 343."""

    def initialize_features(self):
        self.abilities = get_abilities(0, 1, 1, 0, 0, 0)
        self.base_armor_class = 11
        self.hit_die = d8
        self.proficiency = 2
        self.skill_proficiencies["perception"] = True
        self.total_hit_dice = 2

        self.weapon = Weapon(self, d6, "slashing", ability="dex")

    def take_turn(self, encounter: Encounter):
        # Weapon attack
        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Scimitar")

            self.action = False
            self.weapon(encounter.choose_target(self))


class Banshee(Creature):
    """Banshee from the Monster Manual p. 23."""

    def initialize_features(self):
        self.abilities = get_abilities(-5, 2, 0, 1, 0, 3)
        self.base_armor_class = 10
        self.hit_die = d8
        self.immunities["cold"] = True
        self.immunities["necrotic"] = True
        self.immunities["poison"] = True
        self.proficiency = 2
        self.resistances["acid"] = True
        self.resistances["bludgeoning"] = True
        self.resistances["fire"] = True
        self.resistances["lightning"] = True
        self.resistances["piercing"] = True
        self.resistances["slashing"] = True
        self.resistances["thunder"] = True
        self.save_proficiencies["wis"] = True
        self.save_proficiencies["cha"] = True
        self.total_hit_dice = 13
        self.undead = 4

        self.weapon = Weapon(self, Dice(d6, 3), "necrotic", ability="dex")

    def reset_conditions(self):
        # Extend reset_conditions() to recover use of Wail
        super().reset_conditions()
        self.wail = True

    def take_turn(self, encounter: Encounter):
        valid_targets = [enemy for enemy in encounter.get_foes(self) if enemy.hp > 0]
        unfrightened_targets = [
            enemy for enemy in valid_targets if enemy.frightened == 0
        ]

        if self.action:
            self.action = False

            # Wail
            if self.wail:
                if self.verbose:
                    print(f"{self()} used Wail")

                self.wail = False

                if len(valid_targets) <= 2:
                    targets = valid_targets
                else:
                    targets = encounter.choice(valid_targets, 2, replace=False)

                # Roll damage once for both targets in area of effect
                damage = d6(3)

                for target in targets:
                    if target.saving_throw(
                        "con",
                        8 + self.proficiency + self.abilities["cha"],
                    ):
                        target.take_damage(damage, "psychic")

                    else:
                        target.hp = 0
                        target.fall_unconscious()

            # Horrifying Visage
            elif len(unfrightened_targets) > 1:
                if self.verbose:
                    print(f"{self()} used Horrifying Visage")

                if len(unfrightened_targets) <= 2:
                    targets = unfrightened_targets
                else:
                    targets = encounter.choice(
                        unfrightened_targets,
                        2,
                        replace=False,
                    )

                for target in targets:
                    if not target.saving_throw(
                        "wis",
                        8 + self.proficiency + self.abilities["cha"],
                    ):
                        frightened_duration = FrightenedDuration(
                            self,
                            target,
                            10,
                            8 + self.proficiency + self.abilities["cha"],
                        )

            # Weapon attack
            else:
                if self.verbose:
                    print(f"{self()} made an attack with Corrupting Touch")

                self.weapon(encounter.choose_target(self))


class Behir(Creature):
    """Behir from the Monster Manual p. 25."""

    def initialize_features(self):
        self.abilities = get_abilities(6, 3, 4, -2, 2, 1)
        self.base_armor_class = 14
        self.hit_die = d12
        self.immunities["lightning"] = True
        self.proficiency = 4
        self.skill_proficiencies["perception"] = True
        self.skill_proficiencies["stealth"] = True
        self.total_hit_dice = 16

        self.bite_weapon = Weapon(self, Dice(d10, 3), "piercing")
        self.constrict_weapon = Weapon(
            self,
            Dice(d10, 2),
            "bludgeoning",
            secondary_dice=Dice(d10, 2),
            secondary_type="slashing",
        )

    def fall_unconscious(self):
        # Extend fall_unconscious() to release swallowed creatures
        super().fall_unconscious()

        for creature in self.swallowed_creatures[:]:
            creature.swallowed.end()

    def reset_conditions(self):
        # Extend reset_conditions() to recover use of breath weapon and reset
        # swallowed creature and damage taken this turn for regurgitation
        super().reset_conditions()

        self.breath_weapon = True
        self.swallowed_creatures = []
        self.damage_taken_this_turn = 0

    def take_damage(
        self,
        primary_damage: int,
        primary_type: str,
        dealer: Creature = None,
        ranged: bool = False,
        secondary_damage: int = 0,
        secondary_type: str = None,
    ) -> tuple[int, int]:
        # Extend take_damage() to track damage taken from swallowed creature
        primary_damage_taken, secondary_damage_taken = super().take_damage(
            primary_damage,
            primary_type,
            dealer=dealer,
            ranged=ranged,
            secondary_damage=secondary_damage,
            secondary_type=secondary_type,
        )

        if dealer in self.swallowed_creatures:
            self.damage_taken_this_turn += primary_damage_taken + secondary_damage_taken

        return (primary_damage_taken, secondary_damage_taken)

    def take_turn(self, encounter: Encounter):
        # Recover breath weapon
        if not self.breath_weapon and rng.random() >= (2.0 / 3):
            self.breath_weapon = True

        # Deal acid damage to swallowed creatures, rolling once for all targets
        damage = d6(6)
        for creature in self.swallowed_creatures[:]:
            if creature.hp > 0:
                creature.take_damage(damage, "acid")

        # Stop grappling unconscious creatures
        for grapple in self.grappling[:]:
            if grapple.target.hp == 0:
                grapple.end()

        valid_targets = [
            enemy
            for enemy in encounter.get_foes(self)
            if (enemy.hp > 0 and not enemy.swallowed)
        ]

        if self.action and len(valid_targets) > 0:
            self.action = False

            # Lightning breath
            if self.breath_weapon:
                if self.verbose:
                    print(f"{self()} used Lightning Breath")

                self.breath_weapon = False

                # Roll damage once for both targets in area of effect
                damage = d10(12)

                if len(valid_targets) <= 2:
                    targets = valid_targets

                else:
                    targets = encounter.choice(
                        valid_targets,
                        size=2,
                        replace=False,
                    )

                for target in targets:
                    target.half_saving_throw(
                        "dex",
                        8 + self.proficiency + self.abilities["con"],
                        damage,
                        "lightning",
                    )

            # Swallow
            elif len(self.grappling) > 0 and len(self.swallowed_creatures) <= 1:
                if self.verbose:
                    print(f"{self()} used Swallow")

                target = self.grappling[0].target

                attack_result = self.bite_weapon(target)

                if target.hp > 0 and (
                    attack_result == "hit" or attack_result == "crit"
                ):
                    for grapple in target.grappled[:]:
                        grapple.end()

                    swallowed_duration = SwallowedDuration(self, target, 30, 14)

            # Weapon attack
            else:
                if self.verbose:
                    print(f"{self()} made an attack with Bite and Constrict")

                self.bite_weapon(encounter.choice(valid_targets))

                # Constrict
                valid_targets = [
                    enemy
                    for enemy in encounter.get_foes(self)
                    if (enemy.hp > 0 and not enemy.swallowed)
                ]

                if len(valid_targets) > 0:
                    target = encounter.choice(valid_targets)
                    attack_result = self.constrict_weapon(target)

                    # Grapple target if Constrict hits
                    if (
                        target.hp > 0
                        and len(self.grappling) == 0
                        and (attack_result == "hit" or attack_result == "crit")
                    ):
                        grapple_duration = GrappleDuration(
                            self,
                            target,
                            restrained=True,
                        )


class BoneDevil(Creature):
    """Bone devil from the Monster Manual p. 71."""

    def initialize_features(self):
        self.abilities = get_abilities(4, 3, 4, 1, 2, 3)
        self.base_armor_class = 16
        self.hit_die = d10
        self.immunities["fire"] = True
        self.immunities["poison"] = True
        self.magic_resistance = True
        self.proficiency = 4
        self.resistances["bludgeoning"] = True
        self.resistances["cold"] = True
        self.resistances["piercing"] = True
        self.resistances["slashing"] = True
        self.save_proficiencies["int"] = True
        self.save_proficiencies["wis"] = True
        self.save_proficiencies["cha"] = True
        self.skill_proficiencies["deception"] = True
        self.skill_proficiencies["insight"] = True
        self.total_hit_dice = 15

        self.claw_weapon = Weapon(self, d8, "slashing")
        self.sting_weapon = Weapon(
            self,
            Dice(d8, 2),
            "piercing",
            secondary_dice=Dice(d6, 5),
            secondary_type="poison",
        )

    def take_turn(self, encounter: Encounter):
        # Weapon attack
        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Claw and Sting")

            self.action = False

            self.claw_weapon(encounter.choose_target(self))
            self.claw_weapon(encounter.choose_target(self))

            # Sting
            target = encounter.choose_target(self)
            attack_result = self.sting_weapon(target)

            if (
                attack_result == "hit" or attack_result == "crit"
            ) and not target.saving_throw(
                "con",
                8 + self.proficiency + self.abilities["wis"],
                save_type="poison",
            ):
                poisoned_duration = PoisonedDuration(
                    self,
                    target,
                    8 + self.proficiency + self.abilities["wis"],
                    10,
                )


class Bugbear(Creature):
    """Bugbear from the Monster Manual p. 33."""

    def initialize_features(self):
        self.abilities = get_abilities(2, 2, 1, -1, 0, -1)
        self.armor_type = "medium"
        self.base_armor_class = 14
        self.hit_die = d8
        self.proficiency = 2
        self.skill_modifiers["stealth"] = self.proficiency
        self.skill_proficiencies["stealth"] = True
        self.skill_proficiencies["survival"] = True
        self.total_hit_dice = 5

        self.weapon = Weapon(self, Dice(d8, 2), "piercing")
        self.surprise_attack_weapon = Weapon(
            self, ExtraWeaponDice(Dice(d8, 2), d6, 2), "piercing"
        )

    def take_turn(self, encounter: Encounter):
        # Weapon attack
        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Morningstar")

            self.action = False

            surprised_opponents = [
                enemy
                for enemy in encounter.get_foes(self)
                if (enemy.surprised and enemy.hp > 0)
            ]

            # Choose target from encounter, preferring a surprised opponent
            if len(surprised_opponents) > 0:
                self.surprise_attack_weapon(encounter.choice(surprised_opponents))

            else:
                self.weapon(encounter.choose_target(self))


class Bulette(Creature):
    """Bulette from the Monster Manual p. 34."""

    def initialize_features(self):
        self.abilities = get_abilities(4, 0, 5, -4, 0, -3)
        self.base_armor_class = 17
        self.hit_die = d10
        self.proficiency = 3
        self.skill_modifiers["perception"] = self.proficiency
        self.skill_proficiencies["perception"] = True
        self.total_hit_dice = 9

        self.weapon = Weapon(self, Dice(d12, 4), "piercing")

    def reset_conditions(self):
        # Extend reset_conditions() to reset use of Deadly Leap
        super().reset_conditions()
        self.deadly_leap = True

    def take_turn(self, encounter: Encounter):
        if self.action:
            self.action = False

            if self.deadly_leap:
                if self.verbose:
                    print(f"{self()} used Deadly Leap")

                self.deadly_leap = False

                # Roll damage once for both targets in area of effect
                bludgeoning_damage = d6(3) + self.abilities["str"]
                slashing_damage = d6(3) + self.abilities["str"]

                for target in encounter.choose_target(self, N_targets=2):
                    # Target decides between Str or Dex for saving throw
                    str_modifier = (
                        target.abilities["str"] + target.save_modifiers["str"]
                    )

                    if target.save_proficiencies["str"]:
                        str_modifier += target.proficiency

                    dex_modifier = (
                        target.abilities["dex"] + target.save_modifiers["dex"]
                    )

                    if target.save_proficiencies["dex"]:
                        dex_modifier += target.proficiency

                    # Restrained targets have disadvantage on Dex saves, giving
                    # -5 on average
                    if target.restrained > 0:
                        dex_modifier -= 5

                    save_result = target.half_saving_throw(
                        "str" if str_modifier > dex_modifier else "dex",
                        8 + self.proficiency + self.abilities["con"],
                        bludgeoning_damage,
                        "bludgeoning",
                        secondary_damage=slashing_damage,
                        secondary_type="slashing",
                    )

                    if not save_result:
                        target.prone = True

            # Weapon attack
            else:
                if self.verbose:
                    print(f"{self()} made an attack with Bite")

                self.weapon(encounter.choose_target(self))


class Camel(Creature):
    """Camel from the Monster Manual p. 320."""

    def initialize_features(self):
        self.abilities = get_abilities(3, -1, 2, -4, -1, -3)
        self.base_armor_class = 10
        self.hit_die = d10
        self.proficiency = 2
        self.total_hit_dice = 2

        self.weapon = Weapon(self, d4, "bludgeoning")

    def take_turn(self, encounter: Encounter):
        # Weapon attack
        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Bite")

            self.action = False
            self.weapon(encounter.choose_target(self), add_ability=False)


class ChainDevilGrappleDuration(GrappleDuration):
    """
    Grapple condition that deals 2d6 piercing damage at the start of the
    target's turns.
    """

    def start_turn_effect(self):
        if self.target.hp > 0:
            self.target.take_damage(d6(2), "piercing")


class ChainDevilUnnervingMaskDuration(Duration):
    """
    Chain Devil's Unnerving Mask reaction that triggers at the start of
    opponents' turns.
    """

    def __init__(self, chain_devil: Creature, target: Creature):
        """
        Constructor for ChainDevilUnnervingMaskDuration.

        Parameters
        ----------
        chain_devil
            The chain devil taking the Unnerving Mask reaction.
        target
            The creature triggering the Unnerving Mask reaction.
        """

        self.chain_devil = chain_devil
        self.target = target

        target.start_turn_duration.append(self)

    def start_turn_effect(self):
        """
        At the start of an opponents' turn, trigger Unnerving Mask if the target
        is conscious and not frightened.
        """

        if (
            self.target.hp > 0
            and self.target.frightened == 0
            and self.chain_devil.reaction
            and self.chain_devil.hp > 0
            and not self.chain_devil.is_incapacitated()
        ):
            self.chain_devil.reaction = False

            if self.chain_devil.verbose:
                print(f"{self.chain_devil()} used Unnerving Mask")

            if not self.target.saving_throw(
                "wis",
                9 + self.chain_devil.proficiency + self.chain_devil.abilities["cha"],
            ):
                frightened_duration = FrightenedOneTurnDuration(self.target)


class ChainDevil(Creature):
    """Chain devil from the Monster Manual p. 72."""

    def initialize_features(self):
        self.abilities = get_abilities(4, 2, 4, 0, 1, 2)
        self.base_armor_class = 14
        self.hit_die = d8
        self.immunities["fire"] = True
        self.immunities["poison"] = True
        self.magic_resistance = True
        self.proficiency = 3
        self.resistances["bludgeoning"] = True
        self.resistances["cold"] = True
        self.resistances["piercing"] = True
        self.resistances["slashing"] = True
        self.save_proficiencies["con"] = True
        self.save_proficiencies["wis"] = True
        self.save_proficiencies["cha"] = True
        self.total_hit_dice = 10

        self.weapon = Weapon(self, Dice(d6, 2), "slashing", attack_modifier=1)

    def start_encounter(self, encounter: Encounter):
        # Initialize Unnerving Mask
        for enemy in encounter.get_foes(self):
            unnerving_mask_duration = ChainDevilUnnervingMaskDuration(
                self,
                enemy,
            )

    def take_turn(self, encounter: Encounter):
        # Stop grappling unconscious creatures
        for grapple in self.grappling[:]:
            if grapple.target.hp == 0:
                grapple.end()

        # Animated chains can't attack if they are grappling
        N_animated_chain_attacks = min(4, 5 - len(self.grappling))

        # Weapon attack
        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Chain")

            self.action = False
            self.weapon_attack(encounter)
            self.weapon_attack(encounter)

            for i in range(N_animated_chain_attacks):
                self.weapon_attack(encounter)

    def weapon_attack(self, encounter: Encounter):
        """
        Weapon attack that can apply the chain devil's grapple condition.

        Parameters
        ----------
        encounter
            The Encounter in which the attack takes place.
        """

        ungrappled_opponents = [
            enemy
            for enemy in encounter.get_foes(self)
            if enemy.hp > 0 and len(enemy.grappled) == 0
        ]

        # Choose a target from the encounter, prefering opponents that are not
        # grappled
        if len(ungrappled_opponents) > 0:
            target = encounter.choice(ungrappled_opponents)
        else:
            target = encounter.choose_target(self)

        attack_result = self.weapon(target)

        if (attack_result == "hit" or attack_result == "crit") and len(
            self.grappling
        ) <= 5:
            grapple_duration = ChainDevilGrappleDuration(
                self,
                target,
                restrained=True,
            )


class Chimera(Creature):
    """Chimera from the Monster Manual p. 39."""

    def initialize_features(self):
        self.abilities = get_abilities(4, 0, 4, -4, 2, 0)
        self.base_armor_class = 14
        self.hit_die = d10
        self.proficiency = 3
        self.skill_modifiers["perception"] = self.proficiency
        self.skill_proficiencies["perception"] = True
        self.total_hit_dice = 12

        self.bite_weapon = Weapon(self, Dice(d6, 2), "piercing")
        self.claws_weapon = Weapon(self, Dice(d6, 2), "slashing")
        self.horns_weapon = Weapon(self, d12, "bludgeoning")

    def reset_conditions(self):
        # Extend reset_conditions() to recover use of breath weapon
        super().reset_conditions()
        self.breath_weapon = True

    def take_turn(self, encounter: Encounter):
        # Recover breath weapon
        if not self.breath_weapon and rng.random() >= (2.0 / 3):
            self.breath_weapon = True

        if self.action:
            self.action = False

            # Fire Breath
            if self.breath_weapon:
                if self.verbose:
                    print(f"{self()} used Fire Breath")

                self.breath_weapon = False

                # Roll damage once for both targets in area of effect
                damage = d8(7)

                for target in encounter.choose_target(self, N_targets=2):
                    target.half_saving_throw(
                        "dex",
                        8 + self.proficiency + self.abilities["con"],
                        damage,
                        "fire",
                    )

                if self.verbose:
                    print(f"{self()} made an attack with Bite and Claws")

            # Weapon attack
            else:
                if self.verbose:
                    print(f"{self()} made an attack with Horns, Bite, and Claws")

                self.horns_weapon(encounter.choose_target(self))

            self.bite_weapon(encounter.choose_target(self))
            self.claws_weapon(encounter.choose_target(self))


class Chuul(Creature):
    """Chuul from the Monster Manual p. 40."""

    def initialize_features(self):
        self.abilities = get_abilities(4, 0, 3, -3, 0, -3)
        self.base_armor_class = 16
        self.hit_die = d10
        self.immunities["poison"] = True
        self.proficiency = 2
        self.skill_modifiers["perception"] += self.proficiency
        self.skill_proficiencies["perception"] = True
        self.total_hit_dice = 11

        self.weapon = Weapon(self, Dice(d6, 2), "bludgeoning")

    def take_turn(self, encounter: Encounter):
        # Stop grappling unconscious creatures
        for grapple in self.grappling[:]:
            if grapple.target.hp == 0:
                grapple.end()

        # Weapon attack
        if self.action:
            self.action = False
            tentacles = True
            N_attacks = 2

            if self.verbose:
                print(f"{self()} made an attack with Pincer")

            # Prioritize grappled opponents
            for enemy in [grapple.target for grapple in self.grappling]:

                # Use tentacles to paralyze once per turn
                if tentacles and enemy.paralyzed == 0:
                    tentacles = False
                    self.tentacle_attack(enemy)

                # Weapon attack against grappled creature
                N_attacks -= 1
                self.weapon(enemy)

            # Remaining weapon attacks against ungrappled opponents
            for i in range(N_attacks):
                target = encounter.choose_target(self)
                attack_result = self.weapon(target)

                # Grapple the target on a hit
                if (
                    (attack_result == "hit" or attack_result == "crit")
                    and target.hp > 0
                    and len(self.grappling) < 2
                    and target not in [grapple.target for grapple in self.grappling]
                ):
                    grapple_duration = GrappleDuration(self, target)

                    # Use tentacles to paralyze once per turn
                    if tentacles and target.paralyzed == 0 and target.hp > 0:
                        tentacles = False
                        self.tentacle_attack(target)

    def tentacle_attack(self, target: Creature):
        """
        Tentacle attack that applies a paralyzed condition if the target fails a
        Constitution saving throw.

        Parameters
        ----------
        target
            The creature targeted by the tentacle attack.
        """

        if self.verbose:
            print(f"{self()} used Tentacles")

        if not target.saving_throw(
            "con",
            8 + self.proficiency + self.abilities["con"],
            save_type="poison",
        ):
            paralyzed_duration = ParalyzedDuration(
                self,
                target,
                8 + self.proficiency + self.abilities["con"],
                10,
            )


class DisplacementSuppressedDuration(Duration):
    """
    Class for a condition to suppress the Displacement feature of the Displacer
    Beast until the end of its next turn.
    """

    def __init__(self, creature: Creature):
        """
        Constructor for DisplacementSuppressedDuration.

        Parameters
        ----------
        creature
            The Displacer Beaast receiving the condition.
        """

        self.creature = creature

        creature.target_disadv -= 1
        creature.displacement = self
        creature.end_turn_duration.append(self)

    def end(self):
        self.creature.target_disadv += 1
        self.creature.displacement = None
        self.creature.end_turn_duration.remove(self)

    def end_turn_effect(self):
        self.end()


class DisplacerBeast(Creature):
    """Displacer Beast from the Monster Manual p. 81."""

    def half_saving_throw(
        self,
        ability: str,
        difficulty_class: int,
        damage: int,
        damage_type: str,
        secondary_damage: int = 0,
        secondary_type: str | None = None,
        adv: bool = False,
        disadv: bool = False,
        save_type: str | None = None,
    ) -> bool:
        # Override half_saving_throw() to use Avoidance
        result = self.saving_throw(
            ability,
            difficulty_class,
            adv=adv,
            disadv=disadv,
            save_type=save_type,
        )

        if not result:
            self.take_damage(
                int(damage / 2),
                damage_type,
                secondary_damage=int(secondary_damage / 2),
                secondary_type=secondary_type,
            )

        return result

    def initialize_features(self):
        self.abilities = get_abilities(4, 2, 3, -2, 1, -1)
        self.base_armor_class = 11
        self.hit_die = d10
        self.proficiency = 2
        self.total_hit_dice = 10

        self.weapon = Weapon(
            self,
            d6,
            "bludgeoning",
            secondary_dice=d6,
            secondary_type="piercing",
        )

    def reset_conditions(self):
        # Extend reset_conditions() to reset Displacement
        super().reset_conditions()
        self.target_disadv = 1
        self.displacement = None

    def take_damage(
        self,
        primary_damage: int,
        primary_type: str,
        dealer: Creature | None = None,
        ranged: bool = False,
        secondary_damage: int = 0,
        secondary_type: str | None = None,
    ) -> tuple[int, int]:
        # Extend take_damage() to disable Displacement until end of next turn
        primary_damage_taken, secondary_damage_taken = super().take_damage(
            primary_damage,
            primary_type,
            dealer=dealer,
            ranged=ranged,
            secondary_damage=secondary_damage,
            secondary_type=secondary_type,
        )

        if (
            primary_damage_taken + secondary_damage_taken > 0
            and dealer != None
            and self.displacement == None
        ):
            displacement_duration = DisplacementSuppressedDuration(self)

        return (primary_damage_taken, secondary_damage_taken)

    def take_turn(self, encounter: Encounter):
        # Weapon attack
        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Tentacles")

            self.action = False
            self.weapon(encounter.choose_target(self))
            self.weapon(encounter.choose_target(self))


class EarthElemental(Creature):
    """Earth elemental from the Monster Manual p. 124."""

    def initialize_features(self):
        self.abilities = get_abilities(5, -1, 5, -3, 0, -3)
        self.base_armor_class = 18
        self.hit_die = d10
        self.immunities["poison"] = True
        self.proficiency = 3
        self.resistances["bludgeoning"] = True
        self.resistances["piercing"] = True
        self.resistances["slashing"] = True
        self.total_hit_dice = 12
        self.vulnerabilities["thunder"]

        self.weapon = Weapon(self, Dice(d8, 2), "bludgeoning")

    def take_turn(self, encounter: Encounter):
        # Weapon attack
        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Slam")

            self.action = False
            self.weapon(encounter.choose_target(self))
            self.weapon(encounter.choose_target(self))


class Ettin(Creature):
    """Ettin from the Monster Manual p. 132."""

    def initialize_features(self):
        self.abilities = get_abilities(5, -1, 3, -2, 0, -1)
        self.base_armor_class = 13
        self.charm_adv = True
        self.hit_die = d10
        self.proficiency = 2
        self.skill_modifiers["perception"] = self.proficiency
        self.skill_proficiencies["perception"] = True
        self.total_hit_dice = 10

        self.battleaxe_weapon = Weapon(self, Dice(d8, 2), "slashing")
        self.morningstar_weapon = Weapon(self, Dice(d8, 2), "piercing")

    def reset_conditions(self):
        # Extend reset_conditions() to give advantage on Perception checks
        super().reset_conditions()
        self.skill_adv["perception"] += 1

    def take_turn(self, encounter: Encounter):
        # Weapon attack
        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Battleaxe and Morningstar")

            self.action = False
            self.battleaxe_weapon(encounter.choose_target(self))
            self.morningstar_weapon(encounter.choose_target(self))


class FireGiant(Creature):
    """Fire giant from the Monster Manual p. 154."""

    def initialize_features(self):
        self.abilities = get_abilities(7, -1, 6, 0, 2, 1)
        self.armor_type = "heavy"
        self.base_armor_class = 18
        self.hit_die = d12
        self.immunities["fire"] = True
        self.proficiency = 4
        self.save_proficiencies["dex"] = True
        self.save_proficiencies["con"] = True
        self.save_proficiencies["cha"] = True
        self.skill_proficiencies["athletics"] = True
        self.skill_proficiencies["perception"] = True
        self.total_hit_dice = 13

        self.weapon = Weapon(self, Dice(d6, 6), "slashing")

    def take_turn(self, encounter: Encounter):
        # Weapon attack
        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Greatsword")

            self.action = False
            self.weapon(encounter.choose_target(self))
            self.weapon(encounter.choose_target(self))


class FrostGiant(Creature):
    """Frost giant from the Monster Manual p. 155."""

    def initialize_features(self):
        self.abilities = get_abilities(6, -1, 5, -1, 0, 1)
        self.base_armor_class = 16
        self.hit_die = d12
        self.immunities["cold"] = True
        self.proficiency = 3
        self.save_proficiencies["con"] = True
        self.save_proficiencies["wis"] = True
        self.save_proficiencies["cha"] = True
        self.skill_proficiencies["athletics"] = True
        self.skill_proficiencies["perception"] = True
        self.total_hit_dice = 12

        self.weapon = Weapon(self, Dice(d12, 3), "slashing")

    def take_turn(self, encounter: Encounter):
        # Weapon attack
        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Greataxe")

            self.action = False
            self.weapon(encounter.choose_target(self))
            self.weapon(encounter.choose_target(self))


class GelatinousCubeEngulfedDuration(EngulfedDuration):
    """
    Class for the Gelatinous Cube's engulf condition that can be escaped with an
    unskilled Strength check.
    """

    def start_turn_effect(self):
        # The target uses its action to attempt to escape
        if self.target.action:
            self.target.action = False

            if self.target.skill_check("str", self.save_dc):
                self.end()


class GelatinousCube(Creature):
    """Gelatinous Cube from the Monster Manual p. 242."""

    def initialize_features(self):
        self.abilities = get_abilities(2, -4, 5, -5, -2, -5)
        self.base_armor_class = 10
        self.blindsight = True
        self.hit_die = d10
        self.proficiency = 2
        self.total_hit_dice = 8

    def fall_unconscious(self):
        # Extend fall_unconscious() to release engulfed creatures
        super().fall_unconscious()

        for creature in self.engulfed_creatures[:]:
            creature.engulfed.end()

    def reset_conditions(self):
        # Extend reset_conditions() to reset engulfed creatures
        super().reset_conditions()
        self.engulfed_creatures = list()

    def start_turn(self, encounter: Encounter):
        # Extend start_turn() to deal acid damage to engulfed creatures
        for creature in self.engulfed_creatures:
            if creature.hp > 0:
                creature.take_damage(d6(6), "acid")

        super().start_turn(encounter)

    def take_turn(self, encounter: Encounter):
        valid_targets = [
            enemy
            for enemy in encounter.get_foes(self)
            if (enemy.hp > 0 and enemy.engulfed == None)
        ]

        # Engulf
        if self.action and len(valid_targets) > 0:
            self.action = False

            if self.verbose:
                print(f"{self()} used Engulf")

            if len(valid_targets) <= 2:
                targets = valid_targets
            else:
                targets = encounter.choice(valid_targets, 2, replace=False)

            for target in targets:
                if not target.saving_throw(
                    "dex",
                    8 + self.proficiency + self.abilities["str"],
                ):
                    target.take_damage(d6(3), "acid")

                    # Replace with GelatinousCubeEngulfedDuration to force the
                    # target to use its action to escape the condition. In
                    # testing, parties have higher survival if they don't do
                    # this and use their action normally.
                    engulf_duration = EngulfedDuration(
                        self, target, 8 + self.proficiency + self.abilities["str"]
                    )


class Ghoul(Creature):
    """Ghoul from the Monster Manual p. 148."""

    def initialize_features(self):
        self.abilities = get_abilities(1, 2, 0, -2, 0, -2)
        self.base_armor_class = 10
        self.hit_die = d8
        self.immunities["poison"] = True
        self.proficiency = 2
        self.total_hit_dice = 5
        self.undead = 1

        self.bite_weapon = Weapon(
            self,
            Dice(d6, 2),
            "piercing",
            ability="dex",
            proficient=False,
        )
        self.claws_weapon = Weapon(self, Dice(d4, 2), "slashing", ability="dex")

    def take_turn(self, encounter: Encounter):
        # Weapon attack
        if self.action:
            self.action = False

            target = encounter.choose_target(self)

            # Use Bite if target is paralyzed, otherwise use Claws
            if target.paralyzed > 0:

                if self.verbose:
                    print(f"{self()} made an attack with Bite")

                self.bite_weapon(target)

            else:
                if self.verbose:
                    print(f"{self()} made an attack with Claws")

                attack_result = self.claws_weapon(target)

                # Target must save against paralysis on a hit
                if (
                    (attack_result == "hit" or attack_result == "crit")
                    and not target.ghoul_paralysis_immunity
                    and not target.saving_throw(
                        "con",
                        8 + self.proficiency + self.abilities["con"],
                    )
                ):
                    paralyzed_duration = ParalyzedDuration(
                        self,
                        target,
                        10,
                        8 + self.proficiency + self.abilities["con"],
                    )


class GiantBat(Creature):
    """Giant Bat from the Monster Manual p. 323."""

    def initialize_features(self):
        self.abilities = get_abilities(2, 3, 0, -4, 1, -2)
        self.base_armor_class = 10
        self.hit_die = d10
        self.proficiency = 2
        self.total_hit_dice = 4

        self.weapon = Weapon(self, d6, "piercing")

        self.blindsight = True

    def reset_conditions(self):
        # Extend reset_conditions() to give advantage on Perception checks
        super().reset_conditions()
        self.skill_adv["perception"] += 1

    def take_turn(self, encounter: Encounter):
        # Weapon attack
        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Bite")

            self.action = False
            self.weapon(encounter.choose_target(self))


class GiantCentipede(Creature):
    """Giant centipede from the Monster Manual p. 323."""

    def initialize_features(self):
        self.abilities = get_abilities(-3, 2, 1, -5, -2, -4)
        self.base_armor_class = 11
        self.hit_die = d6
        self.proficiency = 2
        self.total_hit_dice = 1

        self.weapon = Weapon(self, d4, "piercing", ability="dex")

    def take_turn(self, encounter: Encounter):
        # Weapon attack
        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Bite")

            self.action = False
            target = encounter.choose_target(self)
            attack_result = self.weapon(target)

            # Save against poison from bite
            if (
                (attack_result == "hit" or attack_result == "crit")
                and target.hp > 0
                and not target.saving_throw(
                    "con",
                    8 + self.proficiency + self.abilities["con"],
                    save_type="poison",
                )
            ):
                target.take_damage(d6(3), "poison")

                if target.hp == 0:
                    target.paralyzed += 1


class GiantRat(Creature):
    """Giant Rat from the Monster Manual p. 327."""

    def initialize_features(self):
        self.abilities = get_abilities(-2, 2, 0, -4, 0, -3)
        self.base_armor_class = 10
        self.hit_die = d6
        self.proficiency = 2
        self.total_hit_dice = 2
        self.skill_proficiencies["perception"] = True

        self.weapon = Weapon(self, d4, "piercing", ability="dex")

    def reset_conditions(self):
        # Extend reset_conditions() to give advantage on Perception checks
        super().reset_conditions()
        self.skill_adv["perception"] += 1

    def take_turn(self, encounter: Encounter):
        # Weapon attack
        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Bite")

            self.action = False
            target = encounter.choose_target(self)

            # Pack Tactics gives advantage if an ally is within 5 ft of target
            allies = encounter.get_allies(self)
            self.weapon(
                target,
                adv=len([ally for ally in allies if ally.hp > 0]) > 1,
            )


class GiantScorpion(Creature):
    """Giant scorpion from the Monster Manual p. 327"""

    def initialize_features(self):
        self.abilities = get_abilities(2, 1, 2, -5, -1, -4)
        self.base_armor_class = 14
        self.hit_die = d10
        self.proficiency = 2
        self.total_hit_dice = 7

        self.claw_weapon = Weapon(self, d8, "bludgeoning")
        self.sting_weapon = Weapon(self, d10, "piercing")

    def take_turn(self, encounter: Encounter):
        # Weapon attack
        if self.action:
            self.action = False

            if self.verbose:
                print(f"{self()} made an attack with Claws and Sting")

            self.claw_weapon(encounter.choose_target(self))
            self.claw_weapon(encounter.choose_target(self))

            target = encounter.choose_target(self)
            attack_result = self.sting_weapon(target)

            # Save against poison from sting
            if (attack_result == "hit" or attack_result == "crit") and target.hp > 0:
                target.half_saving_throw(
                    "con",
                    8 + self.proficiency + self.abilities["con"],
                    d10(4),
                    "poison",
                    save_type="poison",
                )


class GiantSpider(Creature):
    """Giant Spider from the Monster Manual p. 328."""

    def initialize_features(self):
        self.abilities = get_abilities(2, 3, 1, -4, 0, -3)
        self.base_armor_class = 11
        self.hit_die = d10
        self.proficiency = 2
        self.total_hit_dice = 4

        self.bite_weapon = Weapon(self, d8, "piercing", ability="dex")
        self.web_weapon = Weapon(self, lambda: 0, None, ability="dex")

    def reset_conditions(self):
        # Extend reset_conditions() to recover use of Web action
        super().reset_conditions()
        self.web = True

    def take_turn(self, encounter: Encounter):
        # Recover Web action
        if not self.web and rng.random() >= (2.0 / 3):
            self.web = True

        # Weapon attack
        if self.action:
            self.action = False
            target = encounter.choose_target(self)

            # Use Web if available and target is not restrained
            if self.web and target.restrained == 0:
                if self.verbose:
                    print(f"{self()} made an attack with Web")

                attack_result = self.web_weapon.roll_attack(target)

                if attack_result == "hit" or attack_result == "crit":
                    web_duration = RestrainedDuration(
                        target,
                        8 + self.proficiency + self.abilities["str"],
                    )

            else:
                if self.verbose:
                    print(f"{self()} made an attack with Bite")

                attack_result = self.bite_weapon(target)

                # Target must save against poison on a hit
                if attack_result == "hit" or attack_result == "crit":
                    target.half_saving_throw(
                        "con",
                        8 + self.proficiency + self.abilities["con"],
                        d8(2),
                        "poison",
                        save_type="poison",
                    )

                    if target.hp == 0:
                        target.paralyzed += 1


class Gnoll(Creature):
    """Gnoll from the Monster Manual p. 163."""

    def initialize_features(self):
        self.abilities = get_abilities(2, 1, 0, -2, 0, -2)
        self.base_armor_class = 14
        self.hit_die = d8
        self.proficiency = 2
        self.total_hit_dice = 5

        self.bite_weapon = Weapon(self, d4, "piercing")
        self.spear_weapon = Weapon(self, d6, "piercing")

    def take_turn(self, encounter: Encounter):
        # Weapon attack
        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Spear")

            self.action = False

            target = encounter.choose_target(self)
            self.spear_weapon(target)

            # Rampage
            if target.hp == 0 and self.bonus:
                if self.verbose:
                    print(f"{self()} made an attack with Bite")

                self.bonus = False
                self.bite_weapon(encounter.choose_target(self))


class Goblin(Creature):
    """Goblin from the Monster Manual p. 166."""

    def initialize_features(self):
        self.abilities = get_abilities(-1, 2, 0, 0, -1, -1)
        self.base_armor_class = 13
        self.hit_die = d6
        self.proficiency = 2
        self.skill_modifiers["stealth"] = self.proficiency
        self.skill_proficiencies["stealth"] = True
        self.total_hit_dice = 2

        self.weapon = Weapon(self, d6, "slashing", ability="dex")

    def take_turn(self, encounter: Encounter):
        # Weapon attack, abolishing stealth
        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Scimitar")

            self.action = False

            target = encounter.choose_target(self)
            self.weapon(target)

            # Attacking gives away position
            if target is not None:
                self.stealth = 0

        # Bonus action to hide from Nimble Escape
        if self.bonus:
            self.bonus = False
            self.stealth = self.roll_skill("stealth")

            if self.verbose:
                print(f"{self()} used Hide and rolled {self.stealth:d} on Stealth")


class Hawk(Creature):
    """Hawk from the Monster Manual p. 330."""

    def initialize_features(self):
        self.abilities = get_abilities(-3, 3, -1, -4, 2, -2)
        self.base_armor_class = 10
        self.hit_die = d4
        self.proficiency = 2
        self.skill_proficiencies["perception"] = True
        self.total_hit_dice = 1

        self.weapon = Weapon(self, lambda: 1, "slashing", ability="dex")

    def reset_conditions(self):
        # Extend reset_conditions() to give advantage on Perception checks
        super().reset_conditions()
        self.skill_adv["perception"] += 1

    def take_turn(self, encounter: Encounter):
        # Weapon attack
        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Talons")

            self.action = False
            self.weapon(encounter.choose_target(self), add_ability=False)


class HellHound(Creature):
    """Hell Hound from the Monster Manual p. 182."""

    def initialize_features(self):
        self.abilities = get_abilities(3, 1, 2, -2, 1, -2)
        self.base_armor_class = 14
        self.hit_die = d8
        self.immunities["fire"] = True
        self.proficiency = 2
        self.skill_modifiers["perception"] = self.proficiency
        self.skill_proficiencies["perception"] = True
        self.total_hit_dice = 7

        self.weapon = Weapon(
            self,
            d8,
            "piercing",
            secondary_dice=Dice(d6, 2),
            secondary_type="fire",
        )

    def reset_conditions(self):
        # Extend reset_conditions() to give advantage on Perception checks and
        # recover use of breath weapon
        super().reset_conditions()
        self.breath_weapon = True
        self.skill_adv["perception"] += 1

    def take_turn(self, encounter: Encounter):
        # Recover breath weapon
        if not self.breath_weapon and rng.random() >= (2.0 / 3):
            self.breath_weapon = True

        if self.action:
            self.action = False

            # Fire Breath
            if self.breath_weapon:
                if self.verbose:
                    print(f"{self()} used Fire Breath")

                self.breath_weapon = False
                damage = d6(6)

                for target in encounter.choose_target(self, N_targets=2):
                    target.half_saving_throw(
                        "dex",
                        8 + self.proficiency + self.abilities["con"],
                        damage,
                        "fire",
                    )

            # Weapon attack
            else:
                if self.verbose:
                    print(f"{self()} made an attack with Bite")

                target = encounter.choose_target(self)

                # Pack Tactics gives advantage if an ally is within 5 ft of
                # target
                allies = encounter.get_allies(self)
                self.weapon(
                    target,
                    adv=len([ally for ally in allies if ally.hp > 0]) > 1,
                )


class Hobgoblin(Creature):
    """Hobgoblin from the Monster Manual p. 186."""

    def initialize_features(self):
        self.abilities = get_abilities(1, 1, 1, 0, 0, -1)
        self.armor_type = "medium"
        self.base_armor_class = 17
        self.hit_die = d8
        self.proficiency = 2
        self.total_hit_dice = 2

        self.weapon = Weapon(self, d8, "slashing")
        self.martial_advantage_weapon = Weapon(
            self,
            ExtraWeaponDice(d8, d6, 2),
            "slashing",
        )

    def take_turn(self, encounter: Encounter):
        # Weapon attack
        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Longsword")

            self.action = False

            # Martial Advantage gives an extra 2d6 damage if an ally is within
            # 5 ft of target
            allies = encounter.get_allies(self)
            if len([ally for ally in allies if ally.hp > 0]) > 1:
                self.martial_advantage_weapon(encounter.choose_target(self))
            else:
                self.weapon(encounter.choose_target(self))


class HydraDamageDuration(Duration):
    """
    Class for a condition that checks whether other creatures have dealt enough
    damage in a turn to sever a Hydra's head.
    """

    def __init__(self, hydra: Creature):
        """
        Constructor for HydraDamageDuration.

        Parameters
        ----------
        hydra
            The hydra receiving damage.
        """

        self.hydra = hydra

    def end_turn_effect(self):
        # Check whether a head is lost this turn
        if self.hydra.damage_taken_this_turn >= 25:

            if self.hydra.verbose:
                print(f"{self.hydra()} lost a head")

            self.hydra.heads -= 1
            self.hydra.heads_lost_this_round += 1

            if self.hydra.heads == 0:

                self.hydra.hp = 0
                self.hydra.total_hp = 0

                if self.hydra.verbose:
                    print(f"{self.hydra()} has zero heads")

        self.hydra.damage_taken_this_turn = 0


class Hydra(Creature):
    """Hydra from the Monster Manual p. 190."""

    def end_turn(self):
        # Extend end_turn() to regrow heads
        super().end_turn()

        if self.regrow_heads and self.heads_lost_this_round > 0:

            if self.verbose:
                print(f"{self()} regrew {2 * self.heads_lost_this_round:d} headss")

            self.heads += 2 * self.heads_lost_this_round
            self.heal(20 * self.heads_lost_this_round)

        self.heads_lost_this_round = 0
        self.regrow_heads = True

    def initialize_features(self):
        self.abilities = get_abilities(5, 1, 5, -4, 0, -2)
        self.base_armor_class = 14
        self.hit_die = d12
        self.proficiency = 3
        self.skill_modifiers["perception"] = self.proficiency
        self.skill_proficiencies["perception"] = True
        self.total_hit_dice = 15

        self.weapon = Weapon(self, d10, "piercing")

    def reset_conditions(self):
        # Extend reset_conditions() to reset number of heads to five
        super().reset_conditions()
        self.damage_taken_this_turn = 0
        self.heads = 5
        self.heads_lost_this_round = 0
        self.regrow_heads = True

    def start_encounter(self, encounter):
        # Initialize Duration instance to reset damage taken at the end of each turn
        hydra_damage_duration = HydraDamageDuration(self)

        for creature in encounter.side_A + encounter.side_B:
            creature.end_turn_duration.append(hydra_damage_duration)

    def take_damage(
        self,
        primary_damage: int,
        primary_type: str,
        dealer: Creature | None = None,
        ranged: bool = False,
        secondary_damage: int = 0,
        secondary_type: str | None = None,
    ) -> tuple[int, int]:
        # Extend take_damage() to lose heads
        primary_damage_taken, secondary_damage_taken = super().take_damage(
            primary_damage,
            primary_type,
            dealer=dealer,
            ranged=ranged,
            secondary_damage=secondary_damage,
            secondary_type=secondary_type,
        )

        damage_taken = primary_damage_taken + secondary_damage_taken

        self.damage_taken_this_turn += damage_taken

        # Don't regrow heads if fire damage is taken
        if damage_taken > 0 and (primary_type == "fire" or secondary_type == "fire"):
            self.regrow_heads = False

        return (primary_damage_taken, secondary_damage_taken)

    def take_turn(self, encounter: Encounter):
        # Weapon attack
        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Bite")

            self.action = False

            for i in range(self.heads):
                self.weapon(encounter.choose_target(self))


class InvisibleStalker(Creature):
    """Invisible stalker from the Monster Manual p. 192."""

    def initialize_features(self):
        self.abilities = get_abilities(3, 4, 2, 0, 2, 0)
        self.base_armor_class = 10
        self.hit_die = d8
        self.immunities["poison"] = True
        self.proficiency = 3
        self.resistances["bludgeoning"] = True
        self.resistances["piercing"] = True
        self.resistances["slashing"] = True
        self.skill_modifiers["perception"] = self.proficiency
        self.skill_modifiers["stealth"] = self.proficiency
        self.skill_proficiencies["perception"] = True
        self.skill_proficiencies["stealth"] = True
        self.total_hit_dice = 16

        self.weapon = Weapon(self, Dice(d6, 2), "bludgeoning")

    def reset_conditions(self):
        # Extend reset_conditions() to provide invisibility
        super().reset_conditions()
        self.invisible += 1

    def take_turn(self, encounter: Encounter):
        # Weapon attack
        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Slam")

            self.action = False
            self.weapon(encounter.choose_target(self))
            self.weapon(encounter.choose_target(self))


class Jackal(Creature):
    """Jackal from the Monster Manual p. 331."""

    def initialize_features(self):
        self.abilities = get_abilities(-1, 2, 0, -4, 1, -2)
        self.base_armor_class = 10
        self.hit_die = d6
        self.proficiency = 2
        self.skill_proficiencies["perception"] = True
        self.total_hit_dice = 1

        self.weapon = Weapon(self, d4, "piercing")

    def reset_conditions(self):
        # Extend reset_conditions() to give advantage on Perception checks
        super().reset_conditions()
        self.skill_adv["perception"] += 1

    def take_turn(self, encounter: Encounter):
        # Weapon attack
        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Bite")

            self.action = False
            target = encounter.choose_target(self)

            # Pack Tactics gives advantage if an ally is within 5 ft of target
            allies = encounter.get_allies(self)
            self.weapon(target, adv=len([ally for ally in allies if ally.hp > 0]) > 1)


class Kobold(Creature):
    """Kobold from the Monster Manual p. 195."""

    def initialize_features(self):
        self.abilities = get_abilities(-2, 2, -1, -1, -2, -1)
        self.base_armor_class = 10
        self.hit_die = d6
        self.proficiency = 2
        self.total_hit_dice = 2

        self.weapon = Weapon(self, d4, "piercing", ability="dex")

    def take_turn(self, encounter: Encounter):
        # Weapon attack
        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Dagger")

            self.action = False
            target = encounter.choose_target(self)

            # Pack Tactics gives advantage if an ally is within 5 ft of target
            allies = encounter.get_allies(self)
            self.weapon(target, adv=len([ally for ally in allies if ally.hp > 0]) > 1)


class LizardQueen(Creature):
    """Lizard king/queen from the Monster Manual p. 219."""

    def initialize_features(self):
        self.abilities = get_abilities(3, 1, 2, 0, 0, 2)
        self.base_armor_class = 14
        self.hit_die = d8
        self.proficiency = 2
        self.save_proficiencies["con"] = True
        self.save_proficiencies["wis"] = True
        self.skill_modifiers["perception"] = self.proficiency
        self.skill_modifiers["stealth"] = self.proficiency
        self.skill_modifiers["survival"] = self.proficiency
        self.skill_proficiencies["perception"] = True
        self.skill_proficiencies["stealth"] = True
        self.skill_proficiencies["survival"] = True
        self.total_hit_dice = 12

        self.weapon = Weapon(self, d8, "piercing")
        self.skewer_weapon = Weapon(self, ExtraWeaponDice(d8, d6, 3), "piercing")

    def take_turn(self, encounter: Encounter):
        self.skewer = True

        # Weapon attack
        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Trident")

            self.action = False
            self.weapon_attack(encounter)
            self.weapon_attack(encounter)

    def weapon_attack(self, encounter: Encounter):
        """
        Weapon attack that can use the Lizard Queen's Skewer ability.

        Parameters
        ----------
        encounter
            The Encounter in which the attack takes place.
        """

        target = encounter.choose_target(self)

        if target is None:
            return

        if self.skewer:
            attack_result = self.weapon.roll_attack(target)

            if attack_result == "hit" or attack_result == "crit":
                self.skewer = False

                if target.is_incapacitated():
                    attack_result = "crit"

                if attack_result == "crit":
                    damage = self.weapon.roll_damage(dice_multiplier=2)
                else:
                    damage = self.weapon.roll_damage()

                skewer_damage = d6(3)

                if self.verbose:
                    print(
                        f"{self()} scored a {attack_result} on {target()} for "
                        f"{damage + skewer_damage:d} {self.weapon.type} damage"
                    )

                target.take_damage(
                    damage + skewer_damage,
                    self.weapon.type,
                    dealer=self,
                )
                self.total_hp += skewer_damage
                self.heal(skewer_damage)

        else:
            self.weapon(target)


class Mage(Creature):
    """Mage from the Monster Manual p. 347."""

    def hit_armor_class(
        self,
        attacker: Creature,
        attack_roll: int,
        ranged=False,
    ) -> bool:
        # Override hit_armor_class() to cast Shield
        difference = attack_roll - self.armor_class()

        if (
            self.reaction
            and self.hp > 0
            and not self.is_incapacitated()
            and difference >= 0
            and difference < 5
        ):
            self.reaction = False

            self.cast_shield(slot=self.lowest_spell_slots()[0])
            difference = attack_roll - self.armor_class()

        return difference >= 0

    def initialize_features(self):
        self.abilities = get_abilities(-1, 2, 0, 3, 1, 0)
        self.base_armor_class = 13
        self.hit_die = d8
        self.level = 9
        self.proficiency = 3
        self.save_proficiencies["int"] = True
        self.save_proficiencies["wis"] = True
        self.skill_proficiencies["arcana"] = True
        self.skill_proficiencies["history"] = True
        self.spell_ability = "int"
        self.total_hit_dice = 9

        # Spell slots, assuming mage armor was cast at first level
        self.total_spell_slots = [3, 3, 3, 3, 1]

        # Spells
        self.cast_cone_of_cold = spells.ConeOfCold(self)
        self.cast_fireball = spells.Fireball(self)
        self.cast_fire_bolt = spells.FireBolt(self)
        self.cast_greater_invisibility = spells.GreaterInvisibility(self)
        self.cast_magic_missile = spells.MagicMissile(self)
        self.cast_shield = spells.Shield(self)

    def lowest_spell_slots(self) -> list[int | None]:
        """
        Returns the lowest available spell slot greater than each spell level.
        """

        lowest_slots = [None for i in range(5)]

        if self.N_spell_slots[4] > 0:
            lowest_slots[4] = 5

        for slot in range(3, -1, -1):
            if self.N_spell_slots[slot] > 0:
                lowest_slots[slot] = slot + 1
            else:
                lowest_slots[slot] = lowest_slots[slot + 1]

        return lowest_slots

    def reset_conditions(self):
        # Extend reset_conditions() to recover spell slots and then cast Greater
        # Invisibility on self
        super().reset_conditions()

        self.N_spell_slots = [i for i in self.total_spell_slots]
        self.cast_greater_invisibility(targets=self)

    def save_dc(self) -> int:
        """Determine save DC for spells."""

        return 8 + self.abilities[self.spell_ability] + self.proficiency

    def take_turn(self, encounter: Encounter):
        lowest_slots = self.lowest_spell_slots()

        opponents = [enemy for enemy in encounter.get_foes(self) if enemy.hp > 0]
        N_opponents = len(opponents)

        visible_opponents = [enemy for enemy in opponents if not enemy.is_hidden(self)]
        N_visible_opponents = len(visible_opponents)

        if self.action:
            self.action = False

            if lowest_slots[4] is not None:
                self.cast_cone_of_cold(
                    slot=lowest_slots[4],
                    targets=encounter.choose_target(self, N_targets=2),
                )

            elif lowest_slots[3] is not None:
                self.cast_fireball(
                    slot=lowest_slots[3],
                    targets=encounter.choose_target(self, N_targets=2),
                )

            elif lowest_slots[2] is not None:
                self.cast_fireball(
                    slot=lowest_slots[2],
                    targets=encounter.choose_target(self, N_targets=2),
                )

            elif lowest_slots[1] is not None:
                self.cast_magic_missile(
                    slot=lowest_slots[1],
                    targets=encounter.choose_target(
                        self,
                        N_targets=lowest_slots[1] + 2,
                        replacement=True,
                    ),
                )

            elif lowest_slots[0] is not None:
                self.cast_magic_missile(
                    slot=lowest_slots[0],
                    targets=encounter.choose_target(
                        self,
                        N_targets=lowest_slots[0] + 2,
                        replacement=True,
                    ),
                )

            else:
                self.cast_fire_bolt(targets=encounter.choose_target(self))

    def targeted_by_magic_missile(self):
        # Use reaction to cast Shield
        if self.reaction and self.hp > 0 and not self.is_incapacitated():
            self.reaction = False
            self.cast_shield(slot=self.lowest_spell_slots()[0])


class Merrow(Creature):
    """Merrow from the Monster Manual p. 219."""

    def initialize_features(self):
        self.abilities = get_abilities(4, 0, 2, -1, 0, -1)
        self.base_armor_class = 13
        self.hit_die = d10
        self.proficiency = 2
        self.total_hit_dice = 6

        self.bite_weapon = Weapon(self, d8, "piercing")
        self.harpoon_weapon = Weapon(self, Dice(d6, 2), "piercing")

    def take_turn(self, encounter: Encounter):
        # Weapon attack
        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Bite and Harpoon")

            self.action = False
            self.bite_weapon(encounter.choose_target(self))
            self.harpoon_weapon(encounter.choose_target(self))


class MindFlayer(Creature):
    """Mind flayer from the Monster Manual p. 222."""

    def initialize_features(self):
        self.abilities = get_abilities(0, 1, 1, 4, 3, 3)
        self.base_armor_class = 14
        self.hit_die = d8
        self.magic_resistance = True
        self.proficiency = 3
        self.save_proficiencies["int"] = True
        self.save_proficiencies["wis"] = True
        self.save_proficiencies["cha"] = True
        self.skill_proficiencies["arcana"] = True
        self.skill_proficiencies["deception"] = True
        self.skill_proficiencies["insight"] = True
        self.skill_proficiencies["perception"] = True
        self.skill_proficiencies["persuasion"] = True
        self.skill_proficiencies["stealth"] = True
        self.total_hit_dice = 13

        self.extract_brain_weapon = Weapon(
            self,
            Dice(d10, 10),
            "piercing",
            ability="int",
        )
        self.tentacles_weapon = Weapon(
            self,
            Dice(d10, 2),
            "psychic",
            ability="int",
        )

    def reset_conditions(self):
        # Extend reset_conditions() to recover use of mind blast
        super().reset_conditions()
        self.mind_blast = True

    def take_turn(self, encounter: Encounter):
        # Recover mind blast
        if not self.mind_blast and rng.random() >= (2.0 / 3):
            self.mind_blast = True

        active_opponents = [
            enemy
            for enemy in encounter.get_foes(self)
            if enemy.hp > 0 and not enemy.is_incapacitated()
        ]

        if self.action:
            self.action = False

            # Mind blast
            if self.mind_blast and len(active_opponents) > 0:
                if self.verbose:
                    print(f"{self()} used Mind Blast")

                self.mind_blast = False
                damage = d8(4) + self.abilities["int"]

                if len(active_opponents) <= 2:
                    targets = active_opponents

                else:
                    targets = encounter.choice(active_opponents, size=2, replace=False)

                for target in targets:
                    if not target.saving_throw(
                        "int",
                        8 + self.proficiency + self.abilities["int"],
                        save_type="magic",
                    ):
                        target.take_damage(damage, "psychic")
                        stun_duration = StunnedDuration(
                            self,
                            target,
                            8 + self.proficiency + self.abilities["int"],
                            10,
                        )

            # Weapon attack
            else:
                extract_brain_targets = [
                    grapple.target
                    for grapple in self.grappling
                    if (grapple.target.is_incapacitated() and grapple.target.hp > 0)
                ]

                # Extract Brain
                if len(extract_brain_targets) > 0:
                    if self.verbose:
                        print(f"{self()} made an attack with Extract Brain")

                    target = encounter.choice(extract_brain_targets)
                    self.extract_brain_weapon(target, add_ability=False)

                    if target.hp == 0:
                        target.total_hp = 0

                # Tentacles
                else:
                    if self.verbose:
                        print(f"{self()} made an attack with Tentacles")

                    target = encounter.choose_target(self)
                    attack_result = self.tentacles_weapon(target)

                    if attack_result == "hit" or attack_result == "crit":
                        if target.saving_throw(
                            "int",
                            8 + self.proficiency + self.abilities["int"],
                        ):
                            grapple_duration = GrappleDuration(self, target)

                        else:
                            grapple_duration = GrappleDuration(
                                self, target, stunned=True
                            )


class MyconidSprout(Creature):
    """Myconid sprout from the Monster Manual p. 230."""

    def initialize_features(self):
        self.abilities = get_abilities(-1, 0, 0, -1, 0, -3)
        self.base_armor_class = 10
        self.hit_die = d6
        self.proficiency = 2
        self.total_hit_dice = 2

        self.weapon = Weapon(
            self,
            d4,
            "bludgeoning",
            secondary_dice=d4,
            secondary_type="poison",
        )

    def take_turn(self, encounter: Encounter):
        # Weapon attack
        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Fist")

            self.action = False
            self.weapon(encounter.choose_target(self))


class Nothic(Creature):
    """Nothic from the Monster Manual p. 236."""

    def initialize_features(self):
        self.abilities = get_abilities(2, 3, 3, 1, 0, -1)
        self.base_armor_class = 12
        self.hit_die = d8
        self.proficiency = 2
        self.skill_modifiers["insight"] = self.proficiency
        self.skill_proficiencies["arcana"] = True
        self.skill_proficiencies["insight"] = True
        self.skill_proficiencies["perception"] = True
        self.skill_proficiencies["stealth"] = True
        self.total_hit_dice = 6

        self.weapon = Weapon(
            self,
            d6,
            "slashing",
            ability="dex",
            attack_modifier=-1,
        )

    def reset_conditions(self):
        # Extend reset_conditions() to give advantage on Perception checks
        super().reset_conditions()
        self.skill_adv["perception"] += 1

    def take_turn(self, encounter: Encounter):
        if self.action:
            self.action = False
            target = encounter.choose_target(self)

            # Weapon attack
            if target.immunities["necrotic"] or target.is_hidden(self):
                if self.verbose:
                    print(f"{self()} made an attack with Claws")

                self.weapon(target)
                self.weapon(encounter.choose_target(self))

            # Rotting Gaze
            else:
                if self.verbose:
                    print(f"{self()} used Rotting Gaze")

                if not target.saving_throw(
                    "con",
                    7 + self.proficiency + self.abilities["con"],
                    save_type="magic",
                ):
                    target.take_damage(d6(3), "necrotic")


class Ogre(Creature):
    """Ogre from the Monster Manual p. 237."""

    def initialize_features(self):
        self.abilities = get_abilities(4, -1, 3, -3, -2, -2)
        self.armor_type = "medium"
        self.base_armor_class = 12
        self.hit_die = d10
        self.proficiency = 2
        self.total_hit_dice = 7

        self.weapon = Weapon(self, Dice(d8, 2), "bludgeoning")

    def take_turn(self, encounter: Encounter):
        # Weapon attack
        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Greatclub")

            self.action = False
            self.weapon(encounter.choose_target(self))


class Orc(Creature):
    """Orc from the Monster Manual p. 246."""

    def initialize_features(self):
        self.abilities = get_abilities(3, 1, 3, -2, 0, 0)
        self.armor_type = "medium"
        self.base_armor_class = 12
        self.hit_die = d8
        self.proficiency = 2
        self.skill_proficiencies["intimidation"] = True
        self.total_hit_dice = 2

        self.weapon = Weapon(self, d12, "slashing")

    def take_turn(self, encounter: Encounter):
        # Weapon attack
        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Greataxe")

            self.action = False
            self.weapon(encounter.choose_target(self))


class Owlbear(Creature):
    """Owlbear from the Monster Manual p. 249."""

    def initialize_features(self):
        self.abilities = get_abilities(5, 1, 3, -4, 1, -2)
        self.base_armor_class = 12
        self.hit_die = d10
        self.proficiency = 2
        self.skill_proficiencies["perception"] = True
        self.total_hit_dice = 7

        self.beak_weapon = Weapon(self, d10, "piercing")
        self.claws_weapon = Weapon(self, Dice(d8, 2), "slashing")

    def reset_conditions(self):
        # Extend reset_conditions() to give advantage on Perception checks
        super().reset_conditions()
        self.skill_adv["perception"] += 1

    def take_turn(self, encounter: Encounter):
        # Weapon attack
        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Beak and Claws")

            self.action = False
            self.beak_weapon(encounter.choose_target(self))
            self.claws_weapon(encounter.choose_target(self))


class Remorhaz(Creature):
    """Remorhaz from the Monster Manual p. 258."""

    def initialize_features(self):
        self.abilities = get_abilities(7, 1, 5, -3, 0, -3)
        self.base_armor_class = 16
        self.blindsight = True
        self.hit_die = d12
        self.immunities["cold"] = True
        self.immunities["fire"] = True
        self.proficiency = 4
        self.total_hit_dice = 17

        self.weapon = Weapon(
            self,
            Dice(d10, 6),
            "piercing",
            secondary_dice=Dice(d6, 3),
            secondary_type="fire",
        )

    def fall_unconscious(self):
        # Extend fall_unconscious() to release swallowed creatures
        super().fall_unconscious()

        for creature in self.swallowed_creatures[:]:
            creature.swallowed.end()

    def reset_conditions(self):
        # Extend reset_conditions() to reset swallowed creatures and damage
        # taken this turn for regurgitation
        super().reset_conditions()

        self.swallowed_creatures = []
        self.damage_taken_this_turn = 0

    def take_damage(
        self,
        primary_damage: int,
        primary_type: str,
        dealer: Creature | None = None,
        ranged: bool = False,
        secondary_damage: int = 0,
        secondary_type: str | None = None,
    ) -> tuple[int, int]:
        # Extend take_damage() to track damage taken from swallowed creatures
        # and apply damage from Heated Body

        primary_damage_taken, secondary_damage_taken = super().take_damage(
            primary_damage,
            primary_type,
            dealer=dealer,
            ranged=ranged,
            secondary_damage=secondary_damage,
            secondary_type=secondary_type,
        )

        if dealer in self.swallowed_creatures:
            self.damage_taken_this_turn += primary_damage_taken + secondary_damage_taken

        if dealer is not None and not ranged:
            dealer.take_damage(d6(3), "fire")

        return (primary_damage_taken, secondary_damage_taken)

    def take_turn(self, encounter: Encounter):
        # Deal acid damage to swallowed creatures, rolling once for all targets
        damage = d6(6)
        for creature in self.swallowed_creatures[:]:
            if creature.hp > 0:
                creature.take_damage(damage, "acid")

        # Stop grappling unconscious creatures
        for grapple in self.grappling[:]:
            if grapple.target.hp == 0:
                grapple.end()

        valid_targets = [
            enemy
            for enemy in encounter.get_foes(self)
            if (enemy.hp > 0 and not enemy.swallowed)
        ]

        if self.action and len(valid_targets) > 0:
            self.action = False

            # Swallow
            if len(self.grappling) > 0:
                if self.verbose:
                    print(f"{self()} used Swallow")

                target = self.grappling[0].target

                attack_result = self.weapon(target)

                if target.hp > 0 and (
                    attack_result == "hit" or attack_result == "crit"
                ):
                    for grapple in target.grappled[:]:
                        grapple.end()

                    swallowed_duration = SwallowedDuration(self, target, 30, 15)

            # Weapon attack
            else:
                if self.verbose:
                    print(f"{self()} made an attack with Bite")

                target = encounter.choice(valid_targets)
                attack_result = self.weapon(target)

                # Grapple target if Bite hits
                if (
                    target.hp > 0
                    and len(self.grappling) == 0
                    and (attack_result == "hit" or attack_result == "crit")
                ):
                    grapple_duration = GrappleDuration(self, target, restrained=True)


class ShadowDemon(Creature):
    """Shadow Demon from the Monster Manual p. 64."""

    def initialize_features(self):
        self.abilities = get_abilities(-5, 3, 1, 2, 1, 2)
        self.base_armor_class = 10
        self.hit_die = d8
        self.immunities["cold"] = True
        self.immunities["lightning"] = True
        self.immunities["poison"] = True
        self.proficiency = 2
        self.resistances["acid"] = True
        self.resistances["bludgeoning"] = True
        self.resistances["fire"] = True
        self.resistances["necrotic"] = True
        self.resistances["piercing"] = True
        self.resistances["slashing"] = True
        self.resistances["thunder"] = True
        self.save_proficiencies["dex"] = True
        self.save_proficiencies["cha"] = True
        self.skill_modifiers["stealth"] = self.proficiency
        self.skill_proficiencies["stealth"] = True
        self.total_hit_dice = 12
        self.vulnerabilities["radiant"] = True

        self.weapon = Weapon(self, Dice(d6, 2), "psychic", ability="dex")
        self.adv_weapon = Weapon(self, Dice(d6, 4), "psychic", ability="dex")

    def take_turn(self, encounter: Encounter):
        # Weapon attack
        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Claws")

            self.action = False
            target = encounter.choose_target(self)

            if self.has_attack_adv(target, read_only=True):
                self.adv_weapon(target)
            else:
                self.weapon(target)

            self.stealth = 0

        # Bonus action to hide from Shadow Stealth
        if self.bonus:
            self.bonus = False
            self.stealth = self.roll_skill("stealth")

            if self.verbose:
                print(f"{self()} used Hide and rolled {self.stealth:d} on Stealth")


class ShamblingMoundEngulfedDuration(EngulfedDuration):
    """
    Class for the Shambling Mound's engulfed condition that also blinds the
    target and can be escaped by breaking a grapple.
    """

    def __init__(self, engulfer: Creature, target: Creature, save_dc: int):
        # Extend constructor to apply the blinded condition
        super().__init__(engulfer, target, save_dc)
        target.blinded += 1

    def end(self):
        # Extend end() to remove the blinded condition
        self.target.blinded -= 1
        super().end()

    def start_turn_effect(self):
        # The target uses its action to attempt to escape the grapple
        if self.target.action:
            self.target.action = False

            if self.target.escape_grapple() >= self.save_dc:
                self.end()


class ShamblingMound(Creature):
    """Shambling Mound from the Monster Manual p. 270."""

    def initialize_features(self):
        self.abilities = get_abilities(4, -1, 3, -3, 0, -3)
        self.base_armor_class = 16
        self.blindsight = True
        self.hit_die = d10
        self.immunities["lightning"]
        self.proficiency = 3
        self.resistances["cold"]
        self.resistances["fire"]
        self.total_hit_dice = 16

        self.weapon = Weapon(self, Dice(d8, 2), "bludgeoning")

    def fall_unconscious(self):
        # Extend fall_unconscious() to release engulfed creatures
        super().fall_unconscious()

        for creature in self.engulfed_creatures[:]:
            creature.engulfed.end()

    def reset_conditions(self):
        # Extend reset_conditions() to reset engulfed creature
        super().reset_conditions()
        self.engulfed_creatures = list()

    def take_damage(
        self,
        primary_damage: int,
        primary_type: str,
        dealer: Creature | None = None,
        ranged: bool = False,
        secondary_damage: int = 0,
        secondary_type: str | None = None,
    ) -> tuple[int, int]:
        # Extend take_damage() to heal from lightning damage
        if primary_type == "lightning":
            self.heal(primary_damage)

            if secondary_type is not None:
                return super().take_damage(
                    secondary_damage,
                    secondary_type,
                    dealer=dealer,
                )

        elif secondary_type == "lightning":
            self.heal(secondary_damage)
            return super().take_damage(primary_damage, primary_type, dealer=dealer)

        else:
            return super().take_damage(
                primary_damage,
                primary_type,
                dealer=dealer,
                ranged=ranged,
                secondary_damage=secondary_damage,
                secondary_type=secondary_type,
            )

    def take_turn(self, encounter: Encounter):
        for creature in self.engulfed_creatures[:]:
            if creature.hp == 0:
                creature.engulfed.end()

        for creature in self.engulfed_creatures[:]:
            if not creature.saving_throw(
                "con",
                8 + self.proficiency + self.abilities["con"],
            ):
                creature.take_damage(
                    d8(2) + self.abilities["str"],
                    "bludgeoning",
                )

                if creature.hp == 0:
                    creature.engulfed.end()

        valid_targets = [
            enemy
            for enemy in encounter.get_foes(self)
            if (enemy.hp > 0 and not enemy.engulfed)
        ]

        # Weapon attack
        if self.action:
            self.action = False

            if self.verbose:
                print(f"{self()} made an attack with Slam")

            if len(valid_targets) > 0:
                target = encounter.choice(valid_targets)
                attack_result = self.weapon(target)
                attack_result_2 = self.weapon(target)

                # Engulf if both attacks hit
                if (attack_result == "hit" or attack_result == "crit") and (
                    attack_result_2 == "hit" or attack_result_2 == "crit"
                ):
                    if self.verbose:
                        print(f"{self()} used Engulf")

                    engulf_duration = ShamblingMoundEngulfedDuration(
                        self,
                        target,
                        8 + self.proficiency + self.abilities["con"],
                    )

            else:
                self.weapon(encounter.choose_target(self))
                self.weapon(encounter.choose_target(self))


class ShieldGuardian(Creature):
    """Shield Guardian from the Monster Manual p. 271."""

    def initialize_features(self):
        self.abilities = get_abilities(4, -1, 4, -2, 0, -4)
        self.base_armor_class = 18
        self.blindsight = True
        self.construct = True
        self.hit_die = d10
        self.immunities["poison"] = True
        self.level = 7
        self.proficiency = 3
        self.save_dc = lambda: 15
        self.total_hit_dice = 15

        self.weapon = Weapon(self, Dice(d6, 2), "bludgeoning")

        # Stored spell
        self.cast_fireball = spells.Fireball(self)

    def reset_conditions(self):
        # Extend reset_conditions() to recover spell slot
        super().reset_conditions()
        self.N_spell_slots = [0, 0, 0, 1]

    def start_turn(self, encounter: Encounter):
        # Extend start_turn() to recover hit points
        self.heal(10)
        super().start_turn(encounter)

    def take_turn(self, encounter: Encounter):
        if self.action:
            self.action = False

            # Cast fireball
            if (
                self.N_spell_slots[3] > 0
                and len([enemy for enemy in encounter.get_foes(self) if enemy.hp > 0])
                > 1
            ):
                self.cast_fireball(
                    slot=4,
                    targets=encounter.choose_target(self, N_targets=2),
                )

            # Weapon attack
            else:
                if self.verbose:
                    print(f"{self()} made an attack with Fist")

                self.weapon(encounter.choose_target(self))
                self.weapon(encounter.choose_target(self))


class Specter(Creature):
    """Specter from the Monster Manual p. 279."""

    def initialize_features(self):
        self.abilities = get_abilities(-5, 2, 0, 0, 0, 0)
        self.base_armor_class = 10
        self.hit_die = d8
        self.resistances["acid"] = True
        self.resistances["bludgeoning"] = True
        self.resistances["cold"] = True
        self.resistances["fire"] = True
        self.resistances["lightning"] = True
        self.resistances["piercing"] = True
        self.resistances["slashing"] = True
        self.resistances["thunder"] = True
        self.immunities["necrotic"] = True
        self.immunities["poison"] = True
        self.proficiency = 2
        self.total_hit_dice = 5
        self.undead = 1

        self.weapon = Weapon(self, Dice(d6, 3), "necrotic", ability="dex")

    def take_turn(self, encounter: Encounter):
        # Weapon attack
        if self.action:
            self.action = False
            target = encounter.choose_target(self)

            target_current_hp = target.hp
            attack_result = self.weapon(target, add_ability=False)

            # Target must save against reduction in hit point maximum on a hit
            if (
                attack_result == "hit" or attack_result == "crit"
            ) and not target.saving_throw(
                "con",
                8 + self.proficiency + self.abilities["con"],
            ):
                target.total_hp -= target_current_hp - target.hp


class Spy(Creature):
    """Spy from the Monster Manual p. 349."""

    def initialize_features(self):
        self.abilities = get_abilities(0, 2, 0, 1, 2, 3)
        self.base_armor_class = 10
        self.hit_die = d8
        self.proficiency = 2
        self.skill_modifiers["perception"] = self.proficiency
        self.skill_proficiencies["deception"] = True
        self.skill_proficiencies["insight"] = True
        self.skill_proficiencies["investigation"] = True
        self.skill_proficiencies["perception"] = True
        self.skill_proficiencies["persuasion"] = True
        self.skill_proficiencies["sleight_of_hand"] = True
        self.skill_proficiencies["stealth"] = True
        self.total_hit_dice = 6

        self.weapon = Weapon(self, d6, "piercing", ability="dex")
        self.sneak_attack_weapon = Weapon(self, Dice(d6, 3), "piercing", ability="dex")

    def take_turn(self, encounter: Encounter):
        self.sneak_attack = True

        # Weapon attack
        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Shortsword")

            self.action = False
            self.weapon_attack(encounter)
            self.weapon_attack(encounter)

        # Bonus action to hide from Cunning Action
        if self.bonus:
            self.bonus = False
            self.stealth = self.roll_skill("stealth")

            if self.verbose:
                print(f"{self()} used Hide and rolled {self.stealth:d} on Stealth")

    def weapon_attack(self, encounter: Encounter):
        allies = encounter.get_allies(self)

        target = encounter.choose_target(self)

        if target is None:
            return

        if self.sneak_attack and (
            self.has_attack_adv(target, read_only=True)
            or (
                len(
                    [
                        ally
                        for ally in allies
                        if ally.hp > 0 and not ally.is_incapacitated()
                    ]
                )
                > 1
                and not self.has_attack_disadv(target, read_only=True)
            )
        ):
            attack_result = self.sneak_attack_weapon(target)

            if attack_result == "hit" or attack_result == "crit":
                self.sneak_attack = False

        else:
            self.weapon(target)

        self.stealth = 0


class StoneGolem(Creature):
    """Stone golem from the Monster Manual p. 170."""

    def initialize_features(self):
        self.abilities = get_abilities(6, -1, 5, -4, 0, -5)
        self.base_armor_class = 18
        self.construct = True
        self.hit_die = d10
        self.immunities["bludgeoning"] = True
        self.immunities["piercing"] = True
        self.immunities["poison"] = True
        self.immunities["psychic"] = True
        self.immunities["slashing"] = True
        self.magic_resistance = True
        self.proficiency = 4
        self.total_hit_dice = 17

        self.weapon = Weapon(self, Dice(d8, 3), "magic_bludgeoning")

    def reset_conditions(self):
        # Extend reset_conditions() to recover Slow action
        super().reset_conditions()
        self.slow = True

    def take_turn(self, encounter: Encounter):
        # Recover Slow action
        if not self.slow and rng.random() >= (2.0 / 3):
            self.slow = True

        if self.action:
            self.action = False

            valid_targets = [
                enemy
                for enemy in encounter.get_foes(self)
                if (enemy.hp > 0 and enemy.slowed == 0)
            ]

            # Slow
            if self.slow and len(valid_targets) > 0:
                self.slow = False

                if self.verbose:
                    print(f"{self()} used Slow")

                if len(valid_targets) <= 2:
                    slow_targets = valid_targets
                else:
                    slow_targets = encounter.choice(
                        valid_targets,
                        2,
                        replace=False,
                    )

                for target in slow_targets:
                    if not target.saving_throw(
                        "wis",
                        8 + self.proficiency + self.abilities["con"],
                        save_type="magic",
                    ):
                        slowed_duration = SlowedDuration(
                            self,
                            target,
                            8 + self.proficiency + self.abilities["con"],
                        )

            # Weapon attack
            else:
                if self.verbose:
                    print(f"{self()} made an attack with Fist")

                self.weapon(encounter.choose_target(self))
                self.weapon(encounter.choose_target(self))


class Thug(Creature):
    """Thug from the Monster Manual p. 350."""

    def initialize_features(self):
        self.abilities = get_abilities(2, 0, 2, 0, 0, 0)
        self.base_armor_class = 11
        self.hit_die = d8
        self.proficiency = 2
        self.skill_proficiencies["intimidation"] = True
        self.total_hit_dice = 5

        self.weapon = Weapon(self, d6, "bludgeoning")

    def take_turn(self, encounter: Encounter):
        # Weapon attack
        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Mace")

            self.action = False

            # Pack Tactics gives advantage if an ally is within 5 ft of target
            allies = encounter.get_allies(self)
            self.weapon(
                encounter.choose_target(self),
                adv=len([ally for ally in allies if ally.hp > 0]) > 1,
            )
            self.weapon(
                encounter.choose_target(self),
                adv=len([ally for ally in allies if ally.hp > 0]) > 1,
            )


class Troll(Creature):
    """Troll from the Monster Manual p. 291."""

    def initialize_features(self):
        self.abilities = get_abilities(4, 1, 5, -2, -1, -2)
        self.base_armor_class = 14
        self.hit_die = d10
        self.proficiency = 3
        self.skill_proficiencies["perception"] = True
        self.total_hit_dice = 8

        self.bite_weapon = Weapon(self, d6, "piercing")
        self.claw_weapon = Weapon(self, Dice(d6, 2), "slashing")

    def reset_conditions(self):
        # Extend reset_conditions() to give advantage on Perception checks and
        # reset regeneration
        super().reset_conditions()
        self.skill_adv["perception"] += 1
        self.regeneration = True

    def start_turn(self, encounter: Encounter):
        # Extend start_turn() to recover hit points if regeneration is active
        if self.regeneration:
            self.heal(10)

        self.regeneration = True

        super().start_turn(encounter)

    def take_damage(
        self,
        primary_damage: int,
        primary_type: str,
        dealer: Creature | None = None,
        ranged: bool = False,
        secondary_damage: int = 0,
        secondary_type: str | None = None,
    ) -> tuple[int, int]:
        # Extend take_damage() to disable regeneration from fire or acid damage

        primary_damage_taken, secondary_damage_taken = super().take_damage(
            primary_damage,
            primary_type,
            dealer=dealer,
            ranged=ranged,
            secondary_damage=secondary_damage,
            secondary_type=secondary_type,
        )

        if primary_damage_taken + secondary_damage_taken > 0 and (
            primary_type == "acid"
            or primary_type == "fire"
            or secondary_type == "acid"
            or secondary_type == "fire"
        ):
            self.regeneration = False

        return (primary_damage_taken, secondary_damage_taken)

    def take_turn(self, encounter: Encounter):
        # Weapon attack
        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Bite and Claws")

            self.action = False
            self.bite_weapon(encounter.choose_target(self))
            self.claw_weapon(encounter.choose_target(self))
            self.claw_weapon(encounter.choose_target(self))


class Veteran(Creature):
    """Veteran from the Monster Manual p. 350."""

    def initialize_features(self):
        self.abilities = get_abilities(3, 1, 2, 0, 0, 0)
        self.armor_type = "heavy"
        self.base_armor_class = 17
        self.hit_die = d8
        self.proficiency = 2
        self.skill_proficiencies["athletics"] = True
        self.skill_proficiencies["perception"] = True
        self.total_hit_dice = 9

        self.longsword_weapon = Weapon(self, d8, "slashing")
        self.shortsword_weapon = Weapon(self, d6, "piercing")

    def take_turn(self, encounter: Encounter):
        # Weapon attack
        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Longsword and Shortsword")

            self.action = False

            self.longsword_weapon(encounter.choose_target(self))
            self.longsword_weapon(encounter.choose_target(self))
            self.shortsword_weapon(encounter.choose_target(self))


class WhiteDragonWyrmling(Creature):
    """White dragon wyrmling from the Monster Manual p. 102."""

    def initialize_features(self):
        self.abilities = get_abilities(2, 0, 2, -3, 0, 0)
        self.base_armor_class = 16
        self.blindsight = True
        self.hit_die = d8
        self.immunities["cold"] = True
        self.proficiency = 2
        self.save_proficiencies["dex"] = True
        self.save_proficiencies["con"] = True
        self.save_proficiencies["wis"] = True
        self.save_proficiencies["cha"] = True
        self.skill_modifiers["perception"] = self.proficiency
        self.skill_proficiencies["perception"] = True
        self.skill_proficiencies["stealth"] = True
        self.total_hit_dice = 5

        self.weapon = Weapon(
            self,
            d10,
            "piercing",
            secondary_dice=d4,
            secondary_type="cold",
        )

    def reset_conditions(self):
        # Extend reset_conditions() to recover use of breath weapon
        super().reset_conditions()
        self.breath_weapon = True

    def take_turn(self, encounter: Encounter):
        # Recover breath weapon
        if not self.breath_weapon and rng.random() >= (2.0 / 3):
            self.breath_weapon = True

        if self.action:
            self.action = False

            # Cold Breath
            if self.breath_weapon:
                if self.verbose:
                    print(f"{self()} used Cold Breath")

                self.breath_weapon = False
                damage = d8(5)

                for target in encounter.choose_target(self, N_targets=2):
                    target.half_saving_throw(
                        "con",
                        8 + self.proficiency + self.abilities["con"],
                        damage,
                        "cold",
                    )

            # Weapon attack
            else:
                if self.verbose:
                    print(f"{self()} made an attack with Bite")

                self.weapon(encounter.choose_target(self))


class Wolf(Creature):
    """Wolf from the Monster Manual p. 341."""

    def initialize_features(self):
        self.abilities = get_abilities(1, 2, 1, -4, 1, -2)
        self.base_armor_class = 11
        self.hit_die = d8
        self.proficiency = 2
        self.skill_proficiencies["perception"] = True
        self.skill_proficiencies["stealth"] = True
        self.total_hit_dice = 2

        self.weapon = Weapon(self, Dice(d4, 2), "piercing")

    def reset_conditions(self):
        # Extend reset_conditions() to give advantage on Perception checks
        super().reset_conditions()
        self.skill_adv["perception"] += 1

    def take_turn(self, encounter: Encounter):
        # Weapon attack
        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Bite")

            self.action = False
            target = encounter.choose_target(self)

            # Pack Tactics gives advantage if an ally is within 5 ft of target
            allies = encounter.get_allies(self)
            attack_result = self.weapon(
                target,
                adv=len([ally for ally in allies if ally.hp > 0]) > 1,
            )

            # Attempt to knock target prone on a hit
            if (
                (attack_result == "hit" or attack_result == "crit")
                and target.hp > 0
                and not target.prone
                and not target.saving_throw(
                    "str",
                    8 + self.proficiency + self.abilities["str"],
                )
            ):
                target.prone = True


class Worg(Creature):
    """Worg from the Monster Manual p. 341."""

    def initialize_features(self):
        self.abilities = get_abilities(3, 1, 1, -2, 0, -1)
        self.base_armor_class = 12
        self.hit_die = d10
        self.proficiency = 2
        self.skill_modifiers["perception"] = self.proficiency
        self.skill_proficiencies["perception"] = True
        self.total_hit_dice = 4

        self.weapon = Weapon(self, Dice(d6, 2), "piercing")

    def reset_conditions(self):
        # Extend reset_conditions() to give advantage on Perception checks
        super().reset_conditions()
        self.skill_adv["perception"] += 1

    def take_turn(self, encounter: Encounter):
        # Weapon attack
        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Bite")

            self.action = False
            target = encounter.choose_target(self)
            attack_result = self.weapon(target)

            # Attempt to knock target prone on a hit
            if (
                (attack_result == "hit" or attack_result == "crit")
                and target.hp > 0
                and not target.prone
                and not target.saving_throw(
                    "str",
                    8 + self.proficiency + self.abilities["str"],
                )
            ):
                target.prone = True


class Wyvern(Creature):
    """Wyvern from the Monster Manual p. 303."""

    def initialize_features(self):
        self.abilities = get_abilities(4, 0, 3, -3, 1, -2)
        self.base_armor_class = 13
        self.hit_die = d10
        self.proficiency = 3
        self.skill_proficiencies["perception"] = True
        self.total_hit_dice = 13

        self.claws_weapon = Weapon(self, Dice(d8, 2), "slashing")
        self.stinger_weapon = Weapon(self, Dice(d6, 2), "piercing")

    def take_turn(self, encounter: Encounter):
        # Weapon attack
        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Claws and Stinger")

            self.action = False
            self.claws_weapon(encounter.choose_target(self))
            target = encounter.choose_target(self)
            attack_result = self.stinger_weapon(target)

            # Save against poison on a hit
            if (attack_result == "hit" or attack_result == "crit") and target.hp > 0:
                target.half_saving_throw(
                    "con",
                    8 + self.proficiency + self.abilities["str"],
                    d6(7),
                    "poison",
                )


class YoungBlackDragon(Creature):
    """Young black dragon from the Monster Manual p. 88."""

    def initialize_features(self):
        self.abilities = get_abilities(4, 2, 3, 1, 0, 2)
        self.base_armor_class = 16
        self.blindsight = True
        self.hit_die = d10
        self.immunities["acid"] = True
        self.proficiency = 3
        self.save_proficiencies["dex"] = True
        self.save_proficiencies["con"] = True
        self.save_proficiencies["wis"] = True
        self.save_proficiencies["cha"] = True
        self.skill_modifiers["perception"] = self.proficiency
        self.skill_proficiencies["perception"] = True
        self.skill_proficiencies["stealth"] = True
        self.total_hit_dice = 15

        self.bite_weapon = Weapon(
            self,
            Dice(d10, 2),
            "piercing",
            secondary_dice=d8,
            secondary_type="acid",
        )
        self.claw_weapon = Weapon(self, Dice(d6, 2), "slashing")

    def reset_conditions(self):
        # Extend reset_conditions() to recover use of breath weapon
        super().reset_conditions()
        self.breath_weapon = True

    def take_turn(self, encounter: Encounter):
        # Recover breath weapon
        if not self.breath_weapon and rng.random() >= (2.0 / 3):
            self.breath_weapon = True

        if self.action:
            self.action = False

            # Acid Breath
            if self.breath_weapon:
                if self.verbose:
                    print(f"{self()} used Acid Breath")

                self.breath_weapon = False
                damage = d8(11)

                for target in encounter.choose_target(self, N_targets=2):
                    target.half_saving_throw(
                        "dex",
                        8 + self.proficiency + self.abilities["con"],
                        damage,
                        "acid",
                    )

            # Weapon attack
            else:
                if self.verbose:
                    print(f"{self()} made an attack with Bite and Claw")

                self.bite_weapon(encounter.choose_target(self))
                self.claw_weapon(encounter.choose_target(self))
                self.claw_weapon(encounter.choose_target(self))


class YoungRedDragon(Creature):
    """Young red dragon from the Monster Manual p. 98."""

    def initialize_features(self):
        self.abilities = get_abilities(6, 0, 5, 2, 0, 4)
        self.base_armor_class = 18
        self.blindsight = True
        self.hit_die = d10
        self.immunities["fire"] = True
        self.proficiency = 4
        self.save_proficiencies["dex"] = True
        self.save_proficiencies["con"] = True
        self.save_proficiencies["wis"] = True
        self.save_proficiencies["cha"] = True
        self.skill_modifiers["perception"] = self.proficiency
        self.skill_proficiencies["perception"] = True
        self.skill_proficiencies["stealth"] = True
        self.total_hit_dice = 17

        self.bite_weapon = Weapon(
            self,
            Dice(d10, 2),
            "piercing",
            secondary_dice=d6,
            secondary_type="fire",
        )
        self.claw_weapon = Weapon(self, Dice(d6, 2), "slashing")

    def reset_conditions(self):
        # Extend reset_conditions() to recover use of breath weapon
        super().reset_conditions()
        self.breath_weapon = True

    def take_turn(self, encounter: Encounter):
        # Recover breath weapon
        if not self.breath_weapon and rng.random() >= (2.0 / 3):
            self.breath_weapon = True

        if self.action:
            self.action = False

            # Fire Breath
            if self.breath_weapon:
                if self.verbose:
                    print(f"{self()} used Fire Breath")

                self.breath_weapon = False
                damage = d6(16)

                for target in encounter.choose_target(self, N_targets=2):
                    target.half_saving_throw(
                        "dex",
                        8 + self.proficiency + self.abilities["con"],
                        damage,
                        "fire",
                    )

            # Weapon attack
            else:
                if self.verbose:
                    print(f"{self()} made an attack with Bite and Claw")

                self.bite_weapon(encounter.choose_target(self))
                self.claw_weapon(encounter.choose_target(self))
                self.claw_weapon(encounter.choose_target(self))


class Zombie(Creature):
    """Zombie from the Monster Manual p. 316."""

    def initialize_features(self):
        self.abilities = get_abilities(1, -2, 3, -4, -2, -3)
        self.base_armor_class = 10
        self.hit_die = d8
        self.immunities["poison"] = True
        self.proficiency = 2
        self.save_proficiencies["wis"] = True
        self.total_hit_dice = 3
        self.undead = 0.25

        self.weapon = Weapon(self, d6, "bludgeoning")

    def take_damage(
        self,
        primary_damage: int,
        primary_type: str,
        dealer: Creature | None = None,
        ranged: bool = False,
        secondary_damage: int = 0,
        secondary_type: str | None = None,
    ) -> tuple[int, int]:
        # Extend take_damage() to use Undead Fortitude
        primary_damage_taken, secondary_damage_taken = super().take_damage(
            primary_damage,
            primary_type,
            dealer=dealer,
            ranged=ranged,
            secondary_damage=secondary_damage,
            secondary_type=secondary_type,
        )

        if (
            self.hp == 0
            and not (primary_type == "radiant" or secondary_type == "radiant")
            and self.saving_throw(
                "con",
                5 + primary_damage_taken + secondary_damage_taken,
            )
        ):
            self.hp = 1
            self.prone = False

        return (primary_damage_taken, secondary_damage_taken)

    def take_turn(self, encounter: Encounter):
        # Weapon attack
        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Slam")

            self.action = False
            self.weapon(encounter.choose_target(self))


mm_creatures = {
    "Hawk": Hawk,
    "Jackal": Jackal,
    "Myconid sprout": MyconidSprout,
    "Bandit": Bandit,
    "Camel": Camel,
    "Giant rat": GiantRat,
    "Kobold": Kobold,
    "Giant bat": GiantBat,
    "Giant centipede": GiantCentipede,
    "Goblin": Goblin,
    "Wolf": Wolf,
    "Zombie": Zombie,
    "Gnoll": Gnoll,
    "Hobgoblin": Hobgoblin,
    "Orc": Orc,
    "Thug": Thug,
    "Worg": Worg,
    "Bugbear": Bugbear,
    "Ghoul": Ghoul,
    "Giant spider": GiantSpider,
    "Specter": Specter,
    "Spy": Spy,
    "Gelatinous cube": GelatinousCube,
    "Merrow": Merrow,
    "Nothic": Nothic,
    "Ogre": Ogre,
    "White dragon wyrmling": WhiteDragonWyrmling,
    "Displacer beast": DisplacerBeast,
    "Giant scorpion": GiantScorpion,
    "Hell hound": HellHound,
    "Owlbear": Owlbear,
    "Veteran": Veteran,
    "Banshee": Banshee,
    "Chuul": Chuul,
    "Ettin": Ettin,
    "Lizard queen": LizardQueen,
    "Shadow demon": ShadowDemon,
    "Bulette": Bulette,
    "Earth elemental": EarthElemental,
    "Shambling mound": ShamblingMound,
    "Troll": Troll,
    "Chimera": Chimera,
    "Invisible stalker": InvisibleStalker,
    "Mage": Mage,
    "Wyvern": Wyvern,
    "Mind flayer": MindFlayer,
    "Shield guardian": ShieldGuardian,
    "Young black dragon": YoungBlackDragon,
    "Chain devil": ChainDevil,
    "Frost giant": FrostGiant,
    "Hydra": Hydra,
    "Abominable Yeti": AbominableYeti,
    "Bone devil": BoneDevil,
    "Fire giant": FireGiant,
    "Aboleth": Aboleth,
    "Stone golem": StoneGolem,
    "Young red dragon": YoungRedDragon,
    "Behir": Behir,
    "Remorhaz": Remorhaz,
}
