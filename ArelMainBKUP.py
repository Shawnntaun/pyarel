#!/usr/bin/python

import libtcodpy as libtcod
import math
import textwrap
import shelve
import random
import pygame
import datetime
import time

#actual size of the window
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
 
#size of the map
MAP_WIDTH = 80
MAP_HEIGHT = 43
 
#sizes and coordinates relevant for the GUI
BAR_WIDTH = 20
PANEL_HEIGHT = 7
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT
MSG_X = BAR_WIDTH + 2
MSG_WIDTH = SCREEN_WIDTH - BAR_WIDTH - 2
MSG_HEIGHT = PANEL_HEIGHT - 1
INVENTORY_WIDTH = 50
CHARACTER_SCREEN_WIDTH = 30
LEVEL_SCREEN_WIDTH = 40
 
#parameters for dungeon generator
ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30

DEPTH = 7
MIN_SIZE = 6
FULL_ROOMS = False
DOOR_CHANCE = 80
 
#how much does an oil flask fill?
OIL_LAMP = 60
OIL_DECAY = .2
 
#spell values
HEAL_AMOUNT = 40
LIGHTNING_DAMAGE = 40
LIGHTNING_RANGE = 5
CONFUSE_RANGE = 8
CONFUSE_NUM_TURNS = 10
FIREBALL_RADIUS = 3
FIREBALL_DAMAGE = 25
 
 
#experience and level-ups
LEVEL_UP_BASE = 200
LEVEL_UP_FACTOR = 150
 
FOV_ALGO = 0  #default FOV algorithm
FOV_LIGHT_WALLS = True  #light walls or not
TORCH_RADIUS = 10
 
#player options
Opt_Verbose_Messages = True #whether or not to include rolls in messages
Opt_Auto_Open_Door = True #whether or not to automatically open closed doors

#volume options
Opt_SFX_Sound = 1.0
Opt_BGM_Sound = 0.75
 
BGM_TITLEMUSIC = 'audio/bgm/titlemusic.mp3'
BGM_CAVEMUSIC = 'audio/bgm/puzzles.mp3'

SFX_LEVELUP = 'audio/sfx/SFXLevelUp.wav'

SFX_BATHIT = 'audio/sfx/HITBat.wav'
SFX_GNOLLHIT = 'audio/sfx/HITOrc.wav'
SFX_PLAYERHIT = 'audio/sfx/HITPlayer.wav'
SFX_RATHIT = 'audio/sfx/HITRat.wav'
SFX_TROLLHIT = 'audio/sfx/HITTroll.wav'

SFX_GNOLLATK = 'audio/sfx/ATKGnoll.wav'
SFX_PLAYERATK = 'audio/sfx/ATKPlayer.wav'
SFX_TROLLATK = 'audio/sfx/ATKTroll.wav'

SFX_MONSTERDIE = 'audio/sfx/DIEMonster.wav'

SFX_CRITHIT = 'audio/sfx/SFXCrit.wav'

SFX_CONFUSEHIT = 'audio/sfx/HITConfuse.wav'
SFX_FIREBALLHIT = 'audio/sfx/HITFireball.wav'
SFX_LIGHTNINGHIT = 'audio/sfx/HITLightning.wav'

SFX_GOLDPICKUP = 'audio/sfx/PICKUPCoin.wav'
SFX_POTIONPICKUP = 'audio/sfx/PICKUPHealthPot.wav'
SFX_SCROLLPICKUP = 'audio/sfx/PICKUPScroll.wav'

SFX_POTIONUSE = 'audio/sfx/USEHealthPot.wav'
SFX_MAGICMAPUSE = 'audio/sfx/USEMagicMap.wav'

SFX_DOOR = 'audio/sfx/USEDoor.wav'
SFX_DOORSHAKE = 'audio/sfx/SFXDoorShake.wav'
SFX_DOORBREAK = 'audio/sfx/SFXBoxBreak.wav'
SFX_Stairs = 'audio/sfx/SFXStairs.wav'
 
color_dark_wall = libtcod.black
color_light_wall = libtcod.silver
color_dark_ground = libtcod.darkest_gray
color_light_ground = libtcod.darker_sepia
color_dark_wall_bk = libtcod.black
color_light_wall_bk = libtcod.black
color_dark_ground_bk = libtcod.black
color_light_ground_bk = libtcod.black
 
class Tile:
    #a tile of the map and its properties
    def __init__(self, blocked, block_sight = None, is_door = False):
        self.blocked = blocked
        self.is_door = is_door
 
        #all tiles start unexplored
        self.explored = False
 
        #by default, if a tile is blocked, it also blocks sight
        if block_sight is None: block_sight = blocked
        
        self.block_sight = block_sight
 
class Rect:
    #a rectangle on the map. used to characterize a room.
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h
 
    def center(self):
        center_x = (self.x1 + self.x2) / 2
        center_y = (self.y1 + self.y2) / 2
        return (center_x, center_y)
 
    def intersect(self, other):
        #returns true if this rectangle intersects with another one
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)
 
class Object:
    #this is a generic object: the player, a monster, an item, the stairs...
    #it's always represented by a character on screen.
    def __init__(self, x, y, char, name, color, blocks=False, always_visible=False, fighter=None, ai=None, item=None, equipment=None):
        self.x = x
        self.y = y
        self.char = char
        self.name = name
        self.color = color
        self.blocks = blocks
        self.always_visible = always_visible
        self.fighter = fighter
        if self.fighter:  #let the fighter component know who owns it
            self.fighter.owner = self
 
        self.ai = ai
        if self.ai:  #let the AI component know who owns it
            self.ai.owner = self
 
        self.item = item
        if self.item:  #let the Item component know who owns it
            self.item.owner = self
 
        self.equipment = equipment
        if self.equipment:  #let the Equipment component know who owns it
            self.equipment.owner = self
 
            #there must be an Item component for the Equipment component to work properly
            self.item = Item()
            self.item.owner = self
 
    def move(self, dx, dy):
        #move by the given amount, if the destination is not blocked
        if not is_blocked(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy
            
    def move_towards(self, target_x, target_y):
        #vector from this object to the target, and distance
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)
 
        #normalize it to length 1 (preserving direction), then round it and
        #convert to integer so the movement is restricted to the map grid
        dx = int(round(dx / distance))
        dy = int(round(dy / distance))
        self.move(dx, dy)
           
    def move_dijkstra(self, dmap):
        
        
        chance = libtcod.random_get_int(0, 1, 3)
        if chance == 1:
            (dx, dy) = random.choice(dmap.neighbors) # random movement
            open = True
        else:
            moves = dmap.get_move_options(self.x, self.y)
            open = True
            (dx, dy) = random.choice(moves)
            
        if is_blocked(self.x + dx, self.y + dy): #if best move is blocked
                if not map[self.x+dx][self.y+dy].is_door:
                    (dx, dy) = random.choice(dmap.neighbors) # pick a random neighbor
        
        if 0 <= (self.x+dx) < MAP_WIDTH and 0 <= (self.y+dy) < MAP_HEIGHT:
            #in range
            if map[self.x+dx][self.y+dy].is_door:   #is it a door?
                for obj in objects:
                    if obj.x == self.x+dx and obj.y == self.y+dy and obj.name == "closed door":
                        n = libtcod.random_get_int(0, 1, 4)
                        if n >= 2: #3.4 chance to try to open the door
                                
                            chance_helper = 0 #libtcod.random_get_int(0, 1, 3)
                            chance_break_door = libtcod.random_get_int(0, 1, 20) + self.fighter.modifier(self.fighter.strength) + chance_helper
                            bd_check = 18
                            if chance_break_door >= bd_check:
                                for obj in objects:
                                    if obj.x == self.x+dx and obj.y == self.y + dy and obj.name == "closed door":
                                        obj.name = 'open door'
                                        obj.char = '-'
                                        map[obj.x][obj.y].block_sight = False
                                        map[obj.x][obj.y].blocked = False
                                        if libtcod.map_is_in_fov(fov_map, self.x+dx, self.y+dy):
                                            message("The door crashes open!", libtcod.light_orange)
                                            Play_BGSFX(SFX_DOORBREAK)
                                        map_sound(obj.x, obj.y, 1)
                                        fov_recompute = True
                                        initialize_fov()
                                        
                                
                            else:                  
                                #print "knock knock"
                                if libtcod.map_is_in_fov(fov_map, self.x+dx, self.y+dy):
                                    message("The door shakes from the other side.",libtcod.white)
                                    Play_BGSFX(SFX_DOORSHAKE)
            
            if map[self.x+dx][self.y+dy].block_sight == False and open: #you can move there
                self.move(dx, dy) #move
    
    def move_astar(self, target):
        #Create a FOV map that has the dimensions of the map
        fov = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
 
        #Scan the current map each turn and set all the walls as unwalkable
        for y1 in range(MAP_HEIGHT):
            for x1 in range(MAP_WIDTH):
                libtcod.map_set_properties(fov, x1, y1, not map[x1][y1].block_sight, not map[x1][y1].blocked)
 
        #Scan all the objects to see if there are objects that must be navigated around
        #Check also that the object isn't self or the target (so that the start and the end points are free)
        #The AI class handles the situation if self is next to the target so it will not use this A* function anyway   
        for obj in objects:
            if obj.blocks and obj != self and obj != target:
                #Set the tile as a wall so it must be navigated around
                libtcod.map_set_properties(fov, obj.x, obj.y, True, False)
 
        #Allocate a A* path
        #The 1.41 is the normal diagonal cost of moving, it can be set as 0.0 if diagonal moves are prohibited
        my_path = libtcod.path_new_using_map(fov, 1.41)
 
        #Compute the path between self's coordinates and the target's coordinates
        libtcod.path_compute(my_path, self.x, self.y, target.x, target.y)
 
        #Check if the path exists, and in this case, also the path is shorter than 25 tiles
        #The path size matters if you want the monster to use alternative longer paths (for example through other rooms) if for example the player is in a corridor
        #It makes sense to keep path size relatively low to keep the monsters from running around the map if there's an alternative path really far away        
        if not libtcod.path_is_empty(my_path) and libtcod.path_size(my_path) < 25:
            #Find the next coordinates in the computed full path
            x, y = libtcod.path_walk(my_path, True)
            if x or y:
                #Set self's coordinates to the next path tile
                self.x = x
                self.y = y
        else:
            #Keep the old move function as a backup so that if there are no paths (for example another monster blocks a corridor)
            #it will still try to move towards the player (closer to the corridor opening)
            self.move_towards(target.x, target.y)  
 
        #Delete the path to free memory
        libtcod.path_delete(my_path)

    def distance_to(self, other):
        #return the distance to another object
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)
 
    def distance(self, x, y):
        #return the distance to some coordinates
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)
 
    def send_to_back(self):
        #make this object be drawn first, so all others appear above it if they're in the same tile.
        global objects
        objects.remove(self)
        objects.insert(0, self)
 
    def draw(self):
        #only show if it's visible to the player; or it's set to "always visible" and on an explored tile
        if (libtcod.map_is_in_fov(fov_map, self.x, self.y) or
                 (self.always_visible and map[self.x][self.y].explored)):
                    #set the color and then draw the character that represents this object at its position
                    libtcod.console_set_default_foreground(con, self.color)
                    libtcod.console_put_char(con, self.x, self.y, self.char, libtcod.BKGND_NONE)
 
    def clear(self):
        #erase the character that represents this object
        libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE)

def DijkHeat(cmap, infov=False, limit=9):
    #renders a heat map for a provided dijkstra(cmap)
    # if inFoV = true it will render the map within the players fov_map
    # otherwise it only renders outside of the fov_map
    # limit is what value the render stops at 
    
    global map
    
    for y in range (MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            v = cmap.tiles[x][y]
            if v == 1:
                color = libtcod.darkest_azure
            elif v == 2:
                color = libtcod.darkest_sky 
            elif v == 3:
                color = libtcod.darker_azure
            elif v == 4:
                color = libtcod.darker_sky
            elif v == 5:
                color = libtcod.dark_azure
            elif v == 6:
                color = libtcod.dark_sky
            elif v == 7:
                color = libtcod.azure
            elif v == 8:
                color = libtcod.sky
            elif v == 9:
                color = libtcod.light_azure
            elif v == 10:
                color = libtcod.light_sky
            elif v == 11:
                color = libtcod.lighter_azure
            elif v == 12:
                color = libtcod.lighter_sky
            elif v == 13:
                color = libtcod.lightest_azure
            elif v == 15:
                color = libtcod.lightest_sky
            else:
                color = libtcod.white

            render = False
            if infov:
                if libtcod.map_is_in_fov(fov_map, x, y):
                    render = True
            else:
                if libtcod.map_is_in_fov(fov_map, x, y):
                    render = False
                else:
                    render = True
                
            if render:
                if map[x][y].block_sight and map[x][y].is_door == False:
                    pass
                elif v < limit:
                    libtcod.console_set_char_background(0, x, y, color, libtcod.BKGND_SCREEN)
                
        
class DijkstraMap:

    # X, Y Transitions to the 8 neighboring cells
    neighbors = [(-1, -1), (0, -1), (1, -1),
                 (-1, 0), (1, 0),
                 (-1, 1), (0, 1), (1, 1)]

    def __init__(self, width, height):
        """
        Create a Map  showing the movement score of various tiles
        :param int width: Map size in tiles
        :param int height: Map size in tiles
        """
        self.width = width
        self.height = height
        self.goals = []
        self.tiles = []
        self._clear_map()

    def add_goal(self, x, y, score=0):
        """
        Add a goal tile to the map
        :param int x: Tile X coordinate
        :param int y: Tile Y coordinate
        :param int score: Desirability of this location (default: 0)
        """        
        self.goals.append((x, y, score))

    def clear_goals(self):
        self.goals = []
        
    def recalculate_map(self, default=9, doorstop = False):
        """
        Use Dijkstra's Algorithm to calculate the movement score towards
        goals in this map
        """
        
        self._clear_map(default)
        changed = True
        while changed:
            changed = False
            for y in range(0, self.height):
                for x in range(0, self.width):
                    if map[x][y].block_sight and map[x][y].is_door == False:
                        #walls
                        pass
                    elif map[x][y].is_door and map[x][y].block_sight and doorstop:
                        #if doorstop=True, a closed door will stop the progression
                        pass
                    else:
                        lowest_neighbor = self._get_lowest_neighbor_value(x, y)
                        if self.tiles[x][y] > lowest_neighbor + 1:
                            self.tiles[x][y] = lowest_neighbor + 1
                            changed = True
    
    def recalculate_single(self, tx, ty, drange=9, doorstop=False):
        """
        rebuild dijkstra with only one goal..
        rebuilds only area around the goal in order to speed up processing time
        tx, ty = targetx, targety
        """      
        
        self._clear_map(drange)
        changed = True
        while changed:
            changed = False
            for y in range(0-drange, drange):
                for x in range(0-drange, drange):
                    if self.point_in_map(tx+x, ty+y):
                        if map[tx+x][ty+y].block_sight and map[tx+x][ty+y].is_door == False:
                            #walls stop the progression of a sound wave
                            pass
                        elif map[tx+x][ty+y].is_door and map[tx+x][ty+y].block_sight and doorstop:
                            #if doorstop=True, a closed door will stop the progression of a sound wave
                            pass
                        else:
                            lowest_neighbor = self._get_lowest_neighbor_value(tx+x, ty+y)
                            if self.tiles[tx+x][ty+y] > lowest_neighbor + 1:
                                self.tiles[tx+x][ty+y] = lowest_neighbor + 1
                                changed = True
    
    def get_move_options(self, x, y):
        """
        Return a list of ideal moves from a given point
        :param x: Entity X Coordinate
        :param y: Entity Y Coordinate
        :return list: Recommended moves
        """
        best = self._get_lowest_neighbor_value(x, y)
        moves = []
        for dx, dy in DijkstraMap.neighbors:
            tx, ty = x + dx, y + dy
            if self.point_in_map(tx, ty) and self.tiles[tx][ty] == best:
                moves.append((dx, dy))
        return moves

    def point_in_map(self, x, y):
        """
        Checks if a given point falls within the current map
        :param x: Target X position
        :param y: Target Y position
        :return: True if desired location is within map bounds
        """
        return 0 <= x < self.width and 0 <= y < self.height

    def _clear_map(self, default=9):
        """
        Reset the map scores to an arbitrary value and populate goals
        :param int default: the initial value to set for each cell
        """
        self.tiles = [
            [default
             for _ in range(self.height)]
            for _ in range(self.width)]

        for (x, y, score) in self.goals:
            self.tiles[x][y] = score

    def _get_lowest_neighbor_value(self, x, y):
        """
        Get the score in the current lowest-valued neighbor cell
        :param x: Current X Coordinate
        :param y: Current Y Coordinate
        :return int: Lowest neighboring value
        """
        lowest = 100
        for dx, dy in DijkstraMap.neighbors:
            tx, ty = x + dx, y + dy
            if self.point_in_map(tx, ty):
                lowest = min(lowest, self.tiles[tx][ty])
        return lowest

    def __repr__(self):
        """
        Output the current map in a printable fashion
        :return string: Printable form of map
        """
        out = ""
        for y in range(0, self.height):
            for x in range(0, self.width):
                out += str(hex(self.tiles[x][y])[2:])
            out += "\n"
        return out
 
    def cell_at(self, x, y):
        return self.tiles[x][y]
        
class Fighter:
    #combat-related properties and methods (monster, player, NPC).
    def __init__(self, hp, ac, strength, dexterity, constitution, intelligence, wisdom, charisma, luck, damage, speed, xp,
                atk_sound=None, hit_sound=None, death_sound=None, death_function=None):
        self.base_max_hp = hp
        self.hp = hp
        self.base_ac = ac
        self.base_strength = strength
        self.base_dexterity = dexterity
        self.base_constitution = constitution
        self.base_intelligence = intelligence
        self.base_wisdom = wisdom
        self.base_charisma = charisma
        self.base_luck = luck
        self.base_damage = damage
        self.xp = xp
        self.counter = 0
        self.base_speed = speed
        self.atk_sound = atk_sound
        self.hit_sound = hit_sound
        self.death_sound = death_sound
        self.death_function = death_function
 
    @property
    def strength(self):  #return actual strength, by summing up the bonuses from all equipped items
        bonus = sum(equipment.strength_bonus for equipment in get_all_equipped(self.owner))
        return self.base_strength + bonus
        
    @property
    def dexterity(self):
        bonus = sum(equipment.dexterity_bonus for equipment in get_all_equipped(self.owner))
        return self.base_dexterity + bonus

    @property
    def constitution(self):
        bonus = sum(equipment.constitution_bonus for equipment in get_all_equipped(self.owner))
        return self.base_constitution + bonus
    
    @property
    def intelligence(self):
        bonus = sum(equipment.intelligence_bonus for equipment in get_all_equipped(self.owner))
        return self.base_intelligence + bonus
        
    @property
    def wisdom(self):
        bonus = sum(equipment.wisdom_bonus for equipment in get_all_equipped(self.owner))
        return self.base_wisdom + bonus
    
    @property
    def charisma(self):
        bonus = sum(equipment.charisma_bonus for equipment in get_all_equipped(self.owner))
        return self.base_charisma + bonus
    
    @property
    def luck(self):
        bonus = sum(equipment.luck_bonus for equipment in get_all_equipped(self.owner))
        return self.base_luck + bonus
    
    @property
    def speed(self):
        bonus = sum(equipment.speed_bonus for equipment in get_all_equipped(self.owner))
        return self.base_speed + bonus
    
    @property
    def ac(self):  #return actual ac, by summing up the bonuses from all equipped items
        bonus = sum(equipment.ac_bonus for equipment in get_all_equipped(self.owner))
        return self.base_ac + bonus
 
    @property
    def max_hp(self):  #return actual max_hp, by summing up the bonuses from all equipped items
        bonus = sum(equipment.max_hp_bonus for equipment in get_all_equipped(self.owner))
        return self.base_max_hp + bonus
 
    @property
    def damage(self):  #return actual damage for combat damage
        bonus = sum(equipment.damage_bonus for equipment in get_all_equipped(self.owner))
        return self.base_damage + bonus + self.modifier(self.strength)
 
    def modifier(self, stat):
        #return the ability modifier for the provided stat score
        return int((stat - 10)/2)
         
    def attack(self, target):
        #a simple formula for attack damage
        bdamage = self.damage - target.fighter.ac
        
        damage = libtcod.random_get_int(0, 1+self.modifier(self.strength), bdamage+self.modifier(self.strength))
 
        if damage > 0:
            
            if target == player:
                message(self.owner.name + " hits you!", libtcod.grey)
                if self.atk_sound:
                    Play_PlayerCombat(self.atk_sound)
            else:
                message("You hit the " + target.name + ".", libtcod.grey)
                Play_PlayerCombat(SFX_PLAYERATK)
                
            #make the target take some damage
            target.fighter.take_damage(damage)    
                
        else:
            if target == player:
                message(self.owner.name + " misses you!", libtcod.grey)
            else:
                message("You miss the " + target.name, libtcod.grey)

    #def attack(self, target):
    #    
    #    dodgecheck = libtcod.random_get_float(0, 1, 100)
    #    if dodgecheck < ((target.fighter.modifier(target.fighter.dexterity)*10)/7): #dex mod of 2 = 2.86% chance
    #        color = libtcod.light_orange
    #        if Opt_Verbose_Messages:
    #            msgadd = " " + str(((target.fighter.modifier(target.fighter.dexterity)*10)/7)) + "%"
    #        message(self.owner.name + ' attacks ' + target.name + ', but the attack is evaded!' + msgadd, color)
    #    else:
    #        diceroll = 1
    #        atkdescript = " attacks "
    #        atkroll = rolldice(1, 20) + sum(equipment.tohit_bonus for equipment in get_all_equipped(self.owner))
    #        
    #        color = libtcod.light_blue
    #        if target == player: color = libtcod.light_red
    #        
    #        msgadd = ""
    #        if Opt_Verbose_Messages:
    #            msgadd = ' ' + str(atkroll) + 'vs' + str(target.fighter.ac)   
    #        if atkroll - sum(equipment.tohit_bonus for equipment in get_all_equipped(self.owner)) == 20: #crit
    #            diceroll = 2
    #            atkdescript = " CRITS "
    #            Play_BGSFX(SFX_CRITHIT)
    #            
    #        if atkroll >= target.fighter.ac or (atkroll - sum(equipment.tohit_bonus for equipment in get_all_equipped(self.owner)) == 20): #hit vs ac
    #            damage = rolldice(diceroll, self.strength)
    #            if self.atk_sound:
    #                if self.owner == player:
    #                    Play_PlayerCombat(self.atk_sound)
    #                else:
    #                    Play_NPCCombat(self.atk_sound)
    #                    
    #            if damage > 0:
    #                message(self.owner.name + atkdescript + target.name + ' for ' + str(damage) + ' hit points.' + msgadd, color)
    #               
    #                #make the target take some damage
    #                target.fighter.take_damage(damage)
    #            else:
    #                message(self.owner.name + ' attacks ' + target.name + ' but it has no effect!' + msgadd, color)
    #        else: #miss vs ac
    #            message(self.owner.name + ' attacks ' + target.name + ' but misses!' + msgadd, color)

    def take_damage(self, damage):
        #apply damage if possible
        if damage > 0:
            self.hp -= damage
            if self.hit_sound:
                if self.owner == player:
                    Play_PlayerCombat(self.hit_sound)
                else:
                    Play_NPCCombat(self.hit_sound)
                    
            #check for death. if there's a death function, call it
            if self.hp <= 0:
                function = self.death_function
                if function is not None:
                    function(self.owner)
 
                if self.owner != player:  #yield experience to the player
                    player.fighter.xp += self.xp
 
    def heal(self, amount):
        #heal by the given amount, without going over the maximum
        self.hp += amount
        if self.hp > self.max_hp:
            self.hp = self.max_hp
 


class BasicMonster:
    #AI for a basic monster.
    def take_turn(self):
        #a basic monster takes its turn. if you can see it, it can see you
        monster = self.owner
        #if libtcod.map_is_in_fov(fov_map, monster.x, monster.y): # if you can see that mf
        
        n = libtcod.random_get_int(0, 1, 5)
        if monster.distance_to(player) >= 2:        # if you can't sense that mf
            monster.move_dijkstra(player_dijkstra)                 #   move.
        elif player.fighter.hp > 0:                 # otherwise, if that mf is still alive
            if n > 4:
                monster.move_dijkstra(player_dijkstra)
            else:
                monster.fighter.attack(player)          #   attack that mf.
 
class ConfusedMonster:
    #AI for a temporarily confused monster (reverts to previous AI after a while).
    def __init__(self, old_ai, num_turns=CONFUSE_NUM_TURNS):
        self.old_ai = old_ai
        self.num_turns = num_turns
 
    def take_turn(self):
        if self.num_turns > 0:  #still confused...
            #move in a random direction, and decrease the number of turns confused
            self.owner.move(libtcod.random_get_int(0, -1, 1), libtcod.random_get_int(0, -1, 1))
            self.num_turns -= 1
 
        else:  #restore the previous AI (this one will be deleted because it's not referenced anymore)
            self.owner.ai = self.old_ai
            message('The ' + self.owner.name + ' is no longer confused!', libtcod.red)
 
class Item:
    #an item that can be picked up and/or used.
   
    def __init__(self, stacks=False, count=1, use_function=None, pickup_sound=None, use_sound=None):
        self.stacks = stacks
        self.count = count
        self.use_function = use_function
        self.pickup_sound = pickup_sound
        self.use_sound = use_sound
        
    def pick_up(self):
        
            
        if self.owner.name == "open door" or self.owner.name == "closed door":
            message("You can not pick up a door.",libtcod.white)
        else:
            #add to the player's inventory and remove from the map
            if self.stacks:
                ininv = False
                for itm in inventory:
                    if itm.name == self.owner.name:
                        ininv = True
                        #play pickup sound if applicable
                        if self.pickup_sound:
                            s = pygame.mixer.Sound(self.pickup_sound)
                            s.set_volume(Opt_SFX_Sound)
                            CHANNEL_ITEMSFX.play(s)

                        message('You picked up ' +  self.owner.name + "! (x" + str(self.count) + ")", libtcod.green)
                        
                        #add to inventory
                        itm.item.count = itm.item.count + self.count
                        objects.remove(self.owner)
                        
                
                        
            if not self.stacks or ininv == False:
                if len(inventory) >= 26:
                    message('Your inventory is full, cannot pick up ' + self.owner.name + '.', libtcod.red)
                else:
                    #play pickup sound if applicable
                    if self.pickup_sound:
                        s = pygame.mixer.Sound(self.pickup_sound)
                        s.set_volume(Opt_SFX_Sound)
                        CHANNEL_ITEMSFX.play(s)
                    
                    #add to inventory
                    inventory.append(self.owner)
                    objects.remove(self.owner)
                    message('You picked up ' +  self.owner.name + "! (x" + str(self.count) + ")", libtcod.green)
                    
                    #special case: automatically equip, if the corresponding equipment slot is unused
                    equipment = self.owner.equipment
                    if equipment and get_equipped_in_slot(equipment.slot) is None:
                        equipment.equip()
 
    def drop(self):
        #special case: if the object has the Equipment component, dequip it before dropping
        if self.owner.equipment:
            self.owner.equipment.dequip()
 
        #add to the map and remove from the player's inventory. also, place it at the player's coordinates
        objects.append(self.owner)
        inventory.remove(self.owner)
        self.owner.x = player.x
        self.owner.y = player.y
        message('You dropped a ' + self.owner.name + '.', libtcod.yellow)
        #play pickup sound if applicable
        if self.pickup_sound:
            s = pygame.mixer.Sound(self.pickup_sound)
            s.set_volume(Opt_SFX_Sound)
            CHANNEL_ITEMSFX.play(s)
 
    def use(self):
        #special case: if the object has the Equipment component, the "use" action is to equip/dequip
        if self.owner.equipment:
            self.owner.equipment.toggle_equip()
            return
 
        #just call the "use_function" if it is defined
        if self.use_function is None:
            message('The ' + self.owner.name + ' cannot be used.')
        else:
            if self.use_function() != 'cancelled':
                #play use sound if applicable
                if self.use_sound:
                    Play_ItemSFX(self.use_sound)
                    
                if self.stacks:
                    found = False
                    for itm in inventory:
                        if not found:
                            if itm.name == self.owner.name:
                                itm.item.count = itm.item.count - 1
                                if itm.item.count <= 0:
                                    inventory.remove(self.owner)
                                    found = True
                            
                else:  
                    inventory.remove(self.owner)  #destroy after use, unless it was cancelled for some reason
 
class Equipment:
    #an object that can be equipped, yielding bonuses. automatically adds the Item component.
    def __init__(self, slot, strength_bonus=0, dexterity_bonus=0, constitution_bonus=0, intelligence_bonus=0,
                wisdom_bonus=0, charisma_bonus=0, damage_bonus=0, luck_bonus=0, speed_bonus=0, tohit_bonus=0, ac_bonus=0, max_hp_bonus=0):
        self.strength_bonus = strength_bonus
        self.dexterity_bonus = dexterity_bonus
        self.constitution_bonus = constitution_bonus
        self.intelligence_bonus = intelligence_bonus
        self.wisdom_bonus = wisdom_bonus
        self.charisma_bonus = charisma_bonus
        self.damage_bonus = damage_bonus
        self.luck_bonus = luck_bonus
        self.speed_bonus = speed_bonus
        self.tohit_bonus = tohit_bonus
        self.ac_bonus = ac_bonus
        self.max_hp_bonus = max_hp_bonus
 
        self.slot = slot
        self.is_equipped = False
 
    def toggle_equip(self):  #toggle equip/dequip status
        if self.is_equipped:
            self.dequip()
        else:
            self.equip()
 
    def equip(self):
        #if the slot is already being used, dequip whatever is there first
        old_equipment = get_equipped_in_slot(self.slot)
        if old_equipment is not None:
            old_equipment.dequip()
 
        #equip object and show a message about it
        self.is_equipped = True
        message('Equipped ' + self.owner.name + ' on ' + self.slot + '.', libtcod.light_green)
 
    def dequip(self):
        #dequip object and show a message about it
        if not self.is_equipped: return
        self.is_equipped = False
        message('Dequipped ' + self.owner.name + ' from ' + self.slot + '.', libtcod.light_yellow)
 
def map_sound(sourcex, sourcey, intensity=1): 

    sound_dijkstra.clear_goals()
    sound_dijkstra._clear_map(15)
    sound_dijkstra.add_goal(sourcex, sourcey)
    sound_dijkstra.recalculate_single(sourcex, sourcey, 15, True)
    

def decay_map(map, decayrate = 1):
    
    if map == None:
        map = sound_dijkstra
    
    changes = True
    
    while changes:
        for y in range(MAP_HEIGHT): 
            for x in range(MAP_WIDTH):
                changes = False
                if map.tiles[x][y] < 15:
                    map.tiles[x][y] = map.tiles[x][y] + decayrate
                    if map.tiles[x][y] > 15:
                        map.tiles[x][y] = 15
                        changes = True
                        

def Burn_Torch():
    global TORCH_RADIUS, fov_recompute
       
    current = TORCH_RADIUS
    TORCH_RADIUS = int((player.oil) % (player.max_oil_level)/10) #oil formula here
    if TORCH_RADIUS < 2:
        TORCH_RADIUS = 2
    if not current == TORCH_RADIUS:
        fov_recompute = True
    
    
def in_map_range(x, y):
    if 0 < x < MAP_WIDTH and 0 < y < MAP_HEIGHT:
        return True

def tile_blocked(x, y):
    blocked = False
    for obj in objects:
        if obj.x == x and obj.y == y:
            if obj.name == 'closed door' or obj.name == 'open door':
                pass
            else:
                blocked = True
    return blocked
    
    
    
    
def get_equipped_in_slot(slot):  #returns the equipment in a slot, or None if it's empty
    for obj in inventory:
        if obj.equipment and obj.equipment.slot == slot and obj.equipment.is_equipped:
            return obj.equipment
    return None
 
def get_all_equipped(obj):  #returns a list of equipped items
    if obj == player:
        equipped_list = []
        for item in inventory:
            if item.equipment and item.equipment.is_equipped:
                equipped_list.append(item.equipment)
        return equipped_list
    else:
        return []  #other objects have no equipment
 
 
def print_blocks():

    for y in range(MAP_HEIGHT):
        str = ""
        for x in range(MAP_WIDTH):
            if map[x][y].block_sight:
                str = str + "#"
            else:
                str = str + "."
        print str
 
def rolldice(num, dice): #rolls dice, returns the sum of all rolls
        roll = 0
        for x in range (0, num):
            n = random.randint(1, dice)
            roll = roll + n
        return roll

def Play_ItemSFX(path):
    if path != None:
        s = pygame.mixer.Sound(path)
        s.set_volume(Opt_SFX_Sound)
        CHANNEL_ITEMSFX.play(s)

def Play_BGSFX(path):
    if path != None:
        s = pygame.mixer.Sound(path)
        s.set_volume(Opt_SFX_Sound)
        CHANNEL_BGSFX.play(s)

def Play_PlayerCombat(path):
    if path != None:
        s = pygame.mixer.Sound(path)
        s.set_volume(Opt_SFX_Sound)
        CHANNEL_PLAYERCOMBAT.play(s)      

def Play_NPCCombat(path):
    if path != None:
        s = pygame.mixer.Sound(path)
        s.set_volume(Opt_SFX_Sound)
        CHANNEL_NPCCOMBAT.play(s)  
        
def Play_BGM(path):
    if path != None:
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.fadeout(125)
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(Opt_BGM_Sound)
        pygame.mixer.music.play(loops = -1)
        
        
def is_blocked(x, y):
    #first test the map tile
    if map[x][y].blocked:
        return True
 
    #now check for any blocking objects
    for object in objects:
        if object.blocks and object.x == x and object.y == y:
            return True
 
    return False
 
def create_room(room):
    global map
    #go through the tiles in the rectangle and make them passable
    for x in range(room.x1 + 1, room.x2):
        for y in range(room.y1 + 1, room.y2):
            map[x][y].blocked = False
            map[x][y].block_sight = False
 
def create_h_tunnel(x1, x2, y):
    global map
    #horizontal tunnel. min() and max() are used in case x1>x2
    for x in range(min(x1, x2), max(x1, x2) + 1):
        map[x][y].blocked = False
        map[x][y].block_sight = False
 
def create_v_tunnel(y1, y2, x):
    global map
    #vertical tunnel
    for y in range(min(y1, y2), max(y1, y2) + 1):
        map[x][y].blocked = False
        map[x][y].block_sight = False
 
def make_map():
    global map, objects, stairs, gold_dijkstra
 
    #the list of objects with just the player
    objects = [player]
 
    #fill map with "blocked" tiles
    map = [[ Tile(True)
             for y in range(MAP_HEIGHT) ]
           for x in range(MAP_WIDTH) ]
 
    rooms = []
    num_rooms = 0
 
    for r in range(MAX_ROOMS):
        #random width and height
        w = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        h = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        #random position without going out of the boundaries of the map
        x = libtcod.random_get_int(0, 0, MAP_WIDTH - w - 1)
        y = libtcod.random_get_int(0, 0, MAP_HEIGHT - h - 1)
 
        #"Rect" class makes rectangles easier to work with
        new_room = Rect(x, y, w, h)
 
        #run through the other rooms and see if they intersect with this one
        failed = False
        for other_room in rooms:
            if new_room.intersect(other_room):
                failed = True
                break
 
        if not failed:
            #this means there are no intersections, so this room is valid
 
            #"paint" it to the map's tiles
            create_room(new_room)
 
            #center coordinates of new room, will be useful later
            (new_x, new_y) = new_room.center()
 
            if num_rooms == 0:
                #this is the first room, where the player starts at
                player.x = new_x
                player.y = new_y
            else:
                #all rooms after the first:
                #connect it to the previous room with a tunnel
 
                #center coordinates of previous room
                (prev_x, prev_y) = rooms[num_rooms-1].center()
 
                #draw a coin (random number that is either 0 or 1)
                if libtcod.random_get_int(0, 0, 1) == 1:
                    #first move horizontally, then vertically
                    create_h_tunnel(prev_x, new_x, prev_y)
                    create_v_tunnel(prev_y, new_y, new_x)
                else:
                    #first move vertically, then horizontally
                    create_v_tunnel(prev_y, new_y, prev_x)
                    create_h_tunnel(prev_x, new_x, new_y)
 
            #add some contents to this room, such as monsters
            place_objects(new_room)
 
            #finally, append the new room to the list
            rooms.append(new_room)
            num_rooms += 1
 
    #create stairs at the center of the last room
    stairs = Object(new_x, new_y, '<', 'stairs', libtcod.white, always_visible=True)
    objects.append(stairs)
    stairs.send_to_back()  #so it's drawn below the monsters
    
    #build dijkstra maps for ai
    gold_dijkstra = DijkstraMap(MAP_WIDTH, MAP_HEIGHT)
    for obj in objects:
        if obj.name == "gold":
            gold_dijkstra.add_goal(obj.x, obj.y)
            
    gold_dijkstra.recalculate_map()

def make_bsp():
    global map, objects, stairs, bsp_rooms
 
    objects = [player]
 
    map = [[Tile(True) for y in range(MAP_HEIGHT)] for x in range(MAP_WIDTH)]
 
    #Empty global list for storing room coordinates
    bsp_rooms = []
 
    #New root node
    bsp = libtcod.bsp_new_with_size(0, 0, MAP_WIDTH, MAP_HEIGHT)
 
    #Split into nodes
    libtcod.bsp_split_recursive(bsp, 0, DEPTH, MIN_SIZE + 1, MIN_SIZE + 1, 1.5, 1.5)
 
    #Traverse the nodes and create rooms                            
    libtcod.bsp_traverse_inverted_level_order(bsp, traverse_node)
 
    #Random room for the stairs
    stairs_location = random.choice(bsp_rooms)
    bsp_rooms.remove(stairs_location)
    stairs = Object(stairs_location[0], stairs_location[1], '<', 'stairs', libtcod.white, always_visible=True)
    objects.append(stairs)
    stairs.send_to_back()
 
    #Random room for player start
    player_room = random.choice(bsp_rooms)
    bsp_rooms.remove(player_room)
    player.x = player_room[0]
    player.y = player_room[1]
 
    #try 100 times to make doors
    for attempts in range(0, 500):
        tx = libtcod.random_get_int(0, 1, MAP_WIDTH - 1)
        ty = libtcod.random_get_int(0, 1, MAP_HEIGHT - 1)
        
        make_door(tx, ty)
 
    #Add monsters and items
    for room in bsp_rooms:
        new_room = Rect(room[0], room[1], 2, 2)
        place_objects(new_room)
 
    initialize_fov()

def traverse_node(node, dat):
    global map, bsp_rooms
 
    #Create rooms
    if libtcod.bsp_is_leaf(node):
        minx = node.x + 1
        maxx = node.x + node.w - 1
        miny = node.y + 1
        maxy = node.y + node.h - 1
 
        if maxx == MAP_WIDTH - 1:
            maxx -= 1
        if maxy == MAP_HEIGHT - 1:
            maxy -= 1
 
        #If it's False the rooms sizes are random, else the rooms are filled to the node's size
        if FULL_ROOMS == False:
            minx = libtcod.random_get_int(None, minx, maxx - MIN_SIZE + 1)
            miny = libtcod.random_get_int(None, miny, maxy - MIN_SIZE + 1)
            maxx = libtcod.random_get_int(None, minx + MIN_SIZE - 2, maxx)
            maxy = libtcod.random_get_int(None, miny + MIN_SIZE - 2, maxy)
 
        node.x = minx
        node.y = miny
        node.w = maxx-minx + 1
        node.h = maxy-miny + 1
 
        #Dig room
        for x in range(minx, maxx + 1):
            for y in range(miny, maxy + 1):
                map[x][y].blocked = False
                map[x][y].block_sight = False
 
        #Add center coordinates to the list of rooms
        bsp_rooms.append(((minx + maxx) / 2, (miny + maxy) / 2))
 
    #Create corridors    
    else:
        left = libtcod.bsp_left(node)
        right = libtcod.bsp_right(node)
        node.x = min(left.x, right.x)
        node.y = min(left.y, right.y)
        node.w = max(left.x + left.w, right.x + right.w) - node.x
        node.h = max(left.y + left.h, right.y + right.h) - node.y
        if node.horizontal:
            if left.x + left.w - 1 < right.x or right.x + right.w - 1 < left.x:
                x1 = libtcod.random_get_int(None, left.x, left.x + left.w - 1)
                x2 = libtcod.random_get_int(None, right.x, right.x + right.w - 1)
                y = libtcod.random_get_int(None, left.y + left.h, right.y)
                vline_up(map, x1, y - 1)
                hline(map, x1, y, x2)
                vline_down(map, x2, y + 1)
 
            else:
                minx = max(left.x, right.x)
                maxx = min(left.x + left.w - 1, right.x + right.w - 1)
                x = libtcod.random_get_int(None, minx, maxx)
 
                # catch out-of-bounds attempts
                while x > MAP_WIDTH - 1:
                        x -= 1
 
                vline_down(map, x, right.y)
                vline_up(map, x, right.y - 1)
 
        else:
            if left.y + left.h - 1 < right.y or right.y + right.h - 1 < left.y:
                y1 = libtcod.random_get_int(None, left.y, left.y + left.h - 1)
                y2 = libtcod.random_get_int(None, right.y, right.y + right.h - 1)
                x = libtcod.random_get_int(None, left.x + left.w, right.x)
                hline_left(map, x - 1, y1)
                vline(map, x, y1, y2)
                hline_right(map, x + 1, y2)
            else:
                miny = max(left.y, right.y)
                maxy = min(left.y + left.h - 1, right.y + right.h - 1)
                y = libtcod.random_get_int(None, miny, maxy)
 
                # catch out-of-bounds attempts
                while y > MAP_HEIGHT - 1:
                         y -= 1
 
                hline_left(map, right.x - 1, y)
                hline_right(map, right.x, y)
 
    return True
    
def make_door(x, y):
    global map
    
    #check against DOOR_CHANCE %
    door_check = libtcod.random_get_int(0, 100, 1)
    #print str(DOOR_CHANCE) + " > " + str(door_check) + "?"
    if (DOOR_CHANCE >= door_check):
        #print "t ... in range? " + str(x) + "," + str(y) + "?"
        if 0 < x < (MAP_WIDTH - 1) and 0 < y < (MAP_HEIGHT - 1):
            #print "t ... hallway?"
            hallway = False
            if (map[x-1][y].block_sight == True and map[x+1][y].block_sight == True and map[x][y].block_sight == False):
                hallway = True
            elif (map [x][y-1].block_sight == True and map[x][y+1].block_sight == True and map[x][y].block_sight == False):
                hallway = True
                
            if hallway:
                
                other_doors = False
                #check for nearby doors
                for tx in range(-2, 2):
                    for ty in range(-2, 2):
                        if in_map_range(x+tx, y+ty):
                            if map[x+tx][y+ty].is_door:
                                other_doors = True
                
                if not other_doors:
                    #create a door object,
                    #print "t ... door at : " + str(x) + "," + str(y)
                    item_component = Item(use_function=use_door, pickup_sound=None, use_sound=SFX_DOOR)
                    item = Object(x, y, '+', 'closed door', libtcod.white, item=item_component)
                      
                    objects.append(item)
                
                    map[x][y].block_sight = True
                    map[x][y].is_door = True
                    map[x][y].blocked = True
            
    #for obj in objects:
    #    if obj.name == "closed door":
    #        map[obj.x][obj.y].block_sight = True
    #        map[obj.x][obj.y].is_door = True
    #        map[obj.x][obj.y].blocked = True

def try_kick():
    global blood_map
    
    message('Kick in what direction?', libtcod.lighter_blue)
    choice = libtcod.console_wait_for_keypress(True)
    #movement keys
    (dx, dy) = (None, None)
    if choice.vk == libtcod.KEY_UP or choice.vk == libtcod.KEY_KP8:
        (dx, dy) = (0, -1)
        
    elif choice.vk == libtcod.KEY_DOWN or choice.vk == libtcod.KEY_KP2:
        (dx, dy) = (0, 1)
        
    elif choice.vk == libtcod.KEY_LEFT or choice.vk == libtcod.KEY_KP4:
        (dx, dy) = (-1, 0)
        
    elif choice.vk == libtcod.KEY_RIGHT or choice.vk == libtcod.KEY_KP6:
        (dx, dy) = (1, 0)
        
    elif choice.vk == libtcod.KEY_HOME or choice.vk == libtcod.KEY_KP7:
        (dx, dy) = (-1, -1)
        
    elif choice.vk == libtcod.KEY_PAGEUP or choice.vk == libtcod.KEY_KP9:
        (dx, dy) = (1, -1)
        
    elif choice.vk == libtcod.KEY_END or choice.vk == libtcod.KEY_KP1:
        (dx, dy) = (-1, 1)
        
    elif choice.vk == libtcod.KEY_PAGEDOWN or choice.vk == libtcod.KEY_KP3:
        (dx, dy) = (1, 1)
    else:
        (dx, dy) = (None, None)
        
        
    if not (dx, dy) == (None,  None):    
        found = False
        for obj in objects:
            if found == False:
                if obj.x == player.x+dx and obj.y == player.y+dy:
                    found = True
                    if obj.name == 'closed door' or obj.name == 'open door':
                        #add kicking doors here
                        message('You kick the door, but it does not budge.', libtcod.gray)
                        
                    elif obj.name == 'stairs':
                            message('You kick the stairs and manage to mess up your toe pretty badly.', libtcod.gray)
                            player.fighter.take_damage(3)
                            
                    else:
                        if (map[obj.x+dx][obj.y+dy].block_sight and map[obj.x+dx][obj.y+dy].is_door == False) or map[obj.x+dx][obj.y+dy].blocked:
                            message('You kick the ' + obj.name +', but it does not budge.', libtcod.gray)
                            
                        elif obj.fighter:
                                message('The ' + obj.name + ' dodges your kick.', libtcod.gray)
                                
                        elif obj.char == '%':
                            #kick that corpse
                            blood_map[obj.x+dx][obj.y+dy] = 1
                            obj.x = obj.x + dx
                            obj.y = obj.y +dy
                            message('You kick the ' + obj.name + '.', libtcod.gray)
                        else:
                            obj.x = obj.x + dx
                            obj.y = obj.y +dy
                            message('You kick the ' + obj.name + '.', libtcod.gray)
                    
        if not found:
            message('Nothing in that direction to kick.', libtcod.white)
            
            
def try_close_door():
    message('Close door in what direction?', libtcod.lighter_blue)
    choice = libtcod.console_wait_for_keypress(True)
    #movement keys
    (dx, dy) = (None, None)
    if choice.vk == libtcod.KEY_UP or choice.vk == libtcod.KEY_KP8:
        (dx, dy) = (0, -1)
        
    elif choice.vk == libtcod.KEY_DOWN or choice.vk == libtcod.KEY_KP2:
        (dx, dy) = (0, 1)
        
    elif choice.vk == libtcod.KEY_LEFT or choice.vk == libtcod.KEY_KP4:
        (dx, dy) = (-1, 0)
        
    elif choice.vk == libtcod.KEY_RIGHT or choice.vk == libtcod.KEY_KP6:
        (dx, dy) = (1, 0)
        
    elif choice.vk == libtcod.KEY_HOME or choice.vk == libtcod.KEY_KP7:
        (dx, dy) = (-1, -1)
        
    elif choice.vk == libtcod.KEY_PAGEUP or choice.vk == libtcod.KEY_KP9:
        (dx, dy) = (1, -1)
        
    elif choice.vk == libtcod.KEY_END or choice.vk == libtcod.KEY_KP1:
        (dx, dy) = (-1, 1)
        
    elif choice.vk == libtcod.KEY_PAGEDOWN or choice.vk == libtcod.KEY_KP3:
        (dx, dy) = (1, 1)
    else:
        (dx, dy) = (None, None)
    
    if (dx, dy) == (None, None):
        pass #cancel
        
    elif map[player.x+dx][player.y+dy].is_door:
        for obj in objects:
            if obj.x == player.x+dx and obj.y == player.y+dy and obj.name == 'open door':
                if is_blocked(obj.x, obj.y):
                    message('Something is blocking the door.',libtcod.lightest_red)
                else:
                    obj.item.use_function(player.x+dx, player.y+dy)
                    message('You swing the door shut.', libtcod.gray)
                    map_sound(player.x+dx, player.y+dy, intensity=15)
                
    else:
        message('No door in that direction to close.', libtcod.white)
            


def vline(map, x, y1, y2):
    if y1 > y2:
        y1,y2 = y2,y1
 
    for y in range(y1,y2+1):
        map[x][y].blocked = False
        map[x][y].block_sight = False
 
def vline_up(map, x, y):
    while y >= 0 and map[x][y].blocked == True:
        map[x][y].blocked = False
        map[x][y].block_sight = False
        y -= 1
 
def vline_down(map, x, y):
    while y < MAP_HEIGHT and map[x][y].blocked == True:
        map[x][y].blocked = False
        map[x][y].block_sight = False
        y += 1
 
def hline(map, x1, y, x2):
    if x1 > x2:
        x1,x2 = x2,x1
    for x in range(x1,x2+1):
        map[x][y].blocked = False
        map[x][y].block_sight = False
 
def hline_left(map, x, y):
    while x >= 0 and map[x][y].blocked == True:
        map[x][y].blocked = False
        map[x][y].block_sight = False
        x -= 1
 
def hline_right(map, x, y):
    while x < MAP_WIDTH and map[x][y].blocked == True:
        map[x][y].blocked = False
        map[x][y].block_sight = False
        x += 1
           
def random_choice_index(chances):  #choose one option from list of chances, returning its index
    #the dice will land on some number between 1 and the sum of the chances
    dice = libtcod.random_get_int(0, 1, sum(chances))
 
    #go through all chances, keeping the sum so far
    running_sum = 0
    choice = 0
    for w in chances:
        running_sum += w
 
        #see if the dice landed in the part that corresponds to this choice
        if dice <= running_sum:
            return choice
        choice += 1
 
def random_choice(chances_dict):
    #choose one option from dictionary of chances, returning its key
    chances = chances_dict.values()
    strings = chances_dict.keys()
 
    return strings[random_choice_index(chances)]
 
def from_dungeon_level(table):
    #returns a value that depends on level. the table specifies what value occurs after each level, default is 0.
    for (value, level) in reversed(table):
        if dungeon_level >= level:
            return value
    return 0
 
def place_objects(room):
    #this is where we decide the chance of each monster or item appearing.
 
    #maximum number of monsters per room
    max_monsters = from_dungeon_level([[2, 1], [3, 4], [5, 6]])
 
    #chance of each monster
    monster_chances = {}
    monster_chances['gerblin'] = 80  #gerblin always shows up, even if all other monsters have 0 chance
    monster_chances['gnoll pl'] = from_dungeon_level([[15, 3], [30, 5], [60, 7]])
    monster_chances['gnoll foy'] = from_dungeon_level([[1, 1], [5, 3], [10,5]])
 
    #maximum number of items per room
    max_items = from_dungeon_level([[1, 1], [2, 4]])
 
    #chance of each item (by default they have a chance of 0 at level 1, which then goes up)
    item_chances = {}
    item_chances['gold'] = 5 #always shows up  
    item_chances['oil'] = 35 #always shows up
    item_chances['heal'] = 20  #healing potion always shows up, even if all other items have 0 chance
    item_chances['magic map'] = 2
    item_chances['lightning'] = from_dungeon_level([[25, 3]])
    item_chances['fireball'] =  from_dungeon_level([[25, 4]])
    item_chances['confuse'] =   from_dungeon_level([[10, 2]])
    item_chances['sword'] =     from_dungeon_level([[5, 4]])
    item_chances['shield'] =    from_dungeon_level([[15, 6]])
 
 
    #choose random number of monsters
    num_monsters = libtcod.random_get_int(0, 0, max_monsters)
 
    for i in range(num_monsters):
        #choose random spot for this monster
        x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
        y = libtcod.random_get_int(0, room.y1+1, room.y2-1)
 
        #only place it if the tile is not blocked
        if not is_blocked(x, y):
            choice = random_choice(monster_chances)
            if choice == 'gerblin':
                #create a gerblin
                fighter_component = Fighter(hp=7, ac=7, strength=8, dexterity=14, constitution=10, intelligence=10, 
                                            wisdom=8, charisma=8, damage=15, luck=1, speed=3, xp=50,
                                            atk_sound=SFX_GNOLLATK, hit_sound=SFX_GNOLLHIT, death_sound=SFX_MONSTERDIE,
                                            death_function=monster_death)
                ai_component = BasicMonster()
 
                monster = Object(x, y, 'g', 'Gerblin', libtcod.desaturated_green,
                                 blocks=True, fighter=fighter_component, ai=ai_component)
 
            elif choice == 'gnoll pl':
                #create a Gnoll Pack Lord
                fighter_component = Fighter(hp=49, ac=7, strength=16, dexterity=14, constitution=13, intelligence=8, 
                                            wisdom=11, charisma=9, damage=15, luck=1, speed=2.8, xp=450, 
                                            atk_sound=SFX_GNOLLATK, hit_sound=SFX_GNOLLHIT, death_sound=SFX_MONSTERDIE,
                                            death_function=monster_death)
                ai_component = BasicMonster()
 
                monster = Object(x, y, 'g', 'Gnoll Pack Lord', libtcod.dark_orange,
                                 blocks=True, fighter=fighter_component, ai=ai_component)
 
            elif choice == "gnoll foy":
                #create a 'Gnoll Fang of Yeenoghu'
                fighter_component = Fighter(hp=65, ac=6, strength=17, dexterity=15, constitution=15, intelligence=10, 
                                            wisdom=11, charisma=13, damage=20, luck=1, speed=2.5, xp=1100, 
                                            atk_sound=SFX_TROLLATK, hit_sound=SFX_TROLLHIT, death_sound=SFX_MONSTERDIE,
                                            death_function=monster_death)
                ai_component = BasicMonster()
 
                monster = Object(x, y, 'g', 'Gnoll; Fang of Yeenoghu', libtcod.red,
                                blocks=True, fighter=fighter_component, ai=ai_component)            
            
            objects.append(monster)
 
    #choose random number of items
    num_items = libtcod.random_get_int(0, 0, max_items)
 
    for i in range(num_items):
        #choose random spot for this item
        x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
        y = libtcod.random_get_int(0, room.y1+1, room.y2-1)
 
        #only place it if the tile is not blocked
        if not is_blocked(x, y):
            choice = random_choice(item_chances)
            if choice == 'heal':
                #create a healing potion
                item_component = Item(stacks=False, count=1, use_function=cast_heal, pickup_sound=SFX_POTIONPICKUP, use_sound=SFX_POTIONUSE)
                item = Object(x, y, '!', 'Healing Potion', libtcod.light_violet, item=item_component)
                
            elif choice == 'gold':
                #create a gold pile
                item_component = Item(stacks=True, count=10, use_function=throw_gold, pickup_sound=SFX_GOLDPICKUP, use_sound=SFX_GOLDPICKUP)
                item = Object(x, y, '$', 'Gold', libtcod.light_yellow, item=item_component)
            
            elif choice == 'oil':
                #create an oil lamp
                item_component = Item(stacks=False, count=1, use_function=use_oil, pickup_sound=SFX_POTIONPICKUP, use_sound=None)
                item = Object(x, y, '!', 'Oil Flask', libtcod.light_yellow, item=item_component)
            
            elif choice == 'magic map':
                #create a scroll of magic maping
                item_component = Item(stacks=True, count=1, use_function=cast_magicmap, pickup_sound=SFX_SCROLLPICKUP, use_sound=None)
                item = Object(x, y, '#', 'Scroll of Magical Mapping', libtcod.light_yellow, item=item_component)
            
            elif choice == 'lightning':
                #create a lightning bolt scroll
                item_component = Item(use_function=cast_lightning, pickup_sound=SFX_SCROLLPICKUP, use_sound=SFX_LIGHTNINGHIT)
                item = Object(x, y, '#', 'Scroll of Lightning Bolt', libtcod.light_yellow, item=item_component)
 
            elif choice == 'fireball':
                #create a fireball scroll
                item_component = Item(use_function=cast_fireball, pickup_sound=SFX_SCROLLPICKUP, use_sound=SFX_FIREBALLHIT)
                item = Object(x, y, '#', 'Scroll of Fireball', libtcod.light_yellow, item=item_component)
 
            elif choice == 'confuse':
                #create a confuse scroll
                item_component = Item(use_function=cast_confuse, pickup_sound=SFX_SCROLLPICKUP, use_sound=SFX_CONFUSEHIT)
                item = Object(x, y, '#', 'Scroll of Confusion', libtcod.light_yellow, item=item_component)
 
            elif choice == 'sword':
                #create a sword
                equipment_component = Equipment(slot='right hand', strength_bonus=3)
                item = Object(x, y, '/', 'Sword', libtcod.sky, equipment=equipment_component)
 
            elif choice == 'shield':
                #create a shield
                equipment_component = Equipment(slot='left hand', ac_bonus=1)
                item = Object(x, y, '[', 'Shield', libtcod.darker_orange, equipment=equipment_component)
 
            objects.append(item)
            item.send_to_back()  #items appear below other objects
            item.always_visible = True  #items are visible even out-of-FOV, if in an explored area
 
 
def render_bar(x, y, total_width, name, value, maximum, bar_color, back_color):
    #render a bar (HP, experience, etc). first calculate the width of the bar
    bar_width = int(float(value) / maximum * total_width)
 
    #render the background first
    libtcod.console_set_default_background(panel, back_color)
    libtcod.console_rect(panel, x, y, total_width, 1, False, libtcod.BKGND_SCREEN)
 
    #now render the bar on top
    libtcod.console_set_default_background(panel, bar_color)
    if bar_width > 0:
        libtcod.console_rect(panel, x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)
 
    #finally, some centered text with the values
    libtcod.console_set_default_foreground(panel, libtcod.black)
    libtcod.console_print_ex(panel, x + total_width / 2, y, libtcod.BKGND_NONE, libtcod.CENTER,
                                 name + ': ' + str(int(value)) + '/' + str(int(maximum)))
 
def get_names_under_mouse():
    global mouse
    #return a string with the names of all objects under the mouse
 
    (x, y) = (mouse.cx, mouse.cy)
 
    #create a list with the names of all objects at the mouse's coordinates and in FOV
    names = [obj.name for obj in objects
             if obj.x == x and obj.y == y and libtcod.map_is_in_fov(fov_map, obj.x, obj.y)]
 
    names = ', '.join(names)  #join the names, separated by commas
    
    #return str(x) + "," + str(y)
    return names
 
def render_all():
    global fov_map, color_dark_wall, color_light_wall
    global color_dark_ground, color_light_ground
    global fov_recompute, blood_map
 
    if fov_recompute:
        #recompute FOV if needed (the player moved or something)
        fov_recompute = False
        libtcod.map_compute_fov(fov_map, player.x, player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO)
 
        #go through all tiles, and set their background color according to the FOV
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                visible = libtcod.map_is_in_fov(fov_map, x, y)
                blocks = map[x][y].block_sight
                door = map[x][y].is_door
                if not visible:
                    #if it's not visible right now, the player can only see it if it's explored
                    if map[x][y].explored:
                        if blocks:
                            if door:
                                libtcod.console_set_char_background(con, x, y, color_dark_ground, libtcod.BKGND_SET)
                            else:
                                libtcod.console_set_char_background(con, x, y, color_dark_wall, libtcod.BKGND_SET)
                        else:
                            libtcod.console_set_char_background(con, x, y, color_dark_ground, libtcod.BKGND_SET)                               
                else:
                    #since it's visible, explore it
                    map[x][y].explored = True   
                    
                    if blood_map[x][y] > 0:
                         libtcod.console_set_char_background(con, x, y, libtcod.darker_red, libtcod.BKGND_SET)
                    elif blocks:
                        if door:
                            libtcod.console_set_char_background(con, x, y, color_light_ground, libtcod.BKGND_SET )
                        else:
                            libtcod.console_set_char_background(con, x, y, color_light_wall, libtcod.BKGND_SET )
                    else:
                        libtcod.console_set_char_background(con, x, y, color_light_ground, libtcod.BKGND_SET )
                    
    #draw all objects in the list, except the player. we want it to
    #always appear over all other objects! so it's drawn later.
    for object in objects:
        if object != player:
            object.draw()
    player.draw()
    
    
 
    #blit the contents of "con" to the root console
    libtcod.console_blit(con, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0, 0)
 
    #for y in range(MAP_HEIGHT):
    #                for x in range(MAP_WIDTH):
    #                    if not map[x][y].blocked:
    #                        libtcod.console_print_ex(0, x, y, libtcod.BKGND_NONE, libtcod.CENTER, str(player_dijkstra.cell_at(x, y)))
 
    #draw context hints for the first dungeon level
    if dungeon_level == 1:
        libtcod.console_set_default_background(0, libtcod.darker_gray)
        libtcod.console_set_default_foreground(0, libtcod.white)
        
        if player.y >= MAP_HEIGHT/2: #player on bottom half of the screen
            (tx, ty) = (77, 2)
        else: #player on top half of the map
            (tx, ty) = (77, 42)
        
        for object in objects:
            if object.x == player.x and object.y == player.y:
                if object.item:
                    if map[player.x][player.y].is_door == False:
                        libtcod.console_print_ex(0, tx, ty, libtcod.BKGND_SET, libtcod.RIGHT, " Press [g] to grab items. ")
                if object.name == "stairs":
                        libtcod.console_print_ex(0, tx, ty, libtcod.BKGND_SET, libtcod.RIGHT, " Press [,] to go down the stairs. ")
                        
        myneighbors = [(-1, -1), (0, -1), (1, -1),
                     (-1, 0), (1, 0),
                     (-1, 1), (0, 1), (1, 1)]
                     
        for dx, dy in myneighbors:
            tdx, tdy = player.x + dx, player.y + dy
            if map[tdx][tdy].is_door:
                if map[tdx][tdy].block_sight:
                    libtcod.console_print_ex(0, tx, ty, libtcod.BKGND_SET, libtcod.RIGHT, " Bump into a closed door to open it. ")
                        
                else:  
                    libtcod.console_print_ex(0, tx, ty, libtcod.BKGND_SET, libtcod.RIGHT, " Press [c] and then a direction to close an open door. ")
                                
                    
    #prepare to render the GUI panel
    libtcod.console_set_default_background(panel, libtcod.black)
    libtcod.console_clear(panel)
 
    #print the game messages, one line at a time
    y = 1
    for (line, color) in game_msgs:
        libtcod.console_set_default_foreground(panel, color)
        libtcod.console_print_ex(panel, MSG_X, y, libtcod.BKGND_NONE, libtcod.LEFT,line)
        y += 1
 
    #show the player's stats
    render_bar(1, 1, BAR_WIDTH, 'HP', player.fighter.hp, player.fighter.max_hp,
               libtcod.light_red, libtcod.darker_red)
    render_bar(1, 2, BAR_WIDTH, 'Oil', player.oil, player.max_oil_level,
               libtcod.light_yellow, libtcod.darker_yellow)
    libtcod.console_set_default_foreground(panel, libtcod.white)
    libtcod.console_print_ex(panel, 1, 3, libtcod.BKGND_NONE, libtcod.LEFT, 'Dungeon level ' + str(dungeon_level))
 
    #display names of objects under the mouse
    libtcod.console_set_default_foreground(panel, libtcod.light_gray)
    libtcod.console_print_ex(panel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT, get_names_under_mouse())
 
    #blit the contents of "panel" to the root console
    libtcod.console_blit(panel, 0, 0, SCREEN_WIDTH, PANEL_HEIGHT, 0, 0, PANEL_Y)
 
 
def message(new_msg, color = libtcod.white):
    #split the message if necessary, among multiple lines
    new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)
 
    for line in new_msg_lines:
        if new_msg_lines.index(line) > 0:
            line = '   ' + line
        #if the buffer is full, remove the first line to make room for the new one
        if len(game_msgs) == MSG_HEIGHT:
            del game_msgs[0]
 
        #add the new line as a tuple, with the text and the color
        game_msgs.append( (line, color) )
 
 
def player_move_or_attack(dx, dy):
    global fov_recompute
 
    #the coordinates the player is moving to/attacking
    x = player.x + dx
    y = player.y + dy
    
    player.oil = player.oil - OIL_DECAY
    if player.oil < 0:
        player.oil = 0
    
    door = False
 
    #try to find an attackable object there
    target = None
    for object in objects:
        
        if object.name == "closed door":
            if Opt_Auto_Open_Door and object.x == x and object.y == y:
                object.item.use_function(x, y)
                door = True
                
        if object.fighter and object.x == x and object.y == y:
            target = object
            break
 
    #attack if target found, move otherwise
    if target is not None and target is not player:
        player.fighter.attack(target)
    elif door:
        #add player ability to attack doors
        pass
    else:
        player.move(dx, dy)
        player_dijkstra.clear_goals()
        player_dijkstra.add_goal(player.x, player.y)
        #player_dijkstra.recalculate_single(player.x, player.y)
        player_dijkstra.recalculate_single(player.x, player.y)
        fov_recompute = True

        
def menu(header, options, width):
    if len(options) > 26: raise ValueError('Cannot have a menu with more than 26 options.')
 
    #calculate total height for the header (after auto-wrap) and one line per option
    header_height = libtcod.console_get_height_rect(con, 0, 0, width, SCREEN_HEIGHT, header)
    if header == '':
        header_height = 0
    height = len(options) + header_height
 
    #create an off-screen console that represents the menu's window
    window = libtcod.console_new(width, height)
 
    #print the header, with auto-wrap
    libtcod.console_set_default_foreground(window, libtcod.white)
    libtcod.console_print_rect_ex(window, 0, 0, width, height, libtcod.BKGND_NONE, libtcod.LEFT, header)
 
    #print all the options
    y = header_height
    letter_index = ord('a')
    for option_text in options:
        text = '(' + chr(letter_index) + ') ' + option_text
        libtcod.console_print_ex(window, 0, y, libtcod.BKGND_NONE, libtcod.LEFT, text)
        y += 1
        letter_index += 1
 
    #blit the contents of "window" to the root console
    x = SCREEN_WIDTH/2 - width/2
    y = SCREEN_HEIGHT/2 - height/2
    libtcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.7)
 
    #present the root console to the player and wait for a key-press
    libtcod.console_flush()
    key = libtcod.console_wait_for_keypress(True)
 
    if key.vk == libtcod.KEY_ENTER and key.lalt:  #(special case) Alt+Enter: toggle fullscreen
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen)
 
    #convert the ASCII code to an index; if it corresponds to an option, return it
    index = key.c - ord('a')
    if index >= 0 and index < len(options): return index
    return None
 
def inventory_menu(header):
    #show a menu with each item of the inventory as an option
    if len(inventory) == 0:
        options = ['Inventory is empty.']
    else:
        options = []
        for item in inventory:
            text = item.name + " (" + str(item.item.count) + ")"
            #show additional information, in case it's equipped
            if item.equipment and item.equipment.is_equipped:
                text = text + ' (on ' + item.equipment.slot + ')'
            options.append(text)
 
    index = menu(header, options, INVENTORY_WIDTH)
 
    #if an item was chosen, return it
    if index is None or len(inventory) == 0: return None
    return inventory[index].item
 
def msgbox(text, width=50):
    menu(text, [], width)  #use menu() as a sort of "message box"
 
def handle_keys():
    global key
 
    if key.vk == libtcod.KEY_ENTER and key.lalt:
        #Alt+Enter: toggle fullscreen
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
 
    elif key.vk == libtcod.KEY_ESCAPE:
        return 'exit'  #exit game
 
    if game_state == 'playing':
        #movement keys
        if key.vk == libtcod.KEY_UP or key.vk == libtcod.KEY_KP8:
            player_move_or_attack(0, -1)
            
        elif key.vk == libtcod.KEY_DOWN or key.vk == libtcod.KEY_KP2:
            player_move_or_attack(0, 1)
            
        elif key.vk == libtcod.KEY_LEFT or key.vk == libtcod.KEY_KP4:
            player_move_or_attack(-1, 0)
            
        elif key.vk == libtcod.KEY_RIGHT or key.vk == libtcod.KEY_KP6:
            player_move_or_attack(1, 0)
            
        elif key.vk == libtcod.KEY_KP5:
            player_move_or_attack(0, 0)
            player_move_or_attack(0, 0)
            
        elif key.vk == libtcod.KEY_HOME or key.vk == libtcod.KEY_KP7:
            player_move_or_attack(-1, -1)
            
        elif key.vk == libtcod.KEY_PAGEUP or key.vk == libtcod.KEY_KP9:
            player_move_or_attack(1, -1)
            
        elif key.vk == libtcod.KEY_END or key.vk == libtcod.KEY_KP1:
            player_move_or_attack(-1, 1)
            
        elif key.vk == libtcod.KEY_PAGEDOWN or key.vk == libtcod.KEY_KP3:
            player_move_or_attack(1, 1)
            
        elif key.vk == libtcod.KEY_KP5:
            pass  #do nothing ie wait for the monster to come to you
            
                    
        else:
            #test for other keys
            key_char = chr(key.c)
 
            if key_char == 'g':
                #pick up an item
                for object in objects:  #look for an item in the player's tile
                    if object.x == player.x and object.y == player.y and object.item:
                        object.item.pick_up()
                        break
 
            elif key_char == 'i':
                #show the inventory; if an item is selected, use it
                chosen_item = inventory_menu('Press the key next to an item to use it, or any other to cancel.\n')
                if chosen_item is not None:
                    chosen_item.use()
 
            elif key_char == 'k':
                #let's kick some stuff
                try_kick()
 
            elif key_char == 'd':
                #show the inventory; if an item is selected, drop it
                chosen_item = inventory_menu('Press the key next to an item to drop it, or any other to cancel.\n')
                if chosen_item is not None:
                    chosen_item.drop()
 
            elif key_char == 'c':
                #do stuff
                #message("Close door in which direction?",libtcod.white)
                try_close_door()
                
            
            elif key_char == 's':
                #show character information
                level_up_xp = LEVEL_UP_BASE + player.level * LEVEL_UP_FACTOR
                msgbox('Character Information\n\nLevel: ' + str(player.level) + '\nExperience: ' + str(player.fighter.xp) +
                       '\nExperience to level up: ' + str(level_up_xp) + '\n\nMaximum HP: ' + str(player.fighter.max_hp) +
                       '\nAttack: ' + str(player.fighter.strength) + '\nac: ' + str(player.fighter.ac), CHARACTER_SCREEN_WIDTH)
 
            elif key_char == ",":
                #go down stairs, if the player is on them
                if stairs.x == player.x and stairs.y == player.y:
                    next_level()
 
            return 'didnt-take-turn'
 
def check_level_up():
    #see if the player's experience is enough to level-up
    level_up_xp = LEVEL_UP_BASE + player.level * LEVEL_UP_FACTOR
    if player.fighter.xp >= level_up_xp:
        #it is! level up and ask to raise some stats
        player.level += 1
        player.fighter.xp -= level_up_xp
        message('Your battle skills grow stronger! You reached level ' + str(player.level) + '!', libtcod.yellow)
        Play_BGSFX(SFX_LEVELUP)
 
        if player.level % 2 == 0: #even-number levels grant stat bonuses
 
            choice = None
            while choice == None:  #keep asking until a choice is made
                choice = menu('Level up! Choose a stat to raise:\n',
                              ['Constitution (+20 HP, from ' + str(player.fighter.max_hp) + ')',
                               'Strength (+1 attack, from ' + str(player.fighter.strength) + ')',
                               'Agility (+1 ac, from ' + str(player.fighter.ac) + ')'], LEVEL_SCREEN_WIDTH)
     
            if choice == 0:
                player.fighter.base_max_hp += 20
                player.fighter.hp += 20
            elif choice == 1:
                player.fighter.base_strength += 1
            elif choice == 2:
                player.fighter.base_ac += 1
 
def player_death(player):
    #the game ended!
    global game_state
    message('You died!', libtcod.red)
    game_state = 'dead'
 
    #for added effect, transform the player into a corpse!
    player.fighter.hp = 0
    player.char = '%'
    player.name = "Corpse of " + player.name
    player.color = libtcod.dark_red
 
def monster_death(monster):
    #transform it into a nasty corpse! it doesn't block, can't be
    #attacked and doesn't move
    message('The ' + monster.name + ' is dead!', libtcod.grey)
    message('You gain ' + str(monster.fighter.xp) + ' experience points.', libtcod.light_green)
    monster.char = '%'
    monster.color = libtcod.light_red
    monster.blocks = False
    if monster.fighter.death_sound:
        Play_NPCCombat(monster.fighter.death_sound)
    monster.fighter = None
    monster.ai = None
    monster.send_to_back()
    monster.name = monster.name + ' Corpse'
    blood_map[monster.x][monster.y] = 1
    
def target_tile(max_range=None):
    global key, mouse
    #return the position of a tile left-clicked in player's FOV (optionally in a range), or (None,None) if right-clicked.
    while True:
        #render the screen. this erases the inventory and shows the names of objects under the mouse.
        libtcod.console_flush()
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)
        render_all()
 
        (x, y) = (mouse.cx, mouse.cy)
 
        if mouse.rbutton_pressed or key.vk == libtcod.KEY_ESCAPE:
            return (None, None)  #cancel if the player right-clicked or pressed Escape
 
        #accept the target if the player clicked in FOV, and in case a range is specified, if it's in that range
        if (mouse.lbutton_pressed and libtcod.map_is_in_fov(fov_map, x, y) and
                (max_range is None or player.distance(x, y) <= max_range)):
            return (x, y)
 
def target_monster(max_range=None):
    #returns a clicked monster inside FOV up to a range, or None if right-clicked
    while True:
        (x, y) = target_tile(max_range)
        if x is None:  #player cancelled
            return None
 
        #return the first clicked monster, otherwise continue looping
        for obj in objects:
            if obj.x == x and obj.y == y and obj.fighter and obj != player:
                return obj
 
def closest_monster(max_range):
    #find closest enemy, up to a maximum range, and in the player's FOV
    closest_enemy = None
    closest_dist = max_range + 1  #start with (slightly more than) maximum range
 
    for object in objects:
        if object.fighter and not object == player and libtcod.map_is_in_fov(fov_map, object.x, object.y):
            #calculate distance between this object and the player
            dist = player.distance_to(object)
            if dist < closest_dist:  #it's closer, so remember it
                closest_enemy = object
                closest_dist = dist
    return closest_enemy


def use_door(x, y):
    for obj in objects:
        if obj.x == x and obj.y == y:
        
            if obj.name == "closed door":
                obj.name = "open door"
                obj.char = "-"
                map[x][y].block_sight = False
                map[x][y].blocked = False
                fov_recompute = True
                initialize_fov()
                Play_BGSFX(SFX_DOOR)
            
            elif obj.name == "open door":
                obj.name = "closed door"
                obj.char = "+"
                map[x][y].block_sight = True
                map[x][y].blocked = True
                fov_recompute = True
                initialize_fov()

def use_oil():
    global fov_recompute, TORCH_RADIUS
   
    player.oil = player.oil + OIL_LAMP + OIL_DECAY
    if player.oil > player.max_oil_level:
        player.oil = player.max_oil_level
    TORCH_RADIUS = int((player.oil) % (player.max_oil_level)/10) 
    fov_recompute = True
    
def cast_magicmap():
    global fov_recompute, TORCH_RADIUS
    
    #magic map sound is here instead of in the item component.
    #if it is in the item component, it doesnt play until after the effect
    Play_ItemSFX(SFX_MAGICMAPUSE)
    
    mrange = 18
    
    #make dijsktra map with player as goal
    magic_dijsktra = DijkstraMap(MAP_WIDTH, MAP_HEIGHT)
    magic_dijsktra._clear_map(default=mrange)
    magic_dijsktra.add_goal(player.x, player.y)
    magic_dijsktra.recalculate_map(default=mrange)
    
    changes = True
    icount = 0
    while changes == True:
        #magic_dijsktra.recalculate_map()
        icount = icount + 1
        changes = False
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                v = magic_dijsktra.tiles[x][y]
                
                if v > icount:
                    pass
                elif v == icount:
                    libtcod.console_set_char_background(0, x, y, libtcod.light_yellow, libtcod.BKGND_SCREEN)
                    changes = True
                    map[x][y].explored = True
                elif v == icount - 1:
                    libtcod.console_set_char_background(0, x, y, libtcod.lighter_yellow, libtcod.BKGND_SCREEN)
                    changes = True
                    map[x][y].explored = True
                elif v == icount - 2:
                    libtcod.console_set_char_background(0, x, y, libtcod.lightest_yellow, libtcod.BKGND_SCREEN)
                    changes = True
                    map[x][y].explored = True
                elif v == icount - 3:
                    libtcod.console_set_char_background(0, x, y, libtcod.white, libtcod.BKGND_SCREEN)
                    changes = True
                    map[x][y].explored = True

                        
        libtcod.console_flush()
        fov_recompute = True
        render_all()

                
def cast_heal():
    #heal the player
    if player.fighter.hp == player.fighter.max_hp:
        message('You are already at full health.', libtcod.red)
        return 'cancelled'
 
    message('Your wounds start to feel better!', libtcod.light_violet)
    player.fighter.heal(HEAL_AMOUNT)
 
def cast_lightning():
    #find closest enemy (inside a maximum range) and damage it
    monster = closest_monster(LIGHTNING_RANGE)
    if monster is None:  #no enemy found within maximum range
        message('No enemy is close enough to strike.', libtcod.red)
        return 'cancelled'
 
    #zap it!
    message('A lighting bolt strikes the ' + monster.name + ' with a loud thunder! The damage is '
            + str(LIGHTNING_DAMAGE) + ' hit points.', libtcod.light_blue)
    monster.fighter.take_damage(LIGHTNING_DAMAGE)
 
def cast_fireball():
    #ask the player for a target tile to throw a fireball at
    message('Left-click a target tile for the fireball, or right-click to cancel.', libtcod.light_cyan)
    (x, y) = target_tile()
    if x is None: return 'cancelled'
    message('The fireball explodes, burning everything within ' + str(FIREBALL_RADIUS) + ' tiles!', libtcod.orange)
 
    for obj in objects:  #damage every fighter in range, including the player
        if obj.distance(x, y) <= FIREBALL_RADIUS and obj.fighter:
            message('The ' + obj.name + ' gets burned for ' + str(FIREBALL_DAMAGE) + ' hit points.', libtcod.orange)
            obj.fighter.take_damage(FIREBALL_DAMAGE)
 
def cast_confuse():
    #ask the player for a target to confuse
    message('Left-click an enemy to confuse it, or right-click to cancel.', libtcod.light_cyan)
    monster = target_monster(CONFUSE_RANGE)
    if monster is None: return 'cancelled'
 
    #replace the monster's AI with a "confused" one; after some turns it will restore the old AI
    old_ai = monster.ai
    monster.ai = ConfusedMonster(old_ai)
    monster.ai.owner = monster  #tell the new component who owns it
    message('The eyes of the ' + monster.name + ' look vacant, as he starts to stumble around!', libtcod.light_green)

def throw_gold():
       
    found = False
    for itm in inventory:
        if itm.name == "gold":
            #if itm.item.count == 1:
            #    n = 1
            #else:
            n = random.randrange(1, itm.item.count+1)
            itm.item.count = (itm.item.count - n) +1
            if itm.item.count <= 0:
                inventory.remove(itm)
            found = True
        if found:
            break
            
    message("You throw " + str(n) + " gold up in the air and watch as it falls to the ground.", libtcod.white)
              
    dx = random.randrange(-1, 1)
    dy = random.randrange(-1, 1)
    
    added = False
    for obj in objects:
        if added:
            break
        #print obj.name
        if obj.name == "gold" and obj.x == player.x+dx and obj.y == player.y+dy:
            #found gold pile at desired position
                #print "added " + str(n) + " to pile at " + str(dx) + "," + str(dy) + " (from" + str(obj.item.count) + ")"
                obj.item.count = obj.item.count + n
                print str(obj.item.count)
                added = True
    else:
        #create a new gold pile
        item_component = Item(stacks=True, count=n, use_function=throw_gold, pickup_sound=SFX_GOLDPICKUP, use_sound=SFX_GOLDPICKUP)
        item = Object(player.x+dx, player.y+dy, '$', 'gold', libtcod.light_yellow, item=item_component)
    
        objects.append(item)

    gold_dijkstra.clear_goals()
    for obj in objects:
        if obj.name == "gold":
            gold_dijkstra.add_goal(obj.x, obj.y)
    gold_dijkstra.recalculate_single(obj.x, obj.y)
    
def save_game():
    #open a new empty shelve (possibly overwriting an old one) to write the game data
    file = shelve.open('savegame', 'n')
    file['map'] = map
    file['objects'] = objects
    file['player_index'] = objects.index(player)  #index of player in objects list
    file['stairs_index'] = objects.index(stairs)  #same for the stairs
    file['inventory'] = inventory
    file['game_msgs'] = game_msgs
    file['game_state'] = game_state
    file['dungeon_level'] = dungeon_level
    file.close()
 
def load_game():
    #open the previously saved shelve and load the game data
    global map, objects, player, stairs, inventory, game_msgs, game_state, dungeon_level
 
    file = shelve.open('savegame', 'r')
    map = file['map']
    objects = file['objects']
    player = objects[file['player_index']]  #get index of player in objects list and access it
    stairs = objects[file['stairs_index']]  #same for the stairs
    inventory = file['inventory']
    game_msgs = file['game_msgs']
    game_state = file['game_state']
    dungeon_level = file['dungeon_level']
    file.close()
 
    initialize_fov()
 
def new_game():
    global player, inventory, game_msgs, game_state, dungeon_level
 
    #create object representing the player
    fighter_component = Fighter(hp=100, ac=10, strength=10, dexterity=14, constitution=10, 
                                intelligence=10, wisdom=10, charisma=10, damage=2, luck=10, speed=3, xp=0, 
                                atk_sound=SFX_PLAYERATK, death_function=player_death)
    player = Object(0, 0, chr(2), 'Heroman', libtcod.white, blocks=True, fighter=fighter_component)
 
    player.level = 1
    
    #used for oil lamp / light
    player.max_oil_level = 100
    player.oil = player.max_oil_level
 
    #generate map (at this point it's not drawn to the screen
    dungeon_level = 1
    #make_map()
    make_bsp()
    
    initialize_fov()
 
    game_state = 'playing'
    inventory = []
 
    #create the list of game messages and their colors, starts empty
    game_msgs = []
 
    #a warm welcoming message!
    message('Welcome stranger! Prepare to perish in the Tombs of the Ancient Kings.', libtcod.red)
 
    #initial equipment: a dagger
    equipment_component = Equipment(slot='right hand', strength_bonus=2, damage_bonus=8, tohit_bonus=5)
    obj = Object(0, 0, '-', 'dagger', libtcod.sky, equipment=equipment_component)
    inventory.append(obj)
    equipment_component.equip()
    
    #create a scroll of magic mapping
    item_component = Item(stacks=True, count=1, use_function=cast_magicmap, pickup_sound=SFX_SCROLLPICKUP, use_sound=None)
    item = Object(0, 0, '#', 'Scroll of Magic Map', libtcod.light_yellow, item=item_component)
    inventory.append(item)
    
def next_level():
    Play_BGSFX(SFX_Stairs)
    #advance to the next level
    global dungeon_level
    message('You take a moment to rest, and recover your strength.', libtcod.light_violet)
    player.fighter.heal(player.fighter.max_hp / 2)  #heal the player by 50%
    
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            blood_map[x][y] = 0
    
    dungeon_level += 1
    message('You descend deeper into the heart of the dungeon...', libtcod.light_red)
    make_bsp()  #create a fresh new level!
    initialize_fov()
    
def initialize_fov():
    global fov_recompute, fov_map
    fov_recompute = True
 
    #create the FOV map, according to the generated map
    fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            libtcod.map_set_properties(fov_map, x, y, not map[x][y].block_sight, not map[x][y].blocked)
 
    libtcod.console_clear(con)  #unexplored areas start black (which is the default background color)
 
def play_game():
    global key, mouse, player_dijkstra, gold_dijkstra, sound_dijkstra, scent_map, blood_map
    
    player_action = None
 
    mouse = libtcod.Mouse()
    key = libtcod.Key()
    
    Play_BGM(BGM_CAVEMUSIC)
    
    #make the initial dijkstras / AI Maps
    player_dijkstra = DijkstraMap(MAP_WIDTH, MAP_HEIGHT)
    gold_dijkstra = DijkstraMap(MAP_WIDTH, MAP_HEIGHT)
    sound_dijkstra = DijkstraMap(MAP_WIDTH, MAP_HEIGHT)
    sound_dijkstra._clear_map(15)
    
    scent_map = [[ 0 for y in range(MAP_HEIGHT) ]
           for x in range(MAP_WIDTH) ]
        
    blood_map = [[ 0 for y in range(MAP_HEIGHT) ]
           for x in range(MAP_WIDTH) ]    
    
    player_dijkstra.add_goal(player.x, player.y)
    player_dijkstra.recalculate_map()
    
    
    #main loop
    while not libtcod.console_is_window_closed():
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE_RELEASE, key, mouse)
                
        #render the screen
        render_all()
        
        #DijkHeat(player_dijkstra)
        DijkHeat(sound_dijkstra, False)
        libtcod.console_flush()
        
        #level up if needed
        check_level_up()
 
        #erase all objects at their old locations, before they move
        for object in objects:
            object.clear()

        #decay sound/scent maps
        decay_map(sound_dijkstra)
          
        #handle keys and exit game if needed
        player_action = handle_keys()
        if player_action == 'exit':
            save_game()
            Play_BGM(BGM_TITLEMUSIC)
            break
 
        #let monsters take their turn
        if game_state == 'playing' and player_action != 'didnt-take-turn':
        
            #do one-a-turn things
            Burn_Torch()
            
        
            for object in objects:
                if object.ai:
                    object.fighter.counter += object.fighter.speed
                    while object.fighter.counter >= player.fighter.speed:
                        object.ai.take_turn()
                        object.fighter.counter -= player.fighter.speed
                        
        #decay sound/scent maps
        #decay_map(sound_dijkstra)
 
def main_menu():
    img = libtcod.image_load('menu.png')
    Play_BGM(BGM_TITLEMUSIC)
    while not libtcod.console_is_window_closed():
        #show the background image, at twice the regular console resolution
        libtcod.image_blit_2x(img, 0, 0, 0)
 
        #show the game's title, and some credits!
        libtcod.console_set_default_foreground(0, libtcod.yellow)
        libtcod.console_print_ex(0, SCREEN_WIDTH/2, SCREEN_HEIGHT/2-5, libtcod.BKGND_NONE, libtcod.CENTER,
                                 "A'REL")
        libtcod.console_set_default_foreground(0, libtcod.light_yellow)
        libtcod.console_print_ex(0, SCREEN_WIDTH/2, SCREEN_HEIGHT/2-4, libtcod.BKGND_NONE, libtcod.CENTER,
                                 'TOMBS OF THE ANCIENT KINGS')
        libtcod.console_print_ex(0, SCREEN_WIDTH/2, SCREEN_HEIGHT-2, libtcod.BKGND_NONE, libtcod.CENTER, 'By M. R.')
 
        #show options and wait for the player's choice
        choice = menu('', ['Play a new game', 'Continue last game', 'Quit'], 24)
 
        if choice == 0:  #new game
            new_game()
            play_game()
        if choice == 1:  #load last game
            try:
                load_game()
            except:
                msgbox('\n No saved game to load.\n', 24)
                continue
            play_game()
        elif choice == 2:  #quit
            break
 
#set and init root console
libtcod.console_set_custom_font('terminal12x12_gs_ro.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_ASCII_INROW)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, "A'Rel; Tombs of the Ancient Kings", False)

#build additional consoles
con = libtcod.console_new(MAP_WIDTH, MAP_HEIGHT)
panel = libtcod.console_new(SCREEN_WIDTH, PANEL_HEIGHT)

#init pygame / mixer for audio
pygame.init()
pygame.mixer.init()

#set up pygame mixer channels
CHANNEL_BGM = pygame.mixer.Channel(1)
CHANNEL_BGSFX = pygame.mixer.Channel(2)
CHANNEL_ITEMSFX = pygame.mixer.Channel(3)
CHANNEL_PLAYERCOMBAT = pygame.mixer.Channel(4)
CHANNEL_NPCCOMBAT = pygame.mixer.Channel(5)

main_menu()