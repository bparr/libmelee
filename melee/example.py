#!/usr/bin/python3
import melee
import argparse
import signal
import sys

def check_port(value):
    ivalue = int(value)
    if ivalue < 1 or ivalue > 4:
         raise argparse.ArgumentTypeError("%s is an invalid controller port. \
         Must be 1, 2, 3, or 4." % value)
    return ivalue


# TODO ensure maintain four space tabs.
def newGameFrameAdvancer(port, opponent_port, iso_path):
    port = check_port(port)
    opponent_port = check_port(opponent_port)
    # TODO finish implementing.


chain = None

parser = argparse.ArgumentParser(description='Example of libmelee in action')
parser.add_argument('--port', '-p', type=check_port,
                    help='The controller port your AI will play on',
                    default=2)
parser.add_argument('--opponent', '-o', type=check_port,
                    help='The controller port the opponent will play on',
                    default=1)
parser.add_argument('--iso_path', required=True,
                    help='Path to SSBM v1.02 ISO.')

args = parser.parse_args()

#Create our Dolphin object. This will be the primary object that we will interface with
dolphin = melee.dolphin.Dolphin(ai_port=args.port,
                                opponent_port=args.opponent,
                                opponent_type=melee.enums.ControllerType.STANDARD)
#Create our GameState object for the dolphin instance
gamestate = melee.gamestate.GameState(dolphin)
#Create our Controller object that we can press buttons on
controller = melee.controller.Controller(port=args.port, dolphin=dolphin)
opponent_controller = melee.controller.Controller(port=args.opponent, dolphin=dolphin)

def signal_handler(signal, frame):
    dolphin.terminate()
    print("Shutting down cleanly...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

#Run dolphin and render the output
dolphin.run(render=True, iso_path=args.iso_path)

#Plug our controller in
#   Due to how named pipes work, this has to come AFTER running dolphin
#   NOTE: If you're loading a movie file, don't connect the controller,
#   dolphin will hang waiting for input and never receive it
controller.connect()
opponent_controller.connect()
first_match = True

#Main loop
while True:
    #"step" to the next frame
    gamestate.step()
    if(gamestate.processingtime * 1000 > 12):
        print("WARNING: Last frame took " + str(gamestate.processingtime*1000) + "ms to process.")

    #What menu are we in?
    if gamestate.menu_state in [melee.enums.Menu.IN_GAME, melee.enums.Menu.SUDDEN_DEATH]:
        #XXX: This is where your AI does all of its stuff!
        #This line will get hit once per frame, so here is where you read
        #   in the gamestate and decide what buttons to push on the controller
        melee.techskill.multishine(ai_state=gamestate.ai_state, controller=controller)
    #If we're at the character select screen, choose our character
    elif gamestate.menu_state == melee.enums.Menu.CHARACTER_SELECT:
        melee.menuhelper.choosecharacter(character=melee.enums.Character.FOX,
                                        gamestate=gamestate,
                                        port=args.port,
                                        opponent_port=args.opponent,
                                        controller=controller,
                                        swag=False,
                                        start=True)
        if first_match:
          # Only set up opponent on first match. Otherwise, will switch back
          # to non-cpu player, for example.
          melee.menuhelper.choosecharacter(character=melee.enums.Character.MARTH,
                                          gamestate=gamestate,
                                          port=args.opponent,
                                          opponent_port=args.port,
                                          controller=opponent_controller,
                                          make_cpu=True,
                                          swag=False,
                                          start=True)
    #If we're at the postgame scores screen, spam START
    elif gamestate.menu_state == melee.enums.Menu.POSTGAME_SCORES:
        first_match = False
        melee.menuhelper.skippostgame(controller=controller)
    #If we're at the stage select screen, choose a stage
    elif gamestate.menu_state == melee.enums.Menu.STAGE_SELECT:
        melee.menuhelper.choosestage(stage=melee.enums.Stage.FINAL_DESTINATION,
                                    gamestate=gamestate,
                                    controller=controller)
    #Flush any button presses queued up
    controller.flush()
    opponent_controller.flush()

