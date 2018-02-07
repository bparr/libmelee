#!/usr/bin/python3
import melee
import signal
import sys

def check_port(value):
    ivalue = int(value)
    if ivalue < 1 or ivalue > 4:
         raise Exception("%s is an invalid controller port. \
         Must be 1, 2, 3, or 4." % value)
    return ivalue


_frame_advancer = None

# Singleton factory. Multiple calls will just return result from first call.
def getFrameAdvancer(port, opponent_port, iso_path,
                     unlimited_emulation_speed=False):
    global _frame_advancer
    if _frame_advancer is not None:
        return _frame_advancer

    port = check_port(port)
    opponent_port = check_port(opponent_port)
    opponent_type = melee.enums.ControllerType.STANDARD
    dolphin = melee.dolphin.Dolphin(
        ai_port=port, opponent_port=opponent_port, opponent_type=opponent_type,
        unlimited_emulation_speed=unlimited_emulation_speed)
    gamestate = melee.gamestate.GameState(dolphin)
    controller = melee.controller.Controller(port=port, dolphin=dolphin)
    opponent_controller = melee.controller.Controller(port=opponent_port,
                                                      dolphin=dolphin)
    def signal_handler(signal, frame):
        dolphin.terminate()
        print("Shutting down cleanly...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    dolphin.run(render=True, iso_path=iso_path)
    #Plug our controller in
    #   Due to how named pipes work, this has to come AFTER running dolphin
    controller.connect()
    opponent_controller.connect()
    _frame_advancer =  _FrameAdvancer(gamestate, dolphin, controller,
                                      opponent_controller)
    return _frame_advancer


class _FrameAdvancer(object):
    def __init__(self, gamestate, dolphin, controller, opponent_controller):
        self._gamestate = gamestate
        self._dolphin = dolphin
        self._controller = controller
        self._opponent_controller = opponent_controller
        self._first_match = True

    def get_game_state(self):
        return self._gamestate

    def get_controller(self):
        return self._controller

    def terminate_dolphin(self):
        print('Terminating dolphin.')
        self._dolphin.terminate()

    # Note: May step multiple frames to get into a match.
    def step_match_frame(self):
        # Ensure any inputs by user are flushed.
        self._controller.flush()
        self._opponent_controller.flush()

        while not self._step_helper():
            pass

    # If in a match, then spams Start+A+L+R until out of match.
    # Returns when on first frame of next match.
    def reset_match(self):
        # TODO remove this debugging once understand why dolphin is hanging.
        count = 0
        while not self._step_helper(resetting_match=True):
            count += 1
            if count % 1000 == 0 and count < 9000:
              print('Unexpectedly long reset: ', self._gamestate.menu_state)
              sys.stdout.flush()
            if count > 9000:
              self._dolphin.terminate()
              raise Exception('Way too long reseting match')

        self._controller.flush()
        self._opponent_controller.flush()

        while not self._step_helper():
            count += 1
            if count % 1000 == 0 and count < 9000:
              print('Unexpectedly long reset: ', self._gamestate.menu_state)
              sys.stdout.flush()
            if count > 9000:
              self._dolphin.terminate()
              raise Exception('Way too long reseting match')

    def _step_helper(self, resetting_match=False):
        gamestate = self._gamestate
        dolphin = self._dolphin
        gamestate.step()
        if(gamestate.processingtime * 1000 > 12):
            print("WARNING: Last frame took " + str(gamestate.processingtime*1000) + "ms to process.")
            sys.stdout.flush()

        #What menu are we in?
        if gamestate.menu_state in [melee.enums.Menu.IN_GAME, melee.enums.Menu.SUDDEN_DEATH]:
            if resetting_match:
                melee.menuhelper.resetmatch(self._controller)
                self._controller.flush()
                return False
            return True

        #If we're at the character select screen, choose our character
        elif gamestate.menu_state == melee.enums.Menu.CHARACTER_SELECT:
            melee.menuhelper.choosecharacter(character=melee.enums.Character.FOX,
                                            gamestate=gamestate,
                                            port=dolphin.ai_port,
                                            opponent_port=dolphin.opponent_port,
                                            controller=self._controller,
                                            swag=False,
                                            start=True)
            if self._first_match:
              # Only set up opponent on first match. Otherwise, will switch back
              # to non-cpu player, for example.
              melee.menuhelper.choosecharacter(character=melee.enums.Character.MARTH,
                                              gamestate=gamestate,
                                              port=dolphin.opponent_port,
                                              opponent_port=dolphin.ai_port,
                                              controller=self._opponent_controller,
                                              make_cpu=True,
                                              swag=False,
                                              start=True)
        #If we're at the postgame scores screen, spam START
        elif gamestate.menu_state == melee.enums.Menu.POSTGAME_SCORES:
            self._first_match = False
            melee.menuhelper.skippostgame(controller=self._controller)
        #If we're at the stage select screen, choose a stage
        elif gamestate.menu_state == melee.enums.Menu.STAGE_SELECT:
            melee.menuhelper.choosestage(stage=melee.enums.Stage.FINAL_DESTINATION,
                                        gamestate=gamestate,
                                        controller=self._controller)

        self._controller.flush()
        self._opponent_controller.flush()
        return resetting_match

