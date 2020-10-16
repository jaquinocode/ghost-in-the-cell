import sys
from itertools import zip_longest, combinations

def log(*args_tuple):
    print(*args_tuple, file=sys.stderr)

class Game:
    def __init__(self):
        self.game_turn = 0
        self.base_count = 0
        self.distances = {}
        self.my_side_base_ids = []
        self.closest_nodes = {}

        self.my_bases = {}
        self.enemy_bases = {}
        self.neutral_bases = {}
        self.true_defenses = {}

        self.my_troops = {}
        self.enemy_troops = {}

        self.base_dicts = [self.my_bases, self.enemy_bases, self.neutral_bases]
        self.troop_dicts = [self.my_troops, self.enemy_troops]
        self.changeable_data_dicts = self.base_dicts + self.troop_dicts + [self.true_defenses]

        self.bombs_sent = 0
        self.turn_of_last_bomb = float("-inf")
    
    def load_init_data(self):
        self.base_count = int(input())

        # basic conversion of input to an actual dataset
        link_count = int(input())
        for _ in range(link_count):
            base1, base2, dist = map(int, input().split())
            
            self.distances[frozenset((base1, base2))] = dist

        # create a dataset that shows which nodes are closest to a given node, could be more than one
        gen = (base_pair for base_pair in self.distances if 0 in base_pair)
        closest_pair = min(gen, key=lambda pair: self.distances[pair], default=None)
        for id in closest_pair:
            if id != 0:
                closest_id = id

        log(closest_id)

        # self.closest_nodes[boss_node] = closest_id
        # add smallest key to res list, then add that list to our closest node dict
        # now add any other keys that tied with the winner


    def load_game_turn_input(self):
        self.game_turn += 1
        # clean bases & troops data in prep for getting this turn's data
        for d in self.changeable_data_dicts:
            d.clear()

        # start accepting game turn inputs
        # load game state info into respective data structures (just base & troop info)
        entity_count = int(input())  # the number bases & troops
        for _ in range(entity_count):
            # convert inputs into proper types
            entity_id, entity_type, arg_1, arg_2, arg_3, arg_4, arg_5 = input().split()  # a thing's info
            entity_id, arg_1, arg_2, arg_3, arg_4, arg_5 = map(int, (entity_id, arg_1, arg_2, arg_3, arg_4, arg_5))

            if entity_type == "FACTORY":
                base_owner, cyborgs, production = arg_1, arg_2, arg_3
                base_owner = "myself" if base_owner == 1 else "enemy" if base_owner == -1 else "neutral"

                if base_owner == "myself":
                    self.my_bases[entity_id] = {"owner": base_owner, "cyborgs": cyborgs, "prod": production}
                elif base_owner == "enemy":
                    self.enemy_bases[entity_id] = {"owner": base_owner, "cyborgs": cyborgs, "prod": production}
                elif base_owner == "neutral":
                    self.neutral_bases[entity_id] = {"owner": base_owner, "cyborgs": cyborgs, "prod": production}
            elif entity_type == "TROOP":
                troop_owner, source, target, cyborgs, turns_left = arg_1, arg_2, arg_3, arg_4, arg_5
                troop_owner = "myself" if troop_owner == 1 else "enemy"

                if troop_owner == "myself":
                    self.my_troops[entity_id] = {"owner": troop_owner, "source": source, "target": target, "cyborgs": cyborgs, "ETA": turns_left}
                elif troop_owner == "enemy":
                    self.enemy_troops[entity_id] = {"owner": troop_owner, "source": source, "target": target, "cyborgs": cyborgs, "ETA": turns_left}

        # get all the ids from my side bases (bases closer to me than enemy)
        try:
            base_ids = (id for base_dict in self.base_dicts for id in base_dict)
            home_base_id = list(self.my_bases)[0]
            enemy_base_id = list(self.enemy_bases)[0]
        except IndexError:
            pass
        else:
            for id in base_ids:
                dist_to_home_base = self.get_dist(id, home_base_id)
                dist_to_enemy_base = self.get_dist(id, enemy_base_id)

                if dist_to_home_base < dist_to_enemy_base:
                    self.my_side_base_ids.append(id)

        # load each base id's true defenses
        base_ids = (id for base_dict in self.base_dicts for id in base_dict)
        for id in base_ids:
            self.true_defenses[id] = self.calc_true_def(id)

    def get_type(self, id):
        if id in self.my_bases or id in self.enemy_bases or id in self.neutral_bases:
            return "base"
        elif id in self.my_troops or id in self.enemy_troops:
            return "troop"

    def get_owner(self, id):
        if id in self.my_bases:
            return self.my_bases[id]["owner"]
        elif id in self.neutral_bases:
            return self.neutral_bases[id]["owner"]
        elif id in self.enemy_bases:
            return self.enemy_bases[id]["owner"]
        elif id in self.my_troops:
            return self.my_troops[id]["owner"]
        elif id in self.enemy_troops:
            return self.enemy_troops[id]["owner"]

    def get_cyborgs(self, id):
        if id in self.my_bases:
            return self.my_bases[id]["cyborgs"]
        elif id in self.neutral_bases:
            return self.neutral_bases[id]["cyborgs"]
        elif id in self.enemy_bases:
            return self.enemy_bases[id]["cyborgs"]
        elif id in self.my_troops:
            return self.my_troops[id]["cyborgs"]
        elif id in self.enemy_troops:
            return self.enemy_troops[id]["cyborgs"]

    def get_prod(self, id):
        if id in self.my_bases:
            return self.my_bases[id]["prod"]
        elif id in self.neutral_bases:
            return self.neutral_bases[id]["prod"]
        elif id in self.enemy_bases:
            return self.enemy_bases[id]["prod"]

    def calc_true_def(self, id):
        # if we consider a base's cyborgs its defense, its true defense considers production, reinforcements, incoming attacks, etc.
        # distance is attacker dependant so instead that'll be taken into account when the attacker is calculating whether it wants to attack
        # diff calc for diff bases, e.g. neutral bases don't have prod so its def will be different
        average_dist = 4
        cyborgs = self.get_cyborgs(id)
        owner = self.get_owner(id)
        prod = self.get_prod(id)
        incoming_reinforcements = self.get_incoming_reinforcements(id)
        incoming_attacks = self.get_incoming_attacks(id)
        
        true_def = 0
        if owner == "enemy":
            true_def = cyborgs + average_dist*prod + incoming_reinforcements - incoming_attacks
            true_def = abs(true_def)  # neg value means it'll be conquered so this will give its future defense after conquer
        elif owner == "neutral":
            # problem that after conquer the calc gets reinforcements from winning side, neg number here doesn't describe this very well
            true_def = cyborgs - incoming_attacks 
            true_def = abs(true_def)  
        elif owner == "myself":
            true_def = cyborgs + average_dist*prod + incoming_reinforcements - incoming_attacks
            true_def = abs(true_def)
        return true_def

    def get_true_def(self, id):
        # because we're getting value from saved data, this might be an old value if you've altered the game state after true def calculation
        return self.true_defenses[id]

    def desire_score(self, id):
        """Gives score to a base symbolizing desirability to send troops to said base. Lower the better.
        """
        prod = self.get_prod(id)
        true_def = self.get_true_def(id)

        # accounting for cheaters (dud w/ no defense), bases that cheat the system & get way too good scores cause of 0 values
        if true_def == 0 and prod == 0:
            true_def = 1

        # for all duds, has effect of basically tripling their desire score in comparison to the same base if it had 1 prod
        # also protects us from division by 0 error
        if prod == 0:
            prod = .33

        if true_def == 0:
            true_def = 1
        # subtracting prod just so that a base w/ 0 cybs and 3 prod more desirable than if it had 1 prod instead
        return true_def / prod

    def desire_score_from(self, source, target):
        """Gives a score symbolizing desirability to send troops from a source to a target base.

        Since a source is given, the score is more accurate as it can now account for distance.
        """
        distance = self.get_dist(source, target)
        distance_modifier = distance**2

        target_desire = self.desire_score(target)

        return target_desire * distance_modifier

    def get_dist(self, base_id1, base_id2):
        if base_id1 == base_id2: return 0

        base_pair = frozenset((base_id1, base_id2))
        return self.distances[base_pair]

    def get_incoming_reinforcements(self, id):
        if self.get_type(id) == "troop": raise ValueError("id must be from a base, not a troop")

        owner = self.get_owner(id)
        reinforcements = 0
        
        if owner == "enemy":
            # add all enemy cyborgs that are incoming to id's location
            for enemy_troop in self.enemy_troops.values():
                if enemy_troop["target"] == id:
                    reinforcements += enemy_troop["cyborgs"]
        elif owner == "neutral":
            # neutral does not belong to any team, so it cannot have reinforcements, only attackers
            reinforcements = 0
        elif owner == "myself":
            for my_troop in self.my_troops.values():
                if my_troop["target"] == id:
                    reinforcements += my_troop["cyborgs"]
        return reinforcements

    def get_incoming_attacks(self, id):
        # given a base's id, return total incoming cyborgs that seek to attack id
        if self.get_type(id) == "troop": raise ValueError("id must be from a base, not a troop")

        owner = self.get_owner(id)
        attacking_cyborgs = 0
        if owner == "enemy":
            # add all my cyborgs that are incoming to id's location
            for my_troop in self.my_troops.values():
                if my_troop["target"] == id:
                    attacking_cyborgs += my_troop["cyborgs"]
        elif owner == "neutral":
            # neutral does not belong to any team, so all incoming cyborgs are considered attackers
            troops = (v for troop_dict in self.troop_dicts for v in troop_dict.values())
            for troop in troops:
                if troop["target"] == id:
                    attacking_cyborgs += troop["cyborgs"]
        elif owner == "myself":
            for enemy_troop in self.enemy_troops.values():
                if enemy_troop["target"] == id:
                    attacking_cyborgs += enemy_troop["cyborgs"]
        return attacking_cyborgs

    def closest_friendly(self, id):
        if self.get_owner(id) == "myself":
            # look through own bases except for this guys id
            friendly_ids_no_self = (k for k in self.my_bases if k != id)
            closest_id = min(friendly_ids_no_self, key=lambda k: self.get_dist(id, k), default=None)
            return closest_id
        else:
            # just look through own bases
            closest_id = min(self.my_bases, key=lambda k: self.get_dist(id, k), default=None)
            return closest_id

    def end_turn(self):
        """End the current game turn.
        """
        # better than print() since this accounts for ending turn with no prior input
        # as is for all print statements, this code assumes all of your other print commands ended properly with ";", will break otherwise
        print("WAIT")

    def send_message(self, message=""):
        """Sends game message to game screen.
        """
        print(f"MSG {message}", end=";")

    def do_best_launch(self):
        """Launches the best possible troops for the 1st turn.

        It assumes it's the 1st turn in the game.
        """
        def get_combo_bounty(combo):
            return sum(conquer_map[id]["bounty"] for id in combo)

        def get_combo_cost(combo):
            return sum(conquer_map[id]["cost"] for id in combo)

        home_base_id = list(self.my_bases)[0]  # starting base
        available_cyborgs = self.get_cyborgs(home_base_id)
        # make a "map" of all bases from my side, their benefit from conquering (bounty) & troops needed to send for conquer (cost)
        # (bases from my side are the ones that are closer to me than the enemy)
        # id: {bounty: a, cost: b}
        conquer_map = {}
        for id in self.my_side_base_ids:
            # if id is owned by me already, pretend it is a base w/ bounty: 1, cost: 10
            if self.get_owner(id) == "myself":
                if self.get_prod(id) != 3:  # if I can upgrade
                    bounty = 1
                    cost = 10
                else:
                    bounty = 0
                    cost = float("inf")
            else:  # its neutral
                if self.get_prod(id) != 0:
                    bounty = self.get_prod(id)
                    cost = self.get_cyborgs(id) + 1
                else:
                    bounty = 1
                    cost = self.get_cyborgs(id) + 10
            conquer_map[id] = {"bounty": bounty, "cost": cost}

        # trying to see best combo of bases to conquer, has to be doable given our cyborg bank
        # get a list of all combos (tuple of ids, probably) of bases
        all_combos = []
        for i in range(1, len(conquer_map)+1):
            all_combos.extend(combinations(conquer_map.keys(), i))
        log(all_combos)
        # go through all combos and extract the ones that are actually doable given our cyborg bank
        doable_combos = []
        for combo in all_combos:
            combo_cost = get_combo_cost(combo)
            if combo_cost <= available_cyborgs:
                doable_combos.append(combo)
        log(doable_combos)

        # get list of all combos that are tied to have the max total bounty
        max_combo_prod = float("-inf")
        for combo in doable_combos:  # do longer combos before smaller ones
            combo_prod = get_combo_bounty(combo)
            if combo_prod > max_combo_prod:
                max_combo_prod = combo_prod
        combos_with_max_prod = [combo for combo in doable_combos if get_combo_bounty(combo) == max_combo_prod]

        # figure out which of the combos will win the tie, done by seeking least costly combo
        best_combo = min(combos_with_max_prod, key=get_combo_cost, default=tuple())
        log(best_combo)

        # time to fire our troops now that we have the best bases to attack!
        for id in best_combo:
            if id == home_base_id:
                print(f"INC {home_base_id}", end=";")
            else:
                cyborgs_to_send = conquer_map[id]["cost"]
                print(f"MOVE {home_base_id} {id} {cyborgs_to_send}", end=";")

    def move_to_best_target(self, source=None):
        """Given a source, find its best target & move troops there.
        """
        if source is None: return

        # find best target to attack from our given source
        source_target_pairs = ((source, id) for base_dict in self.base_dicts for id in base_dict if source != id)
        best_source_target_pair = min(source_target_pairs, key=lambda pair: self.desire_score_from(*pair), default=None)
        best_target = best_source_target_pair[1]
        if best_target is None:  # no worthy targets
            return
        self.send_message(f"t: {best_target} ({self.desire_score_from(source, best_target):.1f})")

        # figure out how much cyborgs to send
        # send greater percentage if there's nothing to lose (low prod), send less if prod is good
        source_prod = self.get_prod(source)
        cyborgs_percent = .5 if source_prod == 3 else .7 if source_prod == 2 else .9 if source_prod == 1 else .9
        # calculate percentage, send at least 1 if our calc is too low
        cyborgs_to_send = int(self.get_cyborgs(source) * cyborgs_percent)
        cyborgs_to_send = max(cyborgs_to_send, 0)

        # actually attack, while avoiding runtime error of sending cyborgs to self
        if source == best_target: return
        print(f"MOVE {source} {best_target} {cyborgs_to_send}", end=";")
        
        log(f"from: {source} send: {best_target} desire: {self.desire_score_from(source, best_target):.1f}")
        for id in (id for d in self.base_dicts for id in d if id != source):
            log(f"desire {source} to {id}: {self.desire_score_from(source, id)}")
        log()

    def move_strongest_to_weakest(self):
        """Sends troop from strongest base I have to most desirable target base, target could be ANY base.

        Also has to figure out how many cyborgs to send.
        """
        # find best base to send attack from
        best_source = max(self.my_bases.keys(), key=self.get_cyborgs, default=None)
        if best_source is None:  # I no longer have bases
            print("WAIT")
            return

        # find best target to attack
        base_ids_no_duds = (id for base_dict in self.base_dicts for id in base_dict if self.get_prod(id) != 0)
        best_target = min(base_ids_no_duds, key=self.desire_score, default=None)
        if best_target is None:  # no worthy targets
            print("WAIT")
            return
        print(f"MSG t: {best_target} ({self.desire_score(best_target):.1f})", end=";")

        # figure out how much cyborgs to send
        # send greater percentage if there's nothing to lose (low prod), send less if prod is good
        best_source_prod = self.get_prod(best_source)
        cyborgs_percent = .5 if best_source_prod == 3 else .7 if best_source_prod == 2 else .9 if best_source_prod == 1 else 1
        # calculate percentage, send at least 1 if our calc is too low
        cyborgs_to_send = int(self.get_cyborgs(best_source) * cyborgs_percent)
        cyborgs_to_send = max(cyborgs_to_send, 1)

        # actually attack, while avoiding runtime error of sending cyborgs to self
        print(f"MOVE {best_source} {best_target} {cyborgs_to_send}") if best_source != best_target else print("WAIT")

    def send_bomb(self, turns_between_bombs=5):
        """Sends a bomb to best target, from closest base possible.

        turns_between_bombs restricts how close together bombs are sent.
        Does nothing if it can't send bombs or there are only duds to target.
        """
        # check if we should cancel this function request
        if self.bombs_sent >= 2: return
        turns_since_last_bomb = abs(self.game_turn - self.turn_of_last_bomb)
        if turns_since_last_bomb < turns_between_bombs: return

        target_ids_no_duds = (id for id in self.enemy_bases if self.get_prod(id) != 0)
        strongest_enemy_id = max(target_ids_no_duds, key=self.get_cyborgs, default=None)
        if strongest_enemy_id is None:  # exit if there's only duds to aim at
            return
        closest_to_target = self.closest_friendly(strongest_enemy_id)

        print(f"BOMB {closest_to_target} {strongest_enemy_id}", end=";")
        self.bombs_sent += 1
        self.turn_of_last_bomb = self.game_turn

    def print_bases(self):
        log(f"{'id':<5}{'prod':<5}{'cybs':<5}   {'id':<5}{'prod':<5}{'cybs':<5}   {'id':<5}{'prod':<5}{'cybs':<5}")

        for (k1, v1), (k2, v2), (k3, v3) in zip_longest(
                self.my_bases.items(),
                self.neutral_bases.items(),
                self.enemy_bases.items(),
                fillvalue=(None, None)
            ):
            id1, id2, id3 = (str(k)+":" if k is not None else "" for k in (k1, k2, k3))
            prod1, prod2, prod3 = (str(v["prod"]) if v is not None else "" for v in (v1, v2, v3))
            cybs1, cybs2, cybs3 = (str(v["cyborgs"]) if v is not None else "" for v in (v1, v2, v3))

            log(f"{id1:<5}{prod1:<5}{cybs1:<5}   {id2:<5}{prod2:<5}{cybs2:<5}   {id3:<5}{prod3:<5}{cybs3:<5}")

    def print_troops(self):
        log(f"{'id':<5}{'cybs':<5}{'ETA':<5}{'targ':<5}{'':16}{'id':<5}{'cybs':<5}{'ETA':<5}{'targ':<5}")

        for (k1, v1), (k2, v2) in zip_longest(
                self.my_troops.items(),
                self.enemy_troops.items(),
                fillvalue=(None, None)
            ):
            id1, id2 = (str(k)+":" if k is not None else "" for k in (k1, k2))
            cybs1, cybs2 = (str(v["cyborgs"]) if v is not None else "" for v in (v1, v2))
            eta1, eta2 = (str(v["ETA"]) if v is not None else "" for v in (v1, v2))
            target1, target2 = (str(v["target"]) if v is not None else "" for v in (v1, v2))

            log(f"{id1:<5}{cybs1:<5}{eta1:<5}{target1:<5}{'':16}{id2:<5}{cybs2:<5}{eta2:<5}{target2:<5}")

    def print_distances(self):
        for k, v in self.distances.items():
            log(f"{set(k)}: {v}")
        log("")



def main():
    game = Game()
    game.load_init_data()
    game.print_distances()

    while True: # game loop
        game.load_game_turn_input()
        # logging our game state
        # game.print_bases()
        # game.print_troops()

        if game.game_turn == 1:
            game.send_bomb(turns_between_bombs=3)
            game.do_best_launch()
            game.end_turn()
        else:
            game.send_bomb(turns_between_bombs=3)
            for my_base_id in game.my_bases:
                game.move_to_best_target(source=my_base_id)
            game.end_turn()


if __name__ == "__main__":
    main()
