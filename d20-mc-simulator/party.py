"""
    Implements Python classes for specific player characters.
"""

import numpy

import spells
from adventuring_day import Encounter
from classes import Cleric, Fighter, Rogue, Wizard
from creature import Creature, Weapon, get_abilities
from dice_roller import Dice, ExtraWeaponDice, d6, d8, rng, twod6_reroll_1_2
from duration import TurnUndeadDuration


class LifeDomain(Cleric):
    """
    Python class for a specific Life Domain Cleric.
    Variant human.
    Str 14 Dex 8 Con 14 Int 10 Wis 16 Cha 12.
    Level 1: War Caster feat, Acolyte background, proficiency in Medicine and
    Persuasion skills, Life Domain, obtain chain mail, shield, and mace.
    Level 4: Str +2.
    Level 5: obtain plate armor.
    Level 6: obtain +1 mace.
    Level 8: Wis +2.
    Level 11: obtain Major Uncommon.
    Level 12: Con +2.
    Level 14: obtain Major Rare.
    Level 16: Wis +2, obtain Major Very Rare.
    Level 18: obtain Major Legendary.
    Level 19: Con +2.
    """

    def end_encounter(self, encounter: Encounter):
        # Use Preserve Life if there are extra uses of Channel Divinity
        allies = encounter.get_allies(self)

        if (
            self.N_channel_divinity
            > self.channel_divinity_usage[encounter.encounters_since_short_rest]
        ):
            self.use_preserve_life(allies)

        # Heal unconscious allies with a healing spell
        unconscious_allies = [pc for pc in allies if (pc.hp == 0 and pc.total_hp > 0)]
        N_unconscious_allies = len(unconscious_allies)

        if N_unconscious_allies > 0:
            lowest_slots = self.lowest_spell_slots()

            # Cast Cure Wounds on each unconscious ally using lowest spell slot
            if numpy.sum(self.N_spell_slots) >= N_unconscious_allies:
                for character in unconscious_allies:
                    slot = 0
                    while self.N_spell_slots[slot] == 0:
                        slot += 1

                    self.cast_cure_wounds(slot=slot + 1, targets=character)

            # Cast Prayer of Healing using lowest spell slot
            elif lowest_slots[1] is not None:
                valid_targets = [
                    pc for pc in allies if (pc.hp != pc.total_hp and pc.total_hp > 0)
                ]

                if len(valid_targets) <= 6:
                    targets = valid_targets
                elif N_unconscious_allies >= 6:
                    targets = encounter.choice(unconscious_allies, 6, replace=False)
                else:
                    targets = unconscious_allies
                    targets.extend(
                        encounter.choice(
                            [pc for pc in valid_targets if pc.hp > 0],
                            6 - N_unconscious_allies,
                            replace=False,
                        )
                    )

                self.cast_prayer_of_healing(slot=lowest_slots[1], targets=targets)

            # Cast Cure Wounds on as many unconscious allies as possible
            elif lowest_slots[0] is not None:
                for character in encounter.choice(
                    unconscious_allies,
                    self.N_spell_slots[0],
                    replace=False,
                ):
                    self.cast_cure_wounds(targets=character)

    def initialize_features(self):
        # Abilities
        self.base_abilities = get_abilities(2, -1, 2, 0, 3, 1)
        if self.level >= 4:
            self.base_abilities["str"] += 1
        if self.level >= 8:
            self.base_abilities["wis"] += 1
        if self.level >= 12:
            self.base_abilities["con"] += 1
        if self.level >= 16:
            self.base_abilities["wis"] += 1
        if self.level >= 19:
            self.base_abilities["con"] += 1

        self.abilities = {k: self.base_abilities[k] for k in self.base_abilities}

        # Armor class
        self.armor_type = "heavy"
        if self.level >= 5:
            self.base_armor_class = 20
        else:
            self.base_armor_class = 18

        # Acolyte background and skill proficiencies
        self.skill_proficiencies["insight"] = True
        self.skill_proficiencies["medicine"] = True
        self.skill_proficiencies["persuasion"] = True
        self.skill_proficiencies["religion"] = True

        # War Caster feat
        self.war_caster = True

        # Life Domain features
        self.disciple_of_life = True
        self.blessed_healer = self.level >= 6
        self.supreme_healing = self.level >= 17

        # Mace with divine strike
        if self.level >= 14:
            self.weapon = Weapon(
                self,
                d6,
                "magic_bludgeoning",
                secondary_dice=Dice(d8, 2),
                secondary_type="radiant",
                attack_modifier=1,
                damage_modifier=1,
            )

        elif self.level >= 8:
            self.weapon = Weapon(
                self,
                d6,
                "magic_bludgeoning",
                secondary_dice=d8,
                secondary_type="radiant",
                attack_modifier=1,
                damage_modifier=1,
            )

        # +1 mace
        elif self.level >= 6:
            self.weapon = Weapon(
                self,
                d6,
                "magic_bludgeoning",
                attack_modifier=1,
                damage_modifier=1,
            )

        # Mace
        else:
            self.weapon = Weapon(self, d6, "bludgeoning")

        # Domain spells
        self.cast_bless = spells.Bless(self)
        self.cast_cure_wounds = spells.CureWounds(self)

        if self.level >= 3:
            self.cast_lesser_restoration = spells.LesserRestoration(self)
            self.cast_spiritual_weapon = spells.SpiritualWeapon(self)

        # Cantrips
        self.cast_sacred_flame = spells.SacredFlame(self)

        # Prepared spells. Number of spells is cleric level plus Wisdom
        # modifier. At level 7, assume that Death Ward has been prepared and
        # cast after a long rest.
        self.cast_guiding_bolt = spells.GuidingBolt(self)
        self.cast_healing_word = spells.HealingWord(self)

        if self.level >= 3:
            self.cast_aid = spells.Aid(self)
            self.cast_prayer_of_healing = spells.PrayerOfHealing(self)

        if self.level >= 5:
            self.cast_mass_healing_word = spells.MassHealingWord(self)
            self.cast_spirit_guardians = spells.SpiritGuardians(self)

    def reset_conditions(self):
        # Extend reset_conditions() to impose disadvantage on stealth checks for
        # heavy armor and remove spiritual weapon.
        super().reset_conditions()
        self.skill_disadv["stealth"] += 1
        self.spiritual_weapon = None

    def reset_long_rest_features(self):
        # Extend reset_long_rest_conditions() to cast Death Ward
        super().reset_long_rest_features()

        if self.level >= 7:
            self.N_spell_slots[3] -= 1
            self.death_ward = True

    def set_usage_rates(
        self,
        encounters_per_long_rest: int,
        encounters_per_short_rest: int,
    ):
        # Expected number of spell slots remaining per encounter. Expect to
        # consume int(sum_spell_slots / encounters_per_long_rest) per encounter,
        # with the remainder consumed in later encounters. For example, with 14
        # total spell slots and 6 encounters per long rest, the expected usage
        # per encounter is [2, 2, 2, 2, 3, 3]. The remaining spell slots are
        # [12, 10, 8, 6, 3, 0]. Reduce the total number of spell slots by 1 for
        # Death Ward when available.
        sum_spell_slots = numpy.sum(self.total_spell_slots)

        if self.level >= 7:
            sum_spell_slots -= 1

        self.spell_slot_usage = sum_spell_slots - numpy.cumsum(
            [
                int(sum_spell_slots / encounters_per_long_rest)
                + (
                    encounters_per_long_rest - i
                    <= sum_spell_slots % encounters_per_long_rest
                )
                for i in range(encounters_per_long_rest)
            ]
        )

        # Expected number of uses of Channel Divinity remaining per encounter.
        # Expect to consume
        # int(total_channel_divinity / encounters_per_short_rest) uses per
        # encounter, with the remainder consumed in later encounters. For
        # example, with 3 total uses of Channel Divinity and 2 encounters per
        # short rest, the expected usage per encounter is [1, 2]. The remaining
        # uses of Channel Divininty are [2, 0].
        self.channel_divinity_usage = self.total_channel_divinity - numpy.cumsum(
            [
                int(self.total_channel_divinity / encounters_per_short_rest)
                + (
                    encounters_per_short_rest - i
                    <= self.total_channel_divinity % encounters_per_short_rest
                )
                for i in range(encounters_per_short_rest)
            ]
        )

    def take_turn(self, encounter: Encounter):
        allies = encounter.get_allies(self)
        opponents = encounter.get_foes(self)

        unconscious_allies = [
            pc
            for pc in allies
            if (pc.hp == 0 and pc.total_hp > 0 and pc.swallowed == None)
        ]
        N_unconscious_allies = len(unconscious_allies)
        immune_force = numpy.any([enemy.immunities["force"] for enemy in opponents])
        immune_radiant = numpy.any([enemy.immunities["radiant"] for enemy in opponents])
        undead_opponents = [
            enemy for enemy in opponents if (enemy.undead is not None and enemy.hp > 0)
        ]
        lowest_slots = self.lowest_spell_slots()

        # Cast Mass Healing Word if more than one ally is unconscious
        if (
            N_unconscious_allies > 1
            and lowest_slots[2] is not None
            and self.bonus
            and self.blinded == 0
        ):
            self.bonus = False

            if self.slowed > 0:
                self.action = False

            valid_targets = [
                pc
                for pc in allies
                if (pc.hp != pc.total_hp and pc.total_hp > 0 and pc.swallowed == None)
            ]

            if len(valid_targets) <= 6:
                targets = valid_targets
            elif N_unconscious_allies >= 6:
                targets = encounter.choice(unconscious_allies, 6, replace=False)
            else:
                targets = unconscious_allies
                targets.extend(
                    encounter.choice(
                        [pc for pc in valid_targets if pc.hp > 0],
                        6 - N_unconscious_allies,
                        replace=False,
                    )
                )

            self.cast_mass_healing_word(slot=lowest_slots[2], targets=targets)

        # Cast Aid if more than one ally is unconscious
        elif (
            len([pc for pc in unconscious_allies if not pc.aid]) > 1
            and lowest_slots[1] is not None
            and self.action
        ):
            self.action = False

            if self.slowed > 0:
                self.bonus = False

            valid_targets = [
                pc
                for pc in allies
                if (not pc.aid and pc.total_hp > 0 and pc.swallowed == None)
            ]
            valid_unconscious_targets = [pc for pc in unconscious_allies if not pc.aid]
            N_valid_unconscious_targets = len(valid_unconscious_targets)

            if len(valid_targets) <= 3:
                targets = valid_targets
            elif N_valid_unconscious_targets >= 3:
                targets = encounter.choice(valid_unconscious_targets, 3, replace=False)
            else:
                targets = valid_unconscious_targets
                targets.extend(
                    encounter.choice(
                        [pc for pc in valid_targets if pc.hp > 0],
                        3 - N_valid_unconscious_targets,
                        replace=False,
                    )
                )

            self.cast_aid(slot=lowest_slots[1], targets=targets)

        # Cast Healing Word as a bonus action if any allies are unconscious
        elif (
            N_unconscious_allies > 0
            and lowest_slots[0] is not None
            and self.bonus
            and self.blinded == 0
        ):
            self.bonus = False

            if self.slowed > 0:
                self.action = False

            self.cast_healing_word(
                slot=lowest_slots[0], targets=encounter.choice(unconscious_allies)
            )

        # Cast Healing Word on self if below one-quarter health
        elif (
            self.hp <= int(self.total_hp / 4)
            and lowest_slots[0] is not None
            and self.bonus
            and self.blinded == 0
        ):
            self.bonus = False

            if self.slowed > 0:
                self.action = False

            self.cast_healing_word(slot=lowest_slots[0], targets=self)

        # Use Turn Undead
        elif (
            len(undead_opponents) > 1
            and self.action
            and self.swallowed is None
            and self.N_channel_divinity
            > self.channel_divinity_usage[encounter.encounters_since_short_rest]
        ):
            self.action = False

            if self.slowed > 0:
                self.bonus = False

            if self.verbose:
                print(f"{self()} used Turn Undead")

            self.N_channel_divinity -= 1

            if len(undead_opponents) <= 2:
                targets = undead_opponents
            else:
                targets = encounter.choice(undead_opponents, 2, replace=False)

            for target in targets:
                if not target.saving_throw(
                    "wis",
                    self.save_dc(),
                    save_type="turn_undead",
                ):
                    if target.undead <= self.destroy_undead:
                        target.total_hp = 0
                        target.hp = 0
                        target.fall_unconscious()

                    else:
                        turn_undead_duration = TurnUndeadDuration(self, target)

        # Cast a prepared spell if there are more spell slots than the expected
        # usage rate based on the number of encounters since a long rest
        elif (
            numpy.sum(self.N_spell_slots)
            > self.spell_slot_usage[encounter.encounters_since_long_rest]
        ):
            valid_spirit_guardian_targets = [
                enemy
                for enemy in opponents
                if (len(enemy.spirit_guardians) == 0 and enemy.hp > 0)
            ]

            # Cast Spirit Guardians if not concentrating on another spell
            if (
                lowest_slots[2] is not None
                and self.concentration is None
                and not immune_radiant
                and self.action
                and self.blinded == 0
                and len(valid_spirit_guardian_targets) > 1
            ):
                self.action = False

                if self.slowed > 0:
                    self.bonus = False

                if len(valid_spirit_guardian_targets) <= 2:
                    targets = valid_spirit_guardian_targets
                else:
                    targets = encounter.choice(
                        valid_spirit_guardian_targets,
                        2,
                        replace=False,
                    )

                self.cast_spirit_guardians(slot=lowest_slots[2], targets=targets)

            # Cast Spiritual Weapon if not already active
            elif (
                lowest_slots[1] is not None
                and self.spiritual_weapon is None
                and not immune_force
                and self.bonus
            ):
                self.bonus = False

                if self.slowed > 0:
                    self.action = False

                self.cast_spiritual_weapon(slot=lowest_slots[1])
                self.spiritual_weapon.spell_weapon(encounter.choose_target(self))

            # Cast Bless if not concentrating on another spell and allies are
            # not already blessed. If swallowed, attack instead.
            elif (
                lowest_slots[0] == 1
                and self.concentration is None
                and self.action
                and self.swallowed is None
                and len([pc for pc in allies if not pc.blessed]) >= 3
            ):
                self.action = False

                if self.slowed > 0:
                    self.bonus = False

                valid_targets = [pc for pc in allies if not pc.blessed]

                if len(valid_targets) <= 3:
                    targets = valid_targets
                else:
                    targets = encounter.choice(valid_targets, 3, replace=False)

                self.cast_bless(targets=targets)

            # Cast Guiding Bolt
            elif self.action and not immune_radiant:
                self.action = False

                if self.slowed > 0:
                    self.bonus = False

                self.cast_guiding_bolt(
                    slot=lowest_slots[0],
                    targets=encounter.choose_target(self),
                )

        # If Spiritual Weapon is active, make an attack
        if self.bonus and self.spiritual_weapon is not None and self.hp > 0:
            if self.verbose:
                print(f"{self()} made an attack with Spiritual Weapon")

            self.bonus = False

            if self.slowed > 0:
                self.action = False

            self.spiritual_weapon.spell_weapon(encounter.choose_target(self))

        # If there is an action remaining, make a weapon attack or use the
        # Sacred Flame cantrip
        if self.action and self.hp > 0:
            self.action = False

            if self.slowed > 0:
                self.bonus = False

            target = encounter.choose_target(self)
            if target is None:
                return

            # Weapon attack if target is immune to radiant damage or is hidden
            # or if blinded or swallowed. Otherwise, choose randomly between
            # weapon attack and Sacred Flame
            if (
                immune_radiant
                or target.is_hidden(self)
                or self.blinded > 0
                or self.swallowed is not None
                or rng.random() < 0.5
            ):
                if self.verbose:
                    print(f"{self()} made an attack with Mace")

                self.weapon(target)

            else:
                self.cast_sacred_flame(targets=target)

    def use_preserve_life(self, allies: list[Creature]):
        """
        Use Channel Divinity: Preserve Life to heal allies.

        Parameters
        ----------
        allies
            List of Creatures on the same side of an encounter.
        """

        if self.verbose:
            print(f"{self()} used Preserve Life")

        self.N_channel_divinity -= 1
        healing = numpy.zeros(len(allies))
        healing_threshold = [int(pc.total_hp / 2) for pc in allies]

        # Allies at half hit points or less sorted by current hit points
        valid_targets = [
            i
            for i in numpy.argsort([pc.hp for pc in allies])
            if (allies[i].hp <= healing_threshold[i] and allies[i].total_hp > 0)
        ]

        # Distribute healing starting with allies having fewest hit points
        for i in range(5 * self.level):
            N_valid_targets = len(valid_targets)

            if N_valid_targets == 0:
                break

            # Index within valid_targets of ally with lowest hp
            min_hp_index = numpy.argmin([allies[k].hp for k in valid_targets])

            # Index within allies of ally with lowest hp
            min_hp_ally = valid_targets[min_hp_index]
            healing[min_hp_ally] += 1

            if (
                allies[min_hp_ally].hp + healing[min_hp_ally]
                >= healing_threshold[min_hp_ally]
            ):
                del valid_targets[min_hp_index]

        # Apply healing
        for i in range(len(allies)):
            if healing[i] > 0:
                allies[i].heal(healing[i], magic=True)


class Champion(Fighter):
    """
    Python class for a specific Champion fighter.
    Mountain dwarf.
    Str 17 Dex 13 Con 16 Int 8 Wis 12 Cha 10.
    Level 1: Soldier background, proficiency in Acrobatics and Perception skills,
        Great Weapon Fighting fighting style, obtain chain mail and greatsword.
    Level 3: Champion archetype, obtain splint armor.
    Level 4: Heavy Armor Master feat.
    Level 5: Obtain plate armor.
    Level 6: Con +2, obtain +1 greatsword.
    Level 8: Str +2.
    Level 10: Defense fighting style.
    Level 11: obtain Major Uncommon.
    Level 12: Great Weapon Master feat.
    Level 14: Con +2, obtain Major Rare.
    Level 16: Resilient (Dex) feat, obtain Major Very Rare.
    Level 18: obtain Major Legendary.
    Level 19: Tough feat.
    """

    def get_total_hp(self):
        # Override get_total_hp() to use Tough feat
        return super().get_total_hp() + (self.level >= 19) * 2 * self.level

    def initialize_features(self):
        # Abilities
        self.base_abilities = get_abilities(3, 1, 3, -1, 1, 0)
        if self.level >= 4:
            self.base_abilities["str"] += 1
        if self.level >= 6:
            self.base_abilities["con"] += 1
        if self.level >= 8:
            self.base_abilities["str"] += 1
        if self.level >= 14:
            self.base_abilities["con"] += 1
        if self.level >= 16:
            self.base_abilities["dex"] += 1

        self.abilities = {k: self.base_abilities[k] for k in self.base_abilities}

        # Armor class
        self.armor_type = "heavy"
        if self.level >= 10:
            self.base_armor_class = 19
        elif self.level >= 5:
            self.base_armor_class = 18
        elif self.level >= 3:
            self.base_armor_class = 17
        else:
            self.base_armor_class = 16

        # Mountain dwarf racial features
        self.resistances["poison"] = True
        self.poison_adv = True

        # Soldier background and skill proficiencies
        self.skill_proficiencies["acrobatics"] = True
        self.skill_proficiencies["athletics"] = True
        self.skill_proficiencies["intimidation"] = True
        self.skill_proficiencies["perception"] = True

        # Set threshold for critical hits from Champion archetype
        if self.level >= 15:
            self.crit_threshold = 18
        elif self.level >= 3:
            self.crit_threshold = 19

        # Half proficiency to Str, Dex, and Con checks from Remarkable Athlete
        if self.level >= 7:

            self.skill_modifiers["sleight_of_hand"] += int(self.proficiency / 2)
            self.skill_modifiers["stealth"] += int(self.proficiency / 2)

        # Heavy Armor Master feat
        self.heavy_armor_master = self.level >= 4

        # Great Weapon Master feat
        self.great_weapon_master = self.level >= 12

        # Resilient feat
        self.save_proficiencies["dex"] = self.level >= 16

        # +1 greatsword
        if self.level >= 6:
            self.weapon = Weapon(
                self,
                twod6_reroll_1_2,
                "magic_slashing",
                attack_modifier=1,
                damage_modifier=1,
            )

        # Greatsword
        else:
            self.weapon = Weapon(self, twod6_reroll_1_2, "slashing")

    def reset_conditions(self):
        # Extend reset_conditions() to impose disadvantage on stealth checks for
        # heavy armor
        super().reset_conditions()
        self.skill_disadv["stealth"] += 1

    def set_usage_rates(
        self,
        encounters_per_long_rest: int,
        encounters_per_short_rest: int,
    ):
        # Expected number of uses of Action Surge remaining per encounter.
        # Expect to consume int(total_action_surge / encounters_per_short_rest)
        # uses per encounter, with the remainder consumed in earlier encounters.
        # For example, with 1 use of Action Surge and 2 encounters per short
        # rest, the expected usage per encounter is [1, 0]. The remaining uses
        # of Action Surge are [0, 0].
        self.action_surge_usage = self.total_action_surge - numpy.cumsum(
            [
                int(self.total_action_surge / encounters_per_short_rest)
                + (i < self.total_action_surge % encounters_per_short_rest)
                for i in range(encounters_per_short_rest)
            ]
        )

    def take_turn(self, encounter: Encounter):
        # Threshold to use second wind is half of total hit points or the
        # maximum value of a roll, whichever is smaller
        second_wind_threshold = self.total_hp - min(
            int(self.total_hp / 2), self.hit_die.sides + self.level
        )

        # Use second wind if current hit points are below the threshold
        if (
            self.second_wind
            and self.bonus
            and self.slowed == 0
            and self.hp <= second_wind_threshold
        ):
            self.use_second_wind()

        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Greatsword")

            self.action = False

            # Weapon attacks
            if self.slowed > 0:
                self.bonus = False
                self.weapon_attack(encounter)

            else:
                for i in range(self.N_attacks):
                    if self.hp > 0:
                        self.weapon_attack(encounter)

        # Use Action Surge if there are more uses than the expected usage rate
        # based on the number of encounters since a short rest
        if (
            self.N_action_surge > 0
            and self.slowed == 0
            and self.hp > 0
            and self.N_action_surge
            > self.action_surge_usage[encounter.encounters_since_short_rest]
            and len([enemy for enemy in encounter.get_foes(self) if enemy.hp > 0]) > 0
        ):
            if self.verbose:
                print(f"{self()} used Action Surge")
                print(f"{self()} made an attack with Greatsword")

            self.N_action_surge -= 1

            # Take priority action from duration effects
            if self.action and len(self.action_priority) > 0:
                action_priorities = [
                    self.PRIORITY_ACTIONS[effect.priority]
                    for effect in self.action_priority
                ]
                highest_priority = numpy.argmax(action_priorities)
                self.action_priority[highest_priority].take_priority_action()

            # Weapon attacks
            else:
                for i in range(self.N_attacks):
                    if self.hp > 0:
                        self.weapon_attack(encounter)

    def weapon_attack(self, encounter: Encounter):
        """
        Weapon attack that can use the Great Weapon Master feat.

        Parameters
        ----------
        encounter
            The Encounter in which the attack takes place.
        """

        # Choose target from encounter
        target = encounter.choose_target(self)

        if target is None:
            return

        # Use Great Weapon Master damage bonus unless the attack has
        # disadvantage without advantage
        if self.great_weapon_master and not (
            self.has_attack_disadv(target, read_only=True)
            and not self.has_attack_adv(target, read_only=True)
        ):
            attack_result = self.weapon(target, great_weapon_master=True)

        else:
            attack_result = self.weapon(target)

        # Use Great Weapon Master bonus action
        if (
            self.great_weapon_master
            and self.bonus
            and (attack_result == "crit" or (attack_result == "hit" and target.hp == 0))
        ):
            if self.verbose:
                print(f"{self()} used Great Weapon Master to attack with Greatsword")

            self.bonus = False
            self.weapon_attack(target)


class Assassin(Rogue):
    """
    Python class for a specific Assassin Rogue.
    Wood elf.
    Str 8 Dex 16 Con 15 Int 12 Wis 14 Cha 10.
    Level 1: Urchin background, proficiency in Acrobatics, Deception, Insight,
        and Investigation skills, Expertise in thieves' tools and Stealth,
        obtain rapier and leather armor.
    Level 2: obtain studded leather armor.
    Level 3: Assassin archetype.
    Level 4: Dual Wielder feat, obtain second rapier.
    Level 6: Expertise in Acrobatics and Perception skills, obtain +1 rapier.
    Level 8: Dex +2.
    Level 10: Dex +2.
    Level 11: obtain Major Uncommon.
    Level 12: Alert feat.
    Level 14: obtain Major Rare.
    Level 16: Resilient (Con) feat, obtain Major Very Rare.
    Level 18: obtain Major Legendary.
    Level 19: Wis +2.
    """

    def initialize_features(self):
        # Abilities
        self.base_abilities = get_abilities(-1, 3, 2, 1, 2, 0)
        if self.level >= 8:
            self.base_abilities["dex"] += 1
        if self.level >= 10:
            self.base_abilities["dex"] += 1
        if self.level >= 16:
            self.base_abilities["con"] += 1
        if self.level >= 19:
            self.base_abilities["wis"] += 1

        self.abilities = {k: self.base_abilities[k] for k in self.base_abilities}

        # Armor class
        if self.level >= 4:
            self.base_armor_class = 13
        elif self.level >= 2:
            self.base_armor_class = 12
        else:
            self.base_armor_class = 11

        # Wood elf racial features
        self.skill_proficiencies["perception"] = True
        self.charm_adv = True
        self.ghoul_paralysis_immunity = True

        # Urchin background and skill proficiencies
        self.skill_proficiencies["acrobatics"] = True
        self.skill_proficiencies["deception"] = True
        self.skill_proficiencies["insight"] = True
        self.skill_proficiencies["investigation"] = True
        self.skill_proficiencies["sleight_of_hand"] = True
        self.skill_proficiencies["stealth"] = True

        # Expertise
        self.skill_modifiers["stealth"] = self.proficiency
        if self.level >= 6:
            self.skill_modifiers["acrobatics"] = self.proficiency
            self.skill_modifiers["perception"] = self.proficiency

        # Alert feat
        if self.level >= 12:
            self.initiative_modifier += 5
            self.alert = True

        # Resilient feat
        self.save_proficiencies["con"] = self.level >= 16

        # Number of sneak attack dice
        N_sneak_attack_dice = int((self.level + 1) / 2)

        # +1 rapier
        if self.level >= 6:
            self.weapon = Weapon(
                self,
                d8,
                "magic_piercing",
                ability="dex",
                attack_modifier=1,
                damage_modifier=1,
            )
            self.sneak_attack_weapon = Weapon(
                self,
                ExtraWeaponDice(d8, d6, N_sneak_attack_dice),
                "magic_piercing",
                ability="dex",
                attack_modifier=1,
                damage_modifier=1,
            )

        # Rapier
        else:
            self.weapon = Weapon(self, d8, "piercing", ability="dex")
            self.sneak_attack_weapon = Weapon(
                self,
                ExtraWeaponDice(d8, d6, N_sneak_attack_dice),
                "piercing",
                ability="dex",
            )

        # Offhand rapier
        if self.level >= 4:
            self.offhand_weapon = Weapon(self, d8, "piercing", ability="dex")
            self.offhand_sneak_attack_weapon = Weapon(
                self,
                ExtraWeaponDice(d8, d6, N_sneak_attack_dice),
                "piercing",
                ability="dex",
            )

    def take_turn(self, encounter: Encounter):
        if self.action:
            if self.verbose:
                print(f"{self()} made an attack with Rapier")

            self.action = False

            if self.slowed > 0:
                self.bonus = False

            self.weapon_attack(encounter)

            # Bonus action for offhand attack only if first attack missed
            if self.level >= 4 and self.sneak_attack and self.bonus and self.hp > 0:
                if self.verbose:
                    print(f"{self()} made an attack with offhand Rapier")

                self.bonus = False
                self.weapon_attack(encounter, offhand=True)

        # Bonus action to hide from Cunning Action
        if self.level >= 2 and self.bonus and self.hp > 0:
            self.bonus = False
            self.stealth = self.roll_skill("stealth")

            if self.verbose:
                print(f"{self()} used Hide and rolled {self.stealth:d} on Stealth")

    def weapon_attack(self, encounter: Encounter, offhand: bool = False):
        """
        Weapon attack that can use Sneak Attack, Assassinate, Death Strike, and
        Stroke of Luck.

        Parameters
        ----------
        encounter
            The Encounter in which the attack takes place.
        offhand
            Whether the attack is made using the offhand weapon.
        """

        allies = encounter.get_allies(self)
        opponents = encounter.get_foes(self)

        surprised_opponents = [
            enemy for enemy in opponents if (enemy.surprised and enemy.hp > 0)
        ]

        # Choose target from encounter, preferring a surprised opponent
        if self.swallowed is not None:
            target = self.swallowed.swallower
        elif len(surprised_opponents) > 0:
            target = encounter.choice(surprised_opponents)
        else:
            target = encounter.choose_target(self)

        if target is None:
            return

        # Assassinate for advantage and automatic crit against surprised target
        if self.level >= 3 and target.surprised:
            if self.sneak_attack:
                if offhand:
                    weapon = self.offhand_sneak_attack_weapon
                else:
                    weapon = self.sneak_attack_weapon

            else:
                if offhand:
                    weapon = self.offhand_weapon
                else:
                    weapon = self.weapon

            attack_result = weapon.roll_attack(target, adv=True)

            # Stroke of Luck
            if attack_result == "miss" and self.stroke_of_luck:
                if self.verbose:
                    print(f"{self()} used Stroke of Luck")

                self.stroke_of_luck = False
                attack_result = "hit"

            if attack_result == "hit" or attack_result == "crit":
                self.sneak_attack = False
                damage = weapon.roll_damage(add_ability=not offhand, dice_multiplier=2)

                # Death Strike to force Con saving throw to double damage
                if self.level >= 17 and not target.saving_throw(
                    "con",
                    8 + self.abilities["dex"] + self.proficiency,
                ):
                    damage *= 2

                if self.verbose:
                    print(
                        f"{self()} scored a crit on {target()} for {damage:d} "
                        f"{weapon.damage_type} damage"
                    )

                target.take_damage(damage, weapon.damage_type, dealer=self)

        else:
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
                if offhand:
                    weapon = self.offhand_sneak_attack_weapon
                else:
                    weapon = self.sneak_attack_weapon

            else:
                if offhand:
                    weapon = self.offhand_weapon
                else:
                    weapon = self.weapon

            attack_result = weapon(target, add_ability=not offhand)

            if attack_result == "hit" or attack_result == "crit":
                self.sneak_attack = False

        # Attacking gives away position
        self.stealth = 0


class EvocationSchool(Wizard):
    """
    Python class for a specific Evocation School Wizard.
    Forest gnome.
    Str 8 Dex 14 Con 15 Int 16 Wis 12 Cha 10.
    Level 1: Sage background, proficiency in Insight and Investigation skills,
        obtain spell component pouch.
    Level 2: School of Evocation arcane tradition.
    Level 4: Int +2.
    Level 6: obtain +1 wand of the war mage.
    Level 8: Int +2.
    Level 11: obtain Major Uncommon.
    Level 12: Resilient (Con) feat.
    Level 14: obtain Major Rare.
    Level 16: Dex +2, obtain Major Very Rare.
    Level 18: obtain Major Legendary.
    Level 19: Elemental Adept (fire) feat.
    """

    def initialize_features(self):
        # Abilities
        self.base_abilities = get_abilities(-1, 2, 2, 3, 1, 0)
        if self.level >= 4:
            self.base_abilities["int"] += 1
        if self.level >= 8:
            self.base_abilities["int"] += 1
        if self.level >= 12:
            self.base_abilities["con"] += 1
        if self.level >= 16:
            self.base_abilities["dex"] += 1

        self.abilities = {k: self.base_abilities[k] for k in self.base_abilities}

        # Armor class, assuming Mage Armor has been cast
        self.base_armor_class = 13

        # Gnome racial features
        self.gnome_cunning = True

        # Sage background and skill proficiencies
        self.skill_proficiencies["arcana"] = True
        self.skill_proficiencies["history"] = True
        self.skill_proficiencies["insight"] = True
        self.skill_proficiencies["investigation"] = True

        # School of Evocation features
        self.potent_cantrip = self.level >= 6
        self.empowered_evocation = self.level >= 10
        self.total_overchannel = self.level >= 14

        # Wand of the war mage
        if self.level >= 6:
            self.spell_attack_modifier += 1

        # Resilient (Con) feat
        if self.level >= 12:
            self.save_proficiencies["con"] = True

        # Cantrips
        self.cast_acid_splash = spells.AcidSplash(self)
        self.cast_fire_bolt = spells.FireBolt(self)
        self.cast_poison_spray = spells.PoisonSpray(self)

        # Prepared spells. Number of spells is wizard level plus Int modifier.
        # Assume that Mage Armor has been prepared and cast after a long rest.
        self.cast_burning_hands = spells.BurningHands(self)
        self.cast_chromatic_orb = spells.ChromaticOrb(self)
        self.cast_magic_missile = spells.MagicMissile(self)
        self.cast_thunderwave = spells.Thunderwave(self)
        if self.level >= 3:
            self.cast_melfs_acid_arrow = spells.MelfsAcidArrow(self)
            self.cast_scorching_ray = spells.ScorchingRay(self)
        if self.level >= 5:
            self.cast_fireball = spells.Fireball(self)
            self.cast_lightning_bolt = spells.LightningBolt(self)
        if self.level >= 7:
            self.cast_blight = spells.Blight(self)

    def reset_long_rest_features(self):
        # Extend reset_long_rest_conditions() to cast Mage Armor and reset
        # Overchannel
        super().reset_long_rest_features()
        self.N_spell_slots[0] -= 1
        self.N_overchannel = self.total_overchannel

    def set_usage_rates(
        self,
        encounters_per_long_rest: int,
        encounters_since_short_rest: int,
    ):
        # Expected number of spell slots remaining per encounter. Expect to
        # consume int(sum_spell_slots / encounters_per_long_rest) per encounter,
        # with the remainder consumed in later encounters. For example, with 14
        # total spell slots and 6 encounters per long rest, the expected usage
        # per encounter is [2, 2, 2, 2, 3, 3]. The remaining spell slots are
        # [12, 10, 8, 6, 3, 0]. Reduce the total number of spell slots by 1 for
        # Mage Armor.
        sum_spell_slots = numpy.sum(self.total_spell_slots) - 1
        self.spell_slot_usage = sum_spell_slots - numpy.cumsum(
            [
                int(sum_spell_slots / encounters_per_long_rest)
                + (
                    encounters_per_long_rest - i
                    <= sum_spell_slots % encounters_per_long_rest
                )
                for i in range(encounters_per_long_rest)
            ]
        )

    def short_rest(self):
        # Extend short_rest() to use Arcane Recovery
        super().short_rest()

        if self.arcane_recovery and self.hp > 0:
            if self.verbose:
                print(f"{self()} used Arcane Recovery")

            self.arcane_recovery = False
            recovery_slots = int((self.level + 1) / 2)
            for slot in range(5, -1, -1):
                while (
                    self.total_spell_slots[slot] > self.N_spell_slots[slot]
                    and recovery_slots > slot
                ):
                    if self.verbose:
                        print(f"{self()} recovered a spell slot of level {slot + 1:d}")

                    self.N_spell_slots[slot] += 1
                    recovery_slots -= slot + 1

    def take_turn(self, encounter: Encounter):
        lowest_slots = self.lowest_spell_slots()

        opponents = [enemy for enemy in encounter.get_foes(self) if enemy.hp > 0]
        N_opponents = len(opponents)

        visible_opponents = (
            [enemy for enemy in opponents if not enemy.is_hidden(self)]
            if self.blinded == 0
            else []
        )
        N_visible_opponents = len(visible_opponents)

        immune_acid = numpy.any([enemy.immunities["acid"] for enemy in opponents])
        immune_cold = numpy.any([enemy.immunities["cold"] for enemy in opponents])
        immune_fire = numpy.any([enemy.immunities["fire"] for enemy in opponents])
        immune_force = numpy.any([enemy.immunities["force"] for enemy in opponents])
        immune_lightning = numpy.any(
            [enemy.immunities["lightning"] for enemy in opponents]
        )
        immune_necrotic = numpy.any(
            [enemy.immunities["necrotic"] for enemy in opponents]
        )
        immune_poison = numpy.any([enemy.immunities["poison"] for enemy in opponents])
        immune_thunder = numpy.any([enemy.immunities["thunder"] for enemy in opponents])
        construct_or_undead = numpy.any(
            [(enemy.construct or enemy.undead is not None) for enemy in opponents]
        )

        # Cast a prepared spell if there are more spell slots than the expected
        # usage rate based on the number of encounters since a long rest
        if (
            self.action
            and numpy.sum(self.N_spell_slots)
            > self.spell_slot_usage[encounter.encounters_since_long_rest]
        ):
            self.action = False

            if self.slowed > 0:
                self.bonus = False

            # Cast Blight
            if (
                lowest_slots[3] is not None
                and N_opponents == 1
                and not immune_necrotic
                and not construct_or_undead
                and N_visible_opponents > 0
            ):
                self.cast_blight(
                    slot=lowest_slots[3],
                    targets=encounter.choice(visible_opponents),
                )

            # Choose randomly between level 3 spells
            elif (
                lowest_slots[2] is not None
                and N_opponents > 1
                and self.swallowed is None
                and not (immune_fire and immune_lightning)
            ):
                if immune_lightning or (not immune_fire and rng.random() < 0.5):
                    self.cast_fireball(
                        slot=lowest_slots[2],
                        targets=encounter.choose_target(self, N_targets=2),
                    )

                else:
                    self.cast_lightning_bolt(
                        slot=lowest_slots[2],
                        targets=encounter.choose_target(self, N_targets=2),
                    )

            # Choose randomly between level 2 spells
            elif lowest_slots[1] is not None and not (immune_fire and immune_acid):
                if immune_fire or (not immune_acid and rng.random() < 0.5):
                    self.cast_melfs_acid_arrow(
                        slot=lowest_slots[1],
                        targets=encounter.choose_target(self),
                    )

                else:
                    # Call Spell instance to cast and resolve first beam, then
                    # call cast() to resolve additional beams so that targets
                    # are chosen after previous beam resolves
                    self.cast_scorching_ray(
                        slot=lowest_slots[1],
                        targets=encounter.choose_target(self),
                    )

                    for i in range(lowest_slots[1]):
                        self.cast_scorching_ray.cast(
                            lowest_slots[1],
                            encounter.choose_target(self),
                        )

            # Cast a level 1 spell
            elif lowest_slots[0] is not None and self.swallowed is None:
                spell_choice = rng.random()

                # Cast chromatic orb
                if N_opponents == 1 and N_visible_opponents > 0:
                    self.cast_chromatic_orb(
                        slot=lowest_slots[0],
                        targets=encounter.choose_target(self),
                        damage_type="cold" if not immune_cold else "thunder",
                    )

                elif immune_fire:
                    # Choose randomly between Magic Missile and Thunderwave
                    if immune_thunder or (
                        not immune_force
                        and N_visible_opponents > 0
                        and spell_choice < 0.5
                    ):
                        self.cast_magic_missile(
                            slot=lowest_slots[0],
                            targets=encounter.choose_target(
                                self,
                                N_targets=lowest_slots[0] + 2,
                                replacement=True,
                            ),
                        )

                    else:
                        self.cast_thunderwave(
                            slot=lowest_slots[0],
                            targets=encounter.choose_target(self, N_targets=2),
                        )

                elif immune_thunder:
                    # Choose randomly between Burning Hands and Magic Missile
                    if immune_force or N_visible_opponents == 0 or spell_choice < 0.5:
                        self.cast_burning_hands(
                            slot=lowest_slots[0],
                            targets=encounter.choose_target(self, N_targets=2),
                        )

                    else:
                        self.cast_magic_missile(
                            slot=lowest_slots[0],
                            targets=encounter.choose_target(
                                self,
                                N_targets=lowest_slots[0] + 2,
                                replacement=True,
                            ),
                        )

                elif immune_force or N_visible_opponents == 0:
                    # Choose randomly between Burning Hands and Thunderwave
                    if spell_choice < 0.5:
                        self.cast_burning_hands(
                            slot=lowest_slots[0],
                            targets=encounter.choose_target(self, N_targets=2),
                        )

                    else:
                        self.cast_thunderwave(
                            slot=lowest_slots[0],
                            targets=encounter.choose_target(self, N_targets=2),
                        )

                # Choose randomly between Burning Hands, Magic Missile, or Thunderwave
                elif spell_choice < (1.0 / 3):
                    self.cast_burning_hands(
                        slot=lowest_slots[0],
                        targets=encounter.choose_target(self, N_targets=2),
                    )

                elif spell_choice < (2.0 / 3):
                    self.cast_magic_missile(
                        slot=lowest_slots[0],
                        targets=encounter.choose_target(
                            self,
                            N_targets=lowest_slots[0] + 2,
                            replacement=True,
                        ),
                    )

                else:
                    self.cast_thunderwave(
                        slot=lowest_slots[0],
                        targets=encounter.choose_target(self, N_targets=2),
                    )

            # Has a 1st level spell slot but is swallowed
            else:
                self.action = True

        # Cast a cantrip
        if self.action:
            self.action = False

            if self.slowed > 0:
                self.bonus = False

            spell_choice = rng.random()

            if N_visible_opponents == 0:
                self.cast_fire_bolt(targets=encounter.choose_target(self))

            elif immune_poison:
                # Choose randomly between Acid Splash and Fire Bolt
                if immune_fire or (not immune_acid and spell_choice < 0.5):
                    if N_visible_opponents > 1:
                        targets = encounter.choice(
                            visible_opponents,
                            size=2,
                            replace=False,
                        )

                    else:
                        targets = visible_opponents

                    self.cast_acid_splash(targets=targets)

                else:
                    self.cast_fire_bolt(targets=encounter.choose_target(self))

            elif immune_fire and N_visible_opponents > 0:
                # Choose randomly between Acid Splash and Poison Spray
                if not immune_acid and spell_choice < 0.5:
                    if N_visible_opponents > 1:
                        targets = encounter.choice(
                            visible_opponents,
                            size=2,
                            replace=False,
                        )

                    else:
                        targets = visible_opponents

                    self.cast_acid_splash(targets=targets)

                else:
                    self.cast_poison_spray(targets=encounter.choice(visible_opponents))

            elif immune_acid:
                # Choose randomly between Fire Bolt and Poison Spray
                if spell_choice < 0.5:
                    self.cast_fire_bolt(targets=encounter.choose_target(self))
                else:
                    self.cast_poison_spray(targets=encounter.choice(visible_opponents))

            # Choose randomly between Acid Splash, Frie Bolt, and Poison Spray
            elif spell_choice < (1.0 / 3):
                if N_visible_opponents > 1:
                    targets = encounter.choice(visible_opponents, size=2, replace=False)
                else:
                    targets = visible_opponents

                self.cast_acid_splash(targets=targets)

            elif spell_choice < (2.0 / 3):
                self.cast_fire_bolt(targets=encounter.choose_target(self))

            else:
                self.cast_poison_spray(targets=encounter.choice(visible_opponents))


player_characters = {
    "Cleric": LifeDomain,
    "Fighter": Champion,
    "Rogue": Assassin,
    "Wizard": EvocationSchool,
}
