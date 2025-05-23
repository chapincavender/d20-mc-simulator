"""
    Implements classes for creatures, player characters, legendary creatures,
    and weapons.
"""

from abc import ABC, abstractmethod

import numpy

from dice_roller import Dice, Die, d4, roll_d20
from duration import BleedingDuration, Duration


def get_abilities(
    strength: int,
    dexterity: int,
    constitution: int,
    intelligence: int,
    wisdom: int,
    charisma: int,
) -> dict[str, int]:
    """Create a dictionary of ability score modifiers from integers."""

    return {
        "str": strength,
        "dex": dexterity,
        "con": constitution,
        "int": intelligence,
        "wis": wisdom,
        "cha": charisma,
    }


class Creature(ABC):
    """
    An abstract class that represents a combatant, which can be either a monster
    or a player character. For each unique combatant, a derived class should be
    created that overrides the attribute hit_die and the following methods:
        initialize_features(self) to initialize creature features (including
            abilities, armor class, and proficiency)
        take_turn(self, encounter) to determine how to take a turn in combat

    Attributes
    ----------
    ABILITIES
        List of abilities.
    DAMAGE_TYPES
        List of damage types.
    PRIORITY_ACTIONS
        Dictionary of priority actions and their associated priority.
    SKILLS
        Dictionary of skills and their associated ability.
    """

    @abstractmethod
    def initialize_features(self):
        """
        Initialize abilities, armor class, proficiency, and other game features.
        """

        pass

    @abstractmethod
    def take_turn(self, encounter: "Encounter"):
        """
        Determine how to take a turn in combat.

        Parameters
        ----------
        encounter
            The Encounter in which the turn takes place.
        """

        pass

    def lair_action(self, encounter: "Encounter"):
        """
        Determine how to take a lair action on initiative count 20.

        Parameters
        ----------
        encounter
            The Encounter in which the lair action takes place.
        """

        pass

    def start_encounter(self, encouter: "Encounter"):
        """
        Initialize effects at the beginning of an encounter.

        Parameters
        ----------
        encounter
            The Encounter in which the effects take place.
        """

        pass

    # List of abilities
    ABILITIES: list[str] = ["str", "dex", "con", "int", "wis", "cha"]

    # List of damage types
    DAMAGE_TYPES: list[str] = [
        "acid",
        "bludgeoning",
        "cold",
        "fire",
        "force",
        "lightning",
        "magic_bludgeoning",
        "magic_piercing",
        "magic_slashing",
        "necrotic",
        "piercing",
        "poison",
        "psychic",
        "radiant",
        "slashing",
        "thunder",
    ]

    # Dictionary of priority actions and their associated priority.
    # This will overrule the default action in take_turn(). Use sparingly.
    PRIORITY_ACTIONS: dict[str, int] = {"kuo-toa_sticky_shield": 1}

    # Dictionary of skills and their associated ability
    SKILLS: dict[str, str] = {
        "acrobatics": "dex",
        "animal_handling": "wis",
        "arcana": "int",
        "athletics": "str",
        "deception": "cha",
        "history": "int",
        "insight": "wis",
        "intimidation": "cha",
        "investigation": "int",
        "medicine": "wis",
        "nature": "int",
        "perception": "wis",
        "performance": "cha",
        "persuasion": "cha",
        "religion": "int",
        "sleight_of_hand": "dex",
        "stealth": "dex",
        "survival": "wis",
        "str": "str",
        "dex": "dex",
        "con": "con",
        "int": "int",
        "wis": "wis",
        "cha": "cha",
    }

    def __init__(self, name: str = None, verbose: bool = False):
        """
        Constructor for the Creature class. Sets abilities, initializes
        features, resets the combat state, and rolls hit points.

        Parameters
        ----------
        name
            String to identify this Creature in verbose prints.
        verbose
            Whether to print information about this Creature during encounters.
        """

        # Set verbosity and creature name. Name is only used if verbose is True
        self.name = name
        self.verbose = verbose

        # Set creature stats
        self.abilities = {k: 0 for k in self.ABILITIES}
        self.alert = False
        self.armor_type = None
        self.attack_modifier = 0
        self.base_armor_class = 10
        self.blessed_healer = False
        self.blindsight = False
        self.charm_adv = False
        self.construct = False
        self.crit_dice_multiplier = 2
        self.crit_threshold = 20
        self.damage_modifier = 0
        self.disciple_of_life = False
        self.elusive = False
        self.empowered_evocation = False
        self.evasion = False
        self.ghoul_paralysis_immunity = False
        self.gnome_cunning = False
        self.heavy_armor_master = False
        self.immunities = {k: False for k in self.DAMAGE_TYPES}
        self.initiative_modifier = 0
        self.magic_resistance = False
        self.poison_adv = False
        self.potent_cantrip = False
        self.proficiency = 0
        self.resistances = {k: False for k in self.DAMAGE_TYPES}
        self.save_modifiers = {k: 0 for k in self.ABILITIES}
        self.save_proficiencies = {k: 0 for k in self.ABILITIES}
        self.skill_modifiers = {k: 0 for k in self.SKILLS}
        self.skill_proficiencies = {k: False for k in self.SKILLS}
        self.spell_attack_modifier = 0
        self.supreme_healing = False
        self.total_hit_dice = 1
        self.undead = None
        self.vulnerabilities = {k: False for k in self.DAMAGE_TYPES}
        self.war_caster = False

        # Initialize features. Utilized by derived classes.
        self.initialize_features()

        # Reset combat state and roll total hit points
        self.reset_hp()
        self.reset_conditions()

    def __call__(self) -> str:
        """
        Callable for the Creature class. Returns name and current hit points.
        """

        return f"{self.name} {self.hp:d}"

    def armor_class(self) -> int:
        """Determine armor class."""

        # Donned armor
        if self.armor_type == "heavy":
            ac = self.base_armor_class
        elif self.armor_type == "medium":
            ac = self.base_armor_class + min(2, self.abilities["dex"])
        else:
            ac = self.base_armor_class + self.abilities["dex"]

        # Shield spell
        if self.shield != None:
            ac += 5

        return ac

    def end_turn(self):
        """Activate effects that trigger at the end of a creature's turn."""

        for effect in self.end_turn_duration[:]:
            effect.end_turn_effect()

    def escape_grapple(self, adv: bool = False) -> int:
        """
        Roll an Athletics or Acrobatics check to escape a grapple.

        Parameters
        ----------
        adv
            Whether the skill check has advantage.
        """

        # Determine athletics and acrobatics modifiers
        athletics_modifier = self.abilities["str"] + self.skill_modifiers["athletics"]

        if self.skill_proficiencies["athletics"]:
            athletics_modifier += self.proficiency

        # Intrinsic advantage on athletics gives +5 on average
        if self.skill_adv["athletics"] > 0:
            athletics_modifier += 5

        acrobatics_modifier = self.abilities["dex"] + self.skill_modifiers["acrobatics"]

        if self.skill_proficiencies["acrobatics"]:
            acrobatics_modifier += self.proficiency

        # Intrinsic advantage on acrobatics gives +5 on average
        if self.skill_adv["acrobatics"] > 0:
            acrobatics_modifier += 5

        # Roll whichever skill has the higher modifier
        if athletics_modifier >= acrobatics_modifier:
            return self.roll_skill("athletics", adv=adv)
        else:
            return self.roll_skill("acrobatics", adv=adv)

    def fall_unconscious(self):
        """Fall unconscious from dropping to zero hit points."""

        # Death Ward
        if self.death_ward and self.total_hp > 0:

            self.death_ward = False
            self.hp = 1

            if self.verbose:
                print(f"{self()} used Death Ward")

            return

        # Fall prone
        self.prone = True

        # Stop grappling
        for grapple in self.grappling[:]:
            grapple.end()

        # Lose Concentration on spells
        if self.concentration != None:
            self.concentration.end()

    def get_total_hp(self) -> int:
        """Determine total hit points."""

        return max(
            1,
            self.hit_die(self.total_hit_dice)
            + self.total_hit_dice * self.abilities["con"],
        )

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
        """
        Determine the outcome of a saving throw for half damage on a success.

        Parameters
        ----------
        ability
            The ability used to make the saving throw.
        difficulty_class
            The difficulty class for success on the saving throw.
        damage
            The amount of damage taken on failure.
        damage_type
            Type of damage taken.
        secondary_damage
            The amount of damage of a second damage type taken on failure.
        secondary_type
            Type of secondary damage taken.
        adv
            Whether the saving throw has advantage.
        disadv
            Whether the saving throw has disadvantage.
        save_type
            String providing a label to handle creatures that have advantage on
            certain saves, e.g. charm, magic, or poison.
        """

        result = self.saving_throw(
            ability,
            difficulty_class,
            adv=adv,
            disadv=disadv,
            save_type=save_type,
        )

        # Full damage
        if not result and not (ability == "dex" and self.evasion):

            self.take_damage(
                damage,
                damage_type,
                secondary_damage=secondary_damage,
                secondary_type=secondary_type,
            )

        # Half damage for success without evasion or failure with evasion
        elif not (result and ability == "dex" and self.evasion):

            self.take_damage(
                int(damage / 2),
                damage_type,
                secondary_damage=int(secondary_damage / 2),
                secondary_type=secondary_type,
            )

        return result

    def has_attack_adv(self, target: "Creature", read_only: bool = False) -> bool:
        """
        Determine whether an attack against the target has advantage. The
        argument read_only will check but not modify conditions.

        Parameters
        ----------
        target
            Creature targeted by the attack
        read_only
            Check but don't modify limited use conditions such as Guiding Bolt.
        """

        # Guiding Bolt
        if target.guiding_bolt != None:
            if not read_only:
                target.guiding_bolt.end()

            return True

        else:
            return target.is_incapacitated() or (
                not target.elusive
                and (
                    self.attack_adv > 0
                    or target.target_adv > 0
                    or target.prone
                    or target.blinded > 0
                    or target.restrained > 0
                    or (self.is_hidden(target) and not target.alert)
                )
            )

    def has_attack_disadv(self, target: "Creature", read_only: bool = False):
        """
        Determine whether an attack against the target has disadvantage. The
        argument read_only will check but not modify conditions.

        Parameters
        ----------
        target
            Creature targeted by the attack
        read_only
            Check but don't modify limited use conditions such as Vicious Mockery.
        """

        # Vicious Mockery
        if self.vicious_mockery != None:
            if not read_only:
                self.vicious_mockery.end()

            return True

        else:
            return (
                self.attack_disadv > 0
                or target.target_disadv > 0
                or self.poisoned > 0
                or self.prone
                or self.blinded > 0
                or self.frightened > 0
                or self.restrained > 0
                or target.is_hidden(self)
            )

    def heal(self, healing: int, magic: bool = False):
        """
        Recover hit points up to maximum hit points.

        Parameters
        ----------
        healing
            Amount of hit points to recover.
        magic
            Whether the healing comes from a magical source.
        """

        self.hp += healing

        # Current hit points can't be higher than maximum hit points.
        if self.hp > self.total_hp:
            self.hp = self.total_hp

        if self.verbose:
            print(f"{self()} healed for {healing:d} hit points")

        # End effects that are ended by magical healing such as bleeding
        if magic:
            for effect in self.start_turn_duration[:]:
                if isinstance(effect, BleedingDuration):
                    effect.end()

    def hit_armor_class(
        self,
        attacker: "Creature",
        attack_roll: int,
        ranged=False,
    ) -> bool:
        """
        Determine whether an attack roll hits armor class. This can be
        overwritten by a derived class, e.g. for Parry or the Shield spell.

        Parameters
        ----------
        attacker
            Creature making the attack.
        attack_roll
            Value of the attack roll.
        ranged
            Whether the attack is ranged. Used in derived classes for abilities
            that trigger on melee attacks, e.g. Parry.
        """

        return attack_roll >= self.armor_class()

    def is_hidden(self, observer: "Creature") -> bool:
        """
        Determine whether the creature is hidden from an observer.

        Parameters
        ----------
        observer
            Creature trying to observe the hidden creature.
        """

        return (
            self.invisible > 0 or self.stealth > observer.passive_perception()
        ) and not observer.blindsight

    def is_incapacitated(self) -> bool:
        """Determine whether the creature is incapacitated."""

        return self.paralyzed > 0 or self.stunned > 0

    def passive_perception(self, adv: bool = False, disadv: bool = False) -> int:
        """
        Determine a creature's passive Perception.

        Parameters
        ----------
        adv
            Whether the Perception skill check has advantage.
        disadv
            Whether the Perception skill check has disadvantage.
        """

        result = (
            10
            + self.abilities[self.SKILLS["perception"]]
            + self.skill_modifiers["perception"]
        )

        # Advantage gives +5 on average
        if adv:
            result += 5

        # Disadvantage gives -5 on average
        if disadv:
            result -= 5

        if self.skill_proficiencies["perception"]:
            result += self.proficiency

        return result

    def reset_conditions(self):
        """
        Reset combat state, restoring conditions to their default state. This is
        called in between Encounters during an Adventuring Day.
        """

        self.action = False
        self.action_priority = []
        self.attack_adv = 0
        self.attack_disadv = 0
        self.baned = 0
        self.blessed = 0
        self.blinded = 0
        self.bonus = False
        self.concentration = None
        self.death_ward = False
        self.end_turn_duration = []
        self.engulfed = None
        self.frightened = 0
        self.grappled = []
        self.grappling = []
        self.guiding_bolt = None
        self.invisible = 0
        self.paralyzed = 0
        self.poisoned = 0
        self.prone = False
        self.reaction = False
        self.restrained = 0
        self.shield = None
        self.skill_adv = {k: 0 for k in self.SKILLS}
        self.skill_disadv = {k: 0 for k in self.SKILLS}
        self.slowed = 0
        self.spirit_guardians = []
        self.start_turn_duration = []
        self.stealth = 0
        self.stunned = 0
        self.surprised = True
        self.swallowed = None
        self.target_adv = 0
        self.target_disadv = 0
        self.turned = None
        self.vicious_mockery = None

    def reset_hp(self):
        """Reset hit points, including rerolling total hit points."""

        self.aid = False
        self.total_hp = self.get_total_hp()
        self.hp = self.total_hp

    def roll_initiative(self, adv: bool = False) -> int:
        """
        Make an initiative roll.

        Parameters
        ----------
        adv
            Whether the initiative roll has advantage.
        """

        return (
            roll_d20(advantage=adv, verbose=self.verbose)
            + self.abilities["dex"]
            + self.initiative_modifier
        )

    def roll_save(
        self,
        ability: str,
        adv: bool = False,
        disadv: bool = False,
    ) -> int:
        """
        Roll a saving throw.

        Parameters
        ----------
        ability
            The ability used to make the saving throw.
        adv
            Whether the saving throw has advantage.
        disadv
            Whether the saving throw has disadvantage.
        """

        result = (
            roll_d20(advantage=adv, disadvantage=disadv, verbose=self.verbose)
            + self.abilities[ability]
            + self.save_modifiers[ability]
        )

        if self.save_proficiencies[ability]:
            result += self.proficiency

        # Bane spell
        if self.baned:
            result -= d4()

        # Bless spell
        if self.blessed:
            result += d4()

        return result

    def roll_skill(self, skill, adv=False, disadv=False) -> int:
        """
        Roll a skill check.

        Parameters
        ----------
        skill
            The skill used to make the skill check.
        adv
            Whether the saving throw has advantage.
        disadv
            Whether the saving throw has disadvantage.
        """

        if self.skill_adv[skill] > 0:
            adv = True

        # Handle conditions that give disadvantage on skill checks, e.g.
        # Frightened or Poisoned
        if self.skill_disadv[skill] > 0 or self.frightened > 0 or self.poisoned > 0:
            disadv = True

        result = (
            roll_d20(
                advantage=adv,
                disadvantage=disadv,
                verbose=self.verbose,
            )
            + self.abilities[self.SKILLS[skill]]
            + self.skill_modifiers[skill]
        )

        if self.skill_proficiencies[skill]:
            result += self.proficiency

        return result

    def saving_throw(
        self,
        ability: str,
        difficulty_class: int,
        adv: bool = False,
        disadv: bool = False,
        save_type: str | None = None,
    ) -> bool:
        """
        Determine the outcome of a saving throw.

        Parameters
        ----------
        ability
            The ability used to make the saving throw.
        difficulty_class
            The difficulty class for success on the saving throw.
        adv
            Whether the saving throw has advantage.
        disadv
            Whether the saving throw has disadvantage.
        save_type
            String providing a label to handle creatures that have advantage on
            certain saves, e.g. charm, magic, or poison.
        """

        # Paralyzed or stunned creatures automatically fail Str and Dex saves
        if self.is_incapacitated() and (ability == "str" or ability == "dex"):
            return False

        # Restrained creatures have disadvantage on Dex saves
        if self.restrained > 0 and ability == "dex":
            disadv = True

        # Check features that give advantage on saves
        if (
            (self.charm_adv and save_type == "charm")
            or (
                self.gnome_cunning
                and save_type == "magic"
                and ability in ["int", "wis", "cha"]
            )
            or (self.magic_resistance and save_type == "magic")
            or (self.poison_adv and save_type == "poison")
        ):
            adv = True

        result = self.roll_save(ability, adv, disadv)

        if self.verbose:
            print(
                f"{self()} rolled {result:d} on a DC{difficulty_class:d} "
                f"{ability} saving throw"
            )

        return result >= difficulty_class

    def skill_check(self, skill, difficulty_class, adv=False, disadv=False):
        """
        Determine the outcome of a skill check.

        Parameters
        ----------
        skill
            The skill used to make the skill check.
        difficulty_class
            The difficulty class for success on the skill check.
        adv
            Whether the saving throw has advantage.
        disadv
            Whether the saving throw has disadvantage.
        """

        result = self.roll_skill(skill, adv, disadv)

        if self.verbose:
            print(
                f"{self()} rolled {result:d} on a DC{difficulty_class:d} "
                f"{skill} check"
            )

        return result >= difficulty_class

    def start_turn(self, encounter: "Encounter"):
        """
        Recover actions and activate effects that trigger at the start of a
        creature's turn. Then, if conscious and not incapacitated, take a turn.
        """

        self.surprised = False

        # Recover actions
        self.bonus = True

        # Turned undead must use their action to Dash
        if self.turned is None:
            self.action = True

            # Slowed creatures cannot use reactions
            if self.slowed == 0:
                self.reaction = True

        # Activate effects that trigger at the start of a creature's turn
        for effect in self.start_turn_duration[:]:
            effect.start_turn_effect()

        # Trigger highest level instance of Spirit Guardians
        if len(self.spirit_guardians) > 0 and self.hp > 0:
            self.spirit_guardians[0].start_turn_effect(self)

        # Take a normal turn
        if self.hp > 0 and not self.is_incapacitated():
            # Stand up from prone
            self.prone = False

            # Decrement duration of concentration spells
            if self.concentration is not None and self.concentration.duration > 0:

                self.concentration.duration -= 1
                if self.concentration.duration == 0:
                    self.concentration.end()

            # Take priority action from duration effects
            if self.action and len(self.action_priority) > 0:

                self.action = False
                action_priorities = [
                    self.PRIORITY_ACTIONS[effect.priority]
                    for effect in self.action_priority
                ]
                highest_priority = numpy.argmax(action_priorities)
                self.action_priority[highest_priority].take_priority_action()

            # Normal turn defined in derived class
            self.take_turn(encounter)

        # Activate effects that trigger at the end of a creature's turn
        self.end_turn()

    def take_damage_type(self, damage: int, damage_type: str) -> int:
        """
        Take damage of a specified type accounting for immunities, resistances,
        and vulnerabilities.

        Parameters
        ----------
        damage
            The amount of damage taken.
        damage_type
            Type of damage taken.
        """

        # Reduce physical damage by 3 for Heavy Armor Master
        if self.heavy_armor_master and damage_type in [
            "bludgeoning",
            "piercing",
            "slashing",
            "magic_bludgeoning",
            "magic_piercing",
            "magic_slashing",
        ]:
            damage -= 3

        # Apply resistance, then vulnerability, then immunity
        if self.resistances[damage_type]:
            damage = int(damage / 2)
        if self.vulnerabilities[damage_type]:
            damage *= 2
        if damage <= 0 or self.immunities[damage_type]:
            return 0

        self.hp -= damage

        # Hit points cannot be less than zero
        if self.hp < 0:
            self.hp = 0

        if self.verbose:
            print(f"{self()} took {damage:d} {damage_type} damage")

        return damage

    def take_damage(
        self,
        primary_damage: int,
        primary_type: str,
        dealer: "Creature | None" = None,
        ranged: bool = False,
        secondary_damage: int = 0,
        secondary_type: str | None = None,
    ) -> tuple[int, int]:
        """
        Resolve damage accounting for immunities, resistances, and vulnerabilities.

        Parameters
        ----------
        primary_damage
            The amount of damage taken.
        primary_damage_type
            Type of damage taken.
        dealer
            Creature making the attack that deals damage. This should be None
            for damage from sources that aren't attacks, e.g. effects that
            require saving throws or effects that deal damage in an area.
        ranged
            Whether the attack is ranged. Used in derived classes for abilities
            that trigger on melee attacks, e.g. remorhaz's Heated Body.
        secondary_damage
            The amount of damage taken of a second damage type.
        secondary_type
            Type of secondary damage taken.
        """

        primary_damage_taken = self.take_damage_type(primary_damage, primary_type)

        if secondary_type is not None:
            secondary_damage_taken = self.take_damage_type(
                secondary_damage,
                secondary_type,
            )

        else:
            secondary_damage_taken = 0

        damage_taken = primary_damage_taken + secondary_damage_taken

        # Fall unconscious if hit points are zero
        if self.hp == 0:
            self.fall_unconscious()

        # Check Concentration on spells
        if (
            self.concentration != None
            and damage_taken > 0
            and not self.saving_throw(
                "con",
                max(10, int(damage_taken / 2)),
                adv=self.war_caster,
            )
        ):
            self.concentration.end()

        # End turn undead
        if self.turned != None:
            self.turned.end()

        return primary_damage_taken, secondary_damage_taken

    def targeted_by_magic_missile(self):
        """
        For spellcasters, override this function to cast Shield as a reaction.
        """

        pass


class Character(Creature):
    """
    An abstract class that represents a player character, which overrides the
    function for determining maximum hit points and adds functions for taking
    short rests and long rests. For each D&D character class, e.g. Cleric, a
    derived Python class, e.g. class Cleric(Character), should be created that
    overrides the attribute hit_die and the following methods:
        end_encounter(self, encounter) to determine what to do at the end of an
            encounter (e.g. cast a healing spell on unconcscious allies)
        initialize_class_features(self) to initialize D&D class features (e.g.
            spell slots or the Fighter's Second Wind)
        initialize_features(self) to initialize general features (including
            abilities, armor class, and proficiency)
        reset_long_rest_features(self) to reset features that recover after a
            long rest
        reset_short_rest_features(self) to reset features that recover after a
            short rest
        set_usage_rates(self, encounters_per_long_rest, encounters_per_short_rest)
            to determine the maximum number of usages of class features per
            Encounter across an Adventuring Day
        start_encounter(self, encounter) to initialize effects at the beginning
            of an encounter
        take_turn(self, encounter) to determine how to take a turn in combat

    Attributes
    ----------
    ABILITIES
        List of abilities.
    DAMAGE_TYPES
        List of damage types.
    PRIORITY_ACTIONS
        Dictionary of priority actions and their associated priority.
    SKILLS
        Dictionary of skills and their associated ability.
    """

    def end_encounter(self, encounter: "Encounter"):
        """
        Determine what to do at the end of an encounter (e.g. cast a healing
        spell on unconcscious allies).
        """

        pass

    @abstractmethod
    def initialize_class_features(self):
        """
        Initialize D&D class features (e.g. spell slots or the Fighter's Second
        Wind)
        """

        pass

    def reset_long_rest_features(self):
        """Reset features that recover after a long rest."""

        pass

    def reset_short_rest_features(self):
        """Reset features that recover after a short rest."""

        pass

    def set_usage_rates(
        self,
        encounters_per_long_rest: int,
        encounters_per_short_rest: int,
    ):
        """
        Determine the maximum number of usages of class features per Encoutner
        across the Adventuring Day.

        Parameters
        ----------
        encounters_per_long_rest
            Number of encounters before a long rest during an Adventuring Day.
        encounters_per_short_rest
            Number of encounters before a short rest during an Adventuring Day.
        """

        pass

    def __init__(
        self,
        level: int,
        encounters_per_long_rest: int = 6,
        encounters_per_short_rest: int = 2,
        name: str = None,
        verbose: bool = False,
    ):
        """
        Constructor for the Character class. Initializes features, resets the
        combat state, and sets abilities, maximum hit points, and proficiency.

        Parameters
        ----------
        level
            Character level.
        encounters_per_long_rest
            Number of encounters before a long rest during an Adventuring Day.
        encounters_per_short_rest
            Number of encounters before a short rest during an Adventuring Day.
        name
            String to identify this Creature in verbose prints.
        verbose
            Whether to print information about this Creature during encounters.
        """

        # Set up hit dice
        self.level = level
        self.total_hit_dice = level
        self.hit_die_modifier = 0

        # Call constructor of base class Creature
        super().__init__(name=name, verbose=verbose)

        # Determine proficiency bonus
        self.proficiency = int((level - 1) / 4) + 2

        # Initialize class features
        self.initialize_class_features()
        self.set_usage_rates(encounters_per_long_rest, encounters_per_short_rest)
        self.reset_long_rest_features()
        self.reset_short_rest_features()

    def get_total_hp(self):
        # Override get_total_hp() to get maximum hit points at level one and the
        # mean rounded up for subsequent levels. Maximum hit points must be at
        # least one.

        # Level one: Number of sides on hit die + Con
        # Level two and greater: Mean of hit die + Con
        # Total HP = Sides + Con + (Level - 1) * (Mean + Con)
        # Total HP = Sides - Mean + Level * (Mean + Con)
        return max(
            1,
            self.hit_die.sides
            - self.hit_die.mean
            + self.level * (self.hit_die.mean + self.abilities["con"]),
        )

    def long_rest(self):
        """Take a long rest."""

        self.reset_conditions()
        self.reset_hp()
        self.reset_short_rest_features()
        self.reset_long_rest_features()

    def reset_hp(self):
        # Extend reset_hp() to recover hit dice
        super().reset_hp()
        self.N_hit_dice = self.total_hit_dice

    def short_rest(self):
        """
        Take a short rest, rolling hit dice to recover hit points if needed.
        """

        # Reset combat state and short rest class features
        self.reset_conditions()
        self.reset_short_rest_features()

        # Reset ability damage
        self.abilities = {k: self.base_abilities[k] for k in self.base_abilities}

        # Threshold to roll a hit die is half your total hit points or the
        # maximum value of a roll, whichever is smaller
        hit_die_threshold = self.total_hp - min(
            int(self.total_hp / 2), self.hit_die.sides + self.hit_die_modifier
        )

        # Roll hit dice until hit points exceed the threshold
        while self.hp > 0 and self.N_hit_dice > 0 and self.hp <= hit_die_threshold:

            self.N_hit_dice -= 1
            self.heal(self.hit_die() + self.abilities["con"] + self.hit_die_modifier)


class LairAction:
    """
    A class that represents a lair action that activates on initiative count 20.
    A derived class can be created that overrides
    start_encounter(self, encounter) to initialize effects at the beginning of
    an encounter
    """

    def start_encounter(self, encouter: "Encounter"):
        """
        Initialize effects at the beginning of an encounter.

        Parameters
        ----------
        encounter
            The Encounter in which the effects take place.
        """

        pass

    def __init__(self, creature: Creature):
        """
        Constructor for the Lair Action class. Sets the creature performing the
        lair action and sets hit points to one so that Encounter triggers
        start_turn().

        Parameters
        ----------
        creature
            The Creature performing that lair action.
        """

        self.creature = creature
        self.hp = 1

    def __call__(self) -> str:
        """
        Callable for the Lair Action class. Returns the name of the Creature
        performing the lair action.
        """

        return f"{self.creature.name} lair ()"

    def roll_initiative(self):
        """Set initiative to 20."""

        return 20

    def start_turn(self, encounter: "Encounter"):
        """
        Take the lair action if the owning creature is conscious and not
        incapacitated.

        Parameters
        ----------
        encounter
            The Encounter in which the lair action takes place.
        """

        if self.creature.hp > 0 and not self.creature.is_incapacitated():
            self.creature.lair_action(encounter)


class LegendaryAction(Duration):
    """
    Class for a legendary action that activates at the end of a turn. Unlike
    other classes derived from Duration, this class has no duration or end()
    method.
    """

    def __init__(self, creature: Creature, encounter: "Encounter"):
        """
        Constructor for the LegendaryAction class.

        Parameters
        ----------
        creature
            The Creature performing the legendary action.
        encounter
            The Encounter in which the legendary action takes place.
        """

        self.creature = creature
        self.encounter = encounter

    def end_turn_effect(self):
        """
        At the end of the creature's turn, take a legendary action if conscious
        and not incapacitated.
        """

        if (
            self.creature.N_legendary_action > 0
            and self.creature.hp > 0
            and not self.creature.is_incapacitated()
        ):
            self.creature.N_legendary_action -= 1
            self.creature.legendary_action(self.encounter)


class LegendaryCreature(Creature):
    """
    An abstract class representing a creature with legendary actions. For each
    unique legendary creature, a derived class should be created with the
    following methods:
        initialize_features(self) to initialize creature features (including
            abilities, armor class, and proficiency)
        legendary_action(self, encounter) to determine how to take a use a
            legendary action at the end of a turn
        take_turn(self, encounter) to determine how to take a turn in combat
    """

    @abstractmethod
    def legendary_action(self, encounter):
        """
        Determine how to take a legendary action at the end of a turn.

        Parameters
        ----------
        encounter
            The Encounter in which the legendary action takes place.
        """

        pass

    def __init__(self, name=None, verbose=False):
        """
        Constructor for the LegendaryCreature class. Sets abilities, initializes
        features, resets the combat state, and rolls hit points.

        Parameters
        ----------
        name
            String to identify this Creature in verbose prints.
        verbose
            Whether to print information about this Creature during encounters.
        """

        # Initialize number of legendary actions per turn to zero
        self.total_legendary_actions = 0

        super().__init__(name=name, verbose=verbose)

    def reset_conditions(self):
        # Extend reset_conditions() to reset legendary actions
        super().reset_conditions()
        self.N_legendary_action = self.total_legendary_actions

    def start_encounter(self, encounter):
        """
        Add the legendary action to end_turn_duration for every other Creature
        at the beginning of an Encounter.

        Parameters
        ----------
        encounter
            The Encounter in which the effects take place.
        """

        legendary_action = LegendaryAction(self, encounter)

        for creature in encounter.side_A + encounter.side_B:
            if creature is not self:
                creature.end_turn_duration.append(legendary_action)

    def start_turn(self, encounter):
        """
        Extend start_turn() to recover legendary actions.

        Parameters
        ----------
        encounter
            The Encounter in which the effects take place.
        """

        self.N_legendary_action = self.total_legendary_actions
        super().start_turn(encounter)


class Weapon:
    """Implements weapon attacks and damage, including critical hits."""

    def __init__(
        self,
        wielder: Creature,
        dice: Die | Dice,
        damage_type: str,
        ability: str = "str",
        proficient: bool = True,
        ranged: bool = False,
        secondary_dice: Die | Dice | None = None,
        secondary_type: str | None = None,
        attack_modifier: int = 0,
        damage_modifier: int = 0,
    ):
        """
        Initialize the weapon features.

        Parameters
        ----------
        wielder
            The Creature wielding the weapon.
        dice
            The die or dice rolled for the weapon's damage.
        damage_type
            Type of damage dealt by the weapon.
        ability
            Ability modifier used for attack and damage rolls.
        proficient
            Whether the creature is proficient with the weapon.
        ranged
            Whether the weapon's attacks are ranged. Used to handle effects that
            trigger on melee attacks, e.g. remorhaz's Heated Body.
        secondary_dice
            The die or dice rolled for the weapon's damage of a second damage type.
        secondary_type
            Type of secondary damage dealt by the weapon.
        attack_modifier
            Modifier added to attack rolls, e.g. for a magic weapon.
        damage_modifier
            Modifier added to damage rolls, e.g. for a magic weapon.
        """

        self.wielder = wielder
        self.dice = dice
        self.damage_type = damage_type
        self.ability = ability
        self.proficient = proficient
        self.ranged = ranged
        self.secondary_dice = secondary_dice
        self.secondary_type = secondary_type
        self.weapon_attack_modifier = attack_modifier
        self.weapon_damage_modifier = damage_modifier

    def __call__(
        self,
        target: Creature,
        adv: bool = False,
        disadv: bool = False,
        add_ability: bool = True,
        great_weapon_master: bool = False,
    ) -> str | None:
        """
        Callable for the Weapon class. Makes an attack roll and resolves damage.

        Parameters
        ----------
        target
            Creature targeted by the weapon attack.
        adv
            Whether the weapon attack has advantage.
        disadv
            Whether the weapon attack has disadvantage.
        add_ability
            Whether to add the wielder's ability modifier to the damage roll.
        great_weapon_master
            Whether the attack uses Great Weapon Master.
        """

        # Invalid target
        if target is None:
            return None

        attack_result = self.roll_attack(
            target,
            adv=adv,
            disadv=disadv,
            great_weapon_master=great_weapon_master,
        )

        if attack_result == "hit" or attack_result == "crit":
            if target.paralyzed > 0:
                attack_result = "crit"

            dice_multiplier = 1
            if attack_result == "crit":
                dice_multiplier = self.wielder.crit_dice_multiplier

            damage = self.roll_damage(
                add_ability=add_ability,
                dice_multiplier=dice_multiplier,
                great_weapon_master=great_weapon_master,
            )

            if self.secondary_dice != None:

                secondary_damage = self.roll_secondary_damage(
                    dice_multiplier=dice_multiplier
                )

                if self.wielder.verbose:
                    print(
                        f"{self.wielder()} scored a {attack_result} on "
                        f"{target()} for {damage:d} {self.damage_type} and "
                        f"{secondary_damage:d} {self.secondary_type} damage"
                    )

                target.take_damage(
                    damage,
                    self.damage_type,
                    dealer=self.wielder,
                    ranged=self.ranged,
                    secondary_damage=secondary_damage,
                    secondary_type=self.secondary_type,
                )

            else:
                if self.wielder.verbose:
                    print(
                        f"{self.wielder()} scored a {attack_result} on "
                        f"{target()} for {damage:d} {self.damage_type} damage"
                    )

                target.take_damage(
                    damage,
                    self.damage_type,
                    dealer=self.wielder,
                    ranged=self.ranged,
                )

        return attack_result

    def roll_attack(
        self,
        target: Creature,
        adv: bool = False,
        disadv: bool = False,
        great_weapon_master: bool = False,
    ) -> str:
        """
        Make an attack roll.

        Parameters
        ----------
        target
            Creature targeted by the weapon attack.
        adv
            Whether the weapon attack has advantage.
        disadv
            Whether the weapon attack has disadvantage.
        great_weapon_master
            Whether to apply the penalty from Great Weapon Master to the attack
            roll.
        """

        raw_roll = roll_d20(
            advantage=adv or self.wielder.has_attack_adv(target),
            disadvantage=disadv or self.wielder.has_attack_disadv(target),
            verbose=self.wielder.verbose,
        )

        attack = (
            self.wielder.abilities[self.ability]
            + self.wielder.attack_modifier
            + self.weapon_attack_modifier
        )

        if self.proficient:
            attack += self.wielder.proficiency

        # Bane spell
        if self.wielder.baned:
            attack -= d4()

        # Bless spell
        if self.wielder.blessed:
            attack += d4()

        # Great Weapon Master penalty
        if great_weapon_master:
            attack -= 5

        if self.wielder.verbose:
            print(
                f"{self.wielder()} rolled {raw_roll + attack:d} on an attack "
                f"against {target()} with AC {target.armor_class():d}"
            )

        if raw_roll >= self.wielder.crit_threshold:
            return "crit"

        elif raw_roll > 1 and target.hit_armor_class(
            self.wielder,
            raw_roll + attack,
            ranged=self.ranged,
        ):
            return "hit"

        else:
            return "miss"

    def roll_damage(
        self,
        add_ability: bool = True,
        great_weapon_master: bool = False,
        dice_multiplier: int = 1,
    ) -> int:
        """
        Roll damage dice for a hit or critical hit.

        Parameters
        ----------
        add_ability
            Whether to add the wielder's ability modifier to the damage roll.
        great_weapon_master
            Whether to add the bonus from Great Weapon Master to the damage
            roll.
        dice_multiplier
            Number of damage dice to roll on a critical hit.
        """

        # Damage for regular hit
        damage = (
            self.dice() + self.wielder.damage_modifier + self.weapon_damage_modifier
        )

        if add_ability:
            damage += self.wielder.abilities[self.ability]

        # Great Weapon Master bonus
        if great_weapon_master:
            damage += 10

        # Additional damage dice for a critical hit
        for i in range(1, dice_multiplier):
            damage += self.dice()

        return damage

    def roll_secondary_damage(self, dice_multiplier: int = 1) -> int:
        """
        Roll secondary damage dice for a hit or critical hit.

        Parameters
        ----------
        dice_multiplier
            Number of damage dice to roll on a critical hit.
        """

        # Damage for regular hit
        damage = self.secondary_dice()

        # Additional damage dice for a critical hit
        for i in range(1, dice_multiplier):
            damage += self.secondary_dice()

        return damage
