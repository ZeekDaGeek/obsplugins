"""
Window Tracking

## What?
This plugin is designed to allow you to set specific Window Captures to move
at the same rate and position as their real window counter parts with a few
modifiers if required.


## Why?
This OBS plugin was created for instances when streaming a game with coding
mechanics needed an external text editor to be most convenient (eg.
SpaceEngineer, OpenComputers, ComputerCraft...) It allows you to cut down
on the amount of time you're switching scenes and just drag your window into
a convenient spot for whatever UI elements are on screen at the moment.

A full screen capture is a valid solution but performs worse, and shows
everything as apposed to just your Game Capture and Window Capture as you
may desire.

## How?
At the moment use is not as streamlined as it could be, in order for this
script to track a window capture you must put T[] in your source's name.

You can add modifiers to allow for differing functionality of the tracking,
described below.

Examples:
    T[] NotePad++
    T[offsetx,snapy] Eclipse
    T[loop] Idle Game

## Modifiers
    Offset:
        Applies the offsets that are specified in the configuration section
        + Can be limited to one axis.
        + Can be applied negitively.
        Eg. Offset, OffsetX, OffsetY, Offset+, OffsetY- ...
    Snap:
        Will attempt to snap to the edges of the canvas.
        + Can be limited to one axis.
        Eg. Snap, SnapX, SnapY
    Loop:
        When the window is dragged beyond the canvas bounds it will appear
        on the opposite side. (A little bit buggy)
        + Can be limited to one axis.
        Eg. Loop, LoopX, LoopY
    Border: (Not yet implimented)
        Will create an extra source behind the tracked source to act as a
        border, if you wanted to for example make it seem like all of
        your window captures were on Windows 98.
        Eg. Border


"""

import obspython as obs
import win32gui as win
import math
import random
import re

setting_offsetX = 0
setting_offsetY = 0
setting_offsetXMod = 0
setting_offsetYMod = 0

tick_time = 0
cached_items = None
scene_win_map = {}

dimensions = {}

# Structure for tagging:
#  T[] = Trigger tracking.
#   Loop = Looped, calculate offset automatically when dragged off screen
#   Offset+ = Offset negitive modifier
#   Offset- = Offset positive modifier
#   Snap = Make sure it can't be dragged off screen.
#   Border = Add a fake border. @TODO
# 
# Example:
#  T[Snap,Border]
tagRegex = r"T\[(.+)?\]"

def script_description():

    return "A script to track and move sources along with their window counterparts."


def script_properties():

    props = obs.obs_properties_create()

    obs.obs_properties_add_int(props, "offsetX", "Offset X", -100000, 100000, 1)
    obs.obs_properties_add_int(props, "offsetY", "Offset Y", -100000, 100000, 1)

    obs.obs_properties_add_int(props, "offsetXMod", "Offset X (Only applied with modifier)", -100000, 100000, 1)
    obs.obs_properties_add_int(props, "offsetYMod", "Offset Y (Only applied with modifier)", -100000, 100000, 1)

    obs.obs_properties_add_button(props, "button", "Test", button_test)

    return props


def script_defaults(settings):
    
    obs.obs_data_set_default_int(settings, "offsetX", 8)
    obs.obs_data_set_default_int(settings, "offsetY", 50)
    obs.obs_data_set_default_int(settings, "offsetXMod", 1920)
    obs.obs_data_set_default_int(settings, "offsetYMod", 0)


def script_update(settings):

    global setting_offsetX
    global setting_offsetY
    global setting_offsetXMod
    global setting_offsetYMod

    setting_offsetX = obs.obs_data_get_int(settings, "offsetX")
    setting_offsetY = obs.obs_data_get_int(settings, "offsetY")
    setting_offsetXMod = obs.obs_data_get_int(settings, "offsetXMod")
    setting_offsetYMod = obs.obs_data_get_int(settings, "offsetYMod")


def script_unload():

    global cached_items
    global dimensions

    if cached_items is not None:

        for key, item in cached_items.items():

            #obs.obs_source_release(item["source"])
            obs.obs_sceneitem_release(item["item"])

    cached_items = {}

    obs.obs_data_release(dimensions)


def script_tick(tick):

    global tick_time

    tick_time += tick

    if (tick_time > 1):
        tick_time = 0

        cache_scenes()

    process_items()


# -------------------------------------------------------------------------- #

def button_test(props, prop):

    dimensions = obs.obs_video_info()
    obs.obs_get_video_info(dimensions)

    print(dimensions.base_width, dimensions.base_height)

def clear_cache():

    global cached_items

    if cached_items is not None:

        for key, item in cached_items.items():

            #obs.obs_source_release(item["source"])
            obs.obs_sceneitem_release(item["item"])

    cached_items = {}


def cache_scenes():

    global scene_win_map
    global cached_items
    global tagRegex
    global dimensions

    clear_cache()

    cached_num = 0

    currentScene = obs.obs_frontend_get_current_scene()
    sceneName = obs.obs_source_get_name(currentScene)
    sceneObject = obs.obs_scene_from_source(currentScene)
    items = obs.obs_scene_enum_items(sceneObject)

    if items is not None:

        for item in items:

            source = obs.obs_sceneitem_get_source(item)

            source_id = obs.obs_source_get_id(source)
            source_name = obs.obs_source_get_name(source)

            #find = re.match(tagRegex, source_name)
            #print(tagRegex, source_name)

            
            if (re.match(tagRegex, source_name) and source_id == "window_capture"):

                modifiers = {}

                flagsSearch = re.findall(tagRegex, source_name)
                flags = flagsSearch[0].split(",")

                for flag in flags:
                    modifiers[flag.lower()] = True

                data = obs.obs_source_get_settings(source)

                windowData = obs.obs_data_get_string(data, "window")
                windowSplit = windowData.split(":")

                windowTitle = windowSplit[0].replace("#3A", ":")
                #print("Window Title: " + windowData[0])
                #print("Window EXE: " + windowData[1])
                
                obs.obs_data_release(data)
                
                try:
                    if (windowData in scene_win_map):
                        myWin = scene_win_map[windowData]
                    else:
                        myWin = win.FindWindow(None, windowTitle)
                        scene_win_map[windowData] = myWin
                except:
                    pass

                cached_items[cached_num] = {
                        "item": item,
                        "source": source,
                        "modifiers": modifiers,
                        "win32gui": myWin
                    }
                cached_num += 1

            else:

                #obs.obs_source_release(source)
                obs.obs_sceneitem_release(item)
                pass

            #obs.obs_source_release(source)
            #obs.obs_sceneitem_release(item)

    obs.obs_scene_release(sceneObject)
    #obs.obs_source_release(currentScene)
    
    #print("Cached %d items." % (cached_num))
    
    dimensions = obs.obs_video_info()
    obs.obs_get_video_info(dimensions)

def process_items():

    global setting_offsetX
    global setting_offsetY
    global setting_offsetXMod
    global setting_offsetYMod

    global cached_items
    global dimensions

    if (cached_items == None):
        return

    for key, objects in cached_items.items():

        item = objects["item"]
        source = objects["source"]
        modifiers = objects["modifiers"]
        myWin = objects["win32gui"]

        #sourceData = source.get_properties()

        #print("My id: %s" % sourceData.id)

        try:

            rect = win.GetWindowRect(myWin)

            x = rect[0] + setting_offsetX
            y = rect[1] + setting_offsetY
            w = rect[2] - x
            h = rect[3] - y

            if ("offset+" in modifiers or "offset" in modifiers):
                x += setting_offsetXMod
                y += setting_offsetYMod
            if ("offset-" in modifiers):
                x -= setting_offsetXMod
                y -= setting_offsetYMod

            if ("offsetx+" in modifiers or "offsetx" in modifiers):
                x += setting_offsetXMod
            if ("offsetx-" in modifiers):
                x -= setting_offsetXMod
            if ("offsety+" in modifiers or "offsety" in modifiers):
                y += setting_offsetYMod
            if ("offsety-" in modifiers):
                y -= setting_offsetYMod

            if ("snap" in modifiers):
                if (x < 0):
                    x = 0
                elif (x + w > dimensions.base_width):
                    x = dimensions.base_width - w
                if (y < 0):
                    y = 0
                elif (y + h > dimensions.base_height):
                    y = dimensions.base_height - h

            if ("snapx" in modifiers):
                if (x < 0):
                    x = 0
                elif (x + w > dimensions.base_width):
                    x = dimensions.base_width - w

            if ("snapy" in modifiers):
                if (y < 0):
                    y = 0
                elif (y + h > dimensions.base_height):
                    y = dimensions.base_height - h

            if ("loop" in modifiers):
                if (x < (0 - w / 2)):
                    x += dimensions.base_width
                elif (x > (dimensions.base_width - w / 2)):
                    x -= dimensions.base_width
                if (y < (0 - h / 2)):
                    y += dimensions.base_height
                elif (y > (dimensions.base_height - h / 2)):
                    y -= dimensions.base_height

            if ("loopx" in modifiers):
                if (x < (0 - w / 2)):
                    x += dimensions.base_width
                elif (x > (dimensions.base_width - w / 2)):
                    x -= dimensions.base_width

            if ("loopy" in modifiers):
                if (y < (0 - h / 2)):
                    y += dimensions.base_height
                elif (y > (dimensions.base_height - h / 2)):
                    y -= dimensions.base_height




            #print("\tLocation: (%d, %d)" % (x, y))
            #print("\t    Size: (%d, %d)" % (w, h))

            # Move scene?
            pos_win = obs.vec2()
            obs.vec2_set(pos_win, x, y)
            obs.obs_sceneitem_set_pos(item, pos_win)


        except:
            print("Failed to track window: %s" % windowTitle)
            pass
