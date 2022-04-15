# TODO shebang?

"""
A typing test written in Python.
"""

import sys
import time
import requests

# curses isn't available on Windows by default
# on error, prompt the user to install 'windows-curses'
try:
    import curses
    import curses.ascii
except ImportError:
    print("Could not find the 'curses' module. If you are using Windows, please install the 'windows-curses' package.")
    sys.exit(1)


# TODO this function needs work
def coords(stdscr: curses.window, y: int, x: int | None = None) -> int | tuple[int, int]:
    """A utility function that allows for converting between array and curses matrix coordinates."""

    height, width = stdscr.getmaxyx()

    if x is not None:
        if x < 0:
            return max(y - 1, 0) * width + (width if y - 1 > 0 else 0)

        return y * width + x + (1 if y > 0 else 0)
    else:
        return (y + 1) // width, y % width


def splitter(string: str, indices: list) -> list:
    """Splits a string at the provided indices into a list of substrings."""
    splits = [string[:indices[0]]]  # add first element

    for i in range(1, len(indices)):
        splits.append(string[indices[i - 1] + 1: indices[i]])

    splits.append(string[indices[-1] + 1:])  # add last element

    return splits


def is_enter(key: int) -> bool:
    return key == curses.ascii.LF or key == curses.ascii.CR or key == curses.KEY_ENTER


def is_backspace(key: int) -> bool:
    return key == curses.ascii.BS or key == curses.KEY_BACKSPACE


def main(stdscr: curses.window = None) -> int:
    if not stdscr:
        return curses.wrapper(main)

    # using raw mode for compatibility with 'windows-curses'
    # see https://github.com/zephyrproject-rtos/windows-curses/issues/8
    curses.raw()

    # forward declarations
    current_key = curses.ascii.LF  # start with enter
    quote = None
    output = None
    start_time = None

    # game loop
    while True:
        # redraw the screen
        stdscr.refresh()

        # handle ctrl + c
        if current_key == curses.ascii.ETX:
            return 0

        # on enter, get and display a new quote
        if is_enter(current_key):
            response = requests.get("https://api.quotable.io/random")

            # not 200 OK
            if response.status_code != 200:
                print("There was an error retrieving a quote. Be sure that you are connected to the Internet.")
                return 1

            json = response.json()

            quote = json["content"]
            output = f"{quote} ~ {json['author']}"

            stdscr.clear()
            stdscr.addstr(0, 0, output)
            stdscr.move(0, 0)

            current_key = None  # reset for next iteration
            continue

        current_key = stdscr.getch()  # get user input
        current_cursor_index = coords(stdscr, *stdscr.getyx())

        # end of quote
        if current_cursor_index >= len(quote) - 1 and not \
                (current_cursor_index == len(quote) - 1 and is_backspace(current_key)):

            # first time reaching end of quote
            # 'start_time' is set to None at the end of this if block
            if start_time:
                stdscr.addch(current_key)
                y, _ = coords(stdscr, len(output))  # end of output

                elapsed_time = time.time() - start_time
                minute_factor = 60 / elapsed_time  # 'elapsed_time' adjusted to 1 minute

                user_input = stdscr.instr(0, 0)[:len(quote)].decode()

                # position of all spaces within the quote to split on
                space_indices = [i for i, e in enumerate(quote) if curses.ascii.isspace(e)]

                words = splitter(user_input, space_indices)
                correct_words = quote.split()

                word_count = len(correct_words)  # very crude definition of a word
                correct_word_count = 0

                for index in range(len(correct_words)):
                    if words[index] == correct_words[index]:
                        correct_word_count += 1

                # one line (y + 1) left as a visual break
                stdscr.addstr(y + 2, 0, f"Adjusted WPM: {correct_word_count * minute_factor:.2f}")
                stdscr.addstr(y + 3, 0, f"Accuracy: {correct_word_count / word_count:.2%}")
                stdscr.addstr(y + 5, 0, "Press ENTER to continue...")
                start_time = None

            continue

        # first time the user enters a character
        if not start_time:
            start_time = time.time()  # initialize the timer

        # on backspace, correct the previous character and move the cursor back
        if is_backspace(current_key):
            y, x = stdscr.getyx()
            current_cursor_index = coords(stdscr, y, x - 1)
            y, x = coords(stdscr, current_cursor_index)
            stdscr.addch(y, x, output[current_cursor_index])
            stdscr.move(y, x)

        # in all other cases, print what the user input
        else:
            stdscr.addch(current_key)


if __name__ == "__main__":
    sys.exit(curses.wrapper(main))
