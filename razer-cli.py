#!/usr/bin/env python3
"""
Module Docstring
"""

__author__ = "Lorenz Leitner"
__version__ = "0.1.0"
__license__ = "GPL-3.0"

# Libraries
import subprocess, sys
from openrazer.client import DeviceManager
from openrazer.client import constants as razer_constants
import argparse

# Own
import util
import settings

def parse_color_argument(color):
    r = 0
    g = 0
    b = 0

    if len(color) == 1:
        # Hex: Just one input argument
        rgb = color[0]
        r, g, b = util.hex_to_decimal(rgb)
    elif len(color) == 3:
        # RGB: Three base10 input arguments
        r = int(color[0])
        g = int(color[1])
        b = int(color[2])

    return r, g, b

def get_x_color():
    # Get current primary color used by pywal, which is color1 in Xresources
    # Colors could also be read from ~/.cache/wal/colors.json, but this way it
    # doesn't depend on pywal, in case the X colors are set from a different origin
    output = subprocess.check_output(
            "xrdb -query | grep \"*color1:\" | awk -F '#' '{print $2}'", 
            shell=True)
    rgb = output.decode()
    r, g, b = util.hex_to_decimal(rgb)

    return r, g, b

def set_color(color):
    """ Set the color either from the input argument or use a fallback color """

    r = 0
    g = 0
    b = 0

    if(color):
        # Set colors from input argument
        r, g, b = parse_color_argument(color)

    else:
        # Use X colors as fallback if no color argument is set
        # TODO: Maybe also add argument to pull colors from
        # ~/.cache/wal.colors.jason
        r, g, b = get_x_color()

    if args.verbose:
        print("RBG: ")
        sys.stdout.write(str(r) + " ")
        sys.stdout.write(str(g) + " ")
        sys.stdout.write(str(b) + "\n")

    rgb = []
    rgb.append(r)
    rgb.append(g)
    rgb.append(b)

    return rgb

def get_effects_of_device(device):
    return [effect for effect in settings.EFFECTS if device.fx.has(effect)]

def list_devices(device_manager):
    """
    List all connected Razer devices
    https://github.com/openrazer/openrazer/blob/master/examples/list_devices.py
    """

    print("Found {} Razer devices".format(len(device_manager.devices)))

    # Iterate over each device and pretty out some standard information about each
    for device in device_manager.devices:
        print("{}:".format(device.name))
        print("   type: {}".format(device.type))
        if (device.type == "mouse"):
            print("   DPI: {}".format(device.dpi))
            print("   max DPI: {}".format(device.max_dpi))
        print("   serial: {}".format(device.serial))
        print("   firmware version: {}".format(device.firmware_version))
        print("   driver version: {}".format(device.driver_version))

        device_effects = get_effects_of_device(device)
        print("   effects: {}".format(device_effects))

        if (args.list_devices_long):
            print("   capabilities: {}".format(device.capabilities))
    print()

def set_dpi(device_manager):
    # Iterate over each device and set DPI
    for device in device_manager.devices:
        # If -d argument is set, only set those devices
        if (args.device and device.name in args.device) or (not args.device):
            if (device.type != "mouse"):
                if args.verbose:
                    print("Device {} is not a mouse".format(device.name))
            else:
                if args.verbose:
                    print("Setting DPI of device {} to {}".format(device.name,
                        args.dpi))
                dpi_to_use = int(args.dpi)
                device.dpi = (dpi_to_use, dpi_to_use)

def set_effect_to_device(device, effect, color):
    # Save used settings for this device to a file
    util.write_settings_to_file(device, effect, color)

    r = color[0]
    g = color[1]
    b = color[2]

    if (effect == "static"):
        # Set the effect to static, requires colors in 0-255 range
        try:
            # Avoid checking for device type
            # Keyboard - doesn't throw
            device.fx.static(r, g, b)
            # Mouse - throws
            device.fx.misc.logo.static(r, g, b)
            device.fx.misc.scroll_wheel.static(r, g, b)
            device.fx.misc.left.static(r, g, b)
            device.fx.misc.right.static(r, g, b)
        except:
            pass

    elif (effect == "breath_single"):
        device.fx.breath_single(r, g, b)

    elif (effect == "reactive"):
        times = [razer_constants.REACTIVE_500MS, razer_constants.REACTIVE_1000MS,
        razer_constants.REACTIVE_1500MS, razer_constants.REACTIVE_2000MS]
        device.fx.reactive(r, g, b, times[3])

    elif (effect == "ripple"):
        device.fx.ripple(r, g, b, razer_constants.RIPPLE_REFRESH_RATE)

    else:
        print("Effect is supported by device but not yet implemented.\n"
                "Consider opening a PR:\n"
                "https://github.com/LoLei/razer-x-color/pulls")
        return

    print("Setting device: {} to effect {}".format(device.name,
        effect))


def set_effect_to_all_devices(device_manager, input_effect, color):
    """ Set one effect to all connected devices, if they support that effect """

    # Iterate over each device and set the effect
    for device in device_manager.devices:
        # If -d argument is set, only set those devices
        if (args.device and device.name in args.device) or (not args.device):
            if not input_effect:
                effect_to_use = "static"
            else:
                effect_to_use = input_effect

            if not device.fx.has(effect_to_use):
                effect_to_use = "static"
                if args.verbose:
                    print("Device does not support chosen effect (yet). Using "
                            " static as fallback...")

            set_effect_to_device(device, effect_to_use, color)

def main():
    """ Main entry point of the app """

    # -------------------------------------------------------------------------
    # COLORS
    color = set_color(args.color)

    # -------------------------------------------------------------------------
    # DEVICES
    # Create a DeviceManager. This is used to get specific devices
    device_manager = DeviceManager()

    if (args.list_devices or args.list_devices_long):
        list_devices(device_manager)

    # Disable daemon effect syncing.
    # Without this, the daemon will try to set the lighting effect to every device.
    # TODO: Could be enabled as flag
    device_manager.sync_effects = False

    # Do below only if dry run is not specified
    if args.automatic or args.effect or args.color:
        set_effect_to_all_devices(device_manager, args.effect, color)
    
    if args.dpi:
        set_dpi(device_manager)

if __name__ == "__main__":
    """ This is executed when run from the command line """

    # -------------------------------------------------------------------------
    # ARGS
    parser = argparse.ArgumentParser()

    parser.add_argument("-e", "--effect",
                        help="set effect",
                        action="store")

    parser.add_argument("-v", "--verbose",
                        help="increase output verbosity",
                        action="store_true")

    parser.add_argument("-c","--color", nargs="+",
                        help="choose color (default: X color1), use one argument "
                             "for hex, or three for base10 rgb")

    parser.add_argument("-l", "--list_devices",
                        help="list available devices and their supported effects",
                        action="store_true")

    parser.add_argument("-ll", "--list_devices_long",
                        help="list available devices and all their capabilities",
                        action="store_true")

    parser.add_argument("-a", "--automatic",
                        help="try to find colors and set them to all devices "
                             "without user arguments, uses X or pywal colors",
                        action="store_true")

    parser.add_argument("-d", "--device", nargs="+",
                        help="only affect these devices, same name as output "
                             "of -l")

    parser.add_argument("--dpi",
                        help="set DPI of device",
                        action="store")

    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()
        sys.exit(1)

    if args.verbose:
        print("Starting Razer colors script...")

    main()
