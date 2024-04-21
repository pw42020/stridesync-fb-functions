"""
Description
-----------
This script filters the raw data from the run data file and saves the filtered data to a new file.
It uses previous run data to create a new run with interpolated data points to increase the frame rate
to 30 frames per second, and then filters the data using a Kallman filter to n=10 in order to
smooth the data and help against possible noise or acceleration issues in the IMU.


Author
------
Patrick Walsh

Notes
-----
*.run files are in the form of csv's with the following columns:
l_shank_x,l_shank_y,l_shank_z,l_thigh_x,l_thigh_y,l_thigh_z,r_shank_x,r_shank_y,r_shank_z,r_thigh_x,r_thigh_y,r_thigh_z
"""

import sys
import csv
from typing import Final
from typing import Optional

KALLMAN_FILTER_N: Final[int] = 4


def filter_run_data(run_file: str, output_file: str) -> None:
    """
    Filters the raw data from the run data file and saves the filtered data to a new file.

    Parameters
    ----------
    run_file : str
        The file path of the raw run data file.
    output_file : str
        The file path of the output file to save the filtered data to.

    Returns
    -------
    None
    """
    previous_lines: list[dict[str, str]] = []
    with open(run_file, "r") as file:
        print("Reading run data...")
        # n_lines = len(file.readlines())
        RUN_DATA: Final[csv.DictReader] = csv.DictReader(file, delimiter=",")
        # n_lines: int = sum(1 for row in RUN_DATA)
        # print(n_lines)
        # for row in RUN_DATA:
        #     print(row['l_shank_x'])
        # RUN_DATA_LIST = list(RUN_DATA)
        new_values: dict[str, str] = {}
        with open(output_file, "w") as output:
            print("Writing filtered run data...")
            output.write(
                "l_shank_x,l_shank_y,l_shank_z,l_thigh_x,l_thigh_y,l_thigh_z,r_shank_x,r_shank_y,r_shank_z,r_thigh_x,r_thigh_y,r_thigh_z\n"
            )
            for i, row in enumerate(RUN_DATA):
                print(row["l_shank_x"])
                # interpolate the values to 30 fps and filter on the newly interpolated values
                if len(previous_lines) != 0:
                    interpolated_values: dict[str, str] = interpolate_to_30_fps(
                        previous_line=previous_lines, current_line=row, it=i
                    )
                else:
                    interpolated_values = row
                new_values: dict[str, str] = get_kallman_values(
                    previous_lines=previous_lines, current_line=interpolated_values
                )
                output.write(",".join(new_values.values()) + "\n")
                if len(previous_lines) >= KALLMAN_FILTER_N:
                    previous_lines.append(interpolated_values)
                    previous_lines.pop(0)

                # get new kallman filter values for previous line
                new_values: dict[str, str] = {}
                if len(previous_lines) != 0:
                    new_values: dict[str, str] = get_kallman_values(
                        previous_lines=previous_lines, current_line=row
                    )
                    new_values = row
                else:
                    new_values = row
                if len(previous_lines) >= KALLMAN_FILTER_N:
                    previous_lines.append(new_values)
                    previous_lines.pop(0)
                output.write(",".join(new_values.values()) + "\n")


def interpolate_to_30_fps(
    *, previous_line: dict[str, str], current_line: dict[str, str], it: int
) -> dict:
    """
    Interpolates the run data to 30 frames per second.

    Parameters
    ----------
    run_data : dict
        The raw run data.

    Returns
    -------
    dict
        The interpolated run data.
    """
    keys: list[str] = list(current_line.keys())
    new_values: dict[str, str] = {}
    for key in keys:
        # average the values of the current frame and the next frame
        if previous_line[key] != "" and current_line[key] != "":
            new_values[key] = str(
                (float(previous_line[key]) + float(current_line[key])) / 2
            )
        else:
            print(f"Error: Missing value in frame {it} or {it + 1}")
    return new_values


def get_kallman_values(
    *, previous_lines: list[dict[str, str]], current_line: dict[str, str]
) -> dict:
    """
    Returns the Kallman filter values for the run data.

    Returns
    -------
    dict
        The Kallman filter values.
    """
    keys: list[str] = list(current_line.keys())
    new_values: dict[str, str] = {}

    for key in keys:
        new_values[key] = current_line[key]
        # if the value is not empty, add it to the sum
        for it, line in enumerate(previous_lines[::-1]):
            alpha: float = 1 / (it + 1)
            if line[key] != "":
                # loop through the number of frames to go back
                new_values[key] += str(
                    (alpha) * (float(new_values[key]) - float(line[key]))
                )
            else:
                print(f"Error: Missing value in frame {it}")
        # if there are values to interpolate, interpolate the value
    return new_values


if __name__ == "__main__":
    run_file: str = sys.argv[1]
    output_file: str = sys.argv[2]
    filter_run_data(run_file, output_file)
