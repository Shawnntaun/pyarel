
           ,ggg,    d8' ,ggggggggggg,                   
          dP""8I   d8' dP"""88""""""Y8,           ,dPYb,
         dP   88  ""   Yb,  88      `8b           IP'`Yb
        dP    88        `"  88      ,8P           I8  8I
       ,8'    88            88aaaad8P"            I8  8'
       d88888888            88""""Yb,     ,ggg,   I8 dP 
 __   ,8"     88            88     "8b   i8" "8i  I8dP  
dP"  ,8P      Y8            88      `8i  I8, ,8I  I8P   
Yb,_,dP       `8b,          88       Yb, `YbadP' ,d8b,_ 
 "Y8P"         `Y8          88        Y8888P"Y8888P'"Y88
 
 A'Rel Readme
 
 v 0.0.0.3
 ObservantDoggo
 
 Based on libtcod
 
 
 *********
 * SETUP *
 *********
 
 You will need Python (v2.7.13) installed to run.   (https://www.python.org/downloads/)
 You will need PyGame installed for audio to work   (https://www.pygame.org/wiki/GettingStarted)
           No-Audio version will be added. 
           You could also comment-out or remove audio-related code if desired.
 
 **************
 *  CONTROLS  *
 **************
 
    8-Directional movement using numpad keys (Numpad 5 is wait/skip turn)
    4-Directional movement using arrow keys
    
    [c] Close Doors
        press [c] and then a directional key
    [f] Fire Ranged Weapon
        Must have the ranged weapon equipped, and have the appropriate ammo type in the inventory.
    [i] Inventory
        press [i] to open your inventory
            press [i] or [esc] to close the inventory
            press a letter key next to an item to use that item
    
    [k] Kick
        press [k] and then a directional key
        
    [s] Stats
        press [s] to open your stats menu
            press [s] or [esc] to close the stats menu
 
    ****************
    * Known Issues *
    ****************
    
    Occasional issues with item stacking order (try kicking things out of piles)
    
    **************
    * Change log *
    **************
    
    v 0.0.0.4
    dunno yet
    
        1) Overview
            A) Currently sticking with possibly overly-complicated formatting
            
        2) New Mechanics
            A) Ranged Weapons
                - Implemented ranged weapon and ammo system for the player
                    - Need to implement this for enemies
    
        3) Bug Fixes
            A) Context Tips
                - Corrected issue with kicking and door-closing context tips
            B) Interactions
                - Small fixes to kicking mechanics checks
                - Fixed and optimized gold throwing
    
    v 0.0.0.3 
    4/27/18
    
        1) Overview
            A) Decided it was a good idea to start a change long.
                - Started a change log    
                - Started possibly overly-complicated formatting for said change log.
            
        2) New Mechanics
            A) Light
                - FoV based on current oil levels, decays over turns
            B) Combat update ** NOT CURRENTLY BALANCED **
                - Less random, more deterministic 
        
        3) New Items
            A) 'Scroll of Magical Mapping'
                - def cast_magicmap
            B) 'Oil Flask'
                - def use_oil
                
        4) Misc
            A) New Player Tips
                - Interaction/context tips will show up on the first dungeon level
                
        5) Bug Fixes
            A) Doors
                - Updated placement conditions
                    - This seems to have corrected issue of actors being able to walk off the map
    
    