"""Helper functions for navigating the Melee menus in ways that would be
    cumbersome to do on your own."""
from melee import enums
import math

"""Choose a character from the character select menu
    Intended to be called each frame while in the character select menu
    character = The character you want to pick
    gamestate = The current gamestate
    controller = The controller object to press
    swag = Pick random until you get the character
    start = Automatically start the match when it's ready
        NOTE: All controller cursors must be above the character level for this
        to work. The match won't start otherwise."""
def choosecharacter(character, gamestate, port, opponent_port, controller, swag=False, start=False,
                    make_cpu=False, is_20xx=False):

    #Figure out where the character is on the select screen
    #NOTE: This assumes you have all characters unlocked
    #Positions will be totally wrong if something is not unlocked
    ai_state = gamestate.player[port]
    opponent_state = gamestate.player[opponent_port]

    #if is_20xx:
    #  raise Exception('20XX character selection is not implemented yet.')

    if not is_20xx and gamestate.frame < 18:
      # 20xx cursors start higher.
      controller.tilt_analog(enums.Button.BUTTON_MAIN, 0.5, 1.0)
      return
    if gamestate.frame == 18:
      controller.empty_input()

    if make_cpu and gamestate.frame < 44:
      if gamestate.frame == 18 or gamestate.frame == 20:
        controller.press_button(enums.Button.BUTTON_A)
      elif gamestate.frame == 19 or gamestate.frame == 21:
        controller.empty_input()
      elif gamestate.frame == 22:
        controller.tilt_analog(enums.Button.BUTTON_MAIN, 0.5, 0.0)
      elif make_cpu and gamestate.frame == 33:
        controller.press_button(enums.Button.BUTTON_A)
        controller.tilt_analog(enums.Button.BUTTON_MAIN, 1.0, 0.5)
      elif make_cpu and gamestate.frame == 34:
        controller.release_button(enums.Button.BUTTON_A)
      elif make_cpu and gamestate.frame == 42:
        controller.empty_input()
        controller.press_button(enums.Button.BUTTON_A)
      elif make_cpu and gamestate.frame == 43:
        controller.release_button(enums.Button.BUTTON_A)
      return



    row = character.value // 9
    column = character.value % 9
    #The random slot pushes the bottom row over a slot, so compensate for that
    if row == 2:
        column = column+1
    #re-order rows so the math is simpler
    row = 2-row


    if is_20xx:
      if gamestate.frame < 63:
        if not make_cpu:
          controller.tilt_analog(enums.Button.BUTTON_MAIN, 0.5, 0.5)
          return

        # Move back to position before started setting to CPU.
        if gamestate.frame < 54:
          controller.tilt_analog(enums.Button.BUTTON_MAIN, 0.5, 1.0)
        else:
          controller.tilt_analog(enums.Button.BUTTON_MAIN, 0.0, 0.5)
        return

      # Two frames for P1 to move all the way left.
      # Fourteen frames to move left by one player. So P2=16, P3=30, P4=44
      # frames total to move all the way left.
      if gamestate.frame < 63 + 44:
        controller.tilt_analog(enums.Button.BUTTON_MAIN, 0.0, 0.5)
        return


      controller.tilt_analog(enums.Button.BUTTON_MAIN, 0.5, 0.5)
      return

    #Height starts at 1, plus half a box height, plus the number of rows
    target_y = 1 + 3.5 + (row * 7.0)
    #Starts at -32.5, plus half a box width, plus the number of columns
    #NOTE: Technically, each column isn't exactly the same width, but it's close enough
    target_x = -32.5 + 3.5 + (column * 7.0)
    #Wiggle room in positioning character
    wiggleroom = 1.5

    #We want to get to a state where the cursor is NOT over the character,
    # but it's selected. Thus ensuring the token is on the character
    isOverCharacter = abs(ai_state.cursor_x - target_x) < wiggleroom and \
        abs(ai_state.cursor_y - target_y) < wiggleroom

    #Don't hold down on B, since we'll quit the menu if we do
    if controller.prev.button[enums.Button.BUTTON_B] == True:
        controller.release_button(enums.Button.BUTTON_B)
        return

    #If character is selected, and we're in of the area, and coin is down, then we're good
    if (ai_state.character == character) and ai_state.coin_down:
        if start and gamestate.ready_to_start and \
            controller.prev.button[enums.Button.BUTTON_START] == False:
            controller.press_button(enums.Button.BUTTON_START)
            return
        else:
            controller.empty_input()
            return

    #release start in addition to anything else
    controller.release_button(enums.Button.BUTTON_START)

    #If we're in the right area, select the character
    if isOverCharacter:
        #If we're over the character, but it isn't selected,
        #   then the coin must be somewhere else.
        #   Press B to reclaim the coin
        controller.tilt_analog(enums.Button.BUTTON_MAIN, .5, .5)
        if (ai_state.character != character) and (ai_state.coin_down):
            controller.press_button(enums.Button.BUTTON_B)
            return
        #Press A to select our character
        else:
            if controller.prev.button[enums.Button.BUTTON_A] == False:
                controller.press_button(enums.Button.BUTTON_A)
                return
            else:
                controller.release_button(enums.Button.BUTTON_A)
                return
    else:
        #Move in
        controller.release_button(enums.Button.BUTTON_A)
        #Move up if we're too low
        if ai_state.cursor_y < target_y - wiggleroom:
            controller.tilt_analog(enums.Button.BUTTON_MAIN, .5, 1)
            return
        #Move down if we're too high
        if ai_state.cursor_y > target_y + wiggleroom:
            controller.tilt_analog(enums.Button.BUTTON_MAIN, .5, 0)
            return
        #Move right if we're too left
        if ai_state.cursor_x < target_x - wiggleroom:
            controller.tilt_analog(enums.Button.BUTTON_MAIN, 1, .5)
            return
        #Move left if we're too right
        if ai_state.cursor_x > target_x + wiggleroom:
            controller.tilt_analog(enums.Button.BUTTON_MAIN, 0, .5)
            return
    controller.empty_input()

"""Choose a stage from the stage select menu
    Intended to be called each frame while in the stage select menu
    stage = The stage you want to select
    gamestate = The current gamestate
    controller = The controller object to press"""
def choosestage(stage, gamestate, controller):
    if gamestate.frame < 20:
        controller.empty_input()
        return
    target_x, target_y = 0,0
    if stage == enums.Stage.BATTLEFIELD:
        target_x, target_y = 1,-9
    if stage == enums.Stage.FINAL_DESTINATION:
        target_x, target_y = 6.7,-9
    if stage == enums.Stage.DREAMLAND:
        target_x, target_y = 12.5,-9
    if stage == enums.Stage.POKEMON_STADIUM:
        target_x, target_y = 15, 3.5
    if stage == enums.Stage.YOSHIS_STORY:
        target_x, target_y = 3.5, 15.5
    if stage == enums.Stage.FOUNTAIN_OF_DREAMS:
        target_x, target_y = 10, 15.5
    if stage == enums.Stage.RANDOM_STAGE:
        target_x, target_y = -13.5, 3.5

    #Wiggle room in positioning cursor
    wiggleroom = 1.5
    #Move up if we're too low
    if gamestate.stage_select_cursor_y < target_y - wiggleroom:
        controller.release_button(enums.Button.BUTTON_A)
        controller.tilt_analog(enums.Button.BUTTON_MAIN, .5, 1)
        return
    #Move downn if we're too high
    if gamestate.stage_select_cursor_y > target_y + wiggleroom:
        controller.release_button(enums.Button.BUTTON_A)
        controller.tilt_analog(enums.Button.BUTTON_MAIN, .5, 0)
        return
    #Move right if we're too left
    if gamestate.stage_select_cursor_x < target_x - wiggleroom:
        controller.release_button(enums.Button.BUTTON_A)
        controller.tilt_analog(enums.Button.BUTTON_MAIN, 1, .5)
        return
    #Move left if we're too right
    if gamestate.stage_select_cursor_x > target_x + wiggleroom:
        controller.release_button(enums.Button.BUTTON_A)
        controller.tilt_analog(enums.Button.BUTTON_MAIN, 0, .5)
        return

    #If we get in the right area, press A
    controller.press_button(enums.Button.BUTTON_A)

"""Spam the start button"""
def skippostgame(controller):
    # Alternate pressing start and letting go.
    # Ensure all inputs are cleared before leaving this post game menu state
    # by always clearing inputs.
    press_start = (controller.prev.button[enums.Button.BUTTON_START] == False)
    controller.empty_input()
    if press_start:
        controller.press_button(enums.Button.BUTTON_START)


def resetmatch(controller):
    #Alternate pressing Start+A+L+R and letting go.
    if controller.prev.button[enums.Button.BUTTON_START] == False:
        controller.press_button(enums.Button.BUTTON_START)
        controller.press_button(enums.Button.BUTTON_A)
        # TODO switch to controller.press_shoulder?
        controller.press_button(enums.Button.BUTTON_L)
        controller.press_button(enums.Button.BUTTON_R)
    else:
        controller.empty_input()



"""Switch a given player's controller to be of the given state
WARNING: There's a condition on this you need to know. The way controllers work
    in Melee, if a controller is plugged in, only that player can make the status
    go to uplugged. If you've ever played Melee, you probably know this. If your
    friend walks away, you have to press the A button on THEIR controller. (or
    else actually unplug the controller) No way around it."""
def changecontrollerstatus(controller, gamestate, targetport, port, status, character=None):
    ai_state = gamestate.player[port]
    target_x, target_y = 0,-2.2
    if targetport == 1:
        target_x = -31.5
    if targetport == 2:
        target_x = -16.5
    if targetport == 3:
        target_x = -1
    if targetport == 4:
        target_x = 14
    wiggleroom = 1.5

    correctcharacter = (character == None) or \
        (character == gamestate.player[targetport].character)

    #if we're in the right state already, do nothing
    if gamestate.player[targetport].controller_status == status and correctcharacter:
        controller.empty_input()
        return

    #Move up if we're too low
    if ai_state.cursor_y < target_y - wiggleroom:
        controller.tilt_analog(enums.Button.BUTTON_MAIN, .5, 1)
        return
    #Move downn if we're too high
    if ai_state.cursor_y > target_y + wiggleroom:
        controller.tilt_analog(enums.Button.BUTTON_MAIN, .5, 0)
        return
    #Move right if we're too left
    if ai_state.cursor_x < target_x - wiggleroom:
        controller.tilt_analog(enums.Button.BUTTON_MAIN, 1, .5)
        return
    #Move left if we're too right
    if ai_state.cursor_x > target_x + wiggleroom:
        controller.tilt_analog(enums.Button.BUTTON_MAIN, 0, .5)
        return

    #If we get in the right area, press A until we're in the right state
    controller.tilt_analog(enums.Button.BUTTON_MAIN, .5, .5)
    if controller.prev.button[enums.Button.BUTTON_A] == False:
        controller.press_button(enums.Button.BUTTON_A)
    else:
        controller.release_button(enums.Button.BUTTON_A)
