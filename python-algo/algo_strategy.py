import gamelib
import random
import math
import warnings
from sys import maxsize
import json


"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips:

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical
  board states. Though, we recommended making a copy of the map to preserve
  the actual current map state.
"""


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        """
        Read in config and perform any initial setup here
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global FILTER, ENCRYPTOR, DESTRUCTOR, PING, EMP, SCRAMBLER, BITS, CORES
        FILTER = config["unitInformation"][0]["shorthand"]
        ENCRYPTOR = config["unitInformation"][1]["shorthand"]
        DESTRUCTOR = config["unitInformation"][2]["shorthand"]
        PING = config["unitInformation"][3]["shorthand"]
        EMP = config["unitInformation"][4]["shorthand"]
        SCRAMBLER = config["unitInformation"][5]["shorthand"]
        BITS = 0
        CORES = 1
        # This is a good place to do initial setup
        self.scored_on_locations = []
        # PING, EMP, SCRAMBLER
        self.scored_type = [0, 0, 0]

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(
            game_state.turn_number))
        # Comment or remove this line to enable warnings.
        game_state.suppress_warnings(True)

        self.starter_strategy(game_state)

        game_state.submit_turn()

    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def starter_strategy(self, game_state):
        """
        For defense we will use a spread out layout and some Scramblers early on.
        We will place destructors near locations the opponent managed to score on.
        For offense we will use long range EMPs if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Pings to try and score quickly.
        """
        # First, place basic defenses
        self.build_defences(game_state)
        # repair defenses
        self.repair_defense(game_state)

        # send out scramblers if they're sending ton of EMPs
        if game_state.get_resource(BITS, 1) > 20:
            game_state.attempt_spawn(SCRAMBLER, [21, 7], 2)
        elif game_state.get_resource(BITS, 1) > 10:
            game_state.attempt_spawn(SCRAMBLER, [21, 7], 1)

        if game_state.get_resource(BITS, 0) > 13+min(game_state.turn_number/10, 5):
            # check if they have lots of destructors
            # if they do, send EMPs
            # if not, send pings
            num_dest = 0
            threat_loc = [[27, 14], [26, 14], [25, 14], [24, 14],
                          [23, 14], [26, 15], [25, 15], [24, 15], [25, 16]]
            for p in threat_loc:
                if game_state.game_map[p]:
                    if game_state.game_map[p][0].unit_type == DESTRUCTOR:
                        num_dest += 1
                    else:
                        num_dest += 0.5
            if num_dest > 2.5:
                game_state.attempt_spawn(EMP, [21, 7], 6)
            else:
                game_state.attempt_spawn(PING, [5, 8], 3)
                game_state.attempt_spawn(PING, [4, 9], 100)

    def build_defences(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy EMPs can attack them.
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download

        # Place destructors that attack enemy units
        destructor_locations = [[3, 12], [24, 12], [13, 9]]

        corner_left = [[0, 13], [1, 13], [2, 13], [3, 13]]
        corner_right = [[24, 13], [25, 13], [27, 13]]
        fort_left = False
        fort_right = False
        # attempt_spawn will try to spawn units if we have resources, and will check if a blocking unit is already there
        game_state.attempt_spawn(DESTRUCTOR, destructor_locations)
        if (game_state.turn_number <= 10):
            # Place filters in front of destructors to soak up damage for them
            center_locations = [[4, 12], [4, 11], [23, 12], [23, 11], [12, 10], [13, 10], [14, 10], [12, 9], [14, 9], [5, 10], [22, 10], [6, 9], [21, 9], [7, 10], [20, 10],
                                [8, 10], [19, 10], [9, 10], [18, 10], [10, 10], [17, 10], [11, 10], [16, 10], [15, 10]]
            filter_locations = center_locations + corner_left + corner_right
            game_state.attempt_spawn(FILTER, filter_locations)
        else:
            # check for left or right breach
            left = 0
            right = 0
            for p in self.scored_on_locations:
                if p in game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT):
                    left += 1
                else:
                    right += 1
            if left > 5:
                fort_left = True
            if right > 5:
                fort_right = True
            filter_locations = [[4, 12], [4, 11], [12, 10], [13, 10], [14, 10], [12, 9], [14, 9], [5, 10], [6, 9], [7, 10], [20, 10], [8, 10], [19, 10], [9, 10], [18, 10],
                                [10, 10], [17, 10], [11, 10], [16, 10], [15, 10]]
            if not fort_right:
                filter_locations = filter_locations + corner_right
            if not fort_left:
                filter_locations = filter_locations + corner_left
            game_state.attempt_spawn(FILTER, filter_locations)
        destructor_locations = [[8, 9], [19, 9]]
        game_state.attempt_spawn(DESTRUCTOR, destructor_locations)

        dest_left = [[2, 12], [1, 12], [2, 11],
                     [4, 10], [3, 11], [7, 9], [4, 10]]
        # fortify weak side, right side first
        if fort_right:
            for p in corner_right:
                if game_state.game_map[p]:
                    if game_state.game_map[p][0].unit_type == FILTER and game_state.get_resource(CORES, 0) > 6:
                        game_state.attempt_remove(p)
                game_state.attempt_spawn(DESTRUCTOR, p)

        if fort_left:
            for p in corner_left:
                if game_state.game_map[p]:
                    if game_state.game_map[p][0].unit_type == FILTER and game_state.get_resource(CORES, 0) > 6:
                        game_state.attempt_remove(p)
                game_state.attempt_spawn(DESTRUCTOR, p)
            for p in dest_left:
                if game_state.game_map[p]:
                    if game_state.game_map[p][0].unit_type == FILTER and game_state.get_resource(CORES, 0) > 6:
                        game_state.attempt_remove(p)
                game_state.attempt_spawn(DESTRUCTOR, p)

        encryptor_locations = [[21, 10], [22, 11],
                               [23, 12], [23, 11], [22, 10], [21, 9]]
        if (game_state.turn_number > 10):
            for p in encryptor_locations:
                if game_state.game_map[p]:
                    if game_state.game_map[p][0].unit_type == FILTER and game_state.get_resource(CORES, 0) > 4:
                        game_state.attempt_remove(p)
                game_state.attempt_spawn(ENCRYPTOR, p)

    def repair_defense(self, game_state):
        game_map = game_state.game_map
        my_positions = [[x, y] for x in range(game_map.ARENA_SIZE) for y in range(game_map.HALF_ARENA) if game_map.in_arena_bounds([
            x, y])]
        for p in my_positions:
            if game_map[p]:
                unit = game_map[p][0]
                if (game_state.get_resource(BITS, 1) < 8):
                    if (unit.health < 30 and not unit.unit_type == ENCRYPTOR):
                        game_state.attempt_remove(p)

    def stall_with_scramblers(self, game_state):
        """
        Send out Scramblers at random locations to defend our base from enemy moving units.
        """
        # # We can spawn moving units on our edges so a list of all our edge locations
        # friendly_edges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)

        # # Remove locations that are blocked by our own firewalls
        # # since we can't deploy units there.
        # deploy_locations = self.filter_blocked_locations(friendly_edges, game_state)

        # While we have remaining bits to spend lets send out scramblers randomly.
        game_state.attempt_spawn(SCRAMBLER, [9, 4])
        game_state.attempt_spawn(SCRAMBLER, [18, 4])
        """
            We don't have to remove the location since multiple information
            units can occupy the same space.
            """

    def emp_line_strategy(self, game_state):
        """
        Build a line of the cheapest stationary unit so our EMP's can attack from long range.
        """
        # First let's figure out the cheapest unit
        # We could just check the game rules, but this demonstrates how to use the GameUnit class
        stationary_units = [FILTER, DESTRUCTOR, ENCRYPTOR]
        cheapest_unit = FILTER
        for unit in stationary_units:
            unit_class = gamelib.GameUnit(unit, game_state.config)
            if unit_class.cost < gamelib.GameUnit(cheapest_unit, game_state.config).cost:
                cheapest_unit = unit

        # Now let's build out a line of stationary units. This will prevent our EMPs from running into the enemy base.
        # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
        for x in range(27, 5, -1):
            game_state.attempt_spawn(cheapest_unit, [x, 11])

        # Now spawn EMPs next to the line
        # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
        game_state.attempt_spawn(EMP, [24, 10], 1000)

    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path:
                # Get number of enemy destructors that can attack the final location and multiply by destructor damage
                damage += len(game_state.get_attackers(path_location, 0)) * \
                    gamelib.GameUnit(DESTRUCTOR, game_state.config).damage
            damages.append(damage)

        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x=None, valid_y=None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units

    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at: https://docs.c1games.com/json-docs.html
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            u_type = breach[2]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly,
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                if u_type == PING:
                    self.scored_type[0] += 1
                    gamelib.debug_write("A ping scored")
                elif u_type == EMP:
                    self.scored_type[1] += 1
                    gamelib.debug_write("An EMP scored")
                else:
                    self.scored_type[2] += 2
                    gamelib.debug_write("A scrambler scored")
                gamelib.debug_write(
                    "All locations: {}".format(self.scored_on_locations))


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
