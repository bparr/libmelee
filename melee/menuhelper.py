"""Helper functions for navigating the Melee menus in ways that would be
    cumbersome to do on your own."""
from melee import enums
import math


"""Choose a character from the character select menu
    Intended to be called each frame while in the character select menu
    character = The character you want to pick
    gamestate = The current gamestate
    controller = The controller object to press
    start = Automatically start the match when it's ready
        NOTE: All controller cursors must be above the character level for this
        to work. The match won't start otherwise."""
def choosecharacter(character, gamestate, port, opponent_port, controller,
                    start=False, make_cpu=False, is_20xx=False):
    #Figure out where the character is on the select screen
    #NOTE: This assumes you have all characters unlocked
    #Positions will be totally wrong if something is not unlocked
    row = character.value // 9
    column = character.value % 9
    #The random slot pushes the bottom row over a slot, so compensate for that
    if row == 2:
        column = column+1
    #re-order rows so the math is simpler
    row = 2-row

    ai_state = gamestate.player[port]
    opponent_state = gamestate.player[opponent_port]

    if gamestate.frame < 18:
      if not is_20xx:
        # 20xx cursors start higher.
        controller.tilt_analog(enums.Button.BUTTON_MAIN, 0.5, 1.0)
      return

    if gamestate.frame < 63:
      if not make_cpu:
        # Wait during "make cpu" phase of character selection.
        controller.empty_input()
        return

      if gamestate.frame == 18 or gamestate.frame == 20:
        controller.press_button(enums.Button.BUTTON_A)
      elif gamestate.frame == 19 or gamestate.frame == 21:
        controller.empty_input()
      elif gamestate.frame < 33:
        controller.tilt_analog(enums.Button.BUTTON_MAIN, 0.5, 0.0)
      elif gamestate.frame == 33:
        controller.press_button(enums.Button.BUTTON_A)
        controller.tilt_analog(enums.Button.BUTTON_MAIN, 1.0, 0.5)
      elif gamestate.frame < 42:
        controller.release_button(enums.Button.BUTTON_A)
      elif gamestate.frame == 42:
        controller.empty_input()
        controller.press_button(enums.Button.BUTTON_A)
      elif gamestate.frame == 43:
        controller.release_button(enums.Button.BUTTON_A)
      # Move back to position before started setting to CPU.
      elif gamestate.frame < 54:
        controller.tilt_analog(enums.Button.BUTTON_MAIN, 0.5, 1.0)
      else:
        controller.tilt_analog(enums.Button.BUTTON_MAIN, 0.0, 0.5)
      return

    # Two frames for P1 to move all the way left.
    # Fourteen frames to move left by one player. So P2=16, P3=30, P4=44
    # frames total to move all the way left.
    if gamestate.frame < 107:  # 107 = 63 + 44.
      controller.tilt_analog(enums.Button.BUTTON_MAIN, 0.0, 0.5)
      return

    amount_up = 5 + 5 * row
    amount_right = 3 + 6 * column
    if gamestate.frame <  107 + amount_up:
      controller.tilt_analog(enums.Button.BUTTON_MAIN, 0.5, 1.0)
      return

    if gamestate.frame < 107 + amount_up + amount_right:
      controller.tilt_analog(enums.Button.BUTTON_MAIN, 1.0, 0.5)
      return

    if gamestate.frame == 107 + amount_up + amount_right:
      controller.tilt_analog(enums.Button.BUTTON_MAIN, 0.5, 0.5)
      controller.press_button(enums.Button.BUTTON_A)
      return

    controller.release_button(enums.Button.BUTTON_A)
    if start:
      if controller.prev.button[enums.Button.BUTTON_START]:
        controller.release_button(enums.Button.BUTTON_START)
      else:
        controller.press_button(enums.Button.BUTTON_START)



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
def spamstartbutton(controller):
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


