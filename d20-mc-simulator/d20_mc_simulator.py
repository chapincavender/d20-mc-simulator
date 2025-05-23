"""
    Simulates simple combat in D&D 5e for playtesting custom monsters
"""

import click
import numpy

from adventuring_day import AdventuringDay
from creature import Character, Creature
from custom_bestiary import custom_creatures
from mm_bestiary import mm_creatures
from party import player_characters


def create_party(
    classes: list[str],
    party_level: int,
    verbose: bool,
) -> list[Character]:
    """
    Create a list of player characters at the specified party level.

    Parameters
    ----------
    classes
        List of class names for each player character.
    party_level
        Character level of each player characters.
    verbose
        Whether to print detailed combat information.
    """

    return [
        player_characters[character](party_level, name=character, verbose=verbose)
        for character in classes
    ]


def create_adversaries(
    creature_list: list[str],
    N_creature_list: list[int],
    verbose: bool,
) -> list[Creature]:
    """
    Create a list of adversaries.

    Parameters
    ----------
    creature_list
        List of creature names for each adversary type.
    N_creature_list
        List of number of creatures for each adversary type.
    verbose
        Whether to print detailed combat information.
    """

    adversaries = list()

    for creature, N_creatures in zip(creature_list, N_creature_list):
        if creature in custom_creatures:
            creature_type = custom_creatures[creature]
        elif creature in mm_creatures:
            creature_type = mm_creatures[creature]
        else:
            raise ValueError(f"Unknown creature type {creature}")

        adversaries.extend(
            [
                creature_type(name=f"{creature}{i:d}", verbose=verbose)
                for i in range(1, N_creatures + 1)
            ]
        )

    return adversaries


@click.command()
@click.option(
    "-a",
    "--adventuring-days",
    default=1000,
    show_default=True,
    type=click.INT,
    help="Number of adventuring days to simulate.",
)
@click.option(
    "-c",
    "--classes",
    default="Cleric,Fighter,Rogue,Wizard",
    show_default=True,
    type=click.STRING,
    help="Comma-separated list of player character classes to simulate.",
)
@click.option(
    "-d/-s",
    "--debug/--survival",
    default=False,
    help="Run a single adventuring day with verbose information during encounters.",
)
@click.option(
    "-m",
    "--monsters",
    default="Kobold",
    show_default=True,
    type=click.STRING,
    help="Comma-separated list of creature types to simulate.",
)
@click.option(
    "-n",
    "--num-monsters",
    default="4",
    show_default=True,
    type=click.STRING,
    help="Comma-separated list of number of creatures to simulate.",
)
@click.option(
    "-p",
    "--party-level",
    default=1,
    show_default=True,
    type=click.INT,
    help="Character level for the party of PCs to simulate.",
)
@click.option(
    "-t",
    "--test-stats",
    default=None,
    show_default=True,
    type=click.STRING,
    help="Comma-separated list of six stats for test creature.",
)
@click.option(
    "-v/-l",
    "--verbose/--laconic",
    default=False,
    help="Print detailed information about PC and creatures during encounters.",
)
def main(
    adventuring_days: int,
    classes: str,
    debug: bool,
    monsters: str,
    num_monsters: str,
    party_level: int,
    test_stats: str,
    verbose: bool,
):
    character_list = classes.strip("'\"").split(",")
    creature_list = monsters.strip("'\"").split(",")
    N_creature_list = [int(N) for N in num_monsters.strip("'\"").split(",")]

    if len(creature_list) != len(N_creature_list):
        raise ValueError(
            f"Number of creature types {len(creature_list)} does not match number of creature counts {len(N_creature_list)}"
        )

    if debug:
        # Run a single adventuring day to debug PC or creature behavior

        # Set up party of PCs
        pcs = create_party(character_list, party_level, verbose=True)

        # Set up adversaries
        adversaries = create_adversaries(creature_list, N_creature_list, verbose=True)

        # Resolve a single adventuring day
        adventuring_day = AdventuringDay(pcs, adversaries)
        adventuring_day()

    else:
        # Set up party of PCs
        pcs = create_party(character_list, party_level, verbose)

        # Set up adversaries
        if "Test" in creature_list:
            # Parse test_stats argument
            if test_stats is None:
                raise ValueError(
                    "Argument --test-stats must be set for creature type Test."
                )

            test_stats_list = [int(s) for s in test_stats.split(",")]
            if len(test_stats_list) == 6:
                attack, armor_class, damage, hit_points, N_attacks, proficiency = (
                    test_stats_list
                )
            else:
                raise ValueError(
                    "Argument --test-stats must be a comma-separated list of six values."
                )

            test_name = f"Test {attack:2d} {armor_class:2d} {damage:2d} {hit_points:2d} {N_attacks:2d} {proficiency:2d}"
            adversaries = [
                custom_creatures["Test"](
                    attack,
                    armor_class,
                    damage,
                    hit_points,
                    N_attacks=N_attacks,
                    proficiency=proficiency,
                    name=test_name,
                    verbose=verbose,
                )
                for i in range(N_creature_list[0])
            ]
            adversary_str = f"{test_name} {N_creature_list[0]}"

        else:
            adversaries = create_adversaries(creature_list, N_creature_list, verbose)
            adversary_str = " ".join(
                [
                    f"{creature} {N_creatures}"
                    for creature, N_creatures in zip(creature_list, N_creature_list)
                ]
            )

        # Set up adventuring day
        adventuring_day = AdventuringDay(pcs, adversaries)
        survival = numpy.zeros(adventuring_days, dtype="int32")

        # Resolve the first adventuring day
        adventuring_day()
        survival[0] = numpy.sum([character.hp > 0 for character in pcs])

        # Take a long rest and resolve more adventuring days
        for day in range(1, adventuring_days):
            adventuring_day.reset_adversaries()
            adventuring_day.take_long_rest()
            adventuring_day()
            survival[day] = numpy.sum([character.hp > 0 for character in pcs])

        # Print mean number of survivors and standard deviation
        mean_survival = numpy.mean(survival)
        std_survival = numpy.std(survival, ddof=1)
        print(
            f"Level {party_level:2d} {adversary_str} Survival {mean_survival:6.4f} +/- {std_survival:6.4f}"
        )


if __name__ == "__main__":
    main()
