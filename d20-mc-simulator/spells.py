"""Implements classes for spells."""

from abc import ABC, abstractmethod

import numpy

from creature import Creature, Weapon
from dice_roller import Dice, Die, d4, d6, d8, d10, d12, d20, roll_d20
from duration import Duration


class Spell(ABC):
    """
    An abstract class that represents a spell. For each spell, a derived class
    should be created that overrides the attributes name and spell_level and the
    method cast(self, caster) to determine the effects of the spell and
    optionally overrides the attribute concentration and the method end(self) to
    remove the spell's effects.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def spell_level(self) -> int:
        pass

    @abstractmethod
    def cast(self, slot: int, targets: list[Creature]):
        """
        Creates the effects of the spell cast using a specified spell slot.

        Parameters
        ----------
        slot
            Level of spell slot used to cast the spell.
        targets
            List of creatures targeted by the spell.
        """

        pass

    concentration = False

    def end(self):
        pass

    def __init__(self, caster):
        """
        Constructor for Spell. Sets the number of damage dice for cantrips based
        on the caster's level.

        Parameters
        ----------
        caster
            The creature casting the spell.
        """

        self.caster = caster

        # Number of dice for cantrips
        if self.spell_level == 0:
            if self.caster.level >= 17:
                self.N_cantrip_dice = 4
            elif self.caster.level >= 11:
                self.N_cantrip_dice = 3
            elif self.caster.level >= 5:
                self.N_cantrip_dice = 2
            else:
                self.N_cantrip_dice = 1

    def __call__(
        self,
        slot: int = None,
        targets: Creature | list[Creature] | None = None,
        **kwargs,
    ):
        """
        Callable for Spell. Casts the spell using a specified spell slot,
        consuming the spell slot for leveled spells and ending an existing
        concentration spell for concentration spells.

        Parameters
        ----------
        slot
            Level of spell slot used to cast the spell.
        targets
            List of creatures targeted by the spell.
        """

        # Default slot is the minimum slot needed to cast the spell
        if slot == None:
            slot = self.spell_level

        if slot >= self.spell_level and (
            self.spell_level == 0 or self.caster.N_spell_slots[slot - 1] > 0
        ):
            # Consume the caster's spell slot
            if self.spell_level > 0:
                self.caster.N_spell_slots[slot - 1] -= 1

            if self.caster.verbose:
                if self.spell_level > 0:
                    print(
                        f"{self.caster()} {self.caster.N_spell_slots} cast "
                        f"{self.name} at level {slot:d}"
                    )

                else:
                    print(f"{self.caster()} cast {self.name}")

            if self.concentration:
                if self.caster.concentration != None:
                    self.caster.concentration.end()

                self.caster.concentration = self

            self.cast(slot, targets, **kwargs)

    def get_spell_healing(
        self,
        slot: int,
        die: Die,
        N_dice: int,
    ):
        """
        Get the amount of healing applied by a spell, accounting for the
        Life Domain cleric's Disciple of Life, Blessed Healer, and Supreme
        Healing features.

        Parameters
        ----------
        slot
            Level of spell slot used to cast the spell.
        die
            Die rolled to determine amount of healing.
        N_dice
            Number of dice rolled to determine amount of healing.
        """

        if self.caster.blessed_healer:
            self.caster.heal(2 + slot)

        modifier = self.caster.abilities[self.caster.spell_ability]
        if self.caster.supreme_healing:
            healing = N_dice * die.sides + modifier
        else:
            healing = die(N_dice) + modifier

        if self.caster.disciple_of_life:
            healing += 2 + slot

        return healing


class AcidSplash(Spell):
    """Acid Splash cantrip."""

    name = "Acid Splash"
    spell_level = 0

    def cast(self, slot, targets):
        damage = d6(self.N_cantrip_dice)

        for target in targets:
            if target.is_hidden(self.caster):
                continue

            if self.caster.potent_cantrip:
                target.half_saving_throw(
                    "dex",
                    self.caster.save_dc(),
                    damage,
                    "acid",
                    save_type="magic",
                )

            elif not target.saving_throw(
                "dex",
                self.caster.save_dc(),
                save_type="magic",
            ):
                target.take_damage(damage, "acid")


class Aid(Spell):
    """Aid spell."""

    name = "Aid"
    spell_level = 2

    def cast(self, slot, targets):
        hp_increase = 5 * (slot - 1)

        for target in targets:
            if not target.aid:
                if self.caster.verbose:
                    print(f"{target()} received Aid")

                target.aid = True
                target.total_hp += hp_increase
                target.heal(hp_increase, magic=True)


class Bane(Spell):
    """Bane spell."""

    concentration = True
    name = "Bane"
    spell_level = 1

    def cast(self, slot, targets):
        self.duration = 10
        self.targets = []
        for target in targets:
            if not target.saving_throw(
                "cha",
                self.caster.save_dc(),
                save_type="magic",
            ):
                if self.caster.verbose or target.verbose:
                    print(f"{target()} received Bane")

                self.targets.append(target)
                target.baned += 1

        if len(self.targets) == 0:
            self.caster.concentration = None

    def end(self):
        if self.caster.verbose:
            print(f"{self.caster()} lost concentration on Bane")

        self.caster.concentration = None

        for target in self.targets:
            target.baned -= 1

            if (self.caster.verbose or target.verbose) and target.baned == 0:
                print(f"{target()} lost Bane")


class Bless(Spell):
    """Bless spell."""

    concentration = True
    name = "Bless"
    spell_level = 1

    def cast(self, slot, targets):
        self.duration = 10
        self.targets = targets
        for target in self.targets:
            if self.caster.verbose or target.verbose:
                print(f"{target()} received Bless")

            target.blessed += 1

    def end(self):
        if self.caster.verbose:
            print(f"{self.caster()} lost concentration on Bless")

        self.caster.concentration = None

        for target in self.targets:
            target.blessed -= 1

            if (self.caster.verbose or target.verbose) and target.blessed == 0:
                print("{target()} lost Bless")


class Blight(Spell):
    """Blight spell."""

    name = "Blight"
    spell_level = 4

    def cast(self, slot, targets):
        if (
            not targets.construct
            and targets.undead is None
            and not targets.is_hidden(self.caster)
        ):
            targets.half_saving_throw(
                "con",
                self.caster.save_dc(),
                d8(4 + slot),
                "necrotic",
                save_type="magic",
            )


class BurningHands(Spell):
    """Burning Hands spell."""

    name = "Burning Hands"
    spell_level = 1

    def cast(self, slot, targets):
        damage = d6(2 + slot)

        if self.caster.empowered_evocation:
            damage += self.caster.abilities[self.caster.spell_ability]

        for target in targets:
            target.half_saving_throw(
                "dex",
                self.caster.save_dc(),
                damage,
                "fire",
                save_type="magic",
            )


class ChromaticOrb(Spell):
    """Chromatic Orb."""

    name = "Chromatic Orb"
    spell_level = 1

    def cast(self, slot, targets, damage_type="fire"):
        if targets.is_hidden(self.caster):
            return

        spell_weapon = Weapon(
            self.caster,
            Dice(d8, 2 + slot),
            damage_type,
            ability=self.caster.spell_ability,
            ranged=True,
            attack_modifier=self.caster.spell_attack_modifier,
        )
        spell_weapon(targets, add_ability=self.caster.empowered_evocation)


class ConeOfCold(Spell):
    """Cone of Cold spell."""

    name = "Cone of Cold"
    spell_level = 5

    def cast(self, slot, targets):
        damage = d8(3 + slot)

        if self.caster.empowered_evocation:
            damage += self.caster.abilities[self.caster.spell_ability]

        for target in targets:
            target.half_saving_throw(
                "con",
                self.caster.save_dc(),
                damage,
                "cold",
                save_type="magic",
            )


class CureWounds(Spell):
    """Cure Wounds spell."""

    name = "Cure Wounds"
    spell_level = 1

    def cast(self, slot, targets):
        targets.heal(self.get_spell_healing(slot, d8, slot), magic=True)


class Fireball(Spell):
    """Fireball spell."""

    name = "Fireball"
    spell_level = 3

    def cast(self, slot, targets):
        damage = d6(5 + slot)

        if self.caster.empowered_evocation:
            damage += self.caster.abilities[self.caster.spell_ability]

        for target in targets:
            target.half_saving_throw(
                "dex",
                self.caster.save_dc(),
                damage,
                "fire",
                save_type="magic",
            )


class FireBolt(Spell):
    """Fire Bolt cantrip."""

    name = "Firebolt"
    spell_level = 0

    def cast(self, slot, targets):
        spell_weapon = Weapon(
            self.caster,
            Dice(d10, self.N_cantrip_dice),
            "fire",
            ability=self.caster.spell_ability,
            ranged=True,
            attack_modifier=self.caster.spell_attack_modifier,
        )

        spell_weapon(targets, add_ability=self.caster.empowered_evocation)


class GreaterInvisibility(Spell):
    """Greater invisibility spell."""

    concentration = True
    name = "Greater Invisibility"
    spell_level = 4

    def cast(self, slot, targets):
        self.duration = 10
        self.target = targets
        targets.invisible += 1

        if targets.verbose:
            print(f"{targets()} became invisible")

    def end(self):
        if self.caster.verbose:
            print(f"{self.caster()} lost concentration on {self.name}")

        self.caster.concentration = None
        self.target.invisible -= 1

        if self.target.verbose:
            print(f"{self.target()} is no longer invisible")


class GuidingBoltDuration(Duration):
    """
    Class for the condition applied by the Guiding Bolt spell that grants
    advantage on the next attack against a creature.
    """

    def __init__(self, caster, target):
        self.duration = 2
        self.caster = caster
        self.target = target

        target.guiding_bolt = self
        caster.end_turn_duration.append(self)

        if caster.verbose or target.verbose:
            print(f"{target()} received Guiding Bolt")

    def end(self):
        self.target.guiding_bolt = None
        self.caster.end_turn_duration.remove(self)

        if self.caster.verbose or self.target.verbose:
            print(f"{self.target()} lost Guiding Bolt")

    def end_turn_effect(self):
        self.tick()


class GuidingBolt(Spell):
    """Guiding Bolt spell."""

    name = "Guiding Bolt"
    spell_level = 1

    def cast(self, slot, targets):
        spell_weapon = Weapon(
            self.caster,
            Dice(d6, 3 + slot),
            "radiant",
            ability=self.caster.spell_ability,
            ranged=True,
            attack_modifier=self.caster.spell_attack_modifier,
        )

        attack_result = spell_weapon(targets, add_ability=False)

        if attack_result in ["hit", "crit"] and targets.hp > 0:
            if targets.guiding_bolt != None:
                targets.guiding_bolt.caster.end_turn_duration.remove(
                    targets.guiding_bolt
                )

            spell_duration = GuidingBoltDuration(self.caster, targets)


class HealingWord(Spell):
    """Healing Word spell."""

    name = "Healing Word"
    spell_level = 1

    def cast(self, slot, targets):
        targets.heal(self.get_spell_healing(slot, d4, slot), magic=True)


class LesserRestoration(Spell):
    """Lesser Restoration spell."""

    name = "Lesser Restoration"
    spell_level = 2

    def cast(self, slot, targets, condition="paralyzed"):
        """
        Creates the effects of the spell cast using a specified spell slot.

        Parameters
        ----------
        slot
            Level of spell slot used to cast the spell.
        targets
            List of creatures targeted by the spell.
        condition
            Name of the condition to be ended by this spell.
        """

        if condition == "blinded":
            targets.blinded = False

        elif condition == "paralyzed":
            targets.paralyzed = False

        elif condition == "poisoned":
            targets.poisoned = False
        else:
            if self.caster.verbose or targets.verbose:
                print(f"{condition} is not one of blinded, paralyzed, or poisoned")
            return

        if self.caster.verbose or targets.verbose:
            print(f"{targets()} lost condition {condition}")


class LightningBolt(Spell):
    """Lightning Bolt spell."""

    name = "Lightning Bolt"
    spell_level = 3

    def cast(self, slot, targets):
        damage = d6(5 + slot)

        if self.caster.empowered_evocation:
            damage += self.caster.abilities[self.caster.spell_ability]

        for target in targets:
            target.half_saving_throw(
                "dex",
                self.caster.save_dc(),
                damage,
                "lightning",
                save_type="magic",
            )


class MagicMissile(Spell):
    """Magic Missile spell."""

    name = "Magic Missile"
    spell_level = 1

    def cast(self, slot, targets):
        damage = d4() + 1

        if self.caster.empowered_evocation:
            damage += self.caster.abilities[self.caster.spell_ability]

        for target in targets:
            # Target can use reaction to cast shield
            target.targeted_by_magic_missile()

            if not target.is_hidden(self.caster) and target.shield == None:
                target.take_damage(damage, "force")


class MassHealingWord(Spell):
    """Mass Healing Word spell."""

    name = "Mass Healing Word"
    spell_level = 3

    def cast(self, slot, targets):
        healing = self.get_spell_healing(slot, d4, slot - 2)

        for target in targets:
            target.heal(healing, magic=True)


class MelfsAcidArrowDuration(Duration):
    """
    Class for the condition applied by the Melf's Acid Arrow spell that deals
    acid damage at the end of the target's next turn.
    """

    def __init__(self, caster, slot, target):
        self.caster = caster
        self.slot = slot
        self.target = target

        target.end_turn_duration.append(self)

        if caster.verbose or target.verbose:
            print(f"{target()} received Melf's Acid Arrow")

    def end(self):
        damage = d4(self.slot)

        if self.caster.empowered_evocation:
            damage += self.caster.abilities[self.caster.spell_ability]

        self.target.take_damage(damage, "acid")
        self.target.end_turn_duration.remove(self)

        if self.caster.verbose or self.target.verbose:
            print(f"{self.target()} lost Melf's Acid Arrow")

    def end_turn_effect(self):
        self.end()


class MelfsAcidArrow(Spell):
    """Melf's Acid Arrow spell."""

    name = "Melf's Acid Arrow"
    spell_level = 2

    def cast(self, slot, targets):
        spell_weapon = Weapon(
            self.caster,
            Dice(d4, 2 + slot),
            "acid",
            ability=self.caster.spell_ability,
            ranged=True,
            attack_modifier=self.caster.spell_attack_modifier,
        )

        attack_result = spell_weapon(
            targets, add_ability=self.caster.empowered_evocation
        )

        if attack_result == "miss":
            damage = d4(2 + slot)

            if self.caster.empowered_evocation:
                damage += self.caster.abilities[self.caster.spell_ability]

            targets.take_damage(int(damage / 2), "acid")

        elif targets.hp > 0:
            spell_duration = MelfsAcidArrowDuration(self.caster, slot, targets)


class PoisonSpray(Spell):
    """Poison Spray cantrip."""

    name = "Poison Spray"
    spell_level = 0

    def cast(self, slot, targets):
        if targets.is_hidden(self.caster):
            return

        if self.caster.potent_cantrip:
            targets.half_saving_throw(
                "con",
                self.caster.save_dc(),
                d12(self.N_cantrip_dice),
                "poison",
                save_type="magic",
            )

        elif not targets.saving_throw(
            "con",
            self.caster.save_dc(),
            save_type="magic",
        ):
            targets.take_damage(d12(self.N_cantrip_dice), "poison")


class PrayerOfHealing(Spell):
    """Prayer of Healing."""

    name = "Prayer of Healing"
    spell_level = 2

    def cast(self, slot, targets):
        healing = self.get_spell_healing(slot, d8, slot)

        for target in targets:
            target.heal(healing, magic=True)


class SacredFlame(Spell):
    """Sacred Flame cantrip."""

    name = "Sacred Flame"
    spell_level = 0

    def cast(self, slot, targets):
        if targets.is_hidden(self.caster):
            return

        if self.caster.potent_cantrip:
            targets.half_saving_throw(
                "dex",
                self.caster.save_dc(),
                d8(self.N_cantrip_dice),
                "radiant",
                save_type="magic",
            )

        elif not targets.saving_throw(
            "dex",
            self.caster.save_dc(),
            save_type="magic",
        ):
            targets.take_damage(d8(self.N_cantrip_dice), "radiant")


class ScorchingRay(Spell):
    """Scorching Ray spell."""

    name = "Scorching Ray"
    spell_level = 2

    def cast(self, slot, targets):
        spell_weapon = Weapon(
            self.caster,
            Dice(d6, 2),
            "fire",
            ability=self.caster.spell_ability,
            ranged=True,
            attack_modifier=self.caster.spell_attack_modifier,
        )

        spell_weapon(targets, add_ability=self.caster.empowered_evocation)


class ShieldDuration(Duration):
    """
    Class for the condition applied by the Shield spell that increases armor
    class by five and prevents damage from Magic Missile.
    """

    def __init__(self, caster):
        self.duration = 1
        self.caster = caster

        caster.shield = self
        caster.start_turn_duration.append(self)

    def end(self):
        self.caster.shield = None
        self.caster.start_turn_duration.remove(self)

    def start_turn_effect(self):
        self.tick()


class Shield(Spell):
    """Shield spell."""

    name = "Shield"
    spell_level = 1

    def cast(self, slot, targets):
        spell_duration = ShieldDuration(self.caster)


class ShieldOfFaith(Spell):
    """Shield of Faith spell."""

    concentration = True
    name = "Shield of Faith"
    spell_level = 1

    def cast(self, slot, targets):
        self.duration = 100
        self.caster.base_armor_class += 2

    def end(self):
        if self.caster.verbose:
            print(f"{seldf.caster()} lost concentration on Shield of Faith")

        self.caster.concentration = None
        self.caster.base_armor_class -= 2


class SpiritGuardians(Spell):
    """Spirit Guardians spell."""

    concentration = True
    name = "Spirit Guardians"
    spell_level = 3

    def cast(self, slot, targets, damage_type="radiant"):
        """
        Creates the effects of the spell cast using a specified spell slot.

        Parameters
        ----------
        slot
            Level of spell slot used to cast the spell.
        targets
            List of creatures targeted by the spell.
        damage_type
            Damage type for damage dealt by this spell.
        """

        self.duration = 100
        self.N_dice = slot
        self.targets = targets
        self.damage_type = damage_type

        for target in self.targets:
            if len(target.spirit_guardians) == 0:
                target.spirit_guardians = [self]

            # Sort instances of spell on target by potentcy
            else:
                target.spirit_guardians.append(self)
                target.spirit_guardians = [
                    target.spirit_guardians[i]
                    for i in numpy.argsort(
                        [spell.N_dice for spell in target.spirit_guardians]
                    )
                ][::-1]

            if self.caster.verbose or target.verbose:
                print(f"{target()} received Spirit Guardians")

    def end(self):
        if self.caster.verbose:
            print(f"{self.caster()} lost concentration on Spirit Guardians")

        self.caster.concentration = None

        for target in self.targets:
            target.spirit_guardians.remove(self)

            if (self.caster.verbose or target.verbose) and len(
                target.spirit_guardians
            ) == 0:
                print(f"{target()} lost Spirit Guardians")

    def start_turn_effect(self, target):
        if self.caster.verbose or target.verbose:
            print(f"{target()} triggered Spirit Guardians")

        target.half_saving_throw(
            "wis",
            self.caster.save_dc(),
            d8(self.N_dice),
            self.damage_type,
            damage_type="magic",
        )


class SpiritualWeaponDuration(Duration):
    """
    Class for the condition applied by the Spiritual Weapon spell that allows a
    weapon attack as a bonus action.
    """

    def __init__(self, caster, slot):
        self.duration = 10
        self.caster = caster

        # Treat as ranged to avoid melee triggers, e.g. remorhaz's Heated Body
        self.spell_weapon = Weapon(
            caster,
            Dice(d8, int(slot / 2)),
            "force",
            ability=caster.spell_ability,
            ranged=True,
            attack_modifier=caster.spell_attack_modifier,
        )

        caster.spiritual_weapon = self
        caster.start_turn_duration.append(self)

    def end(self):
        if self.caster.verbose:
            print(f"{self.caster()} lost Spiritual Weapon")

        self.caster.spiritual_weapon = None
        self.caster.start_turn_duration.remove(self)

    def start_turn_effect(self):
        self.tick()


class SpiritualWeapon(Spell):
    """Spiritual Weapon spell."""

    name = "Spiritual Weapon"
    spell_level = 2

    def cast(self, slot, targets):
        if self.caster.spiritual_weapon != None:
            self.caster.start_turn_duration.remove(self.caster.spiritual_weapon)

        spell_duration = SpiritualWeaponDuration(self.caster, slot)


class Thunderwave(Spell):
    """Thunderwave spell."""

    name = "Thunderwave"
    spell_level = 1

    def cast(self, slot, targets):
        damage = d8(1 + slot)

        if self.caster.empowered_evocation:
            damage += self.caster.abilities[self.caster.spell_ability]

        for target in targets:
            target.half_saving_throw(
                "con",
                self.caster.save_dc(),
                damage,
                "thunder",
                save_type="magic",
            )


class ViciousMockeryDuration(Duration):
    """
    Class for the condition applied by the Vicious Mockery cantrip that grants
    disadvantage on a creature's next attack.
    """

    def __init__(self, caster, target):
        self.duration = 1
        self.target = target

        target.vicious_mockery = self
        target.end_turn_duration.append(self)

        if caster.verbose or target.verbose:
            print(f"{target()} received Vicious Mockery")

    def end(self):
        self.target.vicious_mockery = None
        self.target.end_turn_duration.remove(self)

        if self.target.verbose:
            print(f"{self.target()} lost Vicious Mockery")

    def end_turn_effect(self):
        self.tick()


class ViciousMockery(Spell):
    """Vicious Mockery cantrip."""

    name = "Vicious Mockery"
    spell_level = 0

    def cast(self, slot, targets):
        if targets.is_hidden(self.caster):
            return

        if self.caster.potent_cantrip:
            save_result = targets.half_saving_throw(
                "wis",
                self.caster.save_dc(),
                d4(self.N_cantrip_dice),
                "psychic",
                save_type="magic",
            )

        else:
            save_result = targets.saving_throw(
                "wis",
                self.caster.save_dc(),
                save_type="magic",
            )

            if not save_result:
                targets.take_damage(d4(self.N_cantrip_dice), "psychic")

        if not save_result:
            if targets.vicious_mockery != None:
                targets.end_turn_duration.remove(targets.vicious_mockery)

            spell_duration = ViciousMockeryDuration(self.caster, targets)
